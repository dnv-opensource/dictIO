import io
import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, MutableMapping, MutableSequence, Type, Union
from xml.dom import minidom
# from lxml.etree import register_namespace
from xml.etree.ElementTree import (Element, SubElement, register_namespace, tostring)

from dictIO import CppDict
from dictIO.utils.counter import BorgCounter


__ALL__ = ['Formatter', 'CppFormatter', 'FoamFormatter', 'JsonFormatter', 'XmlFormatter']

logger = logging.getLogger(__name__)


class Formatter():
    """Abstract Base Class for formatters.

    Formatters serialize a dict into a string applying a specific format.
    """

    def __init__(self):
        self.counter = BorgCounter()

    @classmethod
    def get_formatter(cls, target_file: Union[Path, None] = None):
        """Factory method returning a Formatter instance matching the target file type to be formatted

        Parameters
        ----------
        target_file : Path, optional
            name of the target file to be formatted, by default None

        Returns
        -------
        Formatter
            specific Formatter instance matching the target file type to be formatted
        """
        # Determine the formatter to be applied by a two stage process:

        # 1. If target_file is passed, choose formatter depending on file-ending
        if target_file:
            if target_file.suffix == '.foam':               # .foam -> FoamFormatter  not applicable with xxx.foam, foam dicts are also xxxDict
                return FoamFormatter()
            elif target_file.suffix == '.json':             # .json -> JsonFormatter
                return JsonFormatter()
            elif target_file.suffix in ['.xml', '.ssd']:    # .xml  or  OSP .ssd -> XmlFormatter
                return XmlFormatter()

        # 2. If no target file is passed, return CppFormatter as default / fallback
        return CppFormatter()   # default

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:
        """Creates a string representation of the passed in dict.

        Note: Override this method when implementing a specific Formatter.

        Parameters
        ----------
        dict : Union[MutableMapping, CppDict]
            dict to be formatted

        Returns
        -------
        str
            string representation of the dict
        """
        return ''

    def format_dict(self, arg: Union[MutableMapping, MutableSequence, Any]) -> str:
        """Formats a dict or list object.

        Note: Override this method when implementing a specific Formatter.

        Parameters
        ----------
        arg : Union[MutableMapping, MutableSequence, Any]
            the dict or list to be formatted

        Returns
        -------
        str
            the formatted string representation of the passed in dict or list
        """
        return ''

    def format_type(self, arg: Any) -> str:
        """Formats a single value type (str, int, float, boolean or None)

        Parameters
        ----------
        arg : Any
            the value to be formatted

        Returns
        -------
        str
            the formatted string representation of the passed in value
        """
        # Non-string types:
        # Return the string representation of the type without additional quotes.
        if not isinstance(arg, str):
            if arg is None:
                return self.format_none()
            elif isinstance(arg, bool):
                return self.format_bool(arg)
            elif isinstance(arg, int):
                return self.format_int(arg)
            elif isinstance(arg, float):
                return self.format_float(arg)
            else:
                return str(arg)

        # String type:
        return self.format_string(arg)

    def format_bool(self, arg: bool) -> str:
        """Formats a boolean

        Note: Override this method for specific formatting of booleans when implementing a Formatter.

        Parameters
        ----------
        arg : bool
            the bool value to be formatted

        Returns
        -------
        str
            the formatted string representation of the passed in bool value
        """
        return str(arg)

    def format_int(self, arg: int) -> str:
        """Formats an integer

        Note: Override this method for specific formatting of integers when implementing a Formatter.

        Parameters
        ----------
        arg : int
            the int to be formatted

        Returns
        -------
        str
            the formatted string representation of the passed in int
        """
        return str(arg)

    def format_float(self, arg: float) -> str:
        """Formats a floating point number

        Note: Override this method for specific formatting of floating point numbers when implementing a Formatter.

        Parameters
        ----------
        arg : float
            the float to be formatted

        Returns
        -------
        str
            the formatted string representation of the passed in float
        """
        return str(arg)

    def format_none(self) -> str:
        """Formats None

        Note: Override this method for specific formatting of None when implementing a Formatter.

        Returns
        -------
        str
            the formatted string representation of None
        """
        return str(None)

    def format_string(self, arg: str) -> str:
        """Formats a string

        Parameters
        ----------
        arg : str
            the string to be formatted

        Returns
        -------
        str
            the formatted string
        """
        if re.search(r'[$]', arg):
            if re.search(r'^\$\w[\w\[\]]+$', arg):  # reference
                return self.format_reference_string(arg)
            else:                                   # expression
                return self.format_expression_string(arg)
        elif not arg:                               # empty string
            return self.format_empty_string(arg)
        elif re.search(r'[\s:/\\]', arg):           # contains spaces or path -> complex string
            return self.format_multi_word_string(arg)
        else:                                       # single word string
            return self.format_single_word_string(arg)

    def format_empty_string(self, arg: str) -> str:
        """Formats an empty string

        Note: Override this method for specific formatting of empty strings when implementing a Formatter.

        Parameters
        ----------
        arg : str
            the empty string to be formatted

        Returns
        -------
        str
            the formatted empty string
        """
        return arg

    def format_single_word_string(self, arg: str) -> str:
        """Formats a single word string

        Note: Override this method for specific formatting of single word strings when implementing a Formatter.

        Parameters
        ----------
        arg : str
            the single word string to be formatted

        Returns
        -------
        str
            the formatted single word string
        """
        return arg

    def format_multi_word_string(self, arg: str) -> str:
        """Formats a multi word string

        Note: Override this method for specific formatting of multi word strings when implementing a Formatter.

        Parameters
        ----------
        arg : str
            the multi word string to be formatted

        Returns
        -------
        str
            the formatted multi word string
        """
        return arg

    def format_reference_string(self, arg: str) -> str:
        """Formats a reference

        Note: Override this method for specific formatting of references when implementing a Formatter.

        Parameters
        ----------
        arg : str
            the reference to be formatted

        Returns
        -------
        str
            the formatted reference
        """
        return arg

    def format_expression_string(self, arg: str) -> str:
        """Formats an expression

        Note: Override this method for specific formatting of expressions when implementing a Formatter.

        Parameters
        ----------
        arg : str
            the expression to be formatted

        Returns
        -------
        str
            the formatted expression
        """
        return arg

    def add_single_quotes(self, arg: str) -> str:
        """Adds single quotes to a string

        Leading and trailing single quotes will added to the passed in string
        (i.e. it will be wrapped in single quotes).
        Note: Call this base class method from any specific Formatter implementation
        to easily add single quotes to a string when formatting.

        Parameters
        ----------
        arg : str
            the string to be wrapped in single quotes

        Returns
        -------
        str
            the string wrapped in single quotes
        """
        return '\'' + arg + '\''

    def add_double_quotes(self, arg: str) -> str:
        """Adds double quotes to a string

        Leading and trailing double quotes will added to the passed in string
        (i.e. it will be wrapped in double quotes).
        Note: Call this base class method from any specific Formatter implementation
        to easily add double quotes to a string when formatting.

        Parameters
        ----------
        arg : str
            the string to be wrapped in double quotes

        Returns
        -------
        str
            the string wrapped in double quotes
        """
        return '"' + arg + '"'


