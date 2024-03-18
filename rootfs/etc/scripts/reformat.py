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
#  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(host)
  print(f"Connected to JSON output at {host[0]}:{host[1]}")
  while True:
    msg = txq.get()
    sock.sendall(msg.encode(enc))
#    sock.sendto(msg.encode(enc), host)

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

gesLoc = {
    "ANCXFXA": "Anchorage Domestic (USA)",
    "ANCATYA": "Anchorage Oceanic (USA)",
    "AKLCDYA": "Auckland Oceanic (NZ)",
    "BKKGWXA": "Bangkok (Thailand)",
    "BNECAYA": "Brisbane (AUS)",
    "CTUGWYA": "Chengdu (China)",
    "MAACAYA": "Chennai (India)",
    "FUKJJYA": "Fukuoka (Japan)",
    "YQXE2YA": "Gander Oceanic (Canada)",
    "YQXD2YA": "Gander Domestic (Canada)",
    "YQME2YA": "Moncton (Canada)",
    "YULE2YA": "Montreal (Canada)",
    "YYZE2YA": "Toronto (Canada)",
    "YWGE2YA": "Winnipeg (Canada)",
    "YVRE2YA": "Vancouver (Canada)",
    "USADCXA": "USA Domestic (USA)",
    "JNBCAYA": "Johannesburg Oceanic (SA)",
    "KMGGWYA": "Kunming (China)",
    "LHWGWYA": "Lanzhou (China)",
    "MELCAYA": "Melbourne (AUS)",
    "BOMCAYA": "Mumbai (India)",
    "NANCDYA": "Nadi (Fiji)",
    "NYCODYA": "New York Oceanic (USA)",
    "OAKODYA": "Oakland Oceanic (USA)",
    "REKCAYA": "Reykjavik (Iceland)",
    "SMACAYA": "Santa Maria (Portugal)",
    "PIKCPYA": "Shanwick (UK)",
    "SINCDYA": "Singapore",
    "PPTCDYA": "Tahiti (French Polynesia)",
    "UPGCAYA": "Makassar (Indonesia)",
    "NIMCAYA": "Niamey (Niger)",
    "DKRCAYA": "Dakar Oceanic (Senegal)",
    "NKCCAYA": "Dakar Domestic (Senegal)",
    "GVSCAYA": "Sal Oceanic (Cape Verde)",
    "BZVCAYA": "Brazzaville (Congo)",
    "CAICAYA": "Egypt",
    "PAREUYA": "France",
    "MEXCAYA": "Mexico",
    "BKKCAYA": "Thailand",
    "NDJCAYA": "Ndjamena (Chad)",
    "LPAFAYA": "Canarias (Spain)",
    "ALGCAYA": "Alger (Algeria)",
    "SEZCAYA": "Seychelles",
    "LADCAYA": "Angola (Luanda)",
    "ABJCAYA": "Ivory Coast (Abidjan)",
    "TNRCAYA": "Antananarivo (Madagascar)",
    "KRTCAYA": "Khartoum (Sudan)",
    "CCUCAYA": "Kolkata (India)",
    "SNNCPXA": "Shannon (Ireland)",
    "PIKCAYA": "Scottish (UK)",
    "SOUCAYA": "London (UK)",
    "MSTEC7X": "Maastricht (NL)",
    "POSCLYA": "Piarco (Trinidad)",
    "TGUACYA": "Cenamar (Honduras)",
    "CAYCAYA": "Cayenne (French Guiana)",
    "RECOEYA": "Atlantico (Brazil)",
    "SCLCAYA": "Antofagasta (Chile)",
    "GDXE1XA": "Magadan (Russia)",
    "URCE1YA": "Urumqi (China)",
    "RPHIAYA": "Manila (Philippines)",
    "SGNGWXA": "Ho Chi Minh (Vietnam)",
    "RGNCAYA": "Yangon (Myanmar)",
    "SINCXYA": "Singapore",
    "KULCAYA": "Kuala Lumpur (Malaysia)",
    "POMCAYA": "Port Moresby (PG)",
    "DELCAYA": "Delhi (India)",
    "CMBCBYA": "Colombo (Sri Lanka)",
    "MRUCAYA": "Mauritius (Mauritius)",
    "TGUACAY": "Honduras (CENAMER)",
    "MLECAYA": "Male (Maldives)",
    "BDOCAYA": "Bodo Oceanic (Norway)",
    "NBOCAYA": "Kenya (Niarobi)",
    "ACCFAYA": "Gahna (Accra)",
    "BJSGWYA": "Beijing (China)",
    "CAICDYA": "Cairo (Egypt)",
    "CANGWYA": "Guangzhou (China)",
    "CCUCBYA": "Kolkata (India)",
    "CMBCAYA": "Colombo (Sri Lanka)",
    "DDLCVXA": "Bodo (Norway)",
    "GDXGWXA": "Magadan (Russia)",
    "HKGCCYA": "Hong Kong",
    "HRBGWYA": "Harbin (China)",
    "JAKGWXA": "Jakarta (Indonesia)",
    "KANCAYA": "Kano (Nigeria)",
    "KRTCDYA": "Sudan",
    "LISACYA": "Lisboa (Portugal)",
    "LXAGWYA": "Lhasa (China)",
    "MNLCBYA": "Manila (Philippines)",
    "SELCAXH": "Seoul (Korea)",
    "SHAGWYA": "Shanghai (China)",
    "TASCAXH": "Tashkent (Uzbekistan)",
    "ULNGWXA": "Ulan Bataar (Mongolia)",
    "URCGWYA": "Urum-Qi (China)",
    "YEGCDYA": "Edmonton (Canada)",
    "YEGE2YA": "Edmonton (Canada)",
    "SPLATYA": "Amsterdam Schipol (NL)",
    "CDGATYA": "Paris (France)",
    "MGQCAYA": "Ethiopia",
    "FIHCAYA": "Congo",
    "PIKCLYA": "Prestwick Oceanic (UK)",
    "PIKCLXS": "Prestwick Domestic (UK)",
    "DOHATYA": "Doha (Qatar)",
    "MCTASWY": "Muscat (Oman)",
    "JEDAAYA": " ",
    "DXBEGEK": " ",
    "RUHAAYA": " ",
    "BOMCDYA": " ",
    "BJSATYA": " ",
    "MADAAYA": " ",
    "JEDATYA": " ",
    "GVACBYA": " ",
    "DATSAXS": " ",
    "AUHCAYA": " ",
    "BAHCEYA": " ",
    "MADCDYA": " ",
    "AUHABYA": " ",
    "GYDCDYA": " ",
    "HDQOILX": " ",
    "RIOCDYA": " ",
}

