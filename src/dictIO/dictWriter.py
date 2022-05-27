import logging
import os
import re
from pathlib import Path
from typing import MutableMapping, MutableSequence, Union

from dictIO import CppDict, CppParser, Formatter, order_keys


__ALL__ = ['DictWriter', 'create_target_file_name']

logger = logging.getLogger(__name__)


class DictWriter():
    """Writer for dictionaries in dictIO dict file format, as well as JSON, XML and OpenFoam
    """

    def __init__(self):
        return

    @staticmethod
    def write(
        source_dict: Union[MutableMapping, CppDict],
        target_file: Union[str, os.PathLike[str], None] = None,
        mode: str = 'a',
        order: bool = False,
        formatter: Union[Formatter, None] = None,
    ):
        """Writes a dictionary file in dictIO dict file format, as well as JSON, XML and OpenFoam.

        Writes a dictIO dict (parameter source_dict of type CppDict) to target_file.
        Following file formats are supported and interpreted through target_file's file ending:
        no file ending   ->   dictIO dict file
        '.cpp'           ->   dictIO dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file
        Following modes are supported:
        mode = 'a': append to target file. If the existing file contains a dictionary, write() will append the new dict to the existing through merging. This is the default behaviour.
        mode = 'w': overwrite target file. The existing file will be overwritten.

        Parameters
        ----------
        source_dict : Union[MutableMapping, CppDict]
            source dict file
        target_file : Union[str, os.PathLike[str], None], optional
            target dict file name, by default None
        mode : str, optional
            append to target file ('a') or overwrite target file ('w'), by default 'a'
        order : bool, optional
            if True, the dict will be sorted before writing, by default False
        formatter : Union[Formatter, None], optional
            formatter to be used, by default None
        """

        # Check argument
        if source_dict is None:
            logger.warning(
                "dictWriter.write(): argument 'source_dict' is missing. No file written."
            )
            return
        if mode not in ['a', 'w']:
            logger.warning(
                f"dictWriter.write(): argument 'mode' has invalid value '{mode}'. Used default mode 'w' instead as fallback."
            )

        # Determine target file name
        if target_file is None:
            if isinstance(source_dict, CppDict) and source_dict.source_file:
                target_file = create_target_file_name(source_dict.source_file)
            else:
                logger.error(
                    'DictWriter.write(): parameter target_file is missing. No file written.'
                )
                return

        # Make sure target_file argument is of type Path. If not, cast it to Path type.
        target_file = target_file if isinstance(target_file, Path) else Path(target_file)

        # Create formatter
        # If a formatter has been passed to write(), use that.
        # Otherwise choose the parser depending on target_file.
        formatter = formatter or Formatter.get_formatter(target_file)

        # Before writing the dict, doublecheck once again that all of its elements are correctly typed.
        parser = CppParser()
        parser.parse_types(source_dict)

        # If mode is set to 'a' (append) and target_file exists:
        # Read the existing file and merge the new dict into the existing.
        if mode == 'a' and target_file.exists():
            logger.debug(
                f"DictWriter.write(): append mode: Read existing target file {target_file} and merge dict \n{source_dict}\ninto it."
            )
            from dictIO import DictReader
            existing_dict = DictReader.read(target_file, order=order)
            existing_dict.merge(source_dict)
            source_dict = existing_dict

        # Order the dict
        if order:
            if isinstance(source_dict, CppDict):
                source_dict.order_keys()
            else:
                source_dict = order_keys(source_dict)

        # Create formatted string
        string = formatter.to_string(source_dict)

        # Save formatted string to target_file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with target_file.open(mode='w') as f:
            f.write(string)

        return


def create_target_file_name(
    source_file: Union[str, os.PathLike[str]],
    prefix: Union[str, None] = None,
    scope: Union[MutableSequence[str], None] = None,
    format: Union[str, None] = None,
) -> Path:                                              # sourcery skip: avoid-builtin-shadow
    """Helper function to create a well defined target file name.

    Parameters
    ----------
    source_file : Union[str, os.PathLike[str]]
        source dict file
    prefix : Union[str, None], optional
        prefix to be used, by default None
    scope : Union[MutableSequence[str], None], optional
        scope to be reflected in the target file name, by default None
    format : Union[str, None], optional
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
    if source_file.stem in ['parsed', prefix]:
        file_name = source_file.stem + source_file.suffix
        file_ending = ''

    # File name shall contain the scope the parsed dict had been reduced to
    if scope:
        scope_suffix = '_' + '_'.join(iter(scope))
        file_name += scope_suffix

    # Prepend prefix, but make sure it is contained in the final filename max once.
    if prefix:
        prefix = prefix.removesuffix('.')   # remove trailing '.', if existing
        prefix = f'{prefix}.'
        file_name = prefix + re.sub(f'^{prefix}', '', file_name)

    # If an output format is specified: Set file ending to match the output format
    if format:
        # limit to formats that are supported by DictWriter
        if format not in ['', 'cpp', 'foam', 'json', 'xml']:
            format = 'cpp'
        file_ending = '' if format == 'cpp' else f'.{format}'

    # Add file ending again
    file_name += file_ending

    # Compose Path object
    file_name = Path(source_file.parent, file_name)

    return file_name
