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
    parser.add_argument('-w', '--watch-path', type=str,
                        help='watch for ffmpeg process files in this path')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='enable debug logging')
    parser.add_argument('-x', '--expire', type=int,
                        help='Expire progress files after x seconds. Set to 0 to disable.')
    parser.add_argument('-m', '--host', help='MQTT server hostname')
    parser.add_argument('--port', type=int, help='MQTT server port. Defaults to 1883 or 8883 (TLS).')
    parser.add_argument('-s', '--tls', action='store_true', help='use MQTT over TLS', default=None)
    parser.add_argument('-u', '--username', help='MQTT username')
    parser.add_argument('-p', '--password', help='MQTT password')
    parser.add_argument('-t', '--topic', help='MQTT topic template')
    parser.add_argument('-i', '--mqtt-interval', type=int, help='Interval to send progress via MQTT')
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    asyncio.run(main(args))


def get_setting(env_var: str, cmd_arg, default=None, convert=None):
    if cmd_arg is not None:
        return cmd_arg
    try:
        env = os.environ[f'FFMPEG2MQTT_{env_var}']
        if convert is not None:
            return convert(env)
        return env
    except KeyError:
        return default

def get_setting_bool(env_var: str, cmd_arg, default=None):
    return get_setting(env_var=env_var, cmd_arg=cmd_arg, default=default,
                       convert=lambda value: True if value.lower() in {'on', 'yes', 'true', '1'} else False)


async def main(args):

    watch_path = get_setting('PATH', args.watch_path, '/run/ffmpeg')
    expire = get_setting('EXPIRE', args.expire, 60, convert=int)
    mqtt_host = get_setting('HOST', args.host)
    mqtt_port = get_setting('PORT', args.port, convert=int)
    mqtt_tls = get_setting_bool('TLS', args.tls, default=True)
    mqtt_username = get_setting('USER', args.username)
    mqtt_password = get_setting('PASSWORD', args.password)
    mqtt_topic = get_setting('TOPIC', args.topic, default='voc/ffmpeg/progress/{job}')
    mqtt_interval = get_setting('INTERVAL', args.mqtt_interval, default=5, convert=int)


    if not mqtt_host:
        print('MQTT Host must be set', file=sys.stderr)
        exit(1)

    watcher = Watcher(watch_path)
    sender = MQTTSender(watcher, mqtt_host, username=mqtt_username, password=mqtt_password, tls=mqtt_tls,
                        port=mqtt_port, topic=mqtt_topic, interval=mqtt_interval)
    cleaner = ProgressFileCleaner(watcher, max_age=expire)

    async with asyncio.TaskGroup() as tg:
        watch_task = tg.create_task(watcher.watch())
        send_task = tg.create_task(sender.run())
        cleanup_task = tg.create_task(cleaner.run())
