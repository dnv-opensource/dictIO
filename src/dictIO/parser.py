"""Parsers for different dictionary file formats."""

# ruff: noqa: ARG002
from __future__ import annotations

import logging
import re
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from re import Match, Pattern
from typing import (
    TYPE_CHECKING,
    cast,
)

from lxml.etree import ETCompatXMLParser, fromstring
from lxml.etree import _Element as LxmlElement  # pyright: ignore[reportPrivateUsage]

from dictIO import SDict
from dictIO.types import TKey, TSingleValue, TValue
from dictIO.utils.counter import BorgCounter

if TYPE_CHECKING:
    import os

__ALL__ = ["Parser", "NativeParser", "FoamParser", "JsonParser", "XmlParser"]

logger = logging.getLogger(__name__)


class Parser:
    """Base Class for parsers.

    Parsers deserialize a string into a SDict.
    Subclasses of Parser implement parsing of different, specifically formatted strings (see also Formatters).
    """

    def __init__(self) -> None:
        self.counter = BorgCounter()
        self.source_file: Path | None = None
        return

    @classmethod
    def get_parser(cls, source_file: Path | None = None) -> Parser:
        """Return a Parser instance matching the type of the source file to be parsed (factory method).

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
            if source_file.suffix == ".foam":  # .foam -> FoamParser
                return FoamParser()
            if source_file.suffix == ".json":  # .json -> JsonParser
                return JsonParser()
            if source_file.suffix in [
                ".xml",
                ".ssd",
            ]:  # .xml  or  OSP .ssd -> XmlParser
                return XmlParser()

        # 2. If no source file is passed, return NativeParser as default / fallback
        return NativeParser()  # default

    def parse_file(
        self,
        source_file: str | os.PathLike[str],
        target_dict: SDict[TKey, TValue] | None = None,
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:
        """Parse a file and deserialize it into a dict.

        Parameters
        ----------
        source_file : Union[str, os.PathLike[str]]
            name of the dict file to be parsed
        target_dict : SDict[TKey, TValue], optional
            the target dict the parsed dict file shall be merged into, by default None
        comments : bool, optional
            reads comments from source file, by default True

        Returns
        -------
        SDict
            the parsed dict

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f"source_file not found: {source_file}")
            raise FileNotFoundError(source_file)

        self.source_file = source_file

        # Check whether file to read from exists.
        if not self.source_file.exists():
            logger.warning(
                f"Parser.parse_file(): File or path does not exist: '{source_file}'. Empty dict will be returned."
            )
            file_content = ""
        else:
            with self.source_file.open("r") as f:
                file_content = f.read()

        # Create target dict in case no specific target dict was passed in
        if target_dict is None:
            target_dict = SDict(source_file)
        else:
            target_dict.source_file = source_file.absolute()

        # one final check that the source file exists
        if not self.source_file.exists():
            logger.error(f"Parser.parse_file(): Source file does not exist ('{source_file}').")

        # Parse file content
        parsed_dict = self.parse_string(
            string=file_content,
            target_dict=target_dict,
            comments=comments,
        )

        return parsed_dict

    def parse_string(
        self,
        string: str,
        target_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:  # sourcery skip: lift-return-into-if
        """Parse a string and deserialize it into a SDict.

        Note: Override this method when implementing a specific Parser.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : SDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        SDict
            the parsed dict
        """
        # +++VERIFY STRING CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Check that string is not empty.
        if not string:
            logger.warning(f"Parser.parse_string(): String to parse is empty: {string}")

        # Create a local SDict instance where the stringcontent is temporarily parsed into
        parsed_dict = SDict(target_dict.source_file) if target_dict.source_file else target_dict

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to implement this part.

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++

        # Specific Parser implementations need to, finally, update the target dict!
        # (in the base class, however, this does not make sense - hence commented out)
        # target_dict.merge(parsed_dict)  # noqa: ERA001

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def parse_value(
        self,
        arg: TValue,
    ) -> TSingleValue:
        """Parse a single value.

        Parses a single value and casts it to its native type (TSingleValue = str | int | float | bool | None).

        Parameters
        ----------
        arg : TValue
            the value to be parsed

        Returns
        -------
        TSingleValue
            the value casted to its native type (TSingleValue = str | int | float | bool | None)
        """
        # Numbers (int and float) are returned without conversion
        if isinstance(arg, int) and not isinstance(arg, bool):  # int
            return arg
        if isinstance(arg, float):  # float
            return arg

        # Boolean and None types are returned without conversion
        if isinstance(arg, bool):  # bool
            return arg
        if arg is None:  # None
            return arg

        # Any other non-string type: Return without conversion
        if not isinstance(arg, str):
            return arg

        # String: Convert the string content to its native type, where possible.
        # The following starts a filter cascade, hence the sequence is important,
        # otherwise latter clauses would produce unreasonable matches!

        # Empty string
        check: str = self.remove_quotes_from_string(arg)
        if not check:
            return ""

        # Simple placeholder or reserved expressions -> do nothing
        # Note: This if clause is important: It avoids that distinct placeholders like e.g.
        # '-' are interpreted as float (and then transformed to float .. what might even fail).
        if arg in ["-", "_", "."]:
            return arg

        # String numbers shall be converted to numbers (int and float)
        if re.search(r"^[+-]?\d+$", arg):  # int
            return int(arg)
        if re.search(r"^[+-]?(\d+(\.\d*)?|\.\d+)$", arg):  # float
            return float(arg)
        if re.search(r"^[+-]?\d*(\.\d*)?([eE]?[-+]?\d+)?$", arg):  # float written as fpn like 1.e-03
            return float(arg)

        # Booleans and None types that are masked as strings
        # ('True', 'true', 'False', 'false', 'ON', 'on', 'OFF', 'off', 'None', 'none', 'NULL', 'null')  # noqa: ERA001
        # shall be converted to its native Boolean or None type, respectively
        if re.search(r"^(true)$", arg.strip().lower()):  # True
            return True
        if re.search(r"^(false)$", arg.strip().lower()):  # False
            return False
        if re.search(r"^(on)$", arg.strip().lower()):  # OpenFOAM 'on' -> True
            return True
        if re.search(r"^(off)$", arg.strip().lower()):  # OpenFOAM 'off' -> False
            return False
        if re.search(r"^(none)$", arg.strip().lower()):  # None
            return None
        if re.search(r"^(null)$", arg.strip().lower()):  # C++ 'NULL' or JSON 'null' -> None
            return None

        # Any other string: return 'as is', but make sure extra quotes, if so, are stripped.
        # Note: Also any placeholder strings will fall into this category.
        # Returned 'as is' they are kept unchanged, what is in fact what we want here.
        return self.remove_quotes_from_string(arg)

    def parse_values(self, arg: MutableMapping[TKey, TValue] | MutableSequence[TValue]) -> None:
        """Parse multiple values.

        Parses all values inside a dict or list and casts them to its native types (str, int, float, bool or None).
        The function traverses the passed in dict or list recursively
        so that all values in also nested dicts and lists are parsed.

        Parameters
        ----------
        arg : Union[MutableMapping[TKey, TValue], MutableSequence[TValue]]
            the dict or list containing the values to be parsed and casted to its native types
            (str, int, float, bool or None)

        """
        if isinstance(arg, MutableMapping):  # Dict
            for key in list(arg.keys()):  # work on a copy of keys
                if isinstance(arg[key], MutableMapping | MutableSequence):
                    self.parse_values(cast(MutableMapping[TKey, TValue] | MutableSequence[TValue], arg[key]))
                else:
                    arg[key] = self.parse_value(arg[key])
        else:  # List
            for index in range(len(arg)):
                if isinstance(arg[index], MutableMapping | MutableSequence):
                    self.parse_values(cast(MutableMapping[TKey, TValue] | MutableSequence[TValue], arg[index]))
                else:
                    arg[index] = self.parse_value(arg[index])
        return

    def parse_key(
        self,
        arg: str,
    ) -> TKey:
        """Parse a single key.

        Parses a single key and casts it to its native type (TKey = str | int).

        Parameters
        ----------
        arg : str
            the value to be parsed

        Returns
        -------
        TKey
            the value casted to its native type (TKey = str | int)
        """
        key: TSingleValue = self.parse_value(arg)
        if not isinstance(key, TKey):
            raise TypeError(f"Key '{key}' is not of type TKey. Found type: {type(key)}")
        return key

    @staticmethod
    def remove_quotes_from_string(
        arg: str,
        *,
        all_quotes: bool = False,
    ) -> str:
        """Remove quotes from a string.

        Removes quotes (single and double quotes) from the string object passed in.

        Parameters
        ----------
        arg : str
            the string with quotes
        all_quotes : bool, optional
            if true, all quotes inside the string will be removed (not only leading and trailing quotes),
            by default False

        Returns
        -------
        str
            the string with quotes being removed
        """
        search_pattern: Pattern[str]
        if all_quotes:  # noqa: SIM108
            # Removes ALL quotes in a string:
            # Not only leading and trailing quotes, but also quotes inside a string are removed.
            search_pattern = re.compile(r"[\'\"]")
        else:
            # Removes only leading and trailing quotes. Quotes inside a string are kept.
            search_pattern = re.compile(r'(^[\'\\"]{1}|[\'\\"]{1}$)')

        return re.sub(search_pattern, "", arg)

    @staticmethod
    def remove_quotes_from_strings(
        arg: MutableMapping[TKey, TValue] | MutableSequence[TValue],
    ) -> MutableMapping[TKey, TValue] | MutableSequence[TValue]:
        """Remove quotes from multiple strings.

        Removes quotes (single and double quotes) from all string objects inside a dict or list.
        The function traverses the passed in dict or list recursively
        so that all strings in also nested dicts and lists are processed.


        Parameters
        ----------
        arg : Union[MutableMapping[TKey, TValue], MutableSequence[TValue]]
            the dict or list containing strings the quotes in which shall be removed

        Returns
        -------
        Union[MutableMapping[TKey, TValue], MutableSequence[TValue]]
            the original dict or list, yet with quotes in all strings being removed

        """
        if isinstance(arg, MutableMapping):  # Dict
            for key in list(arg.keys()):  # work on a copy of keys
                if isinstance(arg[key], MutableMapping | MutableSequence):  # dict or list
                    arg[key] = Parser.remove_quotes_from_strings(arg[key])  # (recursion)
                elif isinstance(arg[key], str):  # str
                    arg[key] = Parser.remove_quotes_from_string(arg[key])
        else:  # List
            for index in range(len(arg)):
                if isinstance(arg[index], MutableMapping | MutableSequence):  # dict or list
                    arg[index] = Parser.remove_quotes_from_strings(arg[index])  # (recursion)
                elif isinstance(arg[index], str):  # str
                    arg[index] = Parser.remove_quotes_from_string(arg[index])

        return arg


class NativeParser(Parser):
    """Parser to deserialize a string in dictIO native file format into a SDict."""

    def __init__(self) -> None:
        """Define default configuration for NativeParser."""
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:
        """Parse a string in dictIO native file format and deserialize it into a SDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : SDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        SDict
            the parsed dict
        """
        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict = super().parse_string(string, target_dict)

        # +++PARSE LINE CONTENT+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Split file content into lines and store them in the newly created SDict instance
        parsed_dict.line_content = string.splitlines(keepends=True)

        # Extract line comments
        self._extract_line_comments(
            s_dict=parsed_dict,
            comments=comments,
        )

        # Extract include directives
        self._extract_includes(parsed_dict)

        # +++PARSE BLOCK CONTENT++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Concatenate all lines from line_content
        # As extracting block comments is easier with line endings still existing, at first we preserve them.
        self._convert_line_content_to_block_content(parsed_dict)  # preserves line endings

        # Extract block comments      ..and remove line endings right thereafter

        self._extract_block_comments(
            s_dict=parsed_dict,
            comments=comments,
        )
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

        # Determine the hierarchic level of each token and assign it to the token
        # (the hierarchy is dictated by the sequence of delimiters)
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

    def _extract_line_comments(
        self,
        s_dict: SDict[TKey, TValue],
        *,
        comments: bool,
    ) -> None:
        """Find and extract C++ line comments (// ..) from dict.line_content, and replace them with Placeholders.

        Finds C++ line comments (// line_comment), extracts them,
        and replaces the complete line with a placeholder in the form LINECOMMENT000000 .
        The extracted line comments are stored in .line_comments as key value pairs {index:line_comment}.
        index, therein, corresponds to the integer number in LINECOMMENT000000.

        Parameters
        ----------
        s_dict : SDict
            dict to be processed. _extract_line_comments() works on dict.line_content
        comments : bool
            If False, line comments will be removed
            (they get replaced by an empty placeholder then, which in effect removes them).
        """
        for index, line in enumerate(s_dict.line_content):
            # if it is a line comment or just a "http://"?
            if re.search(r"(?<!:)/{2}.*$", line):
                # if re.search(r'/{2}.*$', line):
                key = self.counter()
                # Search for only the FIRST occurrence of '//' in the line.
                # From there, consider all chars until line ending as ONE comment.
                line_comment = re.findall("/{2}.*$", line)[0]
                s_dict.line_comments.update({key: line_comment})
                placeholder = "LINECOMMENT%06i" % key
                if not comments:
                    placeholder = ""
                # Replace line comment with placeholder
                s_dict.line_content[index] = s_dict.line_content[index].replace(line_comment, placeholder)

        return

    def _extract_includes(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Find and extract #include directives from dict.line_content, and replace them with Placeholders.

        Finds #includes directives (#include file), extracts them,
        and replaces the complete line where the include directive was found
        with a placeholder in the form #INCLUDE000000.
        The absolute path to the file referenced in the include directive is determined.
        The original line with its include directive as well as the absolute path to the file to include
        is then stored as a key-value pair in dict.includes, in the form
        {index:(include_directive, include_file_name, include_file_path)}
        index, therein, corresponds to the integer number in #INCLUDE000000.

        Parameters
        ----------
        s_dict : SDict
            dict to be processed. _extract_includes() works on dict.line_content
        """
        for index, line in enumerate(s_dict.line_content):
            if re.search(r"^\s*#\s*include", line):
                ii = self.counter()
                s_dict.line_content[index] = "INCLUDE%06i\n" % ii

                include_file_name = re.sub(
                    r"(^\s*#\s*include\s*|\s*$)",
                    "",
                    line,
                )
                include_file_name = self.remove_quotes_from_string(include_file_name)

                include_file_path = Path.joinpath(s_dict.path, include_file_name)

                include_directive = line
                if line[-1] == "\n":
                    include_directive = line[:-1]

                s_dict.includes.update({ii: (include_directive, include_file_name, include_file_path)})

        return

    def _convert_line_content_to_block_content(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Concatenate all lines from line_content.

        Concatenate all lines from line_content to one long string (text block)
        and store the result in block_content.
        """
        s_dict.block_content = "".join(s_dict.line_content)
        s_dict.line_content.clear()
        return

    def _remove_line_endings_from_block_content(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Remove all line endings in .block_content and substuitute them by single spaces."""
        s_dict.block_content = re.sub(
            r"\n",
            " ",
            s_dict.block_content,
        ).strip()
        return

    def _extract_block_comments(
        self,
        s_dict: SDict[TKey, TValue],
        *,
        comments: bool,
    ) -> None:
        """Find and extract C++ block comments (/* .. */) from dict.block_content, and replace them with Placeholders.

        Finds C++ block comments (/* block_comment */), extracts them,
        and replaces them with a placeholder in the form BLOCKCOMMENT000000.
        The extracted block comments are stored in .block_comments as key value pairs {index:block_comment}.
        index, therein, corresponds to the integer number in BLOCKCOMMENT000000.

        Parameters
        ----------
        s_dict : SDict
            dict to be processed. _extract_block_comments() works on dict.block_content
        comments : bool
            If False, block comments will be removed
            (they get replaced by an empty placeholder then, which in effect removes them).
        """
        block_comments = re.findall(r"/\*[\w\W\d\D\s]*?\*/", s_dict.block_content, re.MULTILINE)
        s_dict.block_comments = {i: block_comments[i] for i in range(len(block_comments))}

        for key, block_comment in s_dict.block_comments.items():
            placeholder = "BLOCKCOMMENT%06i" % key
            if not comments:
                placeholder = ""
            # Replace block comment with placeholder
            s_dict.block_content = re.sub(
                re.escape(block_comment),
                placeholder,
                s_dict.block_content,
            )

        return

    def _extract_string_literals(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Find and extract string literals from dict.block_content, and replace them with Placeholders.

        Finds string literals, extracts them,
        and replaces them with a placeholder in the form STRINGLITERAL000000.
        Substrings within .block_content that are surrounded by single quotes are identified as string literals.
        The extracted string literals are stored in .string_literals as key value pairs {index:string_literal}.
        index, therein, corresponds to the integer number in STRINGLITERAL000000.

        Parameters
        ----------
        s_dict : SDict
            dict to be processed. _extract_string_literals() works on dict.block_content.
        """
        search_pattern: Pattern[str]
        string_literals: list[str]

        # Step 1: Find single quoted string literals in .block_content
        search_pattern = re.compile(
            pattern=r"(?P<sq>((?<!\\)\\{8}')|((?<!\\)\\{6}')|((?<!\\)\\{4}')|((?<!\\)\\{2}')|(?<!\\)').*?(?P=sq)",
            flags=re.MULTILINE,
        )
        single_quoted_matches: list[Match[str]] = list(re.finditer(search_pattern, s_dict.block_content))

        # Step 2: Find double quoted string literals in .block_content
        # Double quoted strings are identified as string literals only in case they do not contain a $ character.
        # (double quoted strings containing a $ character are considered expressions, not string literals.)
        search_pattern = re.compile(
            pattern=r'(?P<dq>((?<!\\)\\{8}")|((?<!\\)\\{6}")|((?<!\\)\\{4}")|((?<!\\)\\{2}")|(?<!\\)").*?(?P=dq)',
        )
        double_quoted_matches: list[Match[str]] = []
        for match in re.finditer(search_pattern, s_dict.block_content):
            string_literal = match.string[match.start(0) : match.end(0)]
            if "$" not in string_literal:
                double_quoted_matches.append(match)

        # Check for string literals nested inside another string literal
        dq_start: int
        sq_start: int
        sq_end: int
        # Classify all single quoted string literals as to whether they are (also)
        # found as a nested literal in any double quoted string literal, or not.
        _single_quoted_string_literals_found_nested: list[str] = []
        _single_quoted_string_literals_not_nested: list[str] = []
        for single_quoted_match in single_quoted_matches:
            single_quoted_string_literal: str = single_quoted_match.string[
                single_quoted_match.start(0) : single_quoted_match.end(0)
            ]
            dq_start = single_quoted_match.start(0)
            found_nested_in_double_quoted_match: bool = False
            for double_quoted_match in double_quoted_matches:
                sq_start = double_quoted_match.start(0)
                sq_end = double_quoted_match.end(0)
                if dq_start > sq_start and dq_start < sq_end:
                    # sq match is inside dq match -> sq match is nested
                    found_nested_in_double_quoted_match = True
                    break
            if found_nested_in_double_quoted_match:
                _single_quoted_string_literals_found_nested.append(single_quoted_string_literal)
            else:
                _single_quoted_string_literals_not_nested.append(single_quoted_string_literal)

        # Classify all double quoted string literals as to whether they are (also)
        # found as a nested literal in any single quoted string literal, or not.
        _double_quoted_string_literals_found_nested: list[str] = []
        _double_quoted_string_literals_not_nested: list[str] = []
        for double_quoted_match in double_quoted_matches:
            double_quoted_string_literal: str = double_quoted_match.string[
                double_quoted_match.start(0) : double_quoted_match.end(0)
            ]
            dq_start = double_quoted_match.start(0)
            found_nested_in_single_quoted_match: bool = False
            for single_quoted_match in single_quoted_matches:
                sq_start = single_quoted_match.start(0)
                sq_end = single_quoted_match.end(0)
                if dq_start > sq_start and dq_start < sq_end:
                    # dq match is inside sq match -> dq match is nested
                    found_nested_in_single_quoted_match = True
                    break
            if found_nested_in_single_quoted_match:
                _double_quoted_string_literals_found_nested.append(double_quoted_string_literal)
            else:
                _double_quoted_string_literals_not_nested.append(double_quoted_string_literal)

        # For replacement of the string literals inside dict.block_content:
        # Chain the different identified string literals in such a sequence that
        # outer literals (i.e. those that are NOT found nested inside another literal)
        # are replaced first.  String literals that were found (also) nested inside other literals
        # are replaced last. The latter then would only replace occurences of these string literals
        # where they are NOT nested (as the nested occurences are already replaced by
        # the placeholders of the outer string literals they were nested in).
        string_literals = (
            _single_quoted_string_literals_not_nested
            + _double_quoted_string_literals_not_nested
            + _single_quoted_string_literals_found_nested
            + _double_quoted_string_literals_found_nested
        )
        for string_literal in string_literals:
            index = self.counter()
            placeholder = "STRINGLITERAL%06i" % index

            # Replace all occurances of the string literal in .block_content with the placeholder (STRINGLITERAL000000)
            # Note: For re.sub() to work properly we need to escape all special characters
            search_pattern = re.compile(re.escape(string_literal))
            s_dict.block_content = re.sub(
                search_pattern,
                placeholder,
                s_dict.block_content,
            )

            # Register the string literal in .string_literals
            s_dict.string_literals.update({index: Parser.remove_quotes_from_string(string_literal)})

        return

    def _extract_expressions(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Find and extract expressions from dict.block_content, and replace them with Placeholders.

        Finds expressions, extracts them,
        and replaces them with a placeholder in the form EXPRESSION000000.
        Substrings within .block_content that are surrounded by double quotes
        and contain minimum one $reference are identified as expressions.
        The extracted expressions are stored in .expressions as a key'd subdict
        with multiple elements {index:{'index': index, 'expression': expression, 'name': placeholder}}.
        index, therein, corresponds to the integer number in EXPRESSION000000.

        Parameters
        ----------
        s_dict : SDict
            dict to be processed. _extract_expressions() works on dict.block_content.
        """
        s_dict.expressions = {}

        # Step 1: Find expressions in .block_content .
        # Expressions are double quoted strings that contain minimum one reference.
        # References are denoted using the '$' syntax familiar from shell programming.
        # Any key'd entries in a dict are considered variables and can be referenced.
        search_pattern: str | Pattern[str] = r'"[^"]*\$.*?"'
        expressions = re.findall(search_pattern, s_dict.block_content, re.MULTILINE)
        for expression in expressions:
            index = self.counter()
            placeholder = "EXPRESSION%06i" % index

            # Replace all occurances of the expression in .block_content with the placeholder (EXPRESSION000000)
            # Note: For re.sub() to work properly we need to escape all special characters
            # (covering both '$' as well as any mathematical operators in the expression)
            search_pattern = re.compile(re.escape(expression))
            # replace expression in .block_content with placeholder
            s_dict.block_content = re.sub(
                search_pattern,
                placeholder,
                s_dict.block_content,
            )

            # Register the expression in .expressions
            _expression = re.sub(
                r"\"",
                "",
                expression,
            )
            s_dict.expressions |= {index: {"expression": _expression, "name": placeholder}}

        # Step 2: Find references in .block_content (single references to key'd entries that are NOT in double quotes).
        search_pattern = r"\$\w[\w\[\]]*"
        while match := re.search(search_pattern, s_dict.block_content, re.MULTILINE):
            reference = match[0]
            index = self.counter()
            placeholder = "EXPRESSION%06i" % index
            # Replace the found reference in .block_content with the placeholder (EXPRESSION000000)
            s_dict.block_content = match.re.sub(placeholder, s_dict.block_content, count=1)
            # Register the reference as expression in .expressions
            s_dict.expressions.update({index: {"expression": reference, "name": placeholder}})
        return

    def _separate_delimiters(
        self,
        s_dict: SDict[TKey, TValue],
        delimiters: list[str] | None = None,
    ) -> None:
        r"""Ensure that delimiters are separated by exactly one space before and after.

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
            delimiters = s_dict.delimiters

        # Insert at least one \s around every char in list
        for char in delimiters:
            s_dict.block_content = re.sub(
                str(rf"(\{char})"),
                str(f" {char} "),
                s_dict.block_content,
            )

        # Substitute all \s+ to \s
        # This turns multiple spaces into one single space.
        # However, as \s+ matches ANY whitespace character (\s+ is equivalent to [ \t\n\r\f\v]+)
        # this also deletes all line endings (\n). As explained above, this is well intended though.
        s_dict.block_content = re.sub(
            r"\s+",
            " ",
            s_dict.block_content,
        )

        return

    def _convert_block_content_to_tokens(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Decomposes .block_content into a list of tokens."""
        s_dict.tokens = [(0, i) for i in re.split(r"\s", s_dict.block_content)]
        s_dict.block_content = ""

        return

    def _determine_token_hierarchy(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        # sourcery skip: use-join
        """Create the hierarchy among the tokens and test their indentation."""
        level = 0
        count_open: list[str] = []
        count_close: list[str] = []
        for index, item in enumerate(s_dict.tokens):
            if item[1] in s_dict.openingBrackets:
                push_pop = 1
                count_open.append(item[1])
            elif item[1] in s_dict.closingBrackets:
                push_pop = -1
                count_close.append(item[1])
            else:
                push_pop = 0

            if push_pop < 0:
                level += push_pop
                push_pop = 0

            # if not re.search('COMMENT', self.tokens[index][1]):
            s_dict.tokens[index] = (level, s_dict.tokens[index][1])

            if push_pop > 0:
                level += push_pop
                push_pop = 0

        if level != 0:
            counted = ""
            for opening_bracket, closing_bracket in zip(s_dict.openingBrackets, s_dict.closingBrackets, strict=False):
                counted += "".join(
                    [
                        "\t\t\t",
                        opening_bracket,
                        str(len([b for b in count_open if b == opening_bracket])),
                        " -- ",
                        str(len([b for b in count_close if b == closing_bracket])),
                        closing_bracket,
                        "\n",
                    ]
                )
            logger.error(
                "_determine_token_hierarchy: opening and closing delimiters in dict "
                f"{s_dict.name} are not balanced:\n{counted}"
            )

        return

    def _convert_tokens_to_dict(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Convert the hierarchic tokens into a dict."""
        s_dict.update(self._parse_tokenized_dict(s_dict))
        s_dict.tokens.clear()

        return

    def _parse_tokenized_dict(
        self,
        s_dict: SDict[TKey, TValue],
        tokens: list[tuple[int, str]] | None = None,
        level: int = 0,
    ) -> dict[TKey, TValue]:
        """Parse a tokenized dict and return the parsed dict.

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

        parsed_dict: dict[TKey, TValue] = {}

        if tokens is None:
            tokens = s_dict.tokens

        # Iterate through tokens
        last_index: int | None = None
        token_index: int = 0
        key: TKey  # key (name) of the data struct
        while token_index < len(tokens):
            # Nested data struct (list or dict)   '(' = list    '{' = dict
            if tokens[token_index][1] in s_dict.openingBrackets:
                # The key (name) of the data struct is by convention directly preceeding the opening bracket.
                # ..except if there are line comments in between. skip those:
                offset: int = 1
                while re.match("^.*COMMENT.*$", str(tokens[token_index - offset][1])):
                    offset += 1
                # key (name) of the data struct:
                key = self.parse_key(tokens[token_index - offset][1])

                # Closing bracket has by definition same level as opening bracket.
                # (Note: the tokens BETWEEN the brackets are considered one level 'deeper';
                #  but that's not the point here)
                closing_bracket: str = self._find_companion(s_dict, tokens[token_index][1])
                closing_level: int = tokens[token_index][0]

                # Create a temporary data_struct_tokens list for just the nested data struct, containing
                # all tokens from the opening bracket (first token) to the closing bracket (last token)
                data_struct_tokens: list[tuple[int, str]] = []
                i: int = 0
                last_index = None
                # Start at opening bracket, go forward and copy the tokens
                # until (and including) the accompanied closing bracket.
                while (
                    tokens[token_index + i][1] != closing_bracket
                    or tokens[token_index + i][0] != closing_level
                    and not re.match("^.*COMMENT.*$", str(tokens[token_index + i][1]))
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
                if data_struct_tokens[-1][1] == ")" and tokens[token_index + i + 1][1] not in [";", ")"]:
                    # log error: Missing ';' after list
                    logger.warning(
                        "mis-spelled expression / missing ';' around \""
                        f"{' '.join([str(key)] + [t[1] for t in data_struct_tokens] + [tokens[token_index + i + 1][1]])}"  # noqa: E501
                        "\""
                    )
                # dict:
                if data_struct_tokens[-1][1] == "}":
                    # Proof that last key value pair in dict ends with ';'
                    # (= assert that second-to-last token is ';')
                    index: int = -2
                    # ..ok, line comments do not count .. skip them:
                    while re.match("^.*COMMENT.*$", str(data_struct_tokens[index][1])):
                        index -= 1
                    # ..but now: Does the last key value pair end with ';'?
                    if data_struct_tokens[index][1] not in ["{", ";", "}"]:
                        # log error: Missing ';' after key value pair
                        logger.error(
                            "mis-spelled expression / missing ';' around \""
                            f"{' '.join([str(key)] + [t[1] for t in data_struct_tokens])}"
                            "\""
                        )

                # Parse the tokenized data struct, translate it into its type (list or dict),
                # and update parsed_dict with the new list or dict.
                # Again, the code is type specific depending on whether the parsed data struct is a list or a dict.
                # list:
                if data_struct_tokens[0][1] == "(":
                    # Check whether the list is empty
                    if len(data_struct_tokens) < 3:  # noqa: PLR2004
                        # is empty (contains only opening and closing bracket)
                        # update parsed_dict with just the empty list
                        parsed_dict[key] = []
                    else:
                        # has content
                        # parse the nested list
                        nested_list = self._parse_tokenized_list(s_dict, data_struct_tokens, level=level + 1)
                        # update parsed_dict with the nested list
                        parsed_dict[key] = nested_list

                #  dict:
                elif data_struct_tokens[0][1] == "{":
                    # parse the nested dict (recursion)
                    nested_dict = self._parse_tokenized_dict(s_dict, data_struct_tokens[1:-1], level=level + 1)
                    # update parsed_dict with the nested dict
                    parsed_dict[key] = nested_dict

                # All done: Identified data struct is parsed, translated into its corresponding type,
                # and local parsed_dict is updated.
                # To close out and move on, fast-forward the index of tokens
                # to 'after' the data struct we just parsed:
                if last_index is not None:
                    token_index = last_index + 1

            elif tokens[token_index][1] == ";" and tokens[token_index - 1][1] != ")":
                # Read the key (name) and the value from the key value pair
                # Parse from right to left, starting at the identified ';'
                # and then copy the tokens into a temporary key_value_pair_tokens list:
                key_value_pair_tokens: MutableSequence[tuple[int, str]] = [tokens[token_index]]  # ';'
                key_value_pair_token_level: int = tokens[token_index][0]
                i = 1
                last_index = None
                while (
                    token_index - i >= 0
                    and tokens[token_index - i][0] == key_value_pair_token_level
                    and tokens[token_index - i][1] not in [";", "}"]
                    and not re.match(r"^.*COMMENT.*$", str(tokens[token_index - i][1]))
                    and not re.match(r"^.*INCLUDE.*$", str(tokens[token_index - i][1]))
                ):
                    key_value_pair_tokens.append(tokens[token_index - i])
                    i += 1

                # reverse token list
                key_value_pair_tokens = key_value_pair_tokens[::-1]

                # Before proceeding with reading key and value, make sure that what was parsed
                # really represents a key-value pair, consisting of three elements key, value and ';'
                if (
                    len(key_value_pair_tokens) != 3  # noqa: PLR2004
                    or len(key_value_pair_tokens[0]) != 2  # noqa: PLR2004
                    or len(key_value_pair_tokens[1]) != 2  # noqa: PLR2004
                ):
                    # Something is lexically wrong.  Not a valid key-value pair. -> Skip and log warning
                    context_tokens_index_from = max(0, token_index - 20)
                    context_tokens_index_to = min(token_index + 20, len(tokens))
                    context = (
                        "/"
                        + " ".join(
                            [
                                tokens[i][1]
                                for i in range(context_tokens_index_from, context_tokens_index_to)
                                if len(tokens[i]) > 1
                            ]
                        )
                        + "/"
                    )
                    logger.warning(
                        "NativeParser._parse_tokenized_dict(): "
                        f"tokens skipped: {key_value_pair_tokens} inside {context}"
                    )
                else:
                    if len(key_value_pair_tokens) > 3:  # noqa: PLR2004
                        logger.warning(
                            "NativeParser._parse_tokenized_dict(): "
                            f"more tokens in key-value pair than expected: {key_value_pair_tokens!s}"
                        )
                    # read the key (name) (first token, by convention)
                    key = self.parse_key(key_value_pair_tokens[0][1])
                    # read the value (second token, by convention)
                    value = self.parse_value(key_value_pair_tokens[1][1])
                    # update parsed_dict with the parsed key value pair
                    # Note: Following update would be greedy, if parsed_dict would be declared as global variable.
                    # This exactly is why parsed_dict is declared as local variable in _parse_tokenized_dict().
                    # Doing so, an empty local dict is created with each call to _parse_tokenized_dict(),
                    # and that is, also with each RECURSIVE call.
                    # As every recursive call passes in a temporary token list containing only the nested
                    # data struct, updating a key effects the current (and local) parsed_dict only.
                    # Every key hence is being updated exclusively within its own local context;
                    # ambiguous occurences of keys are avoided.
                    if isinstance(key, int):
                        logger.error(f"unexpected type of key 'name': int (value: {key}).")
                    parsed_dict[key] = value

            elif re.match("^.*COMMENT.*$", str(tokens[token_index][1])) or re.match(
                "^.*INCLUDE.*$", str(tokens[token_index][1])
            ):
                parsed_dict[tokens[token_index][1]] = tokens[token_index][1]

            else:
                pass

            # Iterate to next token
            token_index += 1

        # Return the parsed dict
        return parsed_dict

    def _parse_tokenized_list(
        self,
        s_dict: SDict[TKey, TValue],
        tokens: list[tuple[int, str]] | None = None,
        level: int = 0,
    ) -> list[TValue]:
        """Parse a tokenized list and return the parsed list.

        Parses all tokens, identifies the element within the tokenized list each token represents or belongs to,
        converts related tokens into the element's type and stores it in local list (parsed_list).

        Following elements within the tokenized list are identified and parsed:
        - nested data struct (list or dict)
        - single value type

        After all tokens have successfully been parsed, return the parsed list.

        Note: To allow recursive calls in case of nested lists, parsed_list is declared as a local variable.
        """
        # sourcery skip: remove-empty-nested-block, remove-redundant-if, remove-redundant-pass

        parsed_list: list[TValue] = []

        if tokens is None:
            tokens = s_dict.tokens

        # Iterate through tokens
        base_level: int = tokens[0][0]
        token_index: int = 0
        last_index: int | None = None
        while token_index < len(tokens):
            # Nested data struct (list or dict)   '(' = list    '{' = dict
            if tokens[token_index][1] in s_dict.openingBrackets and tokens[token_index][0] > base_level:
                # Closing bracket has by definition same level as opening bracket.
                # (Note: the tokens BETWEEN the brackets are considered one level 'deeper';
                #  but that's not the point here)
                closing_bracket: str = self._find_companion(s_dict, tokens[token_index][1])
                closing_level: int = tokens[token_index][0]

                # Create a temporary token list for just the nested data struct, containing
                # all tokens from the opening bracket (first token) to the closing bracket (last token)
                temp_tokens: list[tuple[int, str]] = []
                i: int = 0
                last_index = None
                # Start at opening bracket, go forward and copy the tokens
                # until (and including) the accompanied closing bracket
                while (
                    tokens[token_index + i][1] != closing_bracket
                    or tokens[token_index + i][0] != closing_level
                    and not re.match("^.*COMMENT.*$", str(tokens[token_index + i][1]))
                ):
                    last_index = token_index + i
                    temp_tokens.append(tokens[token_index + i])
                    i += 1
                temp_tokens.append(tokens[token_index + i])

                # Do a Syntax-Check at the closing bracket of the data struct.
                # As the syntax for lists and dicts is different, the syntax check is type specific:
                # list:
                if temp_tokens[-1][1] == ")":
                    # nothing to proof.  A list nested inside a list simply ends with ')'.
                    # Note: This is different for a list nested inside a dict: Then, the closing
                    # bracket of the list must be followed by ';' (because, basically, the list is then the 'value'
                    # part of a key value pair inside the dict. And key value pairs syntactically close with ';')
                    pass
                # dict:
                if temp_tokens[-1][1] == "}":
                    # Proof that last key value pair in dict ends with ';'
                    # (= assert that second-to-last token is ';')
                    index: int = -2
                    # ..ok, line comments do not count .. skip them:
                    while re.match("^.*COMMENT.*$", str(temp_tokens[index][1])):
                        index -= 1
                    # ..but now: Does the last key value pair end with ';'?
                    if temp_tokens[index][1] not in ["{", ";", "}"]:
                        # log error: Missing ';' after key value pair
                        logger.error(
                            "mis-spelled expression / missing ';' around \""
                            f"{' '.join([t[1] for t in temp_tokens])}"
                            "\""
                        )

                # Parse the tokenized data struct, translate it into its type (list or dict),
                # and update parsed_list with the new list or dict.
                # Again, the code is type specific depending on whether the parsed data struct is a list or a dict.
                # list:
                if temp_tokens[0][1] == "(":
                    # Check whether the list is empty
                    if len(temp_tokens) < 3:  # noqa: PLR2004
                        # list is empty (contains only the opening and the closing bracket)
                        # -> add an empty list to parsed_list
                        parsed_list.append([])
                    else:  # has content
                        # parse the nested list
                        nested_list = self._parse_tokenized_list(s_dict, temp_tokens, level=level + 1)  # (recursion)
                        # add nested list to parsed_list
                        parsed_list.append(nested_list)
                        #  dict:
                elif temp_tokens[0][1] == "{":
                    # parse the nested dict
                    nested_dict = self._parse_tokenized_dict(s_dict, temp_tokens[1:-1], level=level + 1)
                    # add nested dict to parsed_list
                    parsed_list.append(nested_dict)

                # All done: Identified data struct is parsed, translated into its corresponding type,
                # and local parsed_list is updated.
                # To close out and move on, fast-forward the index of tokens
                # to 'after' the data struct we just parsed:
                if last_index is not None:
                    token_index = last_index + 1

            # Single value type
            elif tokens[token_index][1] not in ["(", ")", ";"]:
                value = self.parse_value(tokens[token_index][1])
                parsed_list.append(value)

            # -else = ';' or ')'
            else:
                pass

            # Iterate to next token
            token_index += 1

        # Return the parsed list
        return parsed_list

    def _find_companion(
        self,
        s_dict: SDict[TKey, TValue],
        bracket: str,
    ) -> str:
        """Return the companion bracket character for the passed in bracket character.

        Example: If you pass in '{', _find_companion() will return '}'  (and vice versa)
        """
        companion = ""
        for item in s_dict.brackets:
            if bracket == item[0]:
                companion = item[1]
            elif bracket == item[1]:
                companion = item[0]
        return companion

    def _insert_string_literals(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Substitutes STRINGLITERAL placeholders in the dict with the corresponding entry from dict.string_literals."""
        for index, string_literal in s_dict.string_literals.items():
            # Properties of the expression to be evaluated
            placeholder = "STRINGLITERAL%06i" % index  # STRINGLITERAL000000
            # The entry from dict.string_literals is parsed once again,
            # so that entries representing single value native types
            # (such as bool ,None, int, float) are transformed to its native type, accordingly.
            value = self.parse_value(string_literal)

            # Replace all occurences of placeholder within the dictionary with the original string literal.
            # Note: As find_global_key() is non-greedy and returns the key of
            # only the first occurance of placeholder it finds,
            # we need to loop until we found and replaced all occurances of placholder in the dict
            # and find_global_key() does not find any more occurances.
            while global_key := s_dict.find_global_key(query=placeholder):
                # Back insert the string literal
                s_dict.set_global_key(global_key, value)
        s_dict.string_literals.clear()
        return

    def _clean(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        """Remove NativeFormatter / NativeParser specific internal keys from dict.

        Removes keys written by NativeFormatter for documentation purposes
        but which shall not be created as keys in dict.data.
        In specific, it is the following two keys that get deleted if existing:
        _variables
        _includes
        """
        if "_variables" in s_dict:
            del s_dict["_variables"]
        if "_includes" in s_dict:
            del s_dict["_includes"]


class FoamParser(NativeParser):
    """Parser to deserialize a string in OpenFOAM dictionary format into a SDict."""

    def __init__(self) -> None:
        """Define default configuration for FoamParser."""
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:
        """Parse a string in OpenFOAM dictionary format and deserialize it into a SDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : SDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        SDict
            the parsed dict
        """
        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(
            string=string,
            target_dict=target_dict,
            comments=comments,
        )

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        # target_dict.merge(parsed_dict)  # Not necessary. Done in base class SDictParser already.  # noqa: ERA001

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict


class JsonParser(Parser):
    """Parser to deserialize a string in JSON dictionary format into a SDict."""

    def __init__(self) -> None:
        """Define default configuration for JsonParser."""
        # Invoke base class constructor
        super().__init__()

    def parse_string(
        self,
        string: str,
        target_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:
        """Parse a string in JSON dictionary format and deserialize it into a SDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : SDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        SDict
            the parsed dict
        """
        import json

        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict = super().parse_string(
            string=string,
            target_dict=target_dict,
            comments=comments,
        )

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        parsed_dict.update(json.loads(string))

        # Extract include directives
        self._extract_includes(parsed_dict)

        # Extract expressions
        self._extract_expressions(parsed_dict, parsed_dict)

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def _extract_includes(
        self,
        s_dict: SDict[TKey, TValue],
    ) -> None:
        from copy import deepcopy

        keys: list[TKey] = list(s_dict.keys())
        include_placeholder_keys: dict[TKey, TValue] = {}
        for key in keys:
            if isinstance(key, str) and re.search(r"^\s*#\s*include", key):
                include_file_name = str(s_dict[key])
                include_file_name = self.remove_quotes_from_string(include_file_name)

                include_file_path = Path.joinpath(s_dict.path, include_file_name)

                include_file_name_temp = include_file_name.replace("\\", "\\\\")
                include_directive = f"#include '{include_file_name_temp}'"

                ii = self.counter()
                s_dict.includes.update({ii: (include_directive, include_file_name, include_file_path)})

                include_placeholder_keys[f"INCLUDE{ii:06d}"] = f"INCLUDE{ii:06d}"
                del s_dict[key]

        data_temp = deepcopy(s_dict)
        s_dict.clear()
        s_dict.update(include_placeholder_keys)
        s_dict.update(data_temp)

        return

    def _extract_expression(
        self,
        parsed_dict: SDict[TKey, TValue],
        string: str,
    ) -> str:
        """Extract a single expression.

        Parses a string, checks whether it contains an expression, and if so,
        extracts the expression and replaces it with a placeholder.

        Parameters
        ----------
        parsed_dict : SDict
            the SDict instance the extracted expression shall be saved in
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
        search_pattern: str | Pattern[str] = r"\$\w[\w\[\]]*"
        references = re.findall(search_pattern, string, re.MULTILINE)
        if not references:
            return string

        # Case 1: Reference
        # The string contains only a single plain reference (single reference to a key'd entry in the parsed dict).
        search_pattern = r"^\s*(\$\w[\w\[\]]*){1}\s*$"
        if match := re.search(search_pattern, string, re.MULTILINE):
            reference: str = match.groups()[0]
            # Replace the reference in string with a placeholder (EXPRESSION000000) and register it in parsed_dict:
            return self._replace_and_register_expression(parsed_dict, string, reference)

        # Case 2: Expression
        # The string contains more than just a single reference. In this case we consider the string an expression.
        # Expressions are strings that contain one or more reference but are not a single plain reference
        # (meaning they contain something in addition: An operator, a second reference, a constant, or whatever.).
        expression = string.strip()
        # Replace the expression in string with a placeholder (EXPRESSION000000) and register it in parsed_dict:
        return self._replace_and_register_expression(parsed_dict, string, expression)

    def _replace_and_register_expression(
        self,
        parsed_dict: SDict[TKey, TValue],
        string: str,
        expression: str,
    ) -> str:
        """Replace all occurances of expression in string with a placeholder.

        Replaces all occurances of expression in string with a placeholder (EXPRESSION000000)
        and register the expression in parsed_dict.

        Parameters
        ----------
        parsed_dict : SDict
            the SDict instance the expression will be registered in
        string : str
            the string in which expression shall be found and replaced
        expression : str
            the expression to be found, replaced and registered

        Returns
        -------
        str
            the modified string, in which all occurrences of expression got replaced
            with a placeholder (EXPRESSION000000)
        """
        index: int = self.counter()
        placeholder: str = "EXPRESSION%06i" % index
        # Note: For re.sub() to work properly we need to escape all special characters
        #       (covering both '$' as well as any mathematical operators in the expression)
        _pattern: re.Pattern[str] = re.compile(re.escape(expression))
        modified_string: str = re.sub(
            _pattern,
            placeholder,
            string,
        )
        # Register the expression in .expressions
        parsed_dict.expressions.update({index: {"expression": expression, "name": placeholder}})
        return modified_string

    def _extract_expressions(
        self,
        parsed_dict: SDict[TKey, TValue],
        arg: MutableMapping[TKey, TValue] | MutableSequence[TValue],
    ) -> None:
        """Find and extract expressions in a dict or list and replace them with Placeholders.

        Finds expressions, extracts them, and replaces them with a placeholder in the form EXPRESSION000000.
        String values that contain minimum one $reference are identified as expressions.
        The extracted expressions are stored in .expressions as a key'd subdict with multiple elements
        {index:{'index': index, 'expression': expression, 'name': placeholder}}.
        index, therein, corresponds to the integer number in EXPRESSION000000.

        Parameters
        ----------
        parsed_dict : SDict
            the SDict instance the extracted expressions shall be saved in
        arg : Union[MutableMapping[TKey, TValue], MutableSequence[TValue]]
            the dict or list containing values to be parsed for expressions
        """
        if isinstance(arg, MutableMapping):  # Dict
            for key in arg:
                if isinstance(arg[key], MutableMapping | MutableSequence):
                    self._extract_expressions(parsed_dict, arg[key])
                else:
                    typed_value = self.parse_value(arg[key])
                    if isinstance(typed_value, str):
                        arg[key] = self._extract_expression(parsed_dict, arg[key])
        else:  # List
            for index, _ in enumerate(arg):
                if isinstance(arg[index], MutableMapping | MutableSequence):
                    self._extract_expressions(parsed_dict, arg[index])
                else:
                    typed_value = self.parse_value(arg[index])
                    if isinstance(typed_value, str):
                        arg[index] = self._extract_expression(parsed_dict, arg[index])
        return


class XmlParser(Parser):
    """Parser to deserialize a string in XML format into a SDict."""

    def __init__(
        self,
        *,
        add_node_numbering: bool = True,
    ) -> None:
        """Define default configuration for XmlParser."""
        # Invoke base class constructor
        super().__init__()
        # Save default configuration as attributes
        self.add_node_numbering = add_node_numbering

    def parse_string(
        self,
        string: str,
        target_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> SDict[TKey, TValue]:
        """Parse a string in XML format and deserialize it into a SDict.

        Parameters
        ----------
        string : str
            the string to be parsed (i.e. the content of the file that had been read using parse_file())
        target_dict : SDict
            the target dict the parsed dict file shall be merged into
        comments : bool, optional
            reads comments, by default True

        Returns
        -------
        SDict
            the parsed dict
        """
        # +++CALL BASE CLASS IMPLEMENTATION+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        parsed_dict = super().parse_string(
            string=string,
            target_dict=target_dict,
            comments=comments,
        )

        # +++PARSE XML++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Default configuration
        _namespaces: dict[str | None, str] = {"xs": "https://www.w3.org/2009/XMLSchema/XMLSchema.xsd"}
        root_tag: str = "NOTSPECIFIED"

        # Create XML parser
        parser = ETCompatXMLParser()
        # Read root element from XML string
        root_element: LxmlElement = fromstring(string.encode("utf-8"), parser)  # noqa: S320
        # Read root tag from XML string
        # there is a problem with .tag :
        # fromstring does not completely push all attributes into .attrib
        # only version, not xmlns
        # xmlns remains as {XMLNSCONTENT}ROOTTAG
        # re.sub to fix that temporarily
        # solution needed
        _root_tag: str = str(root_element.tag)
        root_tag = (
            re.sub(
                r"\{.*\}",
                "",
                _root_tag,
            )
            or root_tag
        )
        # Read namespaces from XML string
        _xml_namespaces: dict[str | None, str] = dict(root_element.nsmap)
        _namespaces = _xml_namespaces or _namespaces
        # Reformat None keys in `_namespaces` to key 'None' (as string)
        temp_keys_copy: list[str | None] = list(_namespaces)
        try:
            for key in temp_keys_copy:
                if key is None:
                    value = _namespaces[key]
                    del _namespaces[key]
                    _namespaces["None"] = value
        except Exception:
            logger.exception("XmlParser.parseString(): Reformatting None keys in namespaces to key 'None' failed")
        # If no Exception was thrown, `_namespaces` will now contain no more `None` keys.
        # If a `None` key existed, it had been transformed into its string equivalent 'None',
        # i.e. a `None` entry will now be in the form {'None': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'}
        # We can hence safely cast to `dict[str, str]`.
        namespaces: dict[str, str] = cast(dict[str, str], _namespaces)

        # +++PARSE DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Transform XML root node into dict

        parsed_dict.update(self._parse_nodes(root_element, namespaces))

        # Document XML options inside the dict
        try:
            parsed_dict["_xmlOpts"] = {
                "_nameSpaces": namespaces,
                "_rootTag": root_tag,
                "_rootAttributes": dict(root_element.attrib.items()),
                "_addNodeNumbering": self.add_node_numbering,
            }

        except Exception:
            logger.exception("XmlParser.parseString(): Cannot write _nameSpaces to _xmlOpts")

        # +++MERGE PARSED DICTIONARY INTO TARGET DICTIONARY+++++++++++++++++++++++++++++++++++++++++
        target_dict.merge(parsed_dict)

        # +++RETURN PARSED DICTIONARY+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        return parsed_dict

    def _parse_nodes(
        self,
        root_element: LxmlElement,
        namespaces: dict[str, str],
    ) -> dict[TKey, TValue]:
        """Recursively parses all nodes and saves the nodes' content in a dict."""
        # Default case: Make all node tags temporarily unique by indexing them using BorgCounter
        node_tags: list[str] = [
            re.sub(
                pattern=r"^(\{.*\})",
                repl="",
                string=str(node.tag),
            )
            for node in root_element.findall(
                path="*",
                namespaces=dict(namespaces),
            )
        ]
        indexed_node_tags: list[tuple[str, str]] = []
        node_tag: str
        for node_tag in node_tags:
            index = self.counter()
            indexed_node_tags.append(("%06i_%s" % (index, node_tag), node_tag))

        key: TKey
        parsed_dict: dict[TKey, TValue] = {}

        # Parse all nodes
        for index, indexed_node_tag in enumerate(indexed_node_tags):
            # Read the node
            node_tag = indexed_node_tag[0]

            if not self.add_node_numbering:
                # Non-default case: add_node_numbering has been set to False by the caller
                # -> remove the index again
                node_tag = re.sub(
                    pattern=r"^\d{6}_",
                    repl="",
                    string=node_tag,
                )

            nodes: Sequence[LxmlElement]
            nodes = root_element.findall(
                path="*",
                namespaces=dict(namespaces),
            )
            key = self.parse_key(node_tag)

            # The recursive part.
            # If there is a nested list, step in and resolve,
            # otherwise append node text to dict.

            if list(nodes[index]):
                # node contains child nodes
                parsed_dict[key] = self._parse_nodes(
                    root_element=nodes[index],
                    namespaces=namespaces,
                )

            elif nodes[index].text is None or re.search(r"^[\s\n\r]*$", nodes[index].text or ""):
                # Node has either no content or contains an empty string <NODE ATTRIB=STRING><\NODE>
                # However, in order to be able to attach attributes to a node,
                # we still need to create a dict for the node, even if the node has no content.
                parsed_dict[key] = {}

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
                    text = ("\n".join(stripped_lines)).strip()
                else:
                    text = ""
                parsed_dict[key] = {"_content": text}

            # If the node contains attributes: Save the attributes
            # and merge with the contents
            if len(nodes[index].attrib) > 0:
                # Avoid empty strings in attributes
                # Might be substtituted by any kind of substitution later if required.
                attributes_dict = {"_attributes": {k: str(v) for k, v in nodes[index].attrib.items() if str(v) != ""}}

                if parsed_dict[key] is None:
                    parsed_dict[key] = attributes_dict
                else:
                    parsed_dict[key].update(attributes_dict)

        # before returning the new dict, doublecheck that all of its elements are correctly typed.
        self.parse_values(parsed_dict)

        return parsed_dict
