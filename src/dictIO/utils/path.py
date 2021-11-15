import os
import errno

from pathlib import Path


__all__ = ['silent_remove']


def silent_remove(file: Path):
    try:
        os.remove(file)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise   # re-raise exception if a different error occurred
