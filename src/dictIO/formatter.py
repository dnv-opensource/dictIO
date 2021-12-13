import io
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, MutableMapping, MutableSequence, Union
from xml.dom import minidom
# from lxml.etree import register_namespace
from xml.etree.ElementTree import (Element, SubElement, Comment, register_namespace, tostring)
import logging

from dictIO.utils.counter import BorgCounter

from dictIO.cppDict import CppDict


__ALL__ = ['Formatter']

logger = logging.getLogger(__name__)


class Formatter():
    '''
    Abstract Base Class for dict formatters.
    Dict formatters serialize a dict into a string, applying a specific format.
    '''

    def __init__(self):
        self.counter = BorgCounter()

    @classmethod
    def get_formatter(cls, target_file: Path = None):
        '''
        Factory method to return a Formatter instance matching the output format intended to generate
        '''
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
        '''
        Creates a string representation of the passed in dict.
        dict can be of type dict or CppDict.
        '''
        return ''

    def format_dict(self, arg: Union[MutableMapping, MutableSequence, Any]) -> str:
        '''
        Formats a dict or list.
        '''
        return ''

    def format_type(self, arg: Any) -> str:
        '''
        Formats single value types (str, int, float, boolean and None)
        '''
        return ''


class CppFormatter(Formatter):
    '''
    Dict formatter to serialize a dict into a string in C++ dictionary format
    '''

    def __init__(self):
        '''
        Implementation specific default configuration of CppFormatter
        '''
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        dict: Union[MutableMapping, CppDict],
    ) -> str:
        '''
        Creates a string representation of the passed in dict in C++ dictionary format.
        dict can be of type dict or CppDict.
        '''
        s = super().to_string(dict)

        # Create the string representation of the dictionary in its basic structure.
        if isinstance(dict, CppDict):
            s += self.format_dict(dict.data)
        elif isinstance(dict, MutableMapping):
            # Turn ordinary dict into CppDict.
            # That way, any ordinary python dict is treated in this function like a CppDict.
            temp_dict = CppDict()
            temp_dict.update(dict)
            dict = deepcopy(temp_dict)
            s += self.format_dict(dict.data)
        else:
            logger.error('CppFormatter.to_string(): passed in arg is not of type dict')
            return ''

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
        ancestry=MutableMapping,
    ) -> str:
        '''
        Formats a dict or list in C++ dictionary format.
        '''
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
                        s += self.format_dict(value, level=item_level, end='\n')        # (recursion)
                        last_item_on_this_line = False                                  # (effective with next item)
                        first_item_on_this_line = True                                  # (effective with next item)
                    else:
                                                                                        # Do not add a line ending. Instead, add an adjusted number of spaces after the item to make indentation look pretty.
                        s += self.format_dict(
                            '%s%s' % (value, sep * max(0, (14 - len(str(value))))),
                            level=item_level,
                            end=''
                        )                                                               # (recursion)

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
                        '%s%s%s;' %
                        (key, sep * max(8, (total_indent - len(key) - tab_len * level)), value),
                        level=level
                    )

        # Single item
        # Note: This is the base case. It is reached only through recursion from
        # dict -> key value pair    or from     list -> single value.
        # arg will hence either be a single item from a list, or a key value pair from a dict.
        else:
            string = '%s%s' % (indent, arg) + end
            s += string

        return s

    def format_type(self, arg: Any) -> str:
        '''
        Formats single value types (str, int, float, boolean and None)
        '''
        # Non-string types:
        # Return the string representation of the type without additional quotes.
        if not isinstance(arg, str):
            return str(arg)

        # String type:
        # Add double quotes if ..
        # ..string contains a keyword AND a non-Word character (single keywords do not need quotes)
        if re.search(r'[$]', arg) and re.search(r'[^$a-zA-Z0-9_]', arg):
            return '"' + arg + '"'
        # Add single quotes if..
        # ..string is empty, contains spaces or is a path
        if arg == '' or re.search(r'[\s:/\\]', arg):
            return '\'' + arg + '\''
        else:
            return arg

    def insert_block_comments(self, dict: CppDict, s: str) -> str:
        '''
        Replaces all BLOCKCOMMENT placeholders in s with the actual block_comments saved in dict
        str s is expected to contain the CppDict's block_content containing block comment placeholders to substitute (BLOCKCOMMENT... BLOCKCOMMENT...)
        '''

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

            # Search for the placeholder entry we created in parse_tokenized_dict(),
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
        '''
        Inserts back all include directives
        '''
        for key, (include_directive, _) in cpp_dict.includes.items():
            # Search for the placeholder entry we created in parse_tokenized_dict(),
            # and insert back the original include directive.
            search_pattern = r'INCLUDE%06i\s+INCLUDE%06i;' % (key, key)
            s = re.sub(search_pattern, include_directive.replace('\\', '\\\\'), s)

        return s

    def insert_line_comments(self, cpp_dict: CppDict, s: str) -> str:
        '''
        Inserts back all line comments
        '''
        for key, line_comment in cpp_dict.line_comments.items():
            # Search for the placeholder entry we created in parse_tokenized_dict(),
            # and insert back the original block_comment.
            search_pattern = r'LINECOMMENT%06i\s+LINECOMMENT%06i;' % (key, key)
            s = re.sub(search_pattern, line_comment, s)

        return s

    def remove_trailing_spaces(self, s: str) -> str:
        '''
        Reads all lines from stringObj, removes trailing spaces from each line and
        returns a new string carrying all lines with trailing spaces removed.
        '''
        stream = io.StringIO(newline=None)
        stream.write(s)
        stream.seek(0)
        ns = str()
        for line in stream.readlines():
            match = re.search('[\r\n]*$', line)
            if match:
                line_ending = match.group(0)
                line_without_ending = line[0:len(line) - len(line_ending)]
                line_without_trailingspaces = re.sub(
                    r'\s+$', '', line_without_ending
                ) + line_ending
                ns += line_without_trailingspaces
        return ns