class CppFormatter(Formatter):
    """Formatter to serialize a dict into a string in dictIO dict file format
    """

    def __init__(self):
        '''
        Implementation specific default configuration of CppFormatter
        '''
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:                                   # sourcery skip: avoid-builtin-shadow
        """Creates a string representation of the passed in dict in dictIO dict file format.

        Parameters
        ----------
        dict : Union[MutableMapping, CppDict]
            dict to be formatted

        Returns
        -------
        str
            string representation of the dict in dictIO dict file format
        """
        s = super().to_string(dict)

        if not isinstance(dict, CppDict):
            if isinstance(dict, MutableMapping):
                # Turn ordinary dict into CppDict.
                # That way, any ordinary python dict is treated in this function like a CppDict.
                temp_dict = CppDict()
                temp_dict.update(dict)
                dict = deepcopy(temp_dict)
            else:
                logger.error('CppFormatter.to_string(): passed in arg is not of type dict')
                return ''

        # Sort dict in a way that block comment and include statement come first
        original_data = deepcopy(dict.data)
        sorted_data = {}
        for key, element in original_data.items():
            if re.search(r'BLOCKCOMMENT\d{6}', key):
                sorted_data[key] = element
        for key, element in original_data.items():
            if re.search(r'INCLUDE\d{6}', key):
                sorted_data[key] = element
        for key in sorted_data:
            del original_data[key]
        sorted_data |= original_data
        dict.data = sorted_data

        # Create the string representation of the dictionary in its basic structure.
        s += self.format_dict(dict.data)

        # The following elements a CppDict's .data attribute
        # are usually still substituted by placeholders:
        # - Block comments
        # - Include directives
        # - Line comments
        # Next step hence is to resolve and insert these three element types:
        # 1. Block comments
        s = self.insert_block_comments(dict, s)
        # 2. Include directives
        s = self.insert_includes(dict, s)
        # 3. Line comments
        s = self.insert_line_comments(dict, s)

        # Remove trailing spaces (if any)
        s = self.remove_trailing_spaces(s)
        '''
        # Log variables and includes for debugging purposes
        # variables
        variables = dict.variables
        if variables:
            log_message = self.format_dict({'_variables': variables})
            logger.debug(log_message)
        # includes (the paths of all included files)
        includes = dict.includes
        if includes:
            log_message = self.format_dict({'_includes': [j for i, j in includes.values()]})
            logger.debug(log_message)
        '''

        # Return formatted string
        return s

    def format_dict(
        self,
        arg: Union[MutableMapping, MutableSequence, Any],
        tab_len: int = 4,
        level: int = 0,
        sep: str = ' ',
        items_per_line: int = 10,
        end: str = '\n',
        ancestry: Union[Type[MutableMapping], Type[MutableSequence]] = MutableMapping,
    ) -> str:
        """Formats a dict or list object.
        """
        total_indent = 30
        s = str()
        indent = sep * tab_len * level

        # list
        if isinstance(arg, MutableSequence):

            # Opening bracket
            s += self.format_dict('(', level=level, end=end)

            # List items
            first_item_on_this_line = True
            last_item_on_this_line = False

            for index, item in enumerate(arg):

                # nested list
                if isinstance(item, list):
                    # (recursion)
                    s += self.format_dict(
                        item,
                        tab_len=tab_len,
                        level=level + 1,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end,
                        ancestry=MutableSequence,
                    )

                # nested dict
                elif isinstance(item, dict):
                    s += self.format_dict('', level=level + 1, end='\n')
                    s += self.format_dict('{', level=level + 1)
                    s += self.format_dict(
                        item,
                        tab_len=tab_len,
                        level=level + 2,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end
                    )                                   # (recursion)

                    s += self.format_dict('}', level=level + 1)
                    first_item_on_this_line = True

                # single value
                else:
                    value = self.format_type(item)
                    if first_item_on_this_line:
                        # The first item shall be indented by 1 relative to the (absolute) list level
                        item_level = level + 1
                        first_item_on_this_line = False     # (effective with next item)
                    else:
                                                            # each following item is then indented by 1 relative to its predecessor
                        item_level = 1

                    if ((index + 1) % items_per_line == 0) or (index + 1 == len(arg)):
                        last_item_on_this_line = True

                    if last_item_on_this_line:
                        # Add a line ending
                        s += self.format_dict(value, level=item_level, end='\n')    # (recursion)
                        last_item_on_this_line = False                              # (effective with next item)
                        first_item_on_this_line = True                              # (effective with next item)
                    else:
                                                                                    # Do not add a line ending. Instead, add an adjusted number of spaces after the item to make indentation look pretty.
                        s += self.format_dict(
                            f'{value}{sep * max(0, (14 - len(str(value))))}',
                            level=item_level,
                            end=''
                        )                                                           # (recursion)

            # Closing bracket
            # if list (array) is complete, add semicolon
            if ancestry == MutableSequence:
                s += self.format_dict(')', level=level, end=end)
            else:
                s += self.format_dict(');', level=level, end=end)

        # dict
        elif isinstance(arg, MutableMapping):
            for key in arg.keys():

                # nested dict
                if isinstance(arg[key], dict):
                    s += self.format_dict(key, level=level)
                    s += self.format_dict('{', level=level)
                    s += self.format_dict(
                        arg[key],
                        tab_len=tab_len,
                        level=level + 1,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end,
                    )                                   # (recursion)

                    s += self.format_dict('}', level=level)

                # nested list
                elif isinstance(arg[key], list):
                    s += self.format_dict(key, level=level)
                    s += self.format_dict(arg[key], level=level)    # (recursion)

                # key value pair
                else:
                    value = self.format_type(arg[key])
                    s += self.format_dict(
                        f'{key}{sep * max(8, (total_indent - len(key) - tab_len * level))}{value};',
                        level=level
                    )

        # Single item
        # Note: This is the base case. It is reached only through recursion from
        # dict -> key value pair    or from     list -> single value.
        # arg will hence either be a single item from a list, or a key value pair from a dict.
        else:
            string = f'{indent}{arg}{end}'
            s += string

        return s

    def format_bool(self, arg: bool) -> str:
        return str(arg).lower()

    def format_none(self) -> str:
        return 'NULL'

    def format_empty_string(self, arg: str) -> str:
        return self.add_single_quotes(arg)

    def format_multi_word_string(self, arg: str) -> str:
        return self.add_single_quotes(arg)

    def format_expression_string(self, arg: str) -> str:
        return self.add_double_quotes(arg)

    def insert_block_comments(self, dict: CppDict, s: str) -> str:
        """Inserts back all block comments

        Replaces all BLOCKCOMMENT placeholders in s with the actual block_comments saved in dict
        str s is expected to contain the CppDict's block_content containing block comment placeholders to substitute (BLOCKCOMMENT... BLOCKCOMMENT...)
        """

        # Replace all BLOCKCOMMENT placeholders in s with the actual block_comments saved in dict
        block_comments_inserted_so_far = ''
        first_block_comment = True  # MonoFlop, armed
        for key, block_comment in dict.block_comments.items():

            # If this is the first block_comment, make sure it contains the default block comment
            if first_block_comment:
                # if not re.search(r'\s[Cc]\+{2}\s', block_comment):
                #     # block_comment = default_block_comment + str(dict.block_comments[key])
                #     block_comment = default_block_comment + block_comment
                block_comment = self.make_default_block_comment(block_comment)
                first_block_comment = False     # disarm MonoFlop

            # Check whether the current block comment is identical with a block comment that we already inserted earlier
            # (we do not want to insert any doubled block comments)
            if re.search(re.escape(block_comment), block_comments_inserted_so_far):
                block_comment = ''

            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original block_comment.
            search_pattern = r'BLOCKCOMMENT%06i\s+BLOCKCOMMENT%06i;' % (key, key)
            if len(
                re.findall(search_pattern, s)
            ) > 0:                                                                          # if placeholders exist in s that match the key of the current block_comment
                                                                                            # Substitude the placehlder with the actual block_comment
                                                                                            # s.sub(search_pattern, block_comment)
                s = re.sub(search_pattern, re.sub(r'\\', '\\\\\\\\', block_comment), s)     # no comment
                                                                                            # Document which block comments we already inserted.
                block_comments_inserted_so_far += block_comment

        # If no block_comment had been inserted, insert the default block comment
        if block_comments_inserted_so_far == '':
            s = self.make_default_block_comment() + s

        return s

    def make_default_block_comment(self, block_comment: str = '') -> str:
        """Creates the default block comment (header) for files in dictIO dict file format
        """
        # If there is no ' C++ ' contained in block_comment,
        # then insert the C++ default block comment in front:
        # sourcery skip: move-assign
        default_block_comment = (
            '/*---------------------------------*- C++ -*----------------------------------*\\\n'
            'filetype dictionary; coding utf-8; version 0.1; local --; purpose --;\n'
            '\\*----------------------------------------------------------------------------*/\n'
        )
        if not re.search(r'\s[Cc]\+{2}\s', block_comment):
            # block_comment = default_block_comment + str(dict.block_comments[key])
            block_comment = default_block_comment + block_comment
        return block_comment

    def insert_includes(self, cpp_dict: CppDict, s: str) -> str:
        """Inserts back all include directives
        """
        for key, (include_directive, include_file_name, _) in cpp_dict.includes.items():
            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original include directive.
            include_file_name = include_file_name.replace('\\', '\\\\')
            include_file_name = self.format_type(include_file_name)
            include_directive = f'#include {include_file_name}'
            search_pattern = r'INCLUDE%06i\s+INCLUDE%06i;' % (key, key)
            s = re.sub(search_pattern, include_directive, s)

        return s

    def insert_line_comments(self, cpp_dict: CppDict, s: str) -> str:
        """Inserts back all line directives
        """
        for key, line_comment in cpp_dict.line_comments.items():
            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original block_comment.
            search_pattern = r'LINECOMMENT%06i\s+LINECOMMENT%06i;' % (key, key)
            s = re.sub(search_pattern, line_comment, s)

        return s

    def remove_trailing_spaces(self, s: str) -> str:
        """Removes trailing spaces from all lines

        Reads all lines from the passed in string, removes trailing spaces from each line and
        returns a new string with trailing spaces removed.
        """
        stream = io.StringIO(newline=None)
        stream.write(s)
        stream.seek(0)
        ns = str()
        for line in stream.readlines():
            if match := re.search('[\r\n]*$', line):
                line_ending = match[0]
                line_without_ending = line[:len(line) - len(line_ending)]
                line_without_trailingspaces = re.sub(
                    r'\s+$', '', line_without_ending
                ) + line_ending
                ns += line_without_trailingspaces
        return ns


