import logging
import os
import re
from pathlib import Path
from typing import Any, MutableMapping, MutableSequence, Tuple, Union
from xml.etree.ElementTree import Element

# from lxml.etree import register_namespace
from lxml.etree import ETCompatXMLParser, fromstring

from dictIO import CppDict
from dictIO.utils.counter import BorgCounter


__ALL__ = ['Parser', 'CppParser', 'FoamParser', 'JsonParser', 'XmlParser']

logger = logging.getLogger(__name__)


class Parser():
    """Base Class for parsers.

    Parsers deserialize a string into a CppDict.
    Subclasses of Parser implement parsing of different, specifically formatted strings (see also Formatters).
    """

    def __init__(self):
        self.counter = BorgCounter()
        self.source_file = None
        return

    @classmethod
    def get_parser(cls, source_file: Union[Path, None] = None):
        """Factory method returning a Parser instance matching the source file type to be parsed

        Parameters
        ----------
        source_file : Path, optional
            name of the source file to be parsed, by default None

        Returns
        -------
        Parser
            specific Parser instance matching the source file type to be parsed
        """
        # Determine the parser to be used by a two stage process:

        # 1. If source_file is passed, choose parser depending on file-ending
        if source_file:
            if source_file.suffix == '.foam':               # .foam -> FoamParser
                return FoamParser()
            elif source_file.suffix == '.json':             # .json -> JsonParser
                return JsonParser()
            elif source_file.suffix in ['.xml', '.ssd']:    # .xml  or  OSP .ssd -> XmlParser
                return XmlParser()

        # 2. If no source file is passed, return CppParser as default / fallback
        return CppParser()  # default

    def parse_file(
        self,
        source_file: Union[str, os.PathLike[str]],
        target_dict: Union[CppDict, None] = None,
        comments: bool = True,
    ) -> CppDict:
        # sourcery skip: inline-immediately-returned-variable
        """Parses a file and deserializes it into a dict.

        Parameters
        ----------
        source_file : Union[str, os.PathLike[str]]
            name of the dict file to be parsed
        target_dict : CppDict, optional
            the target dict the parsed dict file shall be merged into, by default None
        comments : bool, optional
            reads comments from source file, by default True

        Returns
        -------
        CppDict
            the parsed dict

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f'source_file not found: {source_file}')
            raise FileNotFoundError(source_file)

        self.source_file = source_file

        # Check whether file to read from exists.
        if not self.source_file.exists():
            logger.warning(
                'Parser.parse_file(): File or path does not exist: \'%s\'. Empty dict will be returned.'
                % source_file
            )
            file_content = ''
        else:
            with self.source_file.open('r') as f:
                file_content = f.read()

        # Create target dict in case no specific target dict was passed in
        if target_dict is None:
            target_dict = CppDict(source_file)
        else:
            target_dict.source_file = source_file.absolute()
            target_dict.path = source_file.parent
            target_dict.name = source_file.name

        # one final check only
        # whether a file exists (can also have zero content)
        # or a dict was given (can also contain nothing)
        if not self.source_file.exists() and target_dict is None:
            logger.error(
                'Parser.parse_file(): File or path does not exist (\'%s\') or no target dict (%s) was given.'
                % (source_file, target_dict)
            )

        # Parse file content
        parsed_dict = self.parse_string(file_content, target_dict, comments)

        return parsed_dict

    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        # sourcery skip: inline-immediately-returned-variable, lift-return-into-if
        """Parses a string and deserializes it into a CppDict.

        Note: Override this method when implementing a specific Parser.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : CppDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        CppDict
            the parsed dict
        """

        # +++VERIFY STRING CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Check that string is not empty.
        if not string:
            logger.warning(f'Parser.parse_string(): String to parse is empty: {string}')

        # Create target dict in case no specific target dict was passed in
        if target_dict is None:
            logger.warning(
                'Parser.parse_string(): Target dict is None. Will create new target dict, however, with empty filename.'
            )
            target_dict = CppDict()

        # Create a local CppDict instance where the stringcontent is temporarily parsed into
        if target_dict.source_file:
            parsed_dict = CppDict(target_dict.source_file)
        else:
            parsed_dict = target_dict

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to implement this part.

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to, finally, update the target dict!
        # (in the base class, however, this does not make sense - hence commented out)
        # target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def parse_type(self, arg: Any) -> Any:
        """Parses a single value

        Parses a single value and casts it to its native type (str, int, float, boolean or None).

        Parameters
        ----------
        arg : Any
            the value to be parsed

        Returns
        -------
        Any
            the value casted to its native type (str, int, float, boolean or None)
        """

        # Numbers (int and float) are returned without conversion
        if isinstance(arg, int) and not isinstance(arg, bool):  # int
            return arg
        if isinstance(arg, float):                              # float
            return arg

        # Boolean and None types are returned without conversion
        if isinstance(arg, bool):   # bool
            return arg
        if arg is None:             # None
            return arg

        # Any other non-string type: Return without conversion
        if not isinstance(arg, str):
            return arg

        # String: Convert the string content to its native type, where possible.
        # The following starts a filter cascade, hence the sequence is important,
        # otherwise latter clauses would produce unreasonable matches!

        # Empty string
        check: str = __class__.remove_quotes_from_string(arg)
        if not check:
            return ''

        # Simple placeholder or reserved expressions -> do nothing
        # Note: This if clause is important: It avoids that distinct placeholders like e.g.
        # '-' are interpreted as float (and then transformed to float .. what might even fail).
        if arg in ['-', '_', '.']:
            return arg

        # String numbers shall be converted to numbers (int and float)
        if re.search(r'^[+-]?\d+$', arg):                           # int
            return int(arg)
        if re.search(r'^[+-]?(\d+(\.\d*)?|\.\d+)$', arg):           # float
            return float(arg)
        if re.search(r'^[+-]?\d*(\.\d*)?([eE]?[-+]?\d+)?$', arg):   # float written as fpn like 1.e-03
            return float(arg)

        # Booleans and None types that are masked as strings
        # ('True', 'true', 'False', 'false', 'ON', 'on', 'OFF', 'off', 'None', 'none', 'NULL', 'null')
        # shall be converted to its native Boolean or None type, respectively
        if re.search(r'^(true)$', arg.strip().lower()):     # True
            return True
        if re.search(r'^(false)$', arg.strip().lower()):    # False
            return False
        if re.search(r'^(on)$', arg.strip().lower()):       # OpenFOAM 'on' -> True
            return True
        if re.search(r'^(off)$', arg.strip().lower()):      # OpenFOAM 'off' -> False
            return False
        if re.search(r'^(none)$', arg.strip().lower()):     # None
            return None
        if re.search(r'^(null)$', arg.strip().lower()):     # C++ 'NULL' or JSON 'null' -> None
            return None

        # Any other string: return 'as is', but make sure extra quotes, if so, are stripped.
        # Note: Also any placeholder strings will fall into this category.
        # Returned 'as is' they are kept unchanged, what is in fact what we want here.
        return __class__.remove_quotes_from_string(arg)

    def parse_types(
        self, arg: Union[MutableMapping, MutableSequence]
    ) -> Union[MutableMapping, MutableSequence]:
        """Parses multiple values

        Parses all values inside a dict or list and casts them to its native types (str, int, float, boolean or None).
        The function traverses the passed in dict or list recursively
        so that all values in also nested dicts and lists are parsed.

        Parameters
        ----------
        arg : Union[MutableMapping, MutableSequence]
            the dict or list containing the values to be parsed

        Returns
        -------
        Union[MutableMapping, MutableSequence]
            the original dict or list, yet with all contained values being casted to its native types (str, int, float, boolean or None).
        """
        if isinstance(arg, MutableSequence):
            for index, _ in enumerate(arg):
                if isinstance(arg[index], (MutableMapping, MutableSequence)):
                    self.parse_types(arg[index])
                else:
                    arg[index] = self.parse_type(arg[index])
        elif isinstance(arg, MutableMapping):
            for key in arg.keys():
                if isinstance(arg[key], (MutableMapping, MutableSequence)):
                    self.parse_types(arg[key])
                else:
                    arg[key] = self.parse_type(arg[key])
        return arg

    @staticmethod
    def remove_quotes_from_string(arg: str, all: bool = False) -> str:
        """Removes quotes from a string

        Removes quotes (single and double quotes) from the string object passed in.

        Parameters
        ----------
        arg : str
            the string with quotes
        all : bool, optional
            if true, all quotes inside the string will be removed (not only leading and trailing quotes), by default False

        Returns
        -------
        str
            the string with quotes being removed

        Raises
        ------
        TypeError
            if arg is not of type str
        """

        if not isinstance(arg, str):                                                                    # any other type
            raise TypeError(
                f'{__class__.__name__}.remove_quotes_from_string(): invalid type of paramter arg:\n'
                f'arg is of type {type(arg)!s} but expected to be str.'
            )

        if all:
            # Removes ALL quotes in a string:
            # Not only leading and trailing quotes, but also quotes inside a string are removed.
            search_pattern = re.compile(r'[\'\"]')
        else:
            # Removes only leading and trailing quotes. Quotes inside a string are kept.
            search_pattern = re.compile(r'(^[\'\\"]{1}|[\'\\"]{1}$)')

        return re.sub(search_pattern, '', arg)

    @staticmethod
    def remove_quotes_from_strings(
        arg: Union[MutableMapping, MutableSequence]
    ) -> Union[MutableMapping, MutableSequence]:
        """Removes quotes from multiple strings

        Removes quotes (single and double quotes) from all string objects inside a dict or list.
        The function traverses the passed in dict or list recursively
        so that all strings in also nested dicts and lists are processed.


        Parameters
        ----------
        arg : Union[MutableMapping, MutableSequence]
            the dict or list containing strings the quotes in which shall be removed

        Returns
        -------
        Union[MutableMapping, MutableSequence]
            the original dict or list, yet with quotes in all strings being removed

        Raises
        ------
        TypeError
            if arg is not of type MutableMapping or MutableSequence (u.e. dict or list)
        """
        if not isinstance(arg, (MutableMapping, MutableSequence)):                                      # any other type
            raise TypeError(
                f'{__class__.__name__}.remove_quotes_from_strings(): invalid type of paramter arg:\n'
                f'arg is of type {type(arg)!s} but expected to be MutableMapping | MutableSequence.'
            )

        if isinstance(arg, MutableMapping):                                     # dict
            for key in arg.keys():
                if isinstance(arg[key], (MutableMapping, MutableSequence)):     # dict or list
                    arg[key] = __class__.remove_quotes_from_strings(arg[key])   # (recursion)
                elif isinstance(arg[key], str):                                 # str
                    arg[key] = __class__.remove_quotes_from_string(arg[key])
        elif isinstance(arg, MutableSequence):                                  # list
            for i in range(len(arg)):
                if isinstance(arg[i], (MutableMapping, MutableSequence)):       # dict or list
                    arg[i] = __class__.remove_quotes_from_strings(arg[i])       # (recursion)
                elif isinstance(arg[i], str):                                   # str
                    arg[i] = __class__.remove_quotes_from_string(arg[i])

        return arg


class CppParser(Parser):
    """Parser to deserialize a string in dictIO dict file format into a CppDict.
    """

    def __init__(self):
        '''
        Implementation specific default configuration of CppParser
        '''
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        """Parses a string in dictIO dict file format and deserializes it into a CppDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : CppDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        CppDict
            the parsed dict
        """

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict = super().parse_string(string, target_dict)

        # +++PARSE LINE CONTENT+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Split file content into lines and store them in the newly created CppDict instance
        parsed_dict.line_content = string.splitlines(keepends=True)

        # Extract line comments
        self._extract_line_comments(parsed_dict, comments)

        # Extract include directives
        self._extract_includes(parsed_dict)

        # +++PARSE BLOCK CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Concatenate all lines from line_content
        # As extracting block comments is easier with line endings still existing, at first we preserve them.
        self._convert_line_content_to_block_content(parsed_dict)    # preserves line endings

        # Extract block comments      ..and remove line endings right thereafter

        self._extract_block_comments(parsed_dict, comments)
        self._remove_line_endings_from_block_content(parsed_dict)

        # Extract string literals
        self._extract_string_literals(parsed_dict)

        # Extract expressions
        self._extract_expressions(parsed_dict)

        # Make sure that all delimiters are surrounded by at least one space before and after
        # to ensure they are properly identified when we tokenize block_content
        self._separate_delimiters(parsed_dict)

        # +++PARSE TOKENS+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Split block_content into tokens
        self._convert_block_content_to_tokens(parsed_dict)

        # Determine the hierarchic level of each token and assign it to the token (the hierarchy is dictated by the sequence of delimiters)
        self._determine_token_hierarchy(parsed_dict)

        # Parse the hierarchic tokens
        self._convert_tokens_to_dict(parsed_dict)

        # Insert back string literals
        self._insert_string_literals(parsed_dict)

        # +++CLEAN PARSED DICTIONARY++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self._clean(parsed_dict)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def _extract_line_comments(self, dict: CppDict, comments: bool):
        """Finds and extracts C++ line comments (// ..) from dict.line_content, and replaces them with Placeholders.

        Finds C++ line comments (// line_comment), extracts them,
        and replaces the complete line with a placeholder in the form LINECOMMENT000000 .
        The extracted line comments are stored in .line_comments as key value pairs {index:line_comment}.
        index, therein, corresponds to the integer number in LINECOMMENT000000.

        Parameters
        ----------
        dict : CppDict
            dict to be processed. _extract_line_comments() works on dict.line_content
        comments : bool
            If False, line comments will be removed (they get replaced by an empty placeholder then, which in effect removes them).
        """
        for index, line in enumerate(dict.line_content):
            # if it is a line comment or just a "http://"?
            if re.search(r'(?<!:)/{2}.*$', line):
                # if re.search(r'/{2}.*$', line):
                key = self.counter()
                # Search for only the FIRST occurrence of '//' in the line.
                # From there, consider all chars until line ending as ONE comment.
                line_comment = re.findall('/{2}.*$', line)[0]
                dict.line_comments.update({key: line_comment})
                placeholder = 'LINECOMMENT%06i' % key
                if not comments:
                    placeholder = ''
                # Replace line comment with placeholder
                dict.line_content[index] = dict.line_content[index].replace(
                    line_comment, placeholder
                )

        return

    def _extract_includes(self, dict: CppDict):
        """Finds and extracts #include directives from dict.line_content, and replaces them with Placeholders.

        Finds #includes directives (#include file), extracts them,
        and replaces the complete line where the include directive was found
        with a placeholder in the form #INCLUDE000000.
        The absolute path to the file referenced in the include directive is determined.
        The original line with its include directive as well as the absolute path to the file to include
        is then stored as a key-value pair in dict.includes, in the form {index:(include_directive, include_file_name, include_file_path)}
        index, therein, corresponds to the integer number in #INCLUDE000000.

        Parameters
        ----------
        dict : CppDict
            dict to be processed. _extract_includes() works on dict.line_content
        """

        for index, line in enumerate(dict.line_content):
            if re.search(r'^\s*#\s*include', line):
                ii = self.counter()
                dict.line_content[index] = 'INCLUDE%06i\n' % ii

                include_file_name = re.sub(r'(^\s*#\s*include\s*|\s*$)', '', line)
                include_file_name = __class__.remove_quotes_from_string(include_file_name)

                include_file_path = Path.joinpath(dict.path, include_file_name)

                include_directive = line
                if line[-1] == '\n':
                    include_directive = line[:-1]

                dict.includes.update(
                    {ii: (include_directive, include_file_name, include_file_path)}
                )

        return

    def _convert_line_content_to_block_content(self, dict: CppDict):
        """Concatenates all lines from line_content to one long string (text block) and stores the result in block_content.
        """
        dict.block_content = ''.join(dict.line_content)
        dict.line_content.clear()
        return

    def _remove_line_endings_from_block_content(self, dict: CppDict):
        """Removes all line endings in .block_content and substuitutes them by single spaces.
        """
        dict.block_content = re.sub(r'\n', ' ', dict.block_content).strip()
        return

    def _extract_block_comments(self, dict: CppDict, comments: bool):
        """Finds and extracts C++ block comments (/* .. */) from dict.block_content, and replaces them with Placeholders.

        Finds C++ block comments (/* block_comment */), extracts them,
        and replaces them with a placeholder in the form BLOCKCOMMENT000000.
        The extracted block comments are stored in .block_comments as key value pairs {index:block_comment}.
        index, therein, corresponds to the integer number in BLOCKCOMMENT000000.

        Parameters
        ----------
        dict : CppDict
            dict to be processed. _extract_block_comments() works on dict.block_content
        comments : bool
            If False, block comments will be removed (they get replaced by an empty placeholder then, which in effect removes them).
        """

        block_comments = re.findall(r'/\*[\w\W\d\D\s]*?\*/', dict.block_content, re.MULTILINE)
        dict.block_comments = {i: block_comments[i] for i in range(len(block_comments))}

        for key, block_comment in dict.block_comments.items():
            placeholder = 'BLOCKCOMMENT%06i' % key
            # placeholder = 'BLOCKCOMMENT%06i BLOCKCOMMENT%06i;' % (key, key)
            if not comments:
                placeholder = ''
            # Replace block comment with placeholder
            dict.block_content = re.sub(re.escape(block_comment), placeholder, dict.block_content)

        return

    def _extract_string_literals(self, dict: CppDict):
        """Finds and extracts string literals from dict.block_content, and replaces them with Placeholders.

        Finds string literals, extracts them,
        and replaces them with a placeholder in the form STRINGLITERAL000000.
        Substrings within .block_content that are surrounded by single quotes are identified as string literals.
        The extracted string literals are stored in .string_literals as key value pairs {index:string_literal}.
        index, therein, corresponds to the integer number in STRINGLITERAL000000.

        Parameters
        ----------
        dict : CppDict
            dict to be processed. _extract_string_literals() works on dict.block_content.
        """

        # Step 1: Find single quoted string literals in .block_content
        search_pattern = r'\'.*?\''
        string_literals = re.findall(search_pattern, dict.block_content, re.MULTILINE)
        for string_literal in string_literals:

            index = self.counter()
            placeholder = 'STRINGLITERAL%06i' % index

            # Replace all occurances of the string literal in .block_content with the placeholder (STRINGLITERAL000000)
            # Note: For re.sub() to work properly we need to escape all special characters
            search_pattern = re.compile(re.escape(string_literal))
            dict.block_content = re.sub(
                search_pattern, placeholder, dict.block_content
            )                                                       # replace string literal in .block_content with placeholder

            # Register the string literal in .string_literals
            dict.string_literals.update(
                {index: __class__.remove_quotes_from_string(string_literal)}
            )

        # Step 2: Find double quoted string literals in .block_content
        # Double quoted strings are identified as string literals only in case they do not contain a $ character.
        # (double quoted strings containing a $ character are considered expressions, not string literals.)
        search_pattern = r'\".*?\"'
        string_literals = re.findall(search_pattern, dict.block_content, re.MULTILINE)
        for string_literal in string_literals:
            if '$' not in string_literal:

                index = self.counter()
                placeholder = 'STRINGLITERAL%06i' % index

                # Replace all occurances of the string literal in .block_content with the placeholder (STRINGLITERAL000000)
                # Note: For re.sub() to work properly we need to escape all special characters
                search_pattern = re.compile(re.escape(string_literal))
                dict.block_content = re.sub(
                    search_pattern, placeholder, dict.block_content
                )                                                       # replace expression in .block_content with placeholder

                # Register the string literal in .string_literals
                dict.string_literals.update(
                    {index: __class__.remove_quotes_from_string(string_literal)}
                )

        return

    def _extract_expressions(self, dict: CppDict):
        """Finds and extracts expressions from dict.block_content, and replaces them with Placeholders.

        Finds expressions, extracts them,
        and replaces them with a placeholder in the form EXPRESSION000000.
        Substrings within .block_content that are surrounded by double quotes and contain minimum one $reference are identified as expressions.
        The extracted expressions are stored in .expressions as a key'd subdict with multiple elements {index:{'index': index, 'expression': expression, 'name': placeholder}}.
        index, therein, corresponds to the integer number in EXPRESSION000000.

        Parameters
        ----------
        dict : CppDict
            dict to be processed. _extract_expressions() works on dict.block_content.
        """

        dict.expressions = {}

        # Step 1: Find expressions in .block_content .
        # Expressions are double quoted strings that contain minimum one reference.
        # References are denoted using the '$' syntax familiar from shell programming.
        # Any key'd entries in a dict are considered variables and can be referenced.
        search_pattern = r'"[^"]*\$.*?"'
        expressions = re.findall(search_pattern, dict.block_content, re.MULTILINE)
        for expression in expressions:

            index = self.counter()
            placeholder = 'EXPRESSION%06i' % index

            # Replace all occurances of the expression in .block_content with the placeholder (EXPRESSION000000)
            # Note: For re.sub() to work properly we need to escape all special characters
            # (covering both '$' as well as any mathematical operators in the expression)
            search_pattern = re.compile(re.escape(expression))
            dict.block_content = re.sub(
                search_pattern, placeholder, dict.block_content
            )                                                       # replace expression in .block_content with placeholder

            # Register the expression in .expressions
            expression = re.sub(r'\"', '', expression)
            dict.expressions.update(
                {index: {
                    'index': index, 'expression': expression, 'name': placeholder
                }}
            )

        # Step 2: Find references in .block_content (single references to key'd entries that are NOT in double quotes).
        search_pattern = r'\$\w[\w\[\]]+'
        while match := re.search(search_pattern, dict.block_content, re.MULTILINE):
            reference = match[0]
            index = self.counter()
            placeholder = 'EXPRESSION%06i' % index
            # Replace the found reference in .block_content with the placeholder (EXPRESSION000000)
            dict.block_content = match.re.sub(placeholder, dict.block_content, count=1)
            # Register the reference as expression in .expressions
            dict.expressions.update(
                {index: {
                    'index': index, 'expression': reference, 'name': placeholder
                }}
            )
        return

    def _separate_delimiters(self, dict: CppDict, delimiters=None):
        """Ensures that delimiters are separated by exactly one space before and after.

        Parses .block_content for occurences of the delimiters passed in, and strips any spaces surrounding each
        delimiter to exactly one single space before and one single space after the delimiter.
        Further, it removes all line endings from .block_content and eventually replaces them with single spaces.

        After _separate_delimiters() returns, .block_content contains only
        - words (with single char delimiters also considered a 'word' here)    and
        - single spaces

        Hence, calling _separate_delimiters() is a preparatory step before
        decomposing .block_content into a list of tokens with re.split('\\s').
        It ensures that re.split('\\s') generates tokens containing one single word each (or a single char delimiter)
        but not any 'waste' tokens with spaces, tabs or line endings will be deleted.
        """

        if delimiters is None:
            delimiters = dict.delimiters

        # Insert at least one \s around every char in list
        for char in delimiters:
            dict.block_content = re.sub(str(r'(\%s)' % char), str(f' {char} '), dict.block_content)

        # Substitute all \s+ to \s
        # This turns multiple spaces into one single space.
        # However, as \s+ matches ANY whitespace character (\s+ is equivalent to [ \t\n\r\f\v]+)
        # this also deletes all line endings (\n). As explained above, this is well intended though.
        dict.block_content = re.sub(r'\s+', ' ', dict.block_content)

        return

    def _convert_block_content_to_tokens(self, dict: CppDict):
        """Decomposes .block_content into a list of tokens.
        """

        dict.tokens = [(0, i) for i in re.split(r'\s', dict.block_content)]
        dict.block_content = ''

        return

    def _determine_token_hierarchy(self, dict: CppDict):
        # sourcery skip: use-join
        """Creates the hierarchy among the tokens and tests their indentation
        """
        level = 0
        count_open = []
        count_close = []
        for index, item in enumerate(dict.tokens):

            if item[1] in dict.openingBrackets:
                push_pop = 1
                count_open.append(item[1])
            elif item[1] in dict.closingBrackets:
                push_pop = -1
                count_close.append(item[1])
            else:
                push_pop = 0

            if push_pop < 0:
                level += push_pop
                push_pop = 0

            # if not re.search('COMMENT', self.tokens[index][1]):
            dict.tokens[index] = (level, dict.tokens[index][1])

            if push_pop > 0:
                level += push_pop
                push_pop = 0

        if level != 0:
            counted = ''
            for opening_bracket, closing_bracket in zip(dict.openingBrackets, dict.closingBrackets):
                counted += ''.join(
                    [
                        '\t\t\t',
                        opening_bracket,
                        str(len([b for b in count_open if b == opening_bracket])),
                        ' -- ',
                        str(len([b for b in count_close if b == closing_bracket])),
                        closing_bracket,
                        '\n'
                    ]
                )
            logger.error(
                '_determine_token_hierarchy: opening and closing delimiters in dict %s are not balanced:\n%s'
                % (dict.name, counted)
            )

        return

    def _convert_tokens_to_dict(self, dict: CppDict):
        """Converts the hierarchic tokens into a dict
        """
        dict.update(self._parse_tokenized_dict(dict))
        dict.tokens.clear()

        return

    def _parse_tokenized_dict(
        self,
        dict: CppDict,
        tokens: Union[MutableSequence[Tuple[int, str]], None] = None,
        level: int = 0,
    ) -> dict:
        """Parses a tokenized dict and returns the parsed dict.

        Parses all tokens, identifies the element within the tokenized dict each token represents or belongs to,
        converts related tokens into the element's type and stores it in local dict (parsed_dict).

        Following elements within the tokenized dict are identified and parsed:
        - nested data struct (list or dict)
        - key value pair
        - comment (string literal containing 'COMMENT')

        After all tokens have successfully been parsed, return the parsed dict.

        Note: To allow recursive calls in case of nested dicts, parsed_dict is declared as a local variable.
        """
        # sourcery skip: remove-redundant-pass

        parsed_dict = {}

        if tokens is None:
            tokens = dict.tokens

        # Iterate through tokens
        token_index = 0
        while token_index < len(tokens):
            # logger.info('token: %s%s' % ('\t'*tokens[tIndex][0], tokens[tIndex][1]))  # 1

            # Nested data struct (list or dict)   '(' = list    '{' = dict
            if tokens[token_index][1] in dict.openingBrackets:

                # The name (key) of the data struct is by convention directly preceeding the opening bracket.
                # ..except if there are line comments in between. skip those:
                offset = 1
                while re.match('^.*COMMENT.*$', str(tokens[token_index - offset][1])):
                    offset += 1
                # name (key) of the data struct:
                name = tokens[token_index - offset][1]

                # Closing bracket has by definition same level as opening bracket.
                # (Note: the tokens BETWEEN the brackets are considered one level 'deeper'; but that's not the point here)
                closing_bracket = self._find_companion(dict, tokens[token_index][1])
                closing_level = tokens[token_index][0]

                # Create a temporary data_struct_tokens list for just the nested data struct, containing
                # all tokens from the opening bracket (first token) to the closing bracket (last token)
                data_struct_tokens = []
                i = 0
                last_index = None
                # Start at opening bracket, go forward and copy the tokens
                # until (and including) the accompanied closing bracket.
                while (
                    tokens[token_index + i][1] != closing_bracket
                    or tokens[token_index + i][0] != closing_level
                    and not re.match('^.*COMMENT.*$', str(tokens[token_index + i][1]))
                ):
                    last_index = token_index + i
                    data_struct_tokens.append(tokens[token_index + i])
                    i += 1
                data_struct_tokens.append(tokens[token_index + i])

                # Do a Syntax-Check at the closing bracket of the data struct.
                # As the syntax for lists and dicts is different, the syntax check is type specific:
                # list:
                # Proof that list properly ends with ';'
                # (= assert that closing bracket of the list is followed by ';')
                if data_struct_tokens[-1][1] == ')' and tokens[token_index + i
                                                               + 1][1] not in [';', ')']:
                    # log error: Missing ';' after list
                    logger.warning(
                        'mis-spelled expression / missing \';\' around \"%s\"' % ' '.join(
                            [name] + [t[1] for t in data_struct_tokens]
                            + [tokens[token_index + i + 1][1]]
                        )
                    )
                # dict:
                if data_struct_tokens[-1][1] == '}':
                    # Proof that last key value pair in dict ends with ';'
                    # (= assert that second-to-last token is ';')
                    index = -2
                    # ..ok, line comments do not count .. skip them:
                    while re.match('^.*COMMENT.*$', str(data_struct_tokens[index][1])):
                        index -= 1
                    # ..but now: Does the last key value pair end with ';'?
                    if data_struct_tokens[index][1] not in ['{', ';', '}']:
                        # log error: Missing ';' after key value pair
                        logger.error(
                            'mis-spelled expression / missing \';\' around \"%s\"'
                            % ' '.join([name] + [t[1] for t in data_struct_tokens])
                        )

                # Parse the tokenized data struct, translate it into its type (list or dict),
                # and update parsed_dict with the new list or dict.
                # Again, the code is type specific depending on whether the parsed data struct is a list or a dict.
                # list:
                if data_struct_tokens[0][1] == '(':
                    # Check whether the list is empty
                    if len(data_struct_tokens) < 3:
                        # is empty (contains only opening and closing bracket)
                        # update parsed_dict with just the empty list
                        parsed_dict[name] = []
                    else:
                        # has content
                        # parse the nested list
                        nested_list = self._parse_tokenized_list(
                            dict, data_struct_tokens, level=level + 1
                        )
                        # update parsed_dict with the nested list
                        parsed_dict[name] = nested_list

                #  dict:
                elif data_struct_tokens[0][1] == '{':
                    # parse the nested dict (recursion)
                    nested_dict = self._parse_tokenized_dict(
                        dict, data_struct_tokens[1:-1], level=level + 1
                    )
                    # update parsed_dict with the nested dict
                    parsed_dict[name] = nested_dict

                # All done: Identified data struct is parsed, translated into its corresponding type,
                # and local parsed_dict is updated.
                # To close out and move on, fast-forward the index of tokens
                # to 'after' the data struct we just parsed:
                if last_index is not None:
                    token_index = last_index + 1

            # Key value pair
            elif tokens[token_index][1] == ';' and tokens[token_index - 1][1] != ')':

                # Read the name (key) and the value from the key value pair
                # Parse from right to left, starting at the identified ';'
                # and then copy the tokens into a temporary key_value_pair_tokens list:
                key_value_pair_tokens: MutableSequence[Tuple[int,
                                                             str]] = [tokens[token_index]]  # ';'
                                                                                            # key_value_pair_tokens.append(tokens[token_index])                       # ';'
                key_value_pair_token_level: int = tokens[token_index][0]
                i = 1
                last_index = None
                while (
                    token_index - i >= 0
                    and tokens[token_index - i][0] == key_value_pair_token_level
                    and tokens[token_index - i][1] not in [';', '}']
                    and not re.match(r'^.*COMMENT.*$', str(tokens[token_index - i][1]))
                    and not re.match(r'^.*INCLUDE.*$', str(tokens[token_index - i][1]))
                ):
                    key_value_pair_tokens.append(tokens[token_index - i])
                    i += 1

                # reverse token list
                key_value_pair_tokens = key_value_pair_tokens[::-1]

                # Before proceeding with reading key and value, make sure that what was parsed
                # really represents a key-value pair, consisting of three elements key, value and ';'
                if not (
                    len(key_value_pair_tokens) == 3 and len(key_value_pair_tokens[0]) == 2
                    and len(key_value_pair_tokens[1]) == 2
                ):
                    # Something is lexically wrong.  Not a valid key-value pair. -> Skip and log warning
                    context_tokens_index_from = max(0, token_index - 20)
                    context_tokens_index_to = min(token_index + 20, len(tokens))
                    context = '/' + ' '.join(
                        [
                            tokens[i][1]
                            for i in range(context_tokens_index_from, context_tokens_index_to)
                            if len(tokens[i]) > 1
                        ]
                    ) + '/'
                    logger.warning(
                        f'CppParser._parse_tokenized_dict(): tokens skipped: {key_value_pair_tokens} inside {context}'
                    )
                else:
                    if len(key_value_pair_tokens) > 3:
                        logger.warning(
                            'CppParser._parse_tokenized_dict(): '
                            'more tokens in key-value pair than expected: %s' %
                            (str(key_value_pair_tokens))
                        )
                    # read the name (key) (first token, by convention)
                    name = key_value_pair_tokens[0][1]
                    # read the value (second token, by convention)
                    value = self.parse_type(key_value_pair_tokens[1][1])
                    # update parsed_dict with the parsed key value pair
                    # Note: Following update would be greedy, if parsed_dict would be declared as global variable.
                    # This exactly is why parsed_dict is declared as local variable in _parse_tokenized_dict().
                    # Doing so, an empty local dict is created with each call to _parse_tokenized_dict(),
                    # and that is, also with each RECURSIVE call.
                    # As every recursive call passes in a temporary token list containing only the nested
                    # data struct, updating a key effects the current (and local) parsed_dict only.
                    # Every key hence is being updated exclusively within its own local context; ambiguous occurences of keys are avoided.
                    if isinstance(name, int):
                        logger.error(f"unexpected type of key 'name': int (value: {name}).")
                    parsed_dict[name] = value

            # Comment
            # As comments cannot be stored "inline" in a structured dictionary
            # the same way as they were stored inline in the dict file parsed,
            # they are stored in parsed_dict in the form of distinct comment keys.
            # As the sequence of keys added to parsed_dict exactly follows the sequence of the tokens parsed,
            # the location of comments in relation to their preceding tokens is preserved.
            # The original comments are back-inserted later in insert_block_comments() and insert_line_comments(), respectively.
            # For now, create an entry with the placeholder string of the comment assigned to both, key and value.
            elif re.match('^.*COMMENT.*$', str(tokens[token_index][1])):
                parsed_dict[tokens[token_index][1]] = tokens[token_index][1]

            # Include directive
            # Create an entry with the placeholder string of the include directive assigned to both, key and value.
            elif re.match('^.*INCLUDE.*$', str(tokens[token_index][1])):
                parsed_dict[tokens[token_index][1]] = tokens[token_index][1]

            # -(Unknown element)
            else:
                pass

            # Iterate to next token
            token_index += 1

        # Return the parsed dict
        return parsed_dict

    def _parse_tokenized_list(
        self,
        dict: CppDict,
        tokens: Union[MutableSequence[Tuple[int, str]], None] = None,
        level: int = 0,
    ) -> list:
        """Parses a tokenized list and returns the parsed list.

        Parses all tokens, identifies the element within the tokenized list each token represents or belongs to,
        converts related tokens into the element's type and stores it in local list (parsed_list).

        Following elements within the tokenized list are identified and parsed:
        - nested data struct (list or dict)
        - single value type

        After all tokens have successfully been parsed, return the parsed list.

        Note: To allow recursive calls in case of nested lists, parsed_list is declared as a local variable.
        """
        # sourcery skip: remove-empty-nested-block, remove-redundant-if, remove-redundant-pass

        parsed_list = []

        if tokens is None:
            tokens = dict.tokens

        # Iterate through tokens
        base_level = tokens[0][0]
        token_index = 0
        while token_index < len(tokens):
            # logger.info('token: %s%s' % ('\t'*tokens[tIndex][0], tokens[tIndex][1]))  # 1

            # Nested data struct (list or dict)   '(' = list    '{' = dict
            if (
                tokens[token_index][1] in dict.openingBrackets
                and tokens[token_index][0] > base_level
            ):
                # Closing bracket has by definition same level as opening bracket.
                # (Note: the tokens BETWEEN the brackets are considered one level 'deeper'; but that's not the point here)
                closing_bracket = self._find_companion(dict, tokens[token_index][1])
                closing_level = tokens[token_index][0]

                # Create a temporary token list for just the nested data struct, containing
                # all tokens from the opening bracket (first token) to the closing bracket (last token)
                temp_tokens = []
                i = 0
                last_index = None
                # Start at opening bracket, go forward and copy the tokens
                # until (and including) the accompanied closing bracket
                while (
                    tokens[token_index + i][1] != closing_bracket
                    or tokens[token_index + i][0] != closing_level
                    and not re.match('^.*COMMENT.*$', str(tokens[token_index + i][1]))
                ):
                    last_index = token_index + i
                    temp_tokens.append(tokens[token_index + i])
                    i += 1
                temp_tokens.append(tokens[token_index + i])

                # Do a Syntax-Check at the closing bracket of the data struct.
                # As the syntax for lists and dicts is different, the syntax check is type specific:
                # list:
                if temp_tokens[-1][1] == ')':
                    # nothing to proof.  A list nested inside a list simply ends with ')'.
                    # Note: This is different for a list nested inside a dict: Then, the closing
                    # bracket of the list must be followed by ';' (because, basically, the list is then the 'value'
                    # part of a key value pair inside the dict. And key value pairs syntactically close with ';')
                    pass
                # dict:
                if temp_tokens[-1][1] == '}':
                    # Proof that last key value pair in dict ends with ';'
                    # (= assert that second-to-last token is ';')
                    index = -2
                    # ..ok, line comments do not count .. skip them:
                    while re.match('^.*COMMENT.*$', str(temp_tokens[index][1])):
                        index -= 1
                    # ..but now: Does the last key value pair end with ';'?
                    if temp_tokens[index][1] not in ['{', ';', '}']:
                        # log error: Missing ';' after key value pair
                        logger.error(
                            'mis-spelled expression / missing \';\' around \"%s\"'
                            % ' '.join(t[1] for t in temp_tokens)
                        )

                # Parse the tokenized data struct, translate it into its type (list or dict),
                # and update parsed_list with the new list or dict.
                # Again, the code is type specific depending on whether the parsed data struct is a list or a dict.
                # list:
                if temp_tokens[0][1] == '(':
                    # Check whether the list is empty
                    if len(
                        temp_tokens
                    ) < 3:                                          # is empty (contains only the opening and the closing bracket)
                                                                    # add an empty list to parsed_list
                        parsed_list.append([])
                    else:                                           # has content
                                                                    # parse the nested list
                        nested_list = self._parse_tokenized_list(
                            dict, temp_tokens, level=level + 1
                        )                                           # (recursion)
                                                                    # add nested list to parsed_list
                        parsed_list.append(nested_list)
                                                                    #  dict:
                elif temp_tokens[0][1] == '{':
                                                                    # parse the nested dict
                    nested_dict = self._parse_tokenized_dict(
                        dict, temp_tokens[1:-1], level=level + 1
                    )
                                                                    # add nested dict to parsed_list
                    parsed_list.append(nested_dict)

                # All done: Identified data struct is parsed, translated into its corresponding type,
                # and local parsed_list is updated.
                # To close out and move on, fast-forward the index of tokens
                # to 'after' the data struct we just parsed:
                if last_index is not None:
                    token_index = last_index + 1

            # Single value type
            elif tokens[token_index][1] not in ['(', ')', ';']:
                value = self.parse_type(tokens[token_index][1])
                parsed_list.append(value)

            # -else = ';' or ')'
            else:
                pass

            # Iterate to next token
            token_index += 1

        # Return the parsed list
        return parsed_list

    def _find_companion(self, dict: CppDict, bracket: str) -> str:
        """Returns the companion bracket character for the passed in bracket character.

        Example: If you pass in '{', _find_companion() will return '}'  (and vice versa)
        """
        companion = ''
        for item in dict.brackets:
            if bracket == item[0]:
                companion = item[1]
            elif bracket == item[1]:
                companion = item[0]
        return companion

    def _insert_string_literals(self, dict: CppDict):
        """Substitutes STRINGLITERAL placeholders in the dict with the corresponding entry from dict.string_literals
        """

        for index, string_literal in dict.string_literals.items():
            # Properties of the expression to be evaluated
            placeholder = 'STRINGLITERAL%06i' % index   # STRINGLITERAL000000
                                                        # The entry from dict.string_literals is parsed once again, so that entries representing single value native types
                                                        # (such as bool ,None, int, float) are transformed to its native type, accordingly.
            value = self.parse_type(string_literal)

            # Replace all occurences of placeholder within the dictionary with the original string literal.
            # Note: As find_global_key() is non-greedy and returns the key of only the first occurance of placeholder it finds,
            # we need to loop until we found and replaced all occurances of placholder in the dict
            # and find_global_key() does not find any more occurances.
            while global_key := dict.find_global_key(query=placeholder):
                # Back insert the string literal
                dict.set_global_key(global_key, value)
        dict.string_literals.clear()
        return

    def _clean(self, dict: CppDict):
        """Removes CppFormatter / CppParser specific internal keys from dict.

        Removes keys written by CppFormatter for documentation purposes
        but which shall not be created as keys in dict.data.
        In specific, it is the following two keys that get deleted if existing:
        _variables
        _includes
        """
        if '_variables' in dict.data.keys():
            del dict.data['_variables']
        if '_includes' in dict.data.keys():
            del dict.data['_includes']


class FoamParser(CppParser):
    """Parser to deserialize a string in OpenFOAM dictionary format into a CppDict.
    """

    def __init__(self):
        '''
        Implementation specific default configuration of FoamParser
        '''
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        # sourcery skip: inline-immediately-returned-variable
        """Parses a string in OpenFOAM dictionary format and deserializes it into a CppDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : CppDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        CppDict
            the parsed dict
        """

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(string, target_dict, comments)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        # target_dict.merge(parsed_dict)  # Not necessary. Done in base class CppDictParser already.

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict


class JsonParser(Parser):
    """Parser to deserialize a string in JSON dictionary format into a CppDict.
    """

    def __init__(self):
        '''
        Implementation specific default configuration of JsonParser
        '''
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        """Parses a string in JSON dictionary format and deserializes it into a CppDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : CppDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        CppDict
            the parsed dict
        """
        import json

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict = super().parse_string(string, target_dict, comments)

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict.data = json.loads(string)

        # Extract include directives
        self._extract_includes(parsed_dict)

        # Extract expressions
        self._extract_expressions(parsed_dict, parsed_dict.data)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def _extract_includes(self, dict: CppDict):
        from copy import deepcopy
        keys = list(dict.data.keys())
        include_placeholder_keys = {}
        for key in keys:
            if isinstance(key, str) and re.search(r'^\s*#\s*include', key):
                include_file_name = str(dict[key])
                include_file_name = __class__.remove_quotes_from_string(include_file_name)

                include_file_path = Path.joinpath(dict.path, include_file_name)

                include_file_name_temp = include_file_name.replace('\\', '\\\\')
                include_directive = f"#include '{include_file_name_temp}'"

                ii = self.counter()
                dict.includes.update(
                    {ii: (include_directive, include_file_name, include_file_path)}
                )

                include_placeholder_keys[f'INCLUDE{ii:06d}'] = f'INCLUDE{ii:06d}'
                del dict[key]

        data_temp = deepcopy(dict.data)
        dict.data.clear()
        dict.data.update(include_placeholder_keys)
        dict.data.update(data_temp)

        return

    def _extract_expression(
        self,
        parsed_dict: CppDict,
        string: str,
    ) -> str:
        """Extracts a single expression

        Parses a string, checks whether it contains an expression, and if so, extracts the expression and replaces it with a placeholder.

        Parameters
        ----------
        parsed_dict : CppDict
            the CppDict instance the extracted expression shall be saved in
        string : str
            the string from which expressions shall be extracted and replaced by placeholders

        Returns
        -------
        str
            the string with all found expressions replaced by the respective placeholders
        """

        # Gatekeeper: Check whether minimum one reference is contained in string.
        # References are denoted using the '$' syntax familiar from shell programming.
        # Any key'd entries in a dict are considered variables and can be referenced.
        # If string does not contain minimum one reference, return.
        search_pattern = r'\$\w[\w\[\]]+'
        references = re.findall(search_pattern, string, re.MULTILINE)
        if not references:
            return string

        # Case 1: Reference
        # The string contains only a single plain reference (single reference to a key'd entry in the parsed dict).
        # If so, extract the single reference and return
        search_pattern = r'^\s*(\$\w[\w\[\]]+){1}\s*$'
        if match := re.search(search_pattern, string, re.MULTILINE):
            reference: str = match.groups()[0]
            # Replace the found reference in the string with the placeholder (EXPRESSION000000)
            # Note: For re.sub() to work properly we need to escape all special characters
            index = self.counter()
            placeholder = 'EXPRESSION%06i' % index
            _pattern = re.compile(re.escape(reference))
            string = re.sub(_pattern, placeholder, string)
            # Register the reference as expression in .expressions
            parsed_dict.expressions.update(
                {index: {
                    'index': index, 'expression': reference, 'name': placeholder
                }}
            )
            return string

        # Case 2: Expression
        # The string contains more than just a single reference -> Treat it as expression.
        # Expressions are strings that contain one or more reference but are not a single plain reference
        # (meaning they contain something in addition: An operator, a second reference, a constant, or whatever.).

        expression = string.strip()

        # Replace the found expression in the string with the placeholder (EXPRESSION000000)
        # Note: For re.sub() to work properly we need to escape all special characters
        # (covering both '$' as well as any mathematical operators in the expression)
        index = self.counter()
        placeholder = 'EXPRESSION%06i' % index
        _pattern = re.compile(re.escape(expression))
        string = re.sub(_pattern, placeholder, string)

        # Register the expression in .expressions
        parsed_dict.expressions.update(
            {index: {
                'index': index, 'expression': expression, 'name': placeholder
            }}
        )

        return string

    def _extract_expressions(
        self,
        parsed_dict: CppDict,
        arg: Union[MutableMapping, MutableSequence],
    ) -> Union[MutableMapping, MutableSequence]:
        """Finds and extracts expressions in a dict or list and replaces them with Placeholders.

        Finds expressions, extracts them, and replaces them with a placeholder in the form EXPRESSION000000.
        String values that contain minimum one $reference are identified as expressions.
        The extracted expressions are stored in .expressions as a key'd subdict with multiple elements {index:{'index': index, 'expression': expression, 'name': placeholder}}.
        index, therein, corresponds to the integer number in EXPRESSION000000.

        Parameters
        ----------
        parsed_dict : CppDict
            the CppDict instance the extracted expressions shall be saved in
        arg : Union[MutableMapping, MutableSequence]
            the dict or list containing values to be parsed for expressions

        Returns
        -------
        Union[MutableMapping, MutableSequence]
            the original dict or list, yet with all contained expressions being extracted and replaced by placeholders.
        """
        if isinstance(arg, MutableSequence):
            for index, _ in enumerate(arg):
                if isinstance(arg[index], (MutableMapping, MutableSequence)):
                    self._extract_expressions(parsed_dict, arg[index])
                else:
                    typed_value = self.parse_type(arg[index])
                    if isinstance(typed_value, str):
                        arg[index] = self._extract_expression(parsed_dict, arg[index])
        elif isinstance(arg, MutableMapping):
            for key in arg.keys():
                if isinstance(arg[key], (MutableMapping, MutableSequence)):
                    self._extract_expressions(parsed_dict, arg[key])
                else:
                    typed_value = self.parse_type(arg[key])
                    if isinstance(typed_value, str):
                        arg[key] = self._extract_expression(parsed_dict, arg[key])
        return arg


class XmlParser(Parser):
    """Parser to deserialize a string in XML format into a CppDict.
    """

    def __init__(
        self,
        add_node_numbering: bool = True,
    ):
        '''
        Implementation specific default configuration of XmlParser
        '''
        # Invoke base class constructor
        super().__init__()
        # Save default configuration as attributes
        self.add_node_numbering = add_node_numbering

    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        """Parses a string in XML format and deserializes it into a CppDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : CppDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        CppDict
            the parsed dict
        """

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(string, target_dict, comments)

        # +++PARSE XML++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Default configuration
        namespaces = {'xs': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'}
        root_tag = 'NOTSPECIFIED'

        # Create XML parser
        parser = ETCompatXMLParser()
        # Read root element from XML string
        root_element = fromstring(string.encode('utf-8'), parser)
        # Read root tag from XML string
        # there is a problem with .tag :
        # fromstring does not completely push all attributes into .attrib
        # only version, not xmlns
        # xmlns remains as {XMLNSCONTENT}ROOTTAG
        # re.sub to fix that temporarily
        # solution needed
        root_tag = re.sub(r'\{.*\}', '', root_element.tag) or root_tag
        # Read namespaces from XML string
        namespaces = dict(root_element.nsmap) or namespaces
        # Reformat None keys in namespaces to key 'None' (as string)
        temp_keys_copy = list(namespaces)
        for key in temp_keys_copy:
            if key is None:
                try:
                    value = namespaces[key]
                    del namespaces[key]
                    namespaces['None'] = value
                except Exception:
                    logger.exception(
                        "XmlParser.parseString(): Reformatting None keys in namespaces to key 'None' failed"
                    )

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Transform XML root node into dict

        parsed_dict.data = dict(self._parse_nodes(root_element, namespaces))

        # Document XML options inside the dict
        try:
            parsed_dict.data['_xmlOpts'] = {
                '_nameSpaces': namespaces,
                '_rootTag': root_tag,
                '_rootAttributes': dict(root_element.attrib.items()),
                '_addNodeNumbering': self.add_node_numbering,
            }

        except Exception:
            logger.exception('XmlParser.parseString(): Cannot write _nameSpaces to _xmlOpts')

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def _parse_nodes(
        self,
        root_element: Element,
        namespaces: MutableMapping,
    ) -> dict:
        """Recursively parses all nodes and saves the nodes' content in a dict
        """
        # Default case: Make all node tags temporarily unique by indexing them using BorgCounter
        node_tags = [
            re.sub(r'^(\{.*\})', '', node.tag)
            for node in root_element.findall('*', dict(namespaces))
        ]
        indexed_node_tags = []
        for item in node_tags:
            index = self.counter()
            indexed_node_tags.append(('%06i_%s' % (index, item), item))
        # indexed_node_tags.sort()

        content_dict = {}

        # Parse all nodes
        for index, item in enumerate(indexed_node_tags):
            # Read the node
            node_tag = item[0]

            if not self.add_node_numbering:
                # Non-default case: add_node_numbering has been set to False by the caller
                # -> remove the index again
                node_tag = re.sub(r'^\d{6}_', '', node_tag)

            nodes = root_element.findall('*', dict(namespaces))

            # The recursive part.
            # If there is a nested list, step in and resolve,
            # otherwise append node text to dict.
            if list(nodes[index]):
                # node contains child nodes
                content_dict[node_tag] = self._parse_nodes(nodes[index], namespaces)

            elif nodes[index].text is None or re.search(r'^[\s\n\r]*$', nodes[index].text or ''):
                # Node has either no content or contains an empty string <NODE ATTRIB=STRING><\NODE>
                # However, in order to be able to attach attributes to a node,
                # we still need to create a dict for the node, even if the node has no content.
                content_dict[node_tag] = {}

            else:
                # Node has content.
                # Unfortunately, multiline text is not properly represented by the text attribute of the Node class:
                # The indentation is made part of each line, which is nonsense.
                # Hence a small workaround: We split into lines, strip each line to get rid of the indentation,
                # and finally rebuild the text by concatenating the stripped lines.
                text = nodes[index].text
                if text is not None:
                    original_lines = text.splitlines(keepends=True)
                    stripped_lines = [line.strip() for line in original_lines]
                    text = ('\n'.join(stripped_lines)).strip()
                else:
                    text = ''
                content_dict[node_tag] = {'_content': text}

            # If the node contains attributes: Save the attributes
            # and merge with the contents
            if len(nodes[index].attrib) > 0:
                # Avoid empty strings in attributes
                # Might be substtituted by any kind of substitution later if required.
                attributes_dict = {
                    '_attributes':
                    {k: str(v)
                     for k, v in nodes[index].attrib.items()
                     if str(v) != ''}
                }

                if content_dict[node_tag] is None:
                    content_dict[node_tag] = attributes_dict
                else:
                    content_dict[node_tag].update(attributes_dict)

        # before returning the new dict, doublecheck that all of its elements are correctly typed.
        self.parse_types(content_dict)

        return content_dict
