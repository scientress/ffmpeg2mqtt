import asyncio
import logging
import time

from ffmpeg2mqtt.watcher import Watcher

logger = logging.getLogger(__name__)


class ProgressFileCleaner():
    def __init__(self, watcher: Watcher, max_age=60, interval=10):
        self.watcher = watcher
        self.max_age = max_age
        self.interval = interval

    async def run(self):
        while True:
            logger.debug('cleaning up progress files')
            now = time.time()
            for name in list(self.watcher.files.keys()):
                file = self.watcher.files[name]
                age = now - file.last_modified
                if age > self.max_age:
                    logger.info(f'expiring progress file: {name}')
                    file.fd.close()
                    file.path.unlink()
                    del self.watcher.files[name]
            await asyncio.sleep(self.interval)