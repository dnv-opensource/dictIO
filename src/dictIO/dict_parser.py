"""DictParser class for parsing and translating dictionaries from and to dictIO native file format, as well as JSON and XML."""  # noqa: E501

import logging
import os
from collections.abc import MutableSequence
from pathlib import Path
from typing import Any

from dictIO import DictReader, DictWriter, SDict, create_target_file_name
from dictIO.types import TKey

__all__: list[str] = ["DictParser"]

logger: logging.Logger = logging.getLogger(__name__)


class DictParser:
    """Parser for dictionaries in dictIO native file format, as well as JSON and XML.

    DictParser is a convenience class.
    DictParser.parse() combines the operations of DictReader.read() and DictWriter.write() .
    """

    def __init__(self) -> None:
        """Initialize a dictionary parser."""
        return

    @staticmethod
    def parse(
        source_file: str | os.PathLike[str],
        *,
        includes: bool = True,
        mode: str = "w",
        order: bool = False,
        comments: bool = True,
        scope: MutableSequence[TKey] | None = None,
        output: str | None = None,
    ) -> SDict[Any, Any] | None:
        """Parse a dictionary file and save it with prefix 'parsed.'.

        This convenience method combines `DictReader.read` and
        `DictWriter.write`.

        The parsed output is written with the `parsed.` prefix. For example,
        parsing `xyz` creates `parsed.xyz`. Output uses dictIO's native format
        by default; JSON, XML, and OpenFOAM formats are also supported.

        Args:
            source_file: Dictionary file to parse.
            includes: Whether to merge sub-dictionaries referenced by include
                directives. Defaults to `True`.
            mode: Whether to append (`"a"`) to an existing output file or
                overwrite it (`"w"`). Defaults to `"w"`.
            order: Whether to sort the parsed dictionary. Defaults to `False`.
            comments: Whether to write comments to the output file. Defaults
                to `True`.
            scope: Keys to retain after parsing. If `None`, do not reduce the
                dictionary by scope. Defaults to `None`.
            output: Output format (`"cpp"`, `"foam"`, `"xml"`, or `"json"`).
                If `None`, infer the format from the default behavior.
                Defaults to `None`.

        Returns:
            Parsed dictionary, or `None` if the writer does not return a
            parsed dictionary.

        Raises:
            FileNotFoundError: If `source_file` does not exist.
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f"DictParser: File {source_file} not found.")
            raise FileNotFoundError(source_file)

        logger.info(f"Parse {source_file}..")

        # Read (parse) the dict file
        parsed_dict = DictReader.read(
            source_file=source_file,
            includes=includes,
            order=order,
            comments=comments,
            scope=scope,
        )
        # Create filename for the parsed dict
        target_file = create_target_file_name(
            source_file=source_file,
            prefix="parsed",
            scope=scope,
            output=output,
        )
        # Save the parsed dict as a default dict file
        DictWriter.write(
            source_dict=parsed_dict,
            target_file=target_file,
            mode=mode,
            order=order,
        )

        logger.info(f"Successfully parsed {source_file} and saved as {target_file}.")

        return parsed_dict
