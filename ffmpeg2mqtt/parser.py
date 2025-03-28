import logging
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, Optional

logger = logging.getLogger(__name__)

ProgressDict = dict[str, str|int|float|dict[str, dict[str, float]]]

@dataclass
class ProgressFile:
    path: Path
    fd: Optional[TextIO] = None
    last_modified: Optional[float] = None
    last_progress: Optional[dict] = None
    last_time_sent: Optional[float] = None
    completed: bool = False

    def __post_init__(self):
        if self.fd is None:
            self.fd = open(self.path, 'r')
        if self.last_modified is None:
            self.update_last_modified()

    def update_last_modified(self):
        self.last_modified = self.path.stat().st_mtime

    @staticmethod
    def parse_progress(progress: list[str]) -> ProgressDict:
        int_fields = {'frame', 'total_size', 'out_time_us', 'out_time_ms', 'dup_frames', 'drop_frames'}
        float_fields = {'fps',}
        parsed = {}
        for line in progress:
            key, value = line.split('=', 1)
            if key in int_fields:
                parsed[key] = int(value)
            elif key in float_fields:
                parsed[key] = float(value)
            elif key.startswith('stream') and key.endswith('q'):
                output, stream = key.removeprefix('stream_').removesuffix('_q').split('_', 1)
                q_dict = parsed.setdefault('q', {}).setdefault(output, {})[stream] = float(value)
            elif key == 'speed':
                parsed[key] = float(value.removesuffix('x'))
            else:
                parsed[key] = value
        return parsed

    def read_progress(self) -> Optional[ProgressDict]:
        # reads progress output and parses the last message
        if self.completed:
            return None
        start = self.fd.tell()
        buffer = previous_buffer = []
        while True:
            pos = self.fd.tell()
            line = self.fd.readline()
            if line == '':
                # eof
                break
            if not line.endswith('\n'):
                # incomplete line
                self.fd.seek(pos)
                break
            buffer.append(line.strip())
            if line.startswith('progress='):
                previous_buffer = buffer
                buffer = []
        if not buffer and not previous_buffer:
            self.fd.seek(start)
            return None
        try:
            progress = self.parse_progress(previous_buffer)
            self.last_progress = progress
            if progress['progress'] == 'end':
                self.completed = True
            return progress
        except (ValueError,) as e:
            logger.exception(f'Can\'t parse progress entry in file "{self.fd.name}".', exc_info=e)

    def serialize(self) -> Optional[ProgressDict]:
        if not self.last_progress:
            return None
        return {
            'job': self.path.name.removesuffix('.txt'),
            'path': str(self.path),
            'host': socket.gethostname(),
            'last_modified': self.last_modified,
            **self.last_progress,
        }