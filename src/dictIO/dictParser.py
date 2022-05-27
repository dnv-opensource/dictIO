import logging
import os
from pathlib import Path
from typing import MutableSequence, Union

from dictIO import CppDict, DictReader, DictWriter, create_target_file_name


__ALL__ = ['DictParser']

logger = logging.getLogger(__name__)


class DictParser():
    """Parser for dictionaries in dictIO dict file format, as well as JSON and XML

    DictParser is a convenience class.
    DictParser.parse() combines the operations of DictReader.read() and DictWriter.write() .
    """

    def __init__(self):
        return

    @staticmethod
    def parse(
        source_file: Union[str, os.PathLike[str]],
        includes: bool = True,
        mode: str = 'w',
        order: bool = False,
        comments: bool = True,
        scope: Union[MutableSequence[str], None] = None,
        output: Union[str, None] = None,
    ) -> Union[CppDict, None]:
        """Parses a dictionary file and saves it with prefix 'parsed.'

        DictParser.parse() combines the otherwise atomic operations
        of DictReader.read() and DictWriter.write() in one chunk:

        1: parsed_dict = DictReader.read(source_file)

        2: DictWriter.write(parsed_dict, target_file)

        The parsed dict is saved with prefix 'parsed.'
        Example: Parsing source file 'xyz' will result in parsed file 'parsed.xyz' being generated.

        The parsed dict will by default be written in dictIO's default dict file format.
        Optionally, output format can be changed to JSON, XML and OpenFOAM.

        Parameters
        ----------
        source_file : Union[str, os.PathLike[str]]
            dict file to be parsed
        includes : bool, optional
            merge sub-dicts being referenced through #include directives, by default True
        mode : str, optional
            append to output file ('a') or overwrite output file ('w'), by default 'w'
        order : bool, optional
            sort the parsed dict, by default False
        comments : bool, optional
            writes comments to output file, by default True
        scope : MutableSequence[str], optional
            scope the dict will be reduced to after parsing, by default None
        output : str, optional
            format of the output file. Choices are 'cpp', 'foam', 'xml' and 'json'., by default None

        Returns
        -------
        Union[CppDict, None]
            the parsed dict

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
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
        target_file = create_target_file_name(source_file, 'parsed', scope, output)
        # Save the parsed dict as a default dict file
        DictWriter.write(
            source_dict=parsed_dict,
            target_file=target_file,
            mode=mode,
            order=order,
        )

        logger.info(f"Successfully parsed {source_file} and saved as {target_file}.")

        return parsed_dict
