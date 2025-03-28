import logging
import time
from pathlib import Path

from asyncinotify import Inotify, Mask
from .parser import ProgressFile

logger = logging.getLogger(__name__)

class Watcher:
    def __init__(self, path: Path):
        self.path = path
        self.files: dict[str, ProgressFile] = dict()

    async def watch(self):
        with Inotify() as inotify:
            # setup watcher
            logger.info(f'setting up watcher for "{self.path}')
            inotify.add_watch(self.path, Mask.CREATE | Mask.MODIFY)
            # Iterate events forever, yielding them one at a time
            async for event in inotify:
                filename = event.path.name
                if event.mask == Mask.CREATE or filename not in self.files:
                    logger.info(f'watching new progress file {event.path.name}')
                    self.files[filename] = ProgressFile(event.path)
                if event.mask == Mask.MODIFY:
                    logger.debug(f'file changed: {filename}')
                    self.files[filename].last_modified = time.time()
                progress = self.files[filename].read_progress()
                logger.debug(progress)
