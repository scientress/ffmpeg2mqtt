import asyncio
import json
import logging
import ssl
import time

import aiomqtt

from .watcher import Watcher

logger = logging.getLogger(__name__)


class MQTTSender:

    def __init__(self, watcher: Watcher, hostname, username=None, password=None, tls=True, port=None, interval=5,
                 **kwargs):
        self.watcher = watcher
        if port is None:
            port = 8883 if tls else 1883
        tls_context = ssl.create_default_context() if tls else None
        self.interval = interval

        self.client = aiomqtt.Client(hostname, port=port, username=username, password=password, tls_context=tls_context,
                                     **kwargs)

    async def run(self):
        while True:
            try:
                async with self.client:
                    while True:
                        logger.debug('sending progress states')
                        now = time.time()
                        for name, file in self.watcher.files.items():
                            age = now - file.last_modified
                            if age > 60 or file.completed and age > 2 * self.interval:
                                continue
                            name = name.removesuffix('.txt').replace('/', '_')
                            await self.client.publish(f'voc/ffmpeg/progess/{name}', json.dumps(file.serialize()))
                        await asyncio.sleep(self.interval)
            except aiomqtt.MqttError:
                logger.error(f"Connection lost; Reconnecting in {self.interval} seconds ...")

            await asyncio.sleep(self.interval)
