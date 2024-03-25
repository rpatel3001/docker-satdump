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
from time import sleep

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

gs1 = compile(r"^\/(?P<gs>\w{7})\.")

while True:
  try:
    raw = rxq.get()
#    print(f"{raw}\n")

    data = loads(raw)
#    if not data or "ACARS" != data.get("msg_name"):
#      continue

    out = data

    try:
      station = data["source"]["station_id"]
      out["source"]["station_id"] = station[:station.rindex("-")]
      out["freq"] = 1545.0 if "6" in station else 1545.075 if "12" in station else 1546.0
    except:
      pass

    if (getenv("LOG_IN_JSON")) or (getenv("LOG_IN_JSON_FILT") and "ACARS" == data.get("msg_name")):
      pprint(data)
      print()
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