class FoamFormatter(CppFormatter):
    """Formatter to serialize a dict into a string in OpenFOAM dictionary format
    """

    def __init__(self):
        '''
        Implementation specific default configuration of FoamFormatter
        '''
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:
        """Creates a string representation of the passed in dict in OpenFOAM dictionary format.

        Parameters
        ----------
        dict : Union[MutableMapping, CppDict]
            dict to be formatted

        Returns
        -------
        str
            string representation of the dict in OpenFOAM dictionary format
        """

        # Foam dicts are, in contrast to dictIO default dicts, restricted in what they may contain.
        # The dict content is hence reduced to what Foam is able to interpret.
        # Elements that Foam cannot interpret - or would misinterpret - are removed:

        # Remove all dict entries starting with underscore
        def remove_underscore_keys_recursive(dict: MutableMapping):
            keys = list(dict.keys())
            for key in keys:
                if str(key).startswith('_'):
                    del dict[key]
                elif isinstance(dict[key], MutableMapping):
                    remove_underscore_keys_recursive(dict[key])     # recursion
            return

        dict_adapted_for_foam = deepcopy(dict)
        remove_underscore_keys_recursive(dict_adapted_for_foam)

        # Call base class implementation (CppFormatter)
        s = super().to_string(dict_adapted_for_foam)

        # Substitute all remeining single quotes, if any, by double quotes:
        # s = re.sub('\'', '"', s)

        return s

    def format_empty_string(self, arg: str) -> str:
        return self.add_double_quotes(arg)

    def format_multi_word_string(self, arg: str) -> str:
        return self.add_double_quotes(arg)

    def format_expression_string(self, arg: str) -> str:
        return self.add_double_quotes(arg)

    def make_default_block_comment(self, block_comment: str = '') -> str:
        """Creates the default block comment (header) for files in OpenFOAM dictionary format
        """
        # If there is no ' C++ ' and 'OpenFoam' contained in block_comment,
        # then insert the OpenFOAM default block comment in front:
        default_block_comment = (
            '/*--------------------------------*- C++ -*----------------------------------*\\\n'
            '| =========                 |                                                 |\n'
            '| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n'
            '|  \\\\    /   O peration     | Version:  dev                                   |\n'
            '|   \\\\  /    A nd           | Web:      www.OpenFOAM.com                      |\n'
            '|    \\\\/     M anipulation  |                                                 |\n'
            '\\*---------------------------------------------------------------------------*/\n'
            'FoamFile\n'
            '{\n'
            '    version                   2.0;\n'
            '    format                    ascii;\n'
            '    class                     dictionary;\n'
            '    object                    foamDict;\n'
            '}\n'
            '// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n'
        )
        if not re.search(r'\s[Cc]\+{2}\s', block_comment):
            # block_comment = default_block_comment + str(dict.block_comments[key])
            block_comment = default_block_comment + block_comment
        if not re.search(r'OpenFOAM', block_comment):
            block_comment = default_block_comment
        return block_comment


