"""Utility functions for working with paths."""

import logging
import os
from collections.abc import Sequence
from pathlib import Path

__all__: list[str] = ["highest_common_root_folder", "relative_path"]

logger: logging.Logger = logging.getLogger(__name__)


def highest_common_root_folder(paths: Sequence[Path]) -> Path:
    """Return the highest common root folder among the passed in paths.

    Paths with a suffix are treated as files, so their parent directories
    participate in the common-root calculation.

    Args:
        paths: Paths to files or folders.

    Returns:
        The highest common directory shared by all input paths.

    Raises:
        ValueError: If `paths` is empty or the paths do not share a common
            root.
    """
    if not paths:
        raise ValueError("argument 'paths' is empty.")

    folders: list[Path] = []
    for path in paths:
        _path: Path = path.resolve()
        _folder: Path = _path.parent if _path.suffix else _path
        folders.append(_folder.absolute())

    if len(folders) == 1:
        return folders[0]

    # Find highest common root folder
    folders_as_parts: list[tuple[str, ...]] = [folder.parts for folder in folders]
    folders_as_parts.sort(key=len, reverse=False)
    shortest_folder_as_parts: tuple[str, ...] = folders_as_parts[0]
    common_parts: list[str] = []
    for index, part in enumerate(shortest_folder_as_parts):
        if len({folder_as_parts[index] for folder_as_parts in folders_as_parts}) > 1:
            break
        common_parts.append(part)
    if common_parts:
        return Path(*tuple(common_parts))
    raise ValueError("The passed in paths do not share a common root folder.")


def relative_path(from_path: Path, to_path: Path) -> Path:
    """Return the relative path from one path to another.

    First resolve the relative path using `Path.relative_to`; if the target is
    outside the source path, calculate a relative path using the operating
    system path rules.

    Args:
        from_path: Starting path.
        to_path: Target path.

    Returns:
        Path from the starting path to the target path.

    Raises:
        ValueError: If neither path operation can calculate a relative path.
    """
    relative_path: Path
    try:
        relative_path = to_path.relative_to(from_path)
    except ValueError:
        msg = "Resolving relative path failed using pathlib.\nNext try will use os.path instead of pathlib."
        logger.debug(msg)
        try:
            relative_path = Path(os.path.relpath(to_path, from_path))
            msg = "Resolving relative path succeeded using os.path"
            logger.debug(msg)
        except Exception as e:
            raise ValueError("Resolving relative path failed using both pathlib and os.path.") from e

    return relative_path
