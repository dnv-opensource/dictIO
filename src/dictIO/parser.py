import re
import os
from pathlib import Path
from typing import Any, MutableMapping, MutableSequence, Union
from xml.etree.ElementTree import Element
import logging

# from lxml.etree import register_namespace
from lxml.etree import ETCompatXMLParser, fromstring
from dictIO.utils.counter import BorgCounter

from dictIO.cppDict import CppDict


__ALL__ = ['Parser']

logger = logging.getLogger(__name__)


class Parser():
    '''
    Base Class for dict parsers.
    Dict parsers deserialize a string into a dict.
    Subclasses of Parser implement parsing of different, specifically formatted strings (see also Formatters).
    '''

    def __init__(self):
        self.counter = BorgCounter()
        self.source_file = None
        return

    @classmethod
    def get_parser(cls, source_file: Path = None):
        '''
        Factory method to return a Parser instance matching the file type intended to parse
        '''
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
        target_dict: CppDict = None,
        comments: bool = True,
    ) -> CppDict:
        # sourcery skip: inline-immediately-returned-variable
        '''
        Parses a file and deserializes it into a dict.
        Return type by default is CppDict, unless a specific Parser implementation supports a different dict type.
        '''
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        # @TODO: Activate raising FileNotFoundError in a new branch and create pull request for it.
        #        CLAROS, 2021-12-12
        # if not source_file.exists():
        #     raise FileNotFoundError(source_file)

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
        # sourcery skip: inline-immediately-returned-variable
        '''
        Parses a string and deserializes it into a dict.
        Return type by default is CppDict, unless a specific Parser implementation supports a different dict type.
        '''

        # +++VERIFY STRING CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Check that string is not empty.
        if (string is None) or (string == ''):
            logger.warning('Parser.parse_string(): String to parse is empty: %s' % string)

        # Create target dict in case no specific target dict was passed in
        if target_dict is None:
            logger.warning(
                'Parser.parse_string(): Target dict is None. Will create new target dict, however, with empty filename.'
            )
            target_dict = CppDict()

        # Create a local CppDict instance where the stringcontent is temporarily parsed into
        parsed_dict = CppDict(target_dict.source_file)

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to implement this part.

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to, finally, update the target dict!
        # (in the base class, however, this does not make sense - hence commented out)
        # target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def parse_type(self, arg: Any) -> Any:
        '''
        Parses arg containing a single value and returns the native single value type (str, int, float, boolean and None)
        '''

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
        if check == '':
            return ''

        # Simple placeholder or reserved expressions -> do nothing
        # Note: This if clause is important: It avoids that distinct placeholders like e.g.
        # '-' are interpreted as float (and then transformed to float .. what might even fail).
        if arg in ['-', '_', '.']:
            return arg

        # String numerals shall be converted to numbers (int and float)
        if re.search(r'^[+-]?\d+$', arg):                           # int
            return int(arg)
        if re.search(r'^[+-]?(\d+(\.\d*)?|\.\d+)$', arg):           # float
            return float(arg)
        if re.search(r'^[+-]?\d*(\.\d*)?([eE]?[-+]?\d+)?$', arg):   # float written as fpn like 1.e-03
            return float(arg)

        # Booleans and None types that are masked as strings
        # (such as 'False', 'false', 'True', 'true' and 'None')
        # shall be converted to its native Boolean or None type, respectively
        if re.search(r'^(True)$|^(true)$', arg.strip()):    # bool True
            return True
        if re.search(r'^(False)$|^(false)$', arg.strip()):  # bool False
            return False
        if re.search(r'^(None)$|^(none)$', arg.strip()):    # None
            return None

        # Any other string: return 'as is', but make sure extra quotes, if so, are stripped.
        # Note: Also any placeholder strings will fall into this category.
        # Returned 'as is' they are kept unchanged, what is in fact what we want here.
        return __class__.remove_quotes_from_string(arg)

    def parse_types(
        self, arg: Union[MutableMapping, MutableSequence]
    ) -> Union[MutableMapping, MutableSequence]:
        '''
        Parses a list or dict for contained single values and turns them into their native single value type (str, int, float, boolean and None).
        '''
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
    def remove_quotes_from_string(arg: str, all: bool = True) -> str:
        '''
        Removes quotes (single or double quotes) from the string object passed in.
        Not only leading and trailing quotes are removed; also any quotes inside a string, if so, are removed.
        '''
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

        # Remove quotes and return
        arg = re.sub(search_pattern, '', arg)
        return arg

    @staticmethod
    def remove_quotes_from_strings(
        arg: Union[MutableMapping, MutableSequence]
    ) -> Union[MutableMapping, MutableSequence]:
        '''
        Removes quotes (single or double quotes) from all string elements within the passed in argument arg.
        arg is expected to be a Mapping or Sequence type (e.g. a dict or list).
        The function traverses the passed in Mapping or Sequence recursively
        so that all strings in also nested dicts and lists are handled.
        '''
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
    '''
    Dict parser to deserialize a string in C++ dictionary format into a dict.
    Returned dict is of type CppDict.
    '''

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
        '''
        Parses a string in C++ dictionary format and deserializes it into a CppDict.
        '''

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict = super().parse_string(string, target_dict)

        # +++PARSE LINE CONTENT+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Split file content into lines and store them in the newly created CppDict instance
        parsed_dict.line_content = string.splitlines(keepends=True)

        # Extract line comments
        self.extract_line_comments(parsed_dict, comments)

        # Extract include directives
        self.extract_includes(parsed_dict)

        # +++PARSE BLOCK CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Concatenate all lines from line_content
        # As extracting block comments is easier with line endings still existing, at first we preserve them.
        self.convert_line_content_to_block_content(parsed_dict)     # preserves line endings

        # Extract block comments      ..and remove line endings right thereafter

        self.extract_block_comments(parsed_dict, comments)
        self.remove_line_endings_from_block_content(parsed_dict)

        # Extract string literals
        self.extract_string_literals(parsed_dict)

        # Extract expressions
        self.extract_expressions(parsed_dict)

        # Make sure that all delimiters are surrounded by at least one space before and after
        # to ensure they are properly identified when we tokenize block_content
        self.separate_delimiters(parsed_dict)

        # +++PARSE TOKENS+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Split block_content into tokens
        self.convert_block_content_to_tokens(parsed_dict)

        # Determine the hierarchic level of each token and assign it to the token (the hierarchy is dictated by the sequence of delimiters)
        self.determine_token_hierarchy(parsed_dict)

        # Parse the hierarchic tokens
        self.convert_tokens_to_dict(parsed_dict)

        # Insert back string literals
        self.insert_string_literals(parsed_dict)

        # +++CLEAN PARSED DICTIONARY++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.clean(parsed_dict)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def extract_line_comments(self, dict: CppDict, comments: bool):
        '''
        Finds C++ line comments (// line_comment), extracts them,
        and replaces them with a placeholder in the form LINECOMMENT000000 .
        The extracted line comments are stored in .line_comments as key value pairs {index:line_comment}.
        index, therein, corresponds to the integer number in LINECOMMENT000000.
        '''
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

    def extract_includes(self, dict: CppDict):
        '''
        Finds include directives (#include file), extracts them,
        and replaces the complete line where the include directive was found
        with a placeholder in the form #INCLUDE000000 .
        The absolute path to the file referenced in the include directive is determined.
        The original line with its include directive as well as the absolute path to the file to include
        is then stored as a key-value pair in dict.includes, in the form {index:(include_directive, path)}
               index, therein, corresponds to the integer number in #INCLUDE000000.
            2. Just the path in .includeList
        '''

        for index, line in enumerate(dict.line_content):
            if re.search(r'^\s*#\s*include', line):
                ii = self.counter()
                dict.line_content[index] = 'INCLUDE%06i\n' % ii

                include_file_name = re.sub(r'(^\s*#\s*include\s*|\s*$)', '', line)
                include_file_name = __class__.remove_quotes_from_string(include_file_name)

                include_file = Path.joinpath(dict.path, include_file_name)

                include_directive = line
                if line[-1] == '\n':
                    include_directive = line[:-1]

                dict.includes.update({ii: (include_directive, include_file)})

        return

    def convert_line_content_to_block_content(self, dict: CppDict):
        '''
        concatenates all lines from line_content to one long string (text block) and stores the result in block_content
        '''
        dict.block_content = ''.join(dict.line_content)
        dict.line_content.clear()
        return

    def remove_line_endings_from_block_content(self, dict: CppDict):
        '''
        removes all line endings in .block_content and substuitutes them by single spaces.
        '''
        dict.block_content = re.sub(r'\n', ' ', dict.block_content).strip()
        return

    def extract_block_comments(self, dict: CppDict, comments: bool):
        '''
        Finds C++ block comments (/* block_comment */), extracts them,
        and replaces them with a placeholder in the form BLOCKCOMMENT000000 .
        The extracted block comments are stored in .block_comments as key value pairs {index:block_comment}.
        index, therein, corresponds to the integer number in BLOCKCOMMENT000000.
        '''

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

    def extract_string_literals(self, dict: CppDict):
        '''
        Finds string literals in .block_content.
        Any substrings within .block_content that are surrounded by single quotes are identified as string literals.
        The function extracts these from .block_content and
        replaces them with a placeholder in the form STRINGLITERAL000000 .
        The extracted string literals are stored in .string_literals as key value pairs {index:string_literal}.
        index, therein, corresponds to the integer number in STRINGLITERAL000000.
        '''
        string_literals = re.findall(r'\'.*?\'', dict.block_content, re.MULTILINE)

        dict.string_literals = {
            self.counter(): __class__.remove_quotes_from_string(s)
            for s in string_literals
        }

        for index, string_literal in dict.string_literals.items():
            dict.block_content = re.sub(
                '\'' + re.escape(string_literal) + '\'',
                'STRINGLITERAL%06i' % index,
                dict.block_content
            )
        return

    def extract_expressions(self, dict: CppDict):

        dict.expressions = {}

        # Step 1: Find expressions in .block_content .
        # Expressions are double quoted strings that contain minimum one reference.
        # References are denoted using the '$' syntax familiar from shell programming.
        # Any key'd entries in a dict are considered variables and can be referenced.
        search_pattern = r'\".*?\"'
        expressions = re.findall(search_pattern, dict.block_content, re.MULTILINE)
        for expression in expressions:
            if '$' in expression:

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

        # Step 2: Find remaining 'single' references in .block_content (single references to key'd entries that are NOT in double quotes).
        search_pattern = r'\$\w[\w\[\]]+'
        references = re.findall(search_pattern, dict.block_content, re.MULTILINE)
        for reference in references:

            index = self.counter()
            placeholder = 'EXPRESSION%06i' % index

            # Replace all occurances of the reference in .block_content with the placeholder (EXPRESSION000000)
            # Note: For re.sub() to work properly we need to escape the '$'
            search_pattern = re.compile(re.escape(reference))
            dict.block_content = re.sub(
                search_pattern, placeholder, dict.block_content
            )                                                       # replace reference in .block_content with placeholder

            # Register the reference as expression in .expressions
            dict.expressions.update(
                {index: {
                    'index': index, 'expression': reference, 'name': placeholder
                }}
            )

        return

    def separate_delimiters(self, dict: CppDict, delimiters=None):
        '''
        Parses .block_content for occurences of the delimiters passed in, and strips any spaces surrounding each
        delimiter to exactly one single space before and one single space after the delimiter.
        Further, it removes all line endings from .block_content and eventually replaces them with single spaces.
        '''
        # Further explanation:
        # After separate_delimiters() returns, .block_content contains only
        #  - words (with single char delimiters also considered a 'word' here)    and
        #  - single spaces
        # Hence, calling separate_delimiters() is a preparatory step before
        # decomposing .block_content into a list of tokens with re.split('\s').
        # It ensures that re.split('\s') generates tokens containing one single word each (or a single char delimiter)
        # but no any 'waste' tokens with spaces, tabs or line endings will be generated.

        if delimiters is None:
            delimiters = dict.delimiters

        # Insert at least one \s around every char in list
        for char in delimiters:
            dict.block_content = re.sub(
                str(r'(\%s)' % char), str(' %s ' % char), dict.block_content
            )

        # Substitute all \s+ to \s
        # This turns multiple spaces into one single space.
        # However, as \s+ matches ANY whitespace character (\s+ is equivalent to [ \t\n\r\f\v]+)
        # this also eliminates all line endings (\n). As explained above, this is well intended though.
        dict.block_content = re.sub(r'\s+', ' ', dict.block_content)

        return

    def convert_block_content_to_tokens(self, dict: CppDict):

        dict.tokens = [(0, i) for i in re.split(r'\s', dict.block_content)]
        dict.block_content = ''

        return

    def determine_token_hierarchy(self, dict: CppDict):
        # sourcery skip: use-join
        '''
        make hierarchy and test the indentation
        '''
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
                'determine_token_hierarchy: opening and closing delimiters in dict %s are not balanced:\n%s'
                % (dict.name, counted)
            )

        return

    def convert_tokens_to_dict(self, dict: CppDict):

        dict.update(self.parse_tokenized_dict(dict))
        dict.tokens.clear()

        return

    def parse_tokenized_dict(
        self,
        dict: CppDict,
        tokens: MutableSequence = None,
        level: int = 0,
    ) -> dict:
        '''
        Parses a tokenized dict and returns the parsed dict.
        '''
        # sourcery skip: remove-redundant-pass

        # Parse all tokens, identify the element within the tokenized dictionary each token represents or belongs to,
        # translate related tokens into the element's type and store it in local dict (parsed_dict).
        #
        # Following elements within the tokenized dictionary are identified and parsed:
        # - nested data struct (list or dict)
        # - key value pair
        # - comment (string literal containing 'COMMENT')
        #
        # After all tokens have successfully been parsed, return the parsed dict.
        #
        # Note: To allow recursive calls in case of nested dicts, parsed_dict is declared as a local variable
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
                closing_bracket = self.find_companion(dict, tokens[token_index][1])
                closing_level = tokens[token_index][0]

                # Create a temporary token list for just the nested data struct, containing
                # all tokens from the opening bracket (first token) to the closing bracket (last token)
                temp_tokens = []
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
                    temp_tokens.append(tokens[token_index + i])
                    i += 1
                temp_tokens.append(tokens[token_index + i])

                # Do a Syntax-Check at the closing bracket of the data struct.
                # As the syntax for lists and dicts is different, the syntax check is type specific:
                # list:
                # Proof that list properly ends with ';'
                # (= assert that closing bracket of the list is followed by ';')
                if temp_tokens[-1][1] == ')' and tokens[token_index + i + 1][1] not in [';', ')']:
                    # log error: Missing ';' after list
                    logger.warning(
                        'mis-spelled expression / missing \';\' around \"%s\"' % ' '.join(
                            [name] + [t[1]
                                      for t in temp_tokens] + [tokens[token_index + i + 1][1]]
                        )
                    )
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
                            % ' '.join([name] + [t[1] for t in temp_tokens])
                        )

                # Parse the tokenized data struct, translate it into its type (list or dict),
                # and update parsed_dict with the new list or dict.
                # Again, the code is type specific depending on whether the parsed data struct is a list or a dict.
                # list:
                if temp_tokens[0][1] == '(':
                    # Check whether the list is empty
                    if len(temp_tokens) < 3:
                        # is empty (contains only opening and closing bracket)
                        # update parsed_dict with just the empty list
                        parsed_dict.update({name: []})
                    else:
                        # has content
                        # parse the nested list
                        nested_list = self.parse_tokenized_list(dict, temp_tokens, level=level + 1)
                        # update parsed_dict with the nested list
                        parsed_dict.update({name: nested_list})

                #  dict:
                elif temp_tokens[0][1] == '{':
                    # parse the nested dict (recursion)
                    nested_dict = self.parse_tokenized_dict(
                        dict, temp_tokens[1:-1], level=level + 1
                    )
                    # update parsed_dict with the nested dict
                    parsed_dict.update({name: nested_dict})

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
                # and then copy the tokens into a temporary token list:
                # (..except line comments, which are skipped)
                temp_tokens = []
                i = 0
                last_index = None
                while (
                    not re.match('^.*COMMENT.*$', str(tokens[token_index - i][1]))
                    and len(temp_tokens) <= 2
                ):
                    temp_tokens.append(tokens[token_index - i])
                    i += 1
                # reverse token list
                temp_tokens = temp_tokens[::-1]
                # Before proceeding with reading key and value, make sure that what was parsed
                # really represents a key-value pair, consisting of three elements key, value and ';'
                if not (
                    len(temp_tokens) >= 3 and len(temp_tokens[0]) == 2 and len(temp_tokens[1]) == 2
                ):
                    logger.warning(
                        'CppParser.parse_tokenized_dict(): tokens skipped: %s' %
                        (str(temp_tokens))
                    )
                else:
                    if len(temp_tokens) > 3:
                        logger.warning(
                            'CppParser.parse_tokenized_dict(): '
                            'more tokens in key-value pair than expected: %s' % (str(temp_tokens))
                        )
                    # read the name (key) (first token, by convention)
                    name = temp_tokens[0][1]
                    # read the value (second token, by convention)
                    value = self.parse_type(temp_tokens[1][1])
                    # update parsed_dict with the parsed key value pair
                    # Note: Following call to .update would be greedy, if parsed_dict would be declared as global variable.
                    # This exactly is why parsed_dict is declared as local variable in parse_tokenized_dict().
                    # Doing so, an empty local dict is created with each call to parse_tokenized_dict(),
                    # and that is, also with each RECURSIVE call.
                    # As every recursive call passes in a temporary token list containing only the nested
                    # data struct, updating a key effects the current (and local) parsed_dict only.
                    # Every key hence is being updated exclusively within its own local context; ambiguous occurences of keys are avoided.
                    if isinstance(name, int):
                        print('shit')
                        pass
                    parsed_dict.update({name: value})

            # Comment
            # As comments cannot be stored "inline" in a structured dictionary
            # the same way as they were stored inline in the dict file parsed,
            # they are stored in parsed_dict in the form of distinct comment keys.
            # As the sequence of keys added to parsed_dict exactly follows the sequence of the tokens parsed,
            # the location of comments in relation to their preceding tokens is preserved.
            # The original comments are back-inserted later in insert_block_comments() and insert_line_comments(), respectively.
            # For now, create an entry with the placeholder string of the comment assigned to both, key and value.
            elif re.match('^.*COMMENT.*$', str(tokens[token_index][1])):
                parsed_dict.update({tokens[token_index][1]: tokens[token_index][1]})

            # Include directive
            # Create an entry with the placeholder string of the include directive assigned to both, key and value.
            elif re.match('^.*INCLUDE.*$', str(tokens[token_index][1])):
                parsed_dict.update({tokens[token_index][1]: tokens[token_index][1]})

            # -(Unknown element)
            else:
                pass

            # Iterate to next token
            token_index += 1

        # Return the parsed dict
        return parsed_dict

    def parse_tokenized_list(
        self,
        dict: CppDict,
        tokens: MutableSequence = None,
        level: int = 0,
    ) -> list:
        '''
        Parses a tokenized list and returns the parsed list.
        '''
        # sourcery skip: remove-redundant-if, remove-redundant-pass

        # Parse all tokens, identify the element within the tokenized list each token represents or belongs to,
        # translate related tokens into the element's type and store it in local list (parsed_list).
        #
        # Following elements within the tokenized list are identified and parsed:
        # - nested data struct (list or dict)
        # - single value type
        #
        # After all tokens have successfully been parsed, return the parsed list.
        #
        # Notes:
        # - To allow recursive calls in case of nested lists, parsed_list is declared as a local variable
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
                closing_bracket = self.find_companion(dict, tokens[token_index][1])
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
                    # Note: This is different for a list nested insode a dict: Then, the closing
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
                        nested_list = self.parse_tokenized_list(
                            dict, temp_tokens, level=level + 1
                        )                                           # (recursion)
                                                                    # add nested list to parsed_list
                        parsed_list.append(nested_list)
                                                                    #  dict:
                elif temp_tokens[0][1] == '{':
                                                                    # parse the nested dict
                    nested_dict = self.parse_tokenized_dict(
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

    def find_companion(self, dict: CppDict, bracket: str) -> str:
        companion = ''
        for item in dict.brackets:
            if bracket == item[0]:
                companion = item[1]
            elif bracket == item[1]:
                companion = item[0]
        return companion

    def insert_string_literals(self, dict: CppDict):
        '''
        substitutes STRINGLITERAL placeholders in the dict with the corresponding entry from dict.string_literals
        working on: dict.data, dict.string_literals
        invoked by: read
        '''

        for index, string_literal in dict.string_literals.items():
            # Properties of the expression to be evaluated
            placeholder = 'STRINGLITERAL%06i' % index   # STRINGLITERAL000000
                                                        # The entry from dict.string_literals is parsed once again, so that entries representing single value native types
                                                        # (such as bool ,None, int, float) are transformed to its native type, accordingly.
            value = self.parse_type(string_literal)

            # Replace all occurences of placeholder within the dictionary with the original string literal.
            # Note: As iter_find_key() is non-greedy and returns the key of only the first occurance of placeholder it finds,
            # we need to loop until we found and replaced all occurances of placholder in the dict
            # and iter_find_key() does not find any more occurances.
            global_key = dict.iter_find_key(query=placeholder)
            while global_key:
                # Back insert the string literal
                dict.iter_set_key(global_key, value)
                global_key = dict.iter_find_key(query=placeholder)
        dict.string_literals.clear()
        return

    def clean(self, dict: CppDict):
        '''
        Removes keys that are written by the CppFormatter for documentation purposes
        but shall not be created as keys in dict.data.
        In specific, it is the following two keys that get deleted if existing:
        _variables
        _includes
        '''
        if '_variables' in dict.data.keys():
            del dict.data['_variables']
        if '_includes' in dict.data.keys():
            del dict.data['_includes']


class FoamParser(CppParser):
    '''
    Dict parser to deserialize a file in Foam dictionary format into a dict.
    Returned dict is of type CppDict.
    '''

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
        '''
        Parses a string in Foam dictionary format and deserializes it into a CppDict.
        '''

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(string, target_dict, comments)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        # target_dict.merge(parsed_dict)  # Not necessary. Done in base class CppDictParser already.

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict


# @TODO: To be implemented
class JsonParser(Parser):
    '''
    Dict parser to deserialize a file in json format into a dict.
    Returned dict is of type CppDict.
    '''

    def __init__(self):
        '''
        Implementation specific default configuration of JsonParser
        '''
        # Invoke base class constructor
        super().__init__()

    # @TODO: To be implemented
    def parse_string(
        self,
        string: str,
        target_dict: CppDict,
        comments: bool = True,
    ) -> CppDict:
        '''
        Parses a string in Json dictionary format and deserializes it into a CppDict.
        '''

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(string, target_dict, comments)

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Place implementation specific code here

        # forced quotes
        # string = re.sub(r'\b([\w\d_]+)\b', '"\\1"', string)
        '''
        # @TODO: To be implemented
        parsed_dict.data = json.load(
            file_content,
            skipkeys=True,
            ensure_ascii=True,
            check_circular=True,
            allow_nan=True,
            sort_keys=True,
            indent=4,
            separators=(',', ':')
        )
        '''

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict


class XmlParser(Parser):
    '''
    Dict parser to deserialize a file in XML format into a dict.
    Returned dict is of type CppDict.
    '''

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
        '''
        Parses a string in XML dictionary format and deserializes it into a CppDict.
        '''

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
        root_tag = root_element.tag or root_tag

        # Read namespaces from XML string
        namespaces = dict(root_element.nsmap) or namespaces
        # Reformat 'None' keys in namespaces to empty string keys
        temp_keys_copy = [key for key in namespaces]
        for key in temp_keys_copy:
            if key is None:
                try:
                    value = namespaces[key]
                    del namespaces[key]
                    namespaces.update({'': value})
                except Exception:
                    logger.exception(
                        'XmlParser.parseString(): Reformatting None keys in namespaces to empty string keys failed'
                    )

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Transform XML root node into dict

        parsed_dict.data = dict(self.parse_nodes(root_element, namespaces))

        # Document XML options inside the dict
        try:
            parsed_dict.data.update(
                {
                    '_xmlOpts': {
                        '_nameSpaces': namespaces,
                        '_rootTag': root_tag,
                        '_rootAttributes': {k: v
                                            for k, v in root_element.attrib.items()},
                        '_addNodeNumbering': self.add_node_numbering,
                    }
                }
            )
        except Exception:
            logger.exception('XmlParser.parseString(): Cannot write _nameSpaces to _xmlOpts')

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def parse_nodes(
        self,
        root_element: Element,
        namespaces: MutableMapping,
    ) -> dict:
        '''
        Recursively parses all nodes and saves the nodes' content in a dict
        '''
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
            if len(list(nodes[index])) == 0:
                # Node contains no chid nodes <NODE ATTRIB=STRING \>
                if nodes[index].text is None or re.search(r'^[\s\n\r]*$', nodes[index].text or ''):
                    # Node has either no content or contains an empty string <NODE ATTRIB=STRING><\NODE>
                    # However, in order to be able to attach attributes to a node,
                    # we still need to create a dict for the node, even if the node has no content.
                    content_dict.update({node_tag: None})
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
                    content_dict.update({node_tag: {'_content': text}})

            else:
                # node contains child nodes
                content_dict.update({node_tag: self.parse_nodes(nodes[index], namespaces)})

            # If the node contains attributes: Save the attributes
            # and merge with the contents
            if len(nodes[index].attrib) > 0:
                # Avoid empty strings in attributes
                # Might be substtituted by any kind of substitution later if required.
                attributes_dict = {
                    '_attributes':
                    {k: str(v)
                     for k, v in nodes[index].attrib.items()
                     if len(str(v)) != 0}
                }

                if content_dict[node_tag] is None:
                    content_dict[node_tag] = attributes_dict
                else:
                    content_dict[node_tag].update(attributes_dict)

        # before returning the new dict, doublecheck that all of its elements are correctly typed.
        self.parse_types(content_dict)

        return content_dict
