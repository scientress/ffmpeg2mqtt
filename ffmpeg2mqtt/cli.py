import asyncio
import logging
import os
import sys
from argparse import ArgumentParser

from ffmpeg2mqtt.cleaner import ProgressFileCleaner
from ffmpeg2mqtt.mqtt import MQTTSender
from ffmpeg2mqtt.watcher import Watcher

logger = logging.getLogger('ffmpeg2mqtt')
stdout_log_handler = logging.StreamHandler(sys.stdout)
stdout_log_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(stdout_log_handler)

def cli():
    parser = ArgumentParser(description='stream ffmpeg progress to mqtt')
    parser.add_argument('-w', '--watch-path', type=str, default='/run/ffmpeg',
                        help='watch for ffmpeg process files in this path')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='enable debug logging')
    parser.add_argument('-x', '--expire', type=int, default=60,
                        help='Expire progress files after x seconds. Set to 0 to disable.')
    parser.add_argument('-m', '--host', help='MQTT server hostname')
    parser.add_argument('--port', type=int, help='MQTT server port. Defaults to 1883 or 8883 (TLS).')
    parser.add_argument('-t', '--tls', action='store_true', default=True, help='use MQTT over TLS')
    parser.add_argument('-u', '--username', help='MQTT username')
    parser.add_argument('-p', '--password', help='MQTT password')
    parser.add_argument('-i', '--mqtt_interval', type=int, default=5,
                        help='Interval to send progress via MQTT')
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    asyncio.run(main(args))


async def main(args):

    mqtt_host = os.environ.get('FFMPEG2MQTT_HOST', args.host)
    mqtt_username = os.environ.get('FFMPEG2MQTT_USER', args.username)
    mqtt_password = os.environ.get('FFMPEG2MQTT_PASSWORD', args.password)

    if not mqtt_host:
        print('MQTT Host must be set', file=sys.stderr)
        exit(1)

    watcher = Watcher(args.watch_path)
    sender = MQTTSender(watcher, mqtt_host, username=mqtt_username, password=mqtt_password, tls=args.tls,
                        port=args.port, interval=args.mqtt_interval)
    cleaner = ProgressFileCleaner(watcher)

    async with asyncio.TaskGroup() as tg:
        watch_task = tg.create_task(watcher.watch())
        send_task = tg.create_task(sender.run())
        cleanup_task = tg.create_task(cleaner.run())