json_in = getenv("UDP_IN", "5556")
json_in = json_in.split(";")
json_in = [int(x) for x in json_in]

sbs_out = getenv("JSON_OUT", "acars_router:5550")
#sbs_out = getenv("JSON_OUT", "10.0.0.109:5559")
sbs_out = sbs_out.split(";")
sbs_out = [x.split(":") for x in sbs_out]
sbs_out = [(x,int(y)) for x,y in sbs_out]

rxq = SimpleQueue()
for p in json_in:
  Thread(name=f"rx {p}", target=thread_wrapper, args=(rx_thread, p, rxq)).start()

txqs = []
for i,s in enumerate(sbs_out):
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
    if not data or "ACARS" != data.get("msg_name"):
      continue

    flight = ""
    fl1 = fn1.search(data.get("message", ""))
    if fl1:
      flight = fl1.groupdict().get("fn")
    if not flight:
      fl2 = fn2.search(data.get("message", ""))
      if fl2:
        flight = fl2.groupdict().get("fn")

    if not flight or len(flight) > 9:
      flight = ""

    gsa = data.get("libacars", {}).get("arinc622", {}).get("gs_addr", "")
    if not gsa:
      ges1 = gs1.search(data.get("message", ""))
      if ges1:
        gsa = ges1.groupdict().get("gs")
    from_decoded = f"{gsa}/{gesLoc.get(gsa, '')}"

    out = {
      "freq": 1545.0 if "6" in data.get("source").get("station_id", "") else 1545.075 if "12" in data.get("source").get("station_id", "") else 1546,
      "channel": 0,
      "error": 0,
      "level": 0.0,
      "timestamp": data.get("timestamp"),
      "app": {
        "name": data.get("source", {}).get("app", {}).get("name", ""),
        "ver": data.get("source", {}).get("app", {}).get("version", "")
      },
      "station_id": data.get("source").get("station_id", ""),
      "icao": data.get("signal_unit", {}).get("aes_id", ""),
      "toaddr": data.get("signal_unit", {}).get("aes_id", ""),
      "mode": str(data.get("mode", "")),
      "label": data.get("label", ""),
      "block_id": str(data.get("bi", "")),
      "ack": "",
      "tail": data.get("plane_reg[1:]", ""),
      "text": data.get("message", ""),
      "msgno": str(data.get("signal_unit", {}).get("ref_no", "")),
      "flight": flight,
      "fromaddr": data.get("signal_unit", {}).get("ges_id"),
      "fromaddr_decoded": from_decoded,
      "end": True
    }

    if data.get("libacars", {}).get("arinc622", {}).get("cpdlc"):
        out["decodedText"] = {
                               "decoder": {
                                            "decodedStatus": "partial"
                                          },
                               "formatted": {
                                              "label": data.get("libacars", {}).get("arinc622", {}).get("msg_type", ""),
                                              "value": dumps(data.get("libacars", {}).get("arinc622", {}).get("cpdlc", ""))
                                            }
                             }
    elif data.get("libacars", {}).get("arinc622", {}).get("adsc"):
        out["decodedText"] = {
                               "decoder": {
                                            "decodedStatus": "partial"
                                          },
                               "formatted": {
                                              "label": data.get("libacars", {}).get("arinc622", {}).get("msg_type", ""),
                                              "value": dumps(data.get("libacars", {}).get("arinc622", {}).get("adsc", ""))
                                            }
                             }
    elif data.get("libacars", {}).get("arinc622"):
        out["decodedText"] = {
                               "decoder": {
                                            "decodedStatus": "partial"
                                          },
                               "formatted": {
                                              "label": data.get("libacars", {}).get("arinc622", {}).get("msg_type", ""),
                                              "value": dumps(data.get("libacars", {}).get("arinc622", ""))
                                            }
                             }

    #pprint(out)
    #print()

    for q in txqs:
      q.put(dumps(out)+"\r\n")
  except KeyboardInterrupt:
    exit()
  except BaseException:
    print("Other exception:", file=stderr)
    pprint(data, stream=stderr)
    print(traceback.format_exc(), file=stderr)
    pass
