# docker-satdump
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/rpatel3001/docker-satdump/deploy.yml?branch=master)](https://github.com/rpatel3001/docker-satdump/actions/workflows/deploy.yml)
[![Discord](https://img.shields.io/discord/734090820684349521)](https://discord.gg/sTf9uYF)

A Docker image with satdump installed. Currently it runs an arbitrary command on startup, but that may change in the future.

There is a python script also run at startup which enriches the satdump JSON with ground station names, frequency and level information, and more.

Under active development, everything is subject to change without notice.

You can view only ACARS message in the log with:

```
docker logs -f satdump | grep -v "(D)" | grep -v "Table Broadcast" | grep -v "Reserved 0x" | grep -v "Channel" | grep -v "Packet" | grep -v "Progress"
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RUN_CMD`  | The command to run when the container starts. The container will restart when it returns.                                             | Unset |
| `UDP_IN`   | The UDP port for the JSON reformatter to listen for raw satdump JSON on. This is set in udp_sinks sections of the Inmarsat.json file. | `5557` |
| `JSON_OUT` | The UDP `host:port` to forward reformatted JSON messages to.                                                                          | `acarshub:5557` |
| `LOG_RAW`  | Set to any value to log the output of the satdump command to stdout.                                                                  | Unset |
| `LOG_IN_JSON`       | Set to any value to log the JSON output of satdump to stdout.                                                                | Unset |
| `LOG_IN_JSON_FILT`  | Set to any value to log the JSON output of satdump to stdout, after filtering out non-ACARS messages.                        | Unset |
| `LOG_OUT_JSON`      | Set to any value to log the reformatted JSON output to stdout.                                                               | Unset |
| `LOG_OUT_JSON_FILT` | Set to any value to log the reformatted JSON output to stdout, after filtering out non-ACARS messages.                       | Unset |
| `OUTPUT_ACARS_ONLY` | Set to any value to prevent outputting JSON for non-ACARS messages to ease the load on your Acarshub instance a little.      | Unset |
| `OUTPUT_NONEMPTY_ONLY` | Set to any value to prevent outputting JSON for non-ACARS messages as well as ACARS messages with no text field.          | Unset |
| `STATION_ID`           | The station ID to set on output messages.                                                                                 | Unset |
| `SNR_UPDATE_SEC`       | How often to poll the HTTP API to update the VFO signal levels to attach to messages.                                     | `1`   |

## Docker Compose

```
services:
  satdump:
    container_name: satdump
    hostname: satdump
    image: ghcr.io/rpatel3001/docker-satdump:latest
    restart: always
#    device_cgroup_rules:
#      - 'c 189:* rwm'
    volumes:
#      - /dev:/dev:ro
      - ./vfo.json:/vfo.json
      - ./Inmarsat.json:/usr/share/satdump/pipelines/Inmarsat.json
    environment:
      - RUN_CMD=satdump live inmarsat_aero_6 /tmp/satdump_out --source rtltcp --ip_address 10.0.0.114 --port 7373 --gain 49 --samplerate 1.536e6 --frequency 1545.6e6 --multi_vfo /vfo.json --http_server 0.0.0.0:5000 2>&1 | grep -v "Invalid CRC!"
#      - RUN_CMD=satdump live inmarsat_aero_6 /tmp/satdump_out --source rtlsdr --source_id 0 --gain 49 --samplerate 1.536e6 --frequency 1545.6e6 --multi_vfo /vfo.json --http_server 0.0.0.0:5000 2>&1 | grep -v "Invalid CRC!"
      - STATION_ID=XX-YYY-IMSL-98W

  acarshub:
    build: https://github.com/rpatel3001/docker-acarshub.git#inmarsat-L
    container_name: acarshub
    restart: always
    ports:
      - 8000:80
    tmpfs:
      - /database:exec,size=64M
      - /run:exec,size=64M
      - /var/log:size=64M
    environment:
      - TZ=America/New_York
      - ENABLE_IMSL=external

```

The above setup is intended to decode Inmarsat 4F3 at 98W from an rtl_tcp stream at 10.0.0.114:7373. To directly use an RTL-SDR instead, uncomment the `cgroup` and `/dev` lines and switch which `RUN_CMD` line is commented. You may need to change the `--source_id` if you have more than one RTL-SDR.

The two files `vfo.json` and `Inmarsat.json`, examples below, need to be created before running the contianer for the first time.

`vfo.json` contains the frequencies and decoder pipelines being used. You may need to set the frequency to be offset from nominal due to frequency inaccuracies in your RTL-SDR. You will likely need to look at a waterfall and adjust these values based on your specific device. They may even need tuning as ambient temperature or the tuned center frequency changes. If all channels require the same offset, you can apply the offset to the satdump --frequency argument instead of adjusting the VFO frequencies. I started testing with an RTL-SDR Blog V3 that required approximately a 3.8 kHz offset. I have since bought a Nooelec SMArt XTR which does not require any offset.

The VFO name and station_id are set to the frequency value. This is to allow the python script to associate each message with a signal level and frequency, because those items are not included in the JSON output.

```
{
        "1545015000": {
                "frequency": 1545015000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545015000"
                }
        },
        "1545020000": {
                "frequency": 1545020000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545020000"
                }
        },
        "1545025000": {
                "frequency": 1545025000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545025000"
                }
        },
        "1545030000": {
                "frequency": 1545030000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545030000"
                }
        },
        "1545035000": {
                "frequency": 1545035000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545035000"
                }
        },
        "1545040000": {
                "frequency": 1545040000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545040000"
                }
        },
        "1545050000": {
                "frequency": 1545050000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545050000"
                }
        },
        "1545060000": {
                "frequency": 1545060000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545060000"
                }
        },
        "1545065000": {
                "frequency": 1545065000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545065000"
                }
        },
        "1545075000": {
                "frequency": 1545075000,
                "pipeline": "inmarsat_aero_12",
                "parameters": {
                        "station_id": "1545075000"
                }
        },
        "1545080000": {
                "frequency": 1545080000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545080000"
                }
        },
        "1545085000": {
                "frequency": 1545085000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545085000"
                }
        },
        "1545090000": {
                "frequency": 1545090000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545090000"
                }
        },
        "1545100000": {
                "frequency": 1545100000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545100000"
                }
        },
        "1545110000": {
                "frequency": 1545110000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545110000"
                }
        },
        "1545170000": {
                "frequency": 1545170000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545170000"
                }
        },
        "1545175000": {
                "frequency": 1545175000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545175000"
                }
        },
        "1545195000": {
                "frequency": 1545195000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545195000"
                }
        },
        "1545205000": {
                "frequency": 1545205000,
                "pipeline": "inmarsat_aero_6",
                "parameters": {
                        "station_id": "1545205000"
                }
        },
        "1546005000": {
                "frequency": 1546005000,
                "pipeline": "inmarsat_aero_105",
                "parameters": {
                        "station_id": "1546005000"
                }
        },
        "1546020000": {
                "frequency": 1546020000,
                "pipeline": "inmarsat_aero_105",
                "parameters": {
                        "station_id": "1546020000"
                }
        },
        "1546062500": {
                "frequency": 1546062500,
                "pipeline": "inmarsat_aero_105",
                "parameters": {
                        "station_id": "1546062500"
                }
        },
        "1546077500": {
                "frequency": 1546077500,
                "pipeline": "inmarsat_aero_105",
                "parameters": {
                        "station_id": "1546077500"
                }
        }
}
```

`Inmarsat.json` overrides the default settings for each decoder pipeline, including station_id, udp_sink, and save_file. The below file does not save files, sends every decoder pipeline's output to the reformatter script at localhost:5557, and sets a `station_id` based on the pipeline.

```
{
    "inmarsat_std_c": {
        "name": "Inmarsat STD-C",
        "live": true,
        "live_cfg": [
            [
                1,
                0
            ],
            [
                2,
                0
            ],
            [
                3,
                0
            ]
        ],
        "work": {
            "baseband": {},
            "soft": {
                "psk_demod": {
                    "constellation": "bpsk",
                    "agc_rate": 0.1,
                    "symbolrate": 1200,
                    "rrc_taps": 31,
                    "rrc_alpha": 0.6,
                    "pll_bw": 0.03
                }
            },
            "frm": {
                "inmarsat_stdc_decoder": {}
            },
            "msg": {
                "inmarsat_stdc_parser": {
                    "save_files": false,
                    "station_id": "XX-YYY-IMSL-98W-STDC",
                    "udp_sinks": {
                        "test": {
                            "address": "127.0.0.1",
                            "port": 5557
                        }
                    }
                }
            }
        }
    },
    // Aero-P
    "inmarsat_aero_6": {
        "name": "Inmarsat Aero 0.6k (WIP)",
        "live": true,
        "live_cfg": [
            [
                1,
                0
            ],
            [
                2,
                0
            ],
            [
                3,
                0
            ]
        ],
        "work": {
            "baseband": {},
            "soft": {
                "sdpsk_demod": {
                    "symbolrate": 600,
                    "rrc_alpha": 0.4
                }
            },
            "frm": {
                "inmarsat_aero_decoder": {
                    "oqpsk": false,
                    "dummy_bits": 0,
                    "inter_cols": 6,
                    "inter_blocks": 3
                }
            },
            "msg": {
                "inmarsat_aero_parser": {
                    "save_files": false,
                    "udp_sinks": {
                        "test": {
                            "address": "127.0.0.1",
                            "port": 5557
                        }
                    }
                }
            }
        }
    },
    "inmarsat_aero_12": {
        "name": "Inmarsat Aero 1.2k (WIP)",
        "live": true,
        "live_cfg": [
            [
                1,
                0
            ],
            [
                2,
                0
            ],
            [
                3,
                0
            ]
        ],
        "work": {
            "baseband": {},
            "soft": {
                "sdpsk_demod": {
                    "symbolrate": 1200,
                    "rrc_alpha": 0.4
                }
            },
            "frm": {
                "inmarsat_aero_decoder": {
                    "oqpsk": false,
                    "dummy_bits": 0,
                    "inter_cols": 9,
                    "inter_blocks": 2
                }
            },
            "msg": {
                "inmarsat_aero_parser": {
                    "save_files": false,
                    "udp_sinks": {
                        "test": {
                            "address": "127.0.0.1",
                            "port": 5557
                        }
                    }
                }
            }
        }
    },
    "inmarsat_aero_105": {
        "name": "Inmarsat Aero 10.5k (WIP)",
        "live": true,
        "live_cfg": [
            [
                1,
                0
            ],
            [
                2,
                0
            ],
            [
                3,
                0
            ]
        ],
        "work": {
            "baseband": {},
            "soft": {
                "psk_demod": {
                    "constellation": "oqpsk",
                    "agc_rate": 0.2,
                    "symbolrate": 5.25e3, //10.5e3,
                    "rrc_alpha": 1.0,
                    "pll_bw": 0.01
                }
            },
            "frm": {
                "inmarsat_aero_decoder": {
                    "oqpsk": true,
                    "dummy_bits": 178,
                    "inter_cols": 78,
                    "inter_blocks": 1
                }
            },
            "msg": {
                "inmarsat_aero_parser": {
                    "save_files": false,
                    "udp_sinks": {
                        "test": {
                            "address": "127.0.0.1",
                            "port": 5557
                        }
                    }
                }
            }
        }
    },
    // Aero-C
    "inmarsat_aero_84": {
        "name": "Inmarsat Aero 8.4k",
        "live": true,
        "live_cfg": [
            [
                1,
                0
            ],
            [
                2,
                0
            ],
            [
                3,
                0
            ]
        ],
        "work": {
            "baseband": {},
            "soft": {
                "psk_demod": {
                    "constellation": "oqpsk",
                    "agc_rate": 0.2,
                    "symbolrate": 4.2e3,
                    "rrc_alpha": 1.0,
                    "pll_bw": 0.01
                }
            },
            "frm": {
                "inmarsat_aero_decoder": {
                    "is_c": true,
                    "oqpsk": true,
                    "dummy_bits": 0,
                    "inter_cols": 4,
                    "inter_blocks": 16,
                    "ber_thresold": 0.25
                }
            },
            "msg": {
                "inmarsat_aero_parser": {
                    "is_c": true,
                    "save_files": false,
                    "udp_sinks": {
                        "test": {
                            "address": "127.0.0.1",
                            "port": 5557
                        }
                    }
                }
            }
        }
    }
}
```