class JsonFormatter(Formatter):
    """Formatter to serialize a dict into a string in JSON dictionary format
    """

    def __init__(self):
        '''
        Implementation specific default configuration of JsonFormatter
        '''
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:
        """Creates a string representation of the passed in dict in JSON dictionary format.

        Parameters
        ----------
        dict : Union[MutableMapping, CppDict]
            dict to be formatted

        Returns
        -------
        str
            string representation of the dict in JSON dictionary format
        """
        # sourcery skip: inline-immediately-returned-variable
        import json

        # For the json dump, we need to distinguish between whether the passed in dict is of type dict or CppDict.
        d = dict.data if isinstance(dict, CppDict) else dict
        # Json dump
        s = json.dumps(
            d,
            skipkeys=True,
            ensure_ascii=True,
            check_circular=True,
            allow_nan=True,
            sort_keys=False,
            indent=4,
            separators=(',', ':'),
        )
        if isinstance(dict, CppDict):
            s = self.insert_includes(dict, s)

        return s

    def insert_includes(self, cpp_dict: CppDict, s: str) -> str:
        """Inserts back all include directives
        """
        for key, (include_directive, include_file_name, _) in cpp_dict.includes.items():
            # Search for the placeholder key in the Json string,
            # and insert back the original include directive.
            # include_file_name = include_file_name.replace('\\', '/')
            include_file_name = include_file_name.replace('\\', '\\\\\\\\')
            include_directive = f'"#include{key:06d}":"{include_file_name}"'
            search_pattern = r'"INCLUDE%06i"\s*:\s*"INCLUDE%06i"' % (key, key)
            s = re.sub(search_pattern, include_directive, s)

        return s


