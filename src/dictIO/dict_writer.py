"""DictWriter class for writing dictionaries in dictIO native file format, as well as JSON and XML."""

import logging
import os
import re
from collections.abc import MutableMapping, MutableSequence
from pathlib import Path
from typing import Any, cast

from dictIO import Formatter, NativeParser, SDict, order_keys
from dictIO.types import K, V

__all__ = ["DictWriter", "create_target_file_name"]

logger = logging.getLogger(__name__)


class DictWriter:
    """Writer for dictionaries in dictIO native file format, as well as JSON, XML and OpenFoam."""

    def __init__(self) -> None:
        """Create a writer for dictionary files."""
        return

    @staticmethod
    def write(
        source_dict: MutableMapping[K, V],
        target_file: str | os.PathLike[str] | None = None,
        mode: str = "a",
        *,
        order: bool = False,
        formatter: Formatter | None = None,
    ) -> None:
        """Serialize a dictionary and write it to a file.

        The file format is selected from the target file extension:
        no file ending   ->   dictIO native dict file
        '.cpp'           ->   dictIO native dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file

        In append mode, an existing dictionary is read and merged with
        `source_dict` before writing. In overwrite mode, the target is replaced.

        Args:
            source_dict: Dictionary content to serialize.
            target_file: Target file name. If `None`, infer the target from
                `source_dict`'s source file; if it has no source file, log an
                error and do not write a file. Defaults to `None`.
            mode: `"a"` to merge with an existing target before writing, or `"w"`
                to overwrite it. An unsupported value logs a warning and writes
                without merging. Defaults to `"a"`.
            order: Whether to sort dictionary keys before serialization.
                Defaults to `False`.
            formatter: Formatter to use. If `None`, select one based on the
                target file format. Defaults to `None`.
        """
        # Check arguments
        if mode not in ["a", "w"]:
            logger.warning(
                f"dictWriter.write(): argument 'mode' has invalid value '{mode}'. "
                "Used default mode 'w' instead as fallback."
            )

        # Determine target file name
        if target_file is None:
            if isinstance(source_dict, SDict) and source_dict.source_file:
                target_file = create_target_file_name(source_dict.source_file)
            else:
                logger.error("DictWriter.write(): parameter target_file is missing. No file written.")
                return

        # Make sure target_file argument is of type Path. If not, cast it to Path type.
        target_file = target_file if isinstance(target_file, Path) else Path(target_file)

        # Create formatter
        # If a formatter has been passed to write(), use that.
        # Otherwise choose the parser depending on target_file.
        formatter = formatter or Formatter.get_formatter(target_file)

        # Before writing the dict, doublecheck once again that all of its elements are correctly typed.
        parser = NativeParser()
        parser.parse_values(source_dict)

        # If mode is set to 'a' (append) and target_file exists:
        # Read the existing file and merge the new dict into the existing.
        if mode == "a" and target_file.exists():
            logger.debug(
                f"DictWriter.write(): append mode: Read existing target file {target_file} and merge dict\n"
                f"{source_dict}\n"
                "into it."
            )
            from dictIO import DictReader  # noqa: PLC0415

            existing_dict = cast("SDict[K, V]", DictReader.read(source_file=target_file, order=order))
            existing_dict.merge(source_dict)
            source_dict = existing_dict

        # Order the dict
        if order:
            if isinstance(source_dict, SDict):
                source_dict.order_keys()
            else:
                source_dict = order_keys(source_dict)

        # Create formatted string
        string = formatter.to_string(source_dict)

        # Save formatted string to target_file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with target_file.open(mode="w") as f:
            _ = f.write(string)

        return


def create_target_file_name(
    source_file: str | os.PathLike[str],
    prefix: str | None = None,
    scope: MutableSequence[Any] | None = None,
    output: str | None = None,
) -> Path:
    """Create a well defined target file name.

    Helper function to create a target file name based on the source file name,
    a prefix, a scope and an output format.

    Args:
        source_file: source dict file.
        prefix: Prefix to prepend to the file name. If `None`, do not add a
            prefix. Defaults to `None`.
        scope: Keys to append to the file name. If `None` or empty, do not add a
            scope suffix. Defaults to `None`.
        output: Output format (`cpp`, `foam`, `xml`, or `json`). If `None`,
            preserve the source file extension; unsupported values use `cpp`.
            Defaults to `None`.

    Returns:
        target dict file name
    """
    # Make sure source_file argument is of type Path. If not, cast it to Path type.
    source_file = source_file if isinstance(source_file, Path) else Path(source_file)

    # Split source_file into file name and file ending, if existing
    file_name = source_file.stem
    file_ending = source_file.suffix

    # In case source_file is of pattern parsed.source_file (or, generically: prefix.source_file),
    # and has NO file ending, the stem/suffix approach doesn't work:
    # pathlib will interpret 'parsed' as file name (stem) and '.file_name' as file ending (suffix)
    # Let's catch that case and use a workaround to correct it:
    if str(source_file.stem) in ["parsed", prefix]:
        file_name = source_file.stem + source_file.suffix
        file_ending = ""

    # File name shall contain the scope the parsed dict had been reduced to
    if scope:
        _scope: list[str] = [str(key) for key in scope]
        scope_suffix = "_" + "_".join(_scope)
        file_name += scope_suffix

    # Prepend prefix, but make sure it is contained in the final filename max once.
    if prefix:
        prefix = prefix.removesuffix(".")  # remove trailing '.', if existing
        prefix = f"{prefix}."
        file_name = prefix + re.sub(pattern=f"^{prefix}", repl="", string=file_name)

    # If an output format is specified: Set file ending to match the output format
    if output:
        # limit to formats that are supported by DictWriter
        if output not in ["", "cpp", "foam", "json", "xml"]:
            output = "cpp"
        file_ending = "" if output == "cpp" else f".{output}"

    # Add file ending again
    file_name += file_ending

    # Compose Path object
    file_path = Path(source_file.parent, file_name)

    return file_path
