# FFMPEG2MQTT

This tool watches a folder for ffmpeg progress files and sends their serialized content via MQTT

WIP

## Install

```shell
# create a virtualenv
python -m venv .venv
# install the package (currently only via git, PyPi is WIP)
pip install https://github.com/scientress/ffmpeg2mqtt.git
```

## Usage

Run ffmpeg encoding tasks with the option `-progress /run/ffmpeg/{jobname}.txt`.
jobname should be a uniq identifier. We use a uuid4.

The only required config option is the MQTT Hostname.
It can be set via a command line argument or via an environment variable.

You can run the tool like this:
```shell
ffmpeg2mqtt -m test.mosquitto.org
```

## Configuration

Most config options are set via the command line.

```
ffmpeg2mqtt --help
usage: ffmpeg2mqtt [-h] [-w WATCH_PATH] [-d] [-x EXPIRE] [-m HOST] [--port PORT] [-s] [-u USERNAME] [-p PASSWORD] [-t TOPIC] [-i MQTT_INTERVAL]

stream ffmpeg progress to mqtt

options:
  -h, --help            show this help message and exit
  -w WATCH_PATH, --watch-path WATCH_PATH
                        watch for ffmpeg process files in this path
  -d, --debug           enable debug logging
  -x EXPIRE, --expire EXPIRE
                        Expire progress files after x seconds. Set to 0 to disable.
  -m HOST, --host HOST  MQTT server hostname
  --port PORT           MQTT server port. Defaults to 1883 or 8883 (TLS).
  -s, --tls             use MQTT over TLS
  -u USERNAME, --username USERNAME
                        MQTT username
  -p PASSWORD, --password PASSWORD
                        MQTT password
  -t TOPIC, --topic TOPIC
                        MQTT topic template
  -i MQTT_INTERVAL, --mqtt_interval MQTT_INTERVAL
                        Interval to send progress via MQTT
```

Additionally there are these environment variables:
* `FFMPEG2MQTT_HOST`
* `FFMPEG2MQTT_USER`
* `FFMPEG2MQTT_PASSWORD`