class XmlFormatter(Formatter):
    """Formatter to serialize a dict into a string in xml format

    Defaults:
        namespaces:      'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd' \n
        root tag:        'NOTSPECIFIED' \n
        root attributes: None \n
        indent:          4

    Defaults can be overwritten by adding a subdict '_xmlOpts' to dict,
    containing '_nameSpaces', '_rootTag', '_rootAttributes'.

    Adding a subdict '_attributes' to a subdict inside dict causes the XmlFormatter to write xml attributes.
    In contrast to xml, there are some specialties in dict format what need to be customized:

    | property     | in xml             | sibling in dict |
    | :----------- | :----------------- | :-------------- |
    | general name | root tag           | the file name is the 'root tag' and hence the name of the dict |
    | name         | element name (tag) | sub-dict name (has to be unique) |
    |              | (multiple occurrences allowed due to attributes) | |
    | attributes   | as required | attributes need to be provided in a separate subdict "_attributes" to take action |
    | style        | namespace(s) | style guide, no namespaces (ns can be provided in a subdict "_xmlOpts") |
    """
    ''' <databases>
            <database id='human_resources' type='mysql'>
                <host>localhost</host>
                <user>usrhr</user>
                <pass>jobby</pass>
                <name>consol_hr</name>
            </database>
            <database id='products' type='my_bespoke'>
                <filename>/home/anthony/products.adb</filename>
            </database>
        </databases>
        the above example exlains it best:
        1:  in xml you can have multiple elements by the same name, distinguished by its content
            in dict not, every subdict (element) has to be unique
            only way to implement is giving as list or name it according element1, element2 etc.
        2:  in xml there are attributes, in dict not
            see best explanation and examples for use here https://stackoverflow.com/questions/1096797/should-i-use-elements-or-attributes-in-xml
            in OSP, I have not seen the use of attributes so far
        3: implementing attributes to dict
            PROS:   control the operation on subdicts (handling how reading, writing, sub-setting etc.)
            CONS:   implementation is expensive and many functions have to be touched (are affected)
                    will not be used anyways
                    diminishes the main advantage of producing human readable code
    '''

    def __init__(
        self,
        omit_prefix: bool = True,
        integrate_attributes: bool = True,
        remove_node_numbering: bool = True,
    ):
        '''
        Implementation specific default configuration of XmlFormatter
        '''
        # Invoke base class constructor
        super().__init__()
        # Save default configuration as attributes
        self.omit_prefix = omit_prefix
        self.integrate_attributes = integrate_attributes
        self.remove_node_numbering = remove_node_numbering

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:
        """Creates a string representation of the passed in dict in XML format.

        Parameters
        ----------
        dict : Union[MutableMapping, CppDict]
            dict to be formatted

        Returns
        -------
        str
            string representation of the dict in XML format
        """
        # Default configuration
        namespaces: MutableMapping = {'xs': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'}
        root_tag: str = 'NOTSPECIFIED'
        root_attributes: Union[MutableMapping, None] = None
        indent = ' ' * 4

        # Check whether xml opts are contained in dict.
        # If so, read and use them
        if '_xmlOpts' in dict.keys():
            xml_opts: MutableMapping = dict['_xmlOpts']
            namespaces = xml_opts['_nameSpaces'] if '_nameSpaces' in xml_opts else namespaces
            root_tag = xml_opts['_rootTag'] if '_rootTag' in xml_opts else root_tag
            root_attributes = xml_opts['_rootAttributes'
                                       ] if '_rootAttributes' in xml_opts else root_attributes
            self.remove_node_numbering = xml_opts[
                '_removeNodeNumbering'
            ] if '_removeNodeNumbering' in xml_opts else self.remove_node_numbering

        prefixes: MutableSequence = []
        for prefix, uri in namespaces.items():
            prefixes.append(prefix)
            if prefix == 'None':
                register_namespace('', uri)
            else:
                register_namespace(prefix, uri)
        prefix: str = prefixes[0]

        xsd_uri: str = namespaces[prefixes[0]]

        attributes: MutableMapping = {}
        if root_attributes and isinstance(root_attributes, MutableMapping):
            for key, item in root_attributes.items():
                attributes.update({key: item})

        # self.version = re.sub('(^.*\-|\.xsd$)', '', xsd_uri)
        # attributes.update({'version':self.version})

        # @TODO: Isn't it contradictory to first pass in here the attributes to root_element
        #        but then thereafter ask whether to integrate the attributes?
        root_element = Element('{%s}%s' % (xsd_uri, root_tag), attrib=attributes)
        if self.integrate_attributes:
            # integrate attributes in root element
            root_element.attrib = {k: str(v) for k, v in attributes.items() if str(v) != ''}

        self.populate_into_element(root_element, dict, xsd_uri)

        s = minidom.parseString(tostring(root_element, encoding='UTF-8',
                                         method='xml')).toprettyxml(indent=indent)
        if self.omit_prefix:
            # objectify.deannotate(root, cleanup_namespaces=True)
            query = f"({'|'.join(f'{s}:' for s in prefixes)})"
            s = re.sub(query, '', s)

        return s

    def populate_into_element(
        self,
        element: Element,
        arg: Union[MutableMapping, MutableSequence, Any],
        xsd_uri: Union[str, None] = None,
    ):
        """Populates arg into the XML element node.

        If arg is a dict or list, method will call itself recursively until all nested content within the dict or list
        is populated into nested elements, eventually creating an XML dom.

        Parameters
        ----------
        element : Element
            element which will be populated
        arg : Union[MutableMapping, MutableSequence, Any]
            value to be populated into the element
        xsd_uri : str, optional
            xsd uri, by default None
        """
        # sourcery skip: merge-duplicate-blocks, remove-pass-body, remove-pass-elif, remove-redundant-pass

        # @TODO: LINECOMMENTs not handled yet

        if isinstance(arg, MutableSequence):
            element.text = ' '.join(str(x) for x in arg)

        elif isinstance(arg, MutableMapping):
            child_nodes = list(arg.keys())

            for index, (key, item) in enumerate(arg.items()):

                if re.match('_content', key):
                    # Write back content (from the key-value pair "_content <content>;") into xml node.text
                    # In case of multiline content, do not write it inline between opening and closing tag,
                    # but add a line ending at the beginning and at the end, so that content gets formatted
                    # as an indented text block beween the opening and closing tag.
                    text = str(item)
                    if text not in [None, ''] and len(text.splitlines()) > 1:
                        text = '\n' + text + '\n'
                    element.text = text

                elif self.integrate_attributes and re.match('_attrib', key):
                    # attributes to integrate in node, otherwise leave in content
                    # and remove attribs with empy strings
                    # correct occurence of true false -> de-pythonize for lowercase
                    # if here is more expense needed, we have to revoke the one-liner
                    element.attrib = {
                        k: str(v).lower() if re.match('^(true|false)$', str(v), re.I) else str(v)
                        for k,
                        v in item.items()
                        if str(v) != ''
                    }

                elif re.match('^(_.*[Oo]pts|INCLUDE)', key):
                    # undescore elements _opts _xmlOpts and INCLUDE are considered not being content so far
                    pass

                elif re.match('BLOCKCOMMENT[0-9]+', key):
                    if re.search('.*0$', key):
                        # take all except the first one as this is /* C++ dict */
                        pass
                    else:
                        # @TODO: Implement substitution of BLOCKCOMMENT
                        # cIndex = int(re.findall('(?<=BLOCKCOMMENT)[0-9]+', key)[0])
                        # element.append(Comment(item))
                        pass

                elif re.match('LINECOMMENT[0-9]+', key):
                    # @TODO: Implement substitution of LINECOMMENT
                    # cIndex = int(re.findall('(?<=LINECOMMENT)[0-9;]+', key)[0])
                    # root_element.append(Comment(re.sub('/', '', self.dict.line_comments[cIndex])))
                    pass

                else:
                    # nested content
                    if self.remove_node_numbering:
                        key = re.sub(r'(^\d{1,6}_)', '', key)

                    # Substitute with empty string to force <NODE/> in favour of <NODE>None</NODE>
                    if item is None:
                        item = ''

                    child_nodes[index] = SubElement(element, '{%s}%s' % (xsd_uri, key))
                    # SubElement(subE[index], self.parseGenerateXml(subE[index], item))
                    self.populate_into_element(child_nodes[index], item, xsd_uri)

        else:
            element.text = str(arg)

        return