class FoamFormatter(CppFormatter):
    '''
    Dict formatter to serialize a dict into a string in foam dictionary format
    '''

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
        '''
        Creates a string representation of the passed in dict in foam dictionary format.
        dict can be of type dict or CppDict.
        '''

        # Foam dicts are, in contrast to C++ dicts, restricted in what they shall contain.
        # The dict content is hence reduced to what Foam is able to interpret.
        # Dict entries that Foam cannot interpret - or would eventually even misinterpret - are hence removed:

        # Remove all dict entries starting with underscore
        def remove_underscore_keys_recursive(dict: MutableMapping):
            keys = [key for key in dict.keys()]
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
        s = re.sub('\'', '"', s)

        return s

    def format_type(self, arg: Any) -> str:
        '''
        Formats single value types (str, int, float, boolean and None)
        '''
        # Call base class implementation (CppFormatter)
        arg = super().format_type(arg)

        # Substitute single quotes by double quotes.
        arg = re.sub('\'', '"', arg)

        return arg

    def make_default_block_comment(self, block_comment: str = '') -> str:
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
    '''
    Dict formatter to serialize a dict into a string in json format
    '''

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
        # sourcery skip: inline-immediately-returned-variable
        '''
        Creates a string representation of the passed in dict in json format.
        dict can be of type dict or CppDict.
        '''
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
            sort_keys=True,
            indent=4,
            separators=(',', ':'),
        )
        # forced quotes
        # s = re.sub(r'\b([\w\d_]+)\b', '"\\1"', s)

        return s


class XmlFormatter(Formatter):
    '''
        <databases>
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
        '''
        Creates a string representation of the passed in dict in XML format.
        dict can be of type dict or CppDict.
        '''
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
            root_element.attrib = {k: str(v) for k, v in attributes.items() if len(str(v)) != 0}

        self.populate_into_element(root_element, dict, xsd_uri)

        s = minidom.parseString(tostring(root_element, encoding='UTF-8',
                                         method='xml')).toprettyxml(indent=indent)
        if self.omit_prefix:
            # objectify.deannotate(root, cleanup_namespaces=True)
            query = '(%s)' % ('|'.join('%s:' % s for s in prefixes))
            s = re.sub(query, '', s)

        return s

    def populate_into_element(
        self,
        element: Element,
        arg: Union[MutableMapping, MutableSequence, Any],
        xsd_uri: str = None
    ):
        '''
        Populates arg into the XML element node.
        If arg is a dict or list, method will call itself recursively until all nested content within the dict or list
        is populated into nested elements, eventually creating an XML dom.
        ToDo:   LINECOMMENT
        '''
        if isinstance(arg, MutableSequence):
            element.text = ' '.join(str(x) for x in arg)

        elif isinstance(arg, MutableMapping):
            child_nodes = [key for key in arg.keys()]

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
                        if len(str(v)) != 0
                    }

                elif re.match('^(_.*[Oo]pts|INCLUDE)', key):
                    # undescore elements _opts _xmlOpts and INCLUDE are considered not being content so far
                    pass

                elif re.match('BLOCKCOMMENT[0-9]+', key):
                    if re.search('.*0$', key):
                        #take all except the first one as this is /* C++ dict */
                        pass
                    else:
                        # @TODO: Implement substitution of BLOCKCOMMENT
                        #cIndex = int(re.findall('(?<=BLOCKCOMMENT)[0-9]+', key)[0])
                        #element.append(Comment(item))
                        pass

                elif re.match('LINECOMMENT[0-9]+', key):
                    # @TODO: Implement substitution of LINECOMMENT
                    #cIndex = int(re.findall('(?<=LINECOMMENT)[0-9;]+', key)[0])
                    #root_element.append(Comment(re.sub('/', '', self.dict.line_comments[cIndex])))
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
