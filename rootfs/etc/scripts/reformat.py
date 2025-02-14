from copy import deepcopy
from re import compile
import locale
import socket
from sys import stderr
import traceback
from datetime import datetime, timezone
from json import loads, dumps
from os import getenv
from pprint import pprint
import prctl
from queue import SimpleQueue
from threading import Thread, current_thread
from time import sleep, time
from csv import DictReader
import requests

from util import geslookup

#from colorama import Fore

def rx_thread(port, rxq):
  prctl.set_name(f"rx {port}")
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(('', port))
#  rdr = sock2lines(sock)
  print(f"Connected to JSON input on port {port}")
  while True:
#    msg = next(rdr).strip()
    msg = sock.recv(65536)
    if msg:
      rxq.put_nowait(msg)
    else:
      sleep(1)

def tx_thread(host, txq):
  prctl.set_name(f"tx {host[0]}:{host[1]}")
  enc = locale.getpreferredencoding(False)
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#  sock.connect(host)
  print(f"Connected to JSON output at {host[0]}:{host[1]}")
  while True:
    msg = txq.get()
#    sock.sendall(msg.encode(enc))
    sock.sendto(msg.encode(enc), host)

# wrapper to catch exceptions and restart threads
def thread_wrapper(func, *args):
    slp = 10
    while True:
        try:
          print(f"[{current_thread().name}] starting thread")
          func(*args)
        except BrokenPipeError:
          print(f"[{current_thread().name}] pipe broken; restarting thread in {slp} seconds")
        except ConnectionRefusedError:
          print(f"[{current_thread().name}] connection refused; restarting thread in {slp} seconds")
        except StopIteration:
          print(f"[{current_thread().name}] lost connection; restarting thread in {slp} seconds")
        except BaseException as exc:
          print(traceback.format_exc())
          print(f"[{current_thread().name}] exception {type(exc).__name__}; restarting thread in {slp} seconds")
        else:
          print(f"[{current_thread().name}] thread function returned; restarting thread in {slp} seconds")
        sleep(slp)

with open('/opt/airports.csv', encoding='utf-8') as csvfile:
  airports_raw = DictReader(csvfile)
  airports = {}
  for row in airports_raw:
    loc = row["city"]
    if not loc:
      loc = row["state"]
    if loc:
      loc += ", "
    loc += row["country_id"]
    airports[row["code"]] = loc

with open('/opt/citycodes.csv', encoding='utf-8') as csvfile:
  citycodes_raw = DictReader(csvfile)
  citycodes = {}
  for row in citycodes_raw:
    citycodes[row["code"]] = " ".join(row["name"].split()[:-2]) + f", {row['country_id']}"

json_in = getenv("UDP_IN", "5557")
json_in = json_in.split(";")
json_in = [int(x) for x in json_in]

json_out = getenv("JSON_OUT", "acarshub:5557")
json_out = json_out.split(";")
json_out = [x.split(":") for x in json_out]
json_out = [(x,int(y)) for x,y in json_out]

rxq = SimpleQueue()
for p in json_in:
  Thread(name=f"rx {p}", target=thread_wrapper, args=(rx_thread, p, rxq)).start()

txqs = []
for i,s in enumerate(json_out):
  txqs.append(SimpleQueue())
  Thread(name=f"tx {s[0]}:{s[1]}", target=thread_wrapper, args=(tx_thread, s, txqs[-1])).start()

fn1 = compile(r"\/FN(?P<fn>\w+)\/")
fn2 = compile(r"\/FMH(?P<fn>\w+),")

gs1 = compile(r"^(\/|- #\w{2}\/\w{2} )(?P<gs>\w{7})\.")

lastSnr = 0

