import logging
import os
from pathlib import Path
from typing import MutableSequence, Union
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name


logger = logging.getLogger(__name__)


class DictParser():
    """Parser for dictionaries in C++ dictionary format, as well as JSON and XML

    DictParser is a convenience class.
    Its parse() method combines the otherwise atomic operations
    of DictReader.read() and DictWriter.write() in one chunk:
        1: parsed_dict = DictReader.read(source_file)
        2: DictWriter.write(parsed_dict, target_file, mode='a')
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
        scope: MutableSequence[str] = None,
        output: str = None,
    ) -> Union[CppDict, None]:
        """Parses a dictionary file and saves it with prefix 'parsed.'

        parse() combines the otherwise atomic operations
        of DictReader.read() and DictWriter.write() in one chunk:
            1: parsed_dict = DictReader.read(source_file)
            2: DictWriter.write(parsed_dict, target_file, mode='a')

        The parsed dict is saved with prefix 'parsed.'
        Example: Parsing source file 'xyz' will result in parsed file 'parsed.xyz' being generated.

        The parsed dict will by default be written in C++ dictionary format.
        Optionally, output format can be changed to JSON, XML and OpenFOAM.

        :param source_file: name of the dict file to be parsed
        :type source_file: Union[str, os.PathLike[str]]
        :param includes: merge sub-dicts being referenced through #include directives, defaults to True
        :type includes: bool, optional
        :param mode: append to output file ('a') or overwrite output file ('w'), defaults to 'w'
        :type mode: str, optional
        :param order: sort the parsed dict, defaults to False
        :type order: bool, optional
        :param comments: writes comments to output file, defaults to True
        :type comments: bool, optional
        :param scope: optionally specifies a scope the dict will be reduced to after parsing.'scope' can be EMPTY, a 'STRING' or a list of strings ['STRING1', 'STRING2'], defaults to None
        :type scope: MutableSequence[str], optional
        :param output: optional format of the output file. Choices are 'cpp', 'foam', 'xml' and 'json'., defaults to None
        :type output: str, optional
        :return: the parsed dict
        :rtype: Union[CppDict, None]
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)

        # Check whether source file exists
        if not source_file.is_file():
            logger.error(f"DictParser: File {source_file} not found.")
            return None

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
        # Save the parsed dict as a C++ dictionary
        DictWriter.write(
            source_dict=parsed_dict,
            target_file=target_file,
            mode=mode,
            order=order,
        )

        logger.info(f"Successfully parsed {source_file} and saved as {target_file}.")

        return parsed_dict
