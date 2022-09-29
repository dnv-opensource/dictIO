import os
import errno

from pathlib import Path
from typing import List, Sequence, Set, Tuple


__all__ = ['silent_remove', 'find_highest_common_root_folder']


def silent_remove(file: Path):
    try:
        os.remove(file)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise   # re-raise exception if a different error occurred


def find_highest_common_root_folder(paths: Sequence[Path]) -> Path:
    """Determines the highest common root folder among the passed in paths.

    Parameters
    ----------
    paths : Sequence[Path]
        A sequence of path objects. Can be files or folders, or both.

    Returns
    -------
    Path
        The highest common root folder among the passed in paths.

    Raises
    ------
    ValueError
        If argument 'paths' is empty or if the passed in paths do not share a common root folder.
    """

    if not paths:
        raise ValueError("argument 'paths' is empty.")

    folders: List[Path] = list(paths)
    for path in paths:
        _path: Path = path.resolve()
        _folder: Path = _path.parent if _path.suffix else _path
        folders.append(_folder.absolute())

    if len(folders) == 1:
        return folders[0]

    # Find highest common root folder
    folders_as_parts: List[Tuple[str]] = [
        folder.parts for folder in folders
    ]
    folders_as_parts.sort(key=lambda x: len(x), reverse=True)
    longest_folder_as_parts: Tuple[str] = folders_as_parts[0]
    all_other_folders_as_parts: List[Tuple[str]] = folders_as_parts[1:]
    common_parts: Set[str] = set(longest_folder_as_parts).intersection(
        *[set(_tuple) for _tuple in all_other_folders_as_parts]
    )
    folders_as_parts.sort(key=lambda x: len(x), reverse=False)
    shortest_folder_as_parts: Tuple[str] = folders_as_parts[0]
    if common_root_folder_as_parts := tuple(part for part in shortest_folder_as_parts if part in common_parts):
        return Path(*common_root_folder_as_parts)
    else:
        raise ValueError('The passed in paths do not share a common root folder.')