while True:
  try:
    raw = rxq.get()

    data = loads(raw)
    if data and (getenv("LOG_IN_JSON") or (getenv("LOG_IN_JSON_FILT") and "ACARS" == data.get("msg_name"))):
      pprint(data)
      print()
    if not data or (getenv("OUTPUT_ACARS_ONLY") and "ACARS" != data.get("msg_name")):
      continue

    try:
      if time() - lastSnr > float(getenv("SNR_UPDATE_SEC", 1)):
        lastSnr = time()
        snrjs = {}
        rawsnrjs = requests.get("http://localhost:5000/api").json()
        for k, v in rawsnrjs.items():
          try:
            snrjs[k] = {"ber": rawsnrjs[k]['inmarsat_aero_decoder']['viterbi_ber'],
                        "lock": rawsnrjs[k]['inmarsat_aero_decoder']['correlator_lock'],
                        "freq": rawsnrjs[k]['psk_demod']['freq'],
                        "signal": rawsnrjs[k]['psk_demod']['signal'],
                        "noise": rawsnrjs[k]['psk_demod']['noise'],
                        "peak_snr": rawsnrjs[k]['psk_demod']['peak_snr'],
                        "snr": rawsnrjs[k]['psk_demod']['snr']}
          except KeyError:
            try:
              snrjs[k] = {"ber": rawsnrjs[k]['inmarsat_aero_decoder']['viterbi_ber'],
                          "lock": rawsnrjs[k]['inmarsat_aero_decoder']['correlator_lock'],
#                          "freq": rawsnrjs[k]['sdpsk_demod']['freq'],
                          "signal": rawsnrjs[k]['sdpsk_demod']['signal'],
                          "noise": rawsnrjs[k]['sdpsk_demod']['noise'],
                          "peak_snr": rawsnrjs[k]['sdpsk_demod']['peak_snr'],
                          "snr": rawsnrjs[k]['sdpsk_demod']['snr']}
            except KeyError:
              pass
    except requests.exceptions.ConnectionError:
      pass

    out = deepcopy(data)

    # convert station ID tag to frequency, remove tag
    try:
      if freq := data["source"]["station_id"]:
        out["freq"] = f"{int(freq)/1e6:.3f}"
    except:
      print("Couldn't set freq")
      print(traceback.format_exc())

    try:
      if id := getenv("STATION_ID"):
        out["source"]["station_id"] = id
    except:
      print("Couldn't set station id")
      print(traceback.format_exc())

    try:
      if id := data.get("source", {}).get("station_id"):
        if sigjs := snrjs.get(id):
          if level := sigjs.get("signal"):
            out["level"] = f"{float(level):.1f}"
        else:
          idint = int(id)
          bestk = None
          bestdiff = 1e6
          for k,v in snrjs.items():
            kint = int(k)
            if abs(idint-kint) < bestdiff:
              bestdiff = abs(idint-kint)
              bestk = k
          if bestk and snrjs[k]['signal']:
            print(f"best match for {id} is {bestk}")
            out["level"] = f"{float(snrjs[bestk]['signal']):.1f}"
    except:
      print("Couldn't set level")
      print(traceback.format_exc())

    # try to extract flight number
    flight = ""
    fl1 = fn1.search(data.get("message", ""))
    if fl1:
      flight = fl1.groupdict().get("fn")
    if not flight:
      fl2 = fn2.search(data.get("message", ""))
      if fl2:
        flight = fl2.groupdict().get("fn")

    if flight and len(flight) <= 9:
      out["flight"] = flight

    # try to parse ground station
    gsa = data.get("libacars", {}).get("arinc622", {}).get("gs_addr", "")
    if not gsa:
      ges1 = gs1.search(data.get("message", ""))
      if ges1:
        gsa = ges1.groupdict().get("gs")

    # try to decode ground station
    if gsa:
      fromaddr = gsa
      decoded = geslookup(gsa)
      if not decoded:
        decoded = citycodes.get(gsa[:3])
      if not decoded:
        decoded = airports.get(gsa[:3])
      if decoded:
        fromaddr += f"/{decoded}"
      else:
        print(f"ground station {gsa} not found")
      out["fromaddr_decoded"] = fromaddr

    if (getenv("OUTPUT_ACARS_ONLY") is None or "ACARS" == out.get("msg_name")) and (getenv("OUTPUT_NONEMPTY_ONLY") is None or out.get("message")):
      if (getenv("LOG_OUT_JSON")) or (getenv("LOG_OUT_JSON_FILT") and "ACARS" == out.get("msg_name")):
        pprint(out)
        print()
      for q in txqs:
        q.put(f"{dumps(out)}\r\n")
  except KeyboardInterrupt:
    exit()
  except BaseException:
    print("Other exception:", file=stderr)
    pprint(data, stream=stderr)
    print(traceback.format_exc(), file=stderr)
    pass
