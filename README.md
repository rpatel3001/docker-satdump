# docker-satdump
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/rpatel3001/docker-satdump/deploy.yml?branch=master)](https://github.com/rpatel3001/docker-satdump/actions/workflows/deploy.yml)
[![Discord](https://img.shields.io/discord/734090820684349521)](https://discord.gg/sTf9uYF)

A Docker image with satdump installed. Currently it runs an arbitrary command on startup, but that will change in the future.

There is a python script also run at startup which takes the satdump UDP JSON messages and reformats them as acarshub compatible JSON.

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

## Docker Compose

```
version: "3"

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
      - RUN_CMD=satdump live inmarsat_aero_6 /tmp/satdump_out --source rtltcp --ip_address 10.0.0.114 --port 7373 --gain 49 --samplerate 1.536e6 --frequency 1545.6e6 --multi_vfo /vfo.json 2>&1 | grep -v "Invalid CRC!"
#      - RUN_CMD=satdump live inmarsat_aero_6 /tmp/satdump_out --source rtlsdr --source_id 0 --gain 49 --samplerate 1.536e6 --frequency 1545.6e6 --multi_vfo /vfo.json 2>&1 | grep -v "Invalid CRC!"

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

The above setup is intended to decode Inmarsat 4F3 98W from an rtl_tcp stream at 10.0.0.114:7373. To directly use an RTL-SDR instead, uncomment the `cgroup` and `/dev` lines and switch which `RUN_CMD` line is commented. You may need to change the `--source_id` if you have more than one RTL-SDR.

The two files `vfo.json` and `Inmarsat.json`, examples below, need to be created before running the contianer for the first time.

`vfo.json` contains the frequencies and decoder pipelines being used. You'll note that they are not exact due to an approximately 3.8 kHz frequency error in my RTL-SDR. You will likely need to look at a waterfall and adjust these values based on your specific device. They may even need tuning as ambient temperature or the tuned center frequency changes. If all channels require the same offset, you can apply the offset in the satdump --frequency argument instead of adjusting the VFO frequencies. I have since bought a Nooelec SMArt XTR which does not require any offset.

```
{
        "vfo1": {
                "frequency": 1545018800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo2": {
                "frequency": 1545023800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo3": {
                "frequency": 1545028800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo4": {
                "frequency": 1545033800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo5": {
                "frequency": 1545038800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo6": {
                "frequency": 1545043800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo7": {
                "frequency": 1545053800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo8": {
                "frequency": 1545063800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo9": {
                "frequency": 1545068800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo10": {
                "frequency": 1545078800,
                "pipeline": "inmarsat_aero_12"
        },
        "vfo11": {
                "frequency": 1545083800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo12": {
                "frequency": 1545088800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo13": {
                "frequency": 1545093800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo14": {
                "frequency": 1545103800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo15": {
                "frequency": 1545113800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo16": {
                "frequency": 1545173800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo18": {
                "frequency": 1545178800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo19": {
                "frequency": 1545198800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo20": {
                "frequency": 1545208800,
                "pipeline": "inmarsat_aero_6"
        },
        "vfo21": {
                "frequency": 1546008800,
                "pipeline": "inmarsat_aero_105"
        },
        "vfo22": {
                "frequency": 1546023800,
                "pipeline": "inmarsat_aero_105"
        },
        "vfo23": {
                "frequency": 1546066300,
                "pipeline": "inmarsat_aero_105"
        },
        "vfo24": {
                "frequency": 1546081300,
                "pipeline": "inmarsat_aero_105"
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
                    "station_id": "XX-YYY-IMSL-98W-AERO6",
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
                    "station_id": "XX-YYY-IMSL-98W-AERO12",
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
                    "station_id": "XX-YYY-IMSL-98W-AERO105",
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
                    "station_id": "XX-YYY-IMSL-98W-AERO84",
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
