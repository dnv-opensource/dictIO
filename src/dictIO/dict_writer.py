"""DictWriter class for writing dictionaries in dictIO native file format, as well as JSON and XML."""

import logging
import os
import re
from collections.abc import MutableMapping, MutableSequence
from pathlib import Path

from dictIO import Formatter, NativeParser, SDict, order_keys
from dictIO.types import TKey, TValue

__ALL__ = ["DictWriter", "create_target_file_name"]

logger = logging.getLogger(__name__)


class DictWriter:
    """Writer for dictionaries in dictIO native file format, as well as JSON, XML and OpenFoam."""

    def __init__(self) -> None:
        return

    @staticmethod
    def write(
        source_dict: MutableMapping[TKey, TValue],
        target_file: str | os.PathLike[str] | None = None,
        mode: str = "a",
        *,
        order: bool = False,
        formatter: Formatter | None = None,
    ) -> None:
        """Write a dictionary file in dictIO native file format, as well as JSON, XML and OpenFoam.

        Writes a dictIO dict (parameter source_dict of type SDict) to target_file.
        Following file formats are supported and interpreted through target_file's file ending:
        no file ending   ->   dictIO native dict file
        '.cpp'           ->   dictIO native dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file
        Following modes are supported:
        mode = 'a': append to target file. If the existing file contains a dictionary, write() will append the new dict
        to the existing through merging. This is the default behaviour.
        mode = 'w': overwrite target file. The existing file will be overwritten.

        Parameters
        ----------
        source_dict : Union[MutableMapping[TKey, TValue], SDict]
            source dict
        target_file : Union[str, os.PathLike[str], None], optional
            target dict file name, by default None
        mode : str, optional
            append to target file ('a') or overwrite target file ('w'), by default 'a'
        order : bool, optional
            if True, the dict will be sorted before writing, by default False
        formatter : Union[Formatter, None], optional
            formatter to be used, by default None
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
            from dictIO import DictReader

            existing_dict = DictReader.read(target_file, order=order)
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
    scope: MutableSequence[TKey] | None = None,
    output: str | None = None,
) -> Path:
    """Create a well defined target file name.

    Helper function to create a target file name based on the source file name,
    a prefix, a scope and an output format.

    Parameters
    ----------
    source_file : Union[str, os.PathLike[str]]
        source dict file
    prefix : Union[str, None], optional
        prefix to be used, by default None
    scope : Union[MutableSequence[str], None], optional
        scope to be reflected in the target file name, by default None
    output : Union[str, None], optional
        format of the target dict file. Choices are 'cpp', 'foam', 'xml' and 'json', by default None

    Returns
    -------
    Path
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
