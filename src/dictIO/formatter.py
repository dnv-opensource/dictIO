"""Formatter for different dictionary file formats."""

from __future__ import annotations

import io
import logging
import re
from collections.abc import Mapping, MutableMapping, MutableSequence
from copy import copy, deepcopy
from pathlib import Path
from re import Pattern
from typing import TYPE_CHECKING, Any, cast, overload
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

from numpy import ndarray

from dictIO import SDict
from dictIO.utils.counter import BorgCounter

if TYPE_CHECKING:
    from dictIO.types import K, M, S, TKey, TValue, V

__all__: list[str] = [
    "FoamFormatter",
    "Formatter",
    "JsonFormatter",
    "NativeFormatter",
    "XmlFormatter",
]


logger: logging.Logger = logging.getLogger(__name__)


class Formatter:
    """Abstract Base Class for formatters.

    Formatters serialize a dict into a string applying a specific format.
    """

    def __init__(self) -> None:
        """Initialize a formatter with a shared placeholder counter."""
        self.counter = BorgCounter()

    @classmethod
    def get_formatter(cls, target_file: Path | None = None) -> Formatter:
        """Return a Formatter instance matching the type of the target file to be formatted (factory method).

        Args:
            target_file: Target path used to choose a format-specific formatter.
                If `None`, return the native formatter. Defaults to `None`.

        Returns:
            Formatter selected for the target file's suffix.
        """
        # Determine the formatter to be applied by a two stage process:

        # 1. If target_file is passed, choose formatter depending on file-ending
        if target_file:
            if (
                target_file.suffix == ".foam"
            ):  # .foam -> FoamFormatter  not applicable with xxx.foam, foam dicts are also xxxDict
                return FoamFormatter()
            if target_file.suffix == ".json":  # .json -> JsonFormatter
                return JsonFormatter()
            if target_file.suffix in [
                ".xml",
                ".ssd",
            ]:  # .xml  or  OSP .ssd -> XmlFormatter
                return XmlFormatter()

        # 2. If no target file is passed, return NativeFormatter as default / fallback
        return NativeFormatter()  # default

    def to_string(
        self,
        arg: MutableMapping[K, V],  # noqa: ARG002
    ) -> str:
        """Create a string representation of the passed in dict.

        Override this method in a format-specific formatter.

        Args:
            arg: Mapping to format.

        Returns:
            Formatted mapping as a string.
        """
        return ""

    def format_value(
        self,
        arg: object,
    ) -> str:
        """Format a single value.

        Format strings, booleans, numbers, paths, and `None` with their
        format-specific handlers. Other values are converted with `str`.

        Args:
            arg: Value to format.

        Returns:
            Formatted value as a string.
        """
        # sourcery skip: assign-if-exp, reintroduce-else

        # NOTE: The sequence of below `isinstance()` checks is important.
        #       Especially, `isinstance(arg, bool)` must be checked _before_ `isinstance(arg, int)`,
        #       as otherwise `isinstance(arg, int)` would catch the bool (bool is a subtype of int) !
        if isinstance(arg, str):
            return self.format_string(arg)
        if isinstance(arg, bool):
            return self.format_bool(arg)
        if isinstance(arg, int):
            return self.format_int(arg)
        if isinstance(arg, float):
            return self.format_float(arg)
        if isinstance(arg, Path):
            return str(arg)
        if arg is None:
            return self.format_none()

        # For all other types, call and return `str(arg)`
        return str(arg)

    @overload
    def format_values(
        self,
        arg: M,
    ) -> M:
        pass

    @overload
    def format_values(
        self,
        arg: S,
    ) -> S:
        pass

    def format_values(
        self,
        arg: M | S,
    ) -> M | S:
        """Format multiple values.

        Traverse nested mappings and sequences recursively. The input object is
        not modified.

        Args:
            arg: Mapping or sequence whose values should be formatted.

        Returns:
            Shallow copy of the input container with formatted values.
        """
        item: TValue
        _arg = copy(arg)  # shallow copy is sufficient because this function is recursive
        if isinstance(_arg, MutableSequence):  # List
            for index in range(len(_arg)):
                item = _arg[index]
                # ndarray -> list
                if isinstance(item, ndarray):
                    item = cast("list[TValue]", item.tolist())
                if isinstance(item, MutableMapping | MutableSequence):
                    _arg[index] = self.format_values(cast("M | S", item))
                else:
                    _arg[index] = self.format_value(item)

        else:  # Dict
            for key in list(_arg.keys()):  # work on a copy of keys
                item = _arg[key]
                # ndarray -> list
                if isinstance(item, ndarray):
                    item = cast("list[TValue]", item.tolist())
                if isinstance(item, MutableMapping | MutableSequence):
                    _arg[key] = self.format_values(cast("M | S", item))
                else:
                    _arg[key] = self.format_value(item)

        return cast("M | S", _arg)

    def format_key(
        self,
        arg: TKey,
    ) -> str:
        """Format a key.

        Args:
            arg: Key to format.

        Returns:
            Formatted key as a string.
        """
        return self.format_value(arg)

    def format_bool(self, arg: bool) -> str:  # noqa: FBT001
        """Format a boolean.

        Override this method for format-specific boolean representations.

        Args:
            arg: Boolean value to format.

        Returns:
            Formatted boolean as a string.
        """
        return str(arg)

    def format_int(self, arg: int) -> str:
        """Format an integer.

        Override this method for format-specific integer representations.

        Args:
            arg: Integer to format.

        Returns:
            Formatted integer as a string.
        """
        return str(arg)

    def format_float(self, arg: float) -> str:
        """Format a floating point number.

        Override this method for format-specific floating-point representations.

        Args:
            arg: Floating-point value to format.

        Returns:
            Formatted value as a string.
        """
        return str(arg)

    def format_none(self) -> str:
        """Format None value.

        Override this method for a format-specific representation of `None`.

        Returns:
            Formatted `None` value as a string.
        """
        return str(None)

    def format_string(self, arg: str) -> str:
        """Format a string.

        Args:
            arg: String to format.

        Returns:
            Formatted string.
        """
        if re.search(r"[$]", arg):
            if re.search(r"^\$\w[\w\[\]]*$", arg):  # reference
                return self.format_reference_string(arg)
            # expression
            return self.format_expression_string(arg)
        if not arg:  # empty string
            return self.format_empty_string(arg)
        if re.search(r"[\"']", arg):  # contains a nested string
            return self.format_string_with_nested_string(arg)
        if re.search(r"[\s:/\\]", arg):  # contains spaces or path -> complex string
            return self.format_multi_word_string(arg)
        # single word string
        return self.format_single_word_string(arg)

    def format_empty_string(self, arg: str) -> str:
        """Format an empty string.

        Override this method for a format-specific representation of an empty
        string.

        Args:
            arg: Empty string to format.

        Returns:
            Formatted empty string.
        """
        return arg

    def format_single_word_string(self, arg: str) -> str:
        """Format a single word string.

        Override this method for a format-specific representation of a
        single-word string.

        Args:
            arg: Single-word string to format.

        Returns:
            Formatted string.
        """
        return arg

    def format_string_with_nested_string(self, arg: str) -> str:
        """Format a string that contains a nested string.

        Override this method for a format-specific representation of a string
        containing nested quotes.

        Args:
            arg: String containing nested quotes.

        Returns:
            Formatted string.

        """
        return self.add_single_quotes(arg)

    def format_multi_word_string(self, arg: str) -> str:
        """Format a multi word string.

        Override this method for a format-specific representation of a
        multi-word string.

        Args:
            arg: Multi-word string to format.

        Returns:
            Formatted string.
        """
        return arg

    def format_reference_string(self, arg: str) -> str:
        """Format a reference.

        Override this method for format-specific reference handling.

        Args:
            arg: Reference string to format.

        Returns:
            Formatted reference.
        """
        return arg

    def format_expression_string(self, arg: str) -> str:
        """Format an expression.

        Override this method for format-specific expression handling.

        Args:
            arg: Expression string to format.

        Returns:
            Formatted expression.
        """
        return arg

    def add_single_quotes(self, arg: str) -> str:
        """Add single quotes to a string.

        This helper is available to subclasses when quoting formatted values.

        Args:
            arg: String to wrap in single quotes.

        Returns:
            String wrapped in single quotes.
        """
        return f"'{arg}'"

    def add_double_quotes(self, arg: str) -> str:
        """Add double quotes to a string.

        This helper is available to subclasses when quoting formatted values.

        Args:
            arg: String to wrap in double quotes.

        Returns:
            String wrapped in double quotes.
        """
        return f'"{arg}"'


class NativeFormatter(Formatter):
    """Formatter to serialize a dict into a string in dictIO native file format."""

    def __init__(self) -> None:
        """Define default configuration for NativeFormatter."""
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        arg: MutableMapping[K, V],
    ) -> str:  # sourcery skip: dict-comprehension
        """Create a string representation of the passed in dict in dictIO native file format.

        Args:
            arg: dict to be formatted

        Returns:
            string representation of the dict in dictIO native file format
        """
        # Create a working copy of the passed in dict, to avoid modifying the original.
        _arg: MutableMapping[K, V] = deepcopy(arg)

        # Sort dict in a way that block comment and include statement come first
        original_data = deepcopy(_arg)
        sorted_data: dict[K, V] = {}
        for key, element in original_data.items():
            if isinstance(key, str) and re.search(r"BLOCKCOMMENT\d{6}", key):
                sorted_data[cast("K", key)] = element
        for key, element in original_data.items():
            if isinstance(key, str) and re.search(r"INCLUDE\d{6}", key):
                sorted_data[cast("K", key)] = element
        for key in sorted_data:
            del original_data[key]
        sorted_data |= original_data
        _arg.clear()
        _arg.update(sorted_data)

        # Create the string representation of the dict in its basic structure.
        s: str = self.format_dict(_arg)

        if isinstance(_arg, SDict):
            # The following elements in an SDict
            # are usually still substituted by placeholders:
            # - Block comments
            # - Include directives
            # - Line comments
            # Next step hence is to resolve and insert these three element types:
            # 1. Block comments
            s = self.insert_block_comments(_arg, s)
            # 2. Include directives
            s = self.insert_includes(_arg, s)
            # 3. Line comments
            s = self.insert_line_comments(_arg, s)

        # Remove trailing spaces (if any)
        s = self.remove_trailing_spaces(s)

        # Return formatted string
        return s

    def format_dict(
        self,
        arg: object,
        tab_len: int = 4,
        level: int = 0,
        sep: str = " ",
        items_per_line: int = 10,
        end: str = "\n",
        ancestry: type[object] = MutableMapping,
    ) -> str:
        """Serialize a mapping, sequence, or scalar value.

        Args:
            arg: Value or nested container to serialize.
            tab_len: Number of indentation characters per level. Defaults to
                `4`.
            level: Initial indentation level. Defaults to `0`.
            sep: Character used between keys and values. Defaults to `" "`.
            items_per_line: Maximum number of sequence items written on a line.
                Defaults to `10`.
            end: Line ending appended to each serialized element. Defaults to
                the newline character.
            ancestry: Container type that determines whether a sequence is
                serialized as a top-level value or as a mapping value.
                Defaults to `MutableMapping`.

        Returns:
            Serialized representation of the input.
        """
        total_indent = 30
        s = ""
        indent = sep * tab_len * level

        item: TValue

        # list
        if isinstance(arg, MutableSequence):
            arg = cast("MutableSequence[Any]", arg)
            # Opening bracket
            s += self.format_dict("(", level=level, end=end)

            # List items
            first_item_on_this_line = True
            last_item_on_this_line = False

            for index in range(len(arg)):
                item = arg[index]
                # ndarray -> list
                if isinstance(item, ndarray):
                    item = cast("list[TValue]", item.tolist())

                # nested list
                if isinstance(item, MutableSequence):
                    # recursion
                    s += self.format_dict(
                        arg=item,
                        tab_len=tab_len,
                        level=level + 1,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end,
                        ancestry=MutableSequence,
                    )

                # nested dict
                elif isinstance(item, MutableMapping):
                    s += self.format_dict("", level=level + 1, end="\n")
                    s += self.format_dict("{", level=level + 1)
                    s += self.format_dict(
                        arg=item,
                        tab_len=tab_len,
                        level=level + 2,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end,
                    )  # (recursion)

                    s += self.format_dict("}", level=level + 1)
                    first_item_on_this_line = True

                # single value
                else:
                    value = self.format_value(item)
                    assert isinstance(value, str)
                    if first_item_on_this_line:
                        # The first item shall be indented by 1 relative to the (absolute) list level
                        item_level = level + 1
                        first_item_on_this_line = False  # (effective with next item)
                    else:
                        # each following item is then indented by 1 relative to its predecessor
                        item_level = 1

                    if ((index + 1) % items_per_line == 0) or (index + 1 == len(arg)):
                        last_item_on_this_line = True

                    if last_item_on_this_line:
                        # Add a line ending
                        s += self.format_dict(value, level=item_level, end="\n")  # (recursion)
                        last_item_on_this_line = False  # (effective with next item)
                        first_item_on_this_line = True  # (effective with next item)
                    else:
                        # Do not add a line ending. Instead, add an adjusted number of spaces
                        # after the item to make indentation look pretty.
                        s += self.format_dict(
                            f"{value}{sep * max(0, (14 - len(str(value))))}",
                            level=item_level,
                            end="",
                        )  # (recursion)

            # Closing bracket
            # if list (array) is complete, add semicolon
            if ancestry == MutableSequence:
                s += self.format_dict(")", level=level, end=end)
            else:
                s += self.format_dict(");", level=level, end=end)

        # dict
        elif isinstance(arg, MutableMapping):
            arg = cast("MutableMapping[Any, Any]", arg)
            for key in arg:
                item = arg[key]
                # ndarray -> list
                if isinstance(item, ndarray):
                    item = cast("list[TValue]", item.tolist())

                # nested dict
                if isinstance(item, dict):
                    s += self.format_dict(key, level=level)
                    s += self.format_dict("{", level=level)
                    s += self.format_dict(
                        item,
                        tab_len=tab_len,
                        level=level + 1,
                        sep=sep,
                        items_per_line=items_per_line,
                        end=end,
                    )  # (recursion)

                    s += self.format_dict("}", level=level)

                # nested list
                elif isinstance(item, list):
                    s += self.format_dict(key, level=level)
                    s += self.format_dict(item, level=level)  # (recursion)

                # key value pair
                else:
                    value = self.format_value(item)
                    assert isinstance(value, str)
                    skey: str = self.format_key(key)
                    s += self.format_dict(
                        f"{skey}{sep * max(8, (total_indent - len(skey) - tab_len * level))}{value};",
                        level=level,
                    )

        # Single item
        # Note: This is the base case. It is reached only through recursion from
        # dict -> key value pair    or from     list -> single value.
        # arg will hence either be a single item from a list, or a key value pair from a dict.
        else:
            string = f"{indent}{arg}{end}"
            s += string

        return s

    def format_bool(self, arg: bool) -> str:  # noqa: FBT001
        """Format a boolean.

        Args:
            arg: the boolean value to be formatted

        Returns:
            the formatted string representation of the passed in boolean value
        """
        return str(arg).lower()

    def format_none(self) -> str:
        """Format None.

        Returns:
            the formatted string representation of None
        """
        return "NULL"

    def format_empty_string(self, arg: str) -> str:
        """Format an empty string.

        Args:
            arg: the empty string to be formatted

        Returns:
            the formatted empty string
        """
        return self.add_single_quotes(arg)

    def format_string_with_nested_string(self, arg: str) -> str:
        """Format a string that contains a nested string.

        Args:
            arg: the string with a nested string to be formatted

        Returns:
            the formatted string with a nested string

        Raises:
            ValueError: If the input does not contain a nested quote.
        """
        if re.search(r'"', arg):
            return self.add_single_quotes(arg)
        if re.search(r"'", arg):
            return self.add_double_quotes(arg)
        raise ValueError(f"expected a string with a nested string. However, following string was passed in: {arg}")

    def format_multi_word_string(self, arg: str) -> str:
        """Format a multi word string.

        Args:
            arg: the multi word string to be formatted

        Returns:
            the formatted multi word string
        """
        return self.add_single_quotes(arg)

    def format_expression_string(self, arg: str) -> str:
        """Format an expression.

        Args:
            arg: the expression to be formatted

        Returns:
            the formatted expression
        """
        return self.add_double_quotes(arg)

    def insert_block_comments(
        self,
        s_dict: SDict[K, V],
        s: str,
    ) -> str:
        """Replace block-comment placeholders with their original text.

        The first inserted block comment receives the default dict header when
        it does not already contain a C++ marker. If no comment placeholder is
        present, insert the default header at the start of the output.

        Args:
            s_dict: Dictionary containing block-comment text.
            s: Formatted text containing block-comment placeholders.

        Returns:
            Text with block-comment placeholders replaced.
        """
        # Replace all BLOCKCOMMENT placeholders in s with the actual block_comments saved in dict
        block_comments_inserted_so_far = ""
        first_block_comment = True  # MonoFlop, armed
        search_pattern: str | Pattern[str]
        block_comment: str
        for key in s_dict.block_comments:
            block_comment = s_dict.block_comments[key]

            # If this is the first block_comment, make sure it contains the default block comment
            if first_block_comment:
                block_comment = self.make_default_block_comment(block_comment)
                first_block_comment = False  # disarm MonoFlop

            # Check whether the current block comment is identical with a block comment that we already inserted earlier
            # (we do not want to insert any doubled block comments)
            if re.search(re.escape(block_comment), block_comments_inserted_so_far):
                block_comment = ""

            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original block_comment.
            search_pattern = rf"BLOCKCOMMENT{key:06d}\s+BLOCKCOMMENT{key:06d};"
            if (
                len(re.findall(search_pattern, s)) > 0
            ):  # if placeholders exist in s that match the key of the current block_comment
                # Substitude the placehlder with the actual block_comment
                s = re.sub(search_pattern, re.sub(r"\\", "\\\\\\\\", block_comment), s)  # no comment
                # Document which block comments we already inserted.
                block_comments_inserted_so_far += block_comment

        # If no block_comment had been inserted, insert the default block comment
        if block_comments_inserted_so_far == "":
            s = self.make_default_block_comment() + s

        return s

    def make_default_block_comment(self, block_comment: str = "") -> str:
        """Ensure a native-format header precedes the supplied block comment.

        Args:
            block_comment: Existing block comment. If it contains a C++ marker,
                leave it unchanged. Defaults to `""`.

        Returns:
            Block comment with the native-format header prepended when needed.
        """
        # If there is no ' C++ ' contained in block_comment,
        # then insert the C++ default block comment in front:
        # sourcery skip: move-assign
        default_block_comment = (
            "/*---------------------------------*- C++ -*----------------------------------*\\\n"
            "filetype dictionary; coding utf-8; version 0.1; local --; purpose --;\n"
            "\\*----------------------------------------------------------------------------*/\n"
        )
        if not re.search(r"\s[Cc]\+{2}\s", block_comment):
            block_comment = default_block_comment + block_comment
        return block_comment

    def insert_includes(
        self,
        s_dict: SDict[K, V],
        s: str,
    ) -> str:
        """Replace include placeholders with their source directives.

        Args:
            s_dict: Dictionary containing include metadata.
            s: Formatted text containing include placeholders.

        Returns:
            Text with include placeholders replaced.
        """
        search_pattern: str | Pattern[str]
        for key, (_, include_file_name, _) in s_dict.includes.items():
            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original include directive.
            _include_file_name = include_file_name.replace("\\", "\\\\")
            _include_file_name = self.format_value(_include_file_name)
            _include_directive = f"#include {_include_file_name}"
            search_pattern = rf"INCLUDE{key:06d}\s+INCLUDE{key:06d};"
            s = re.sub(search_pattern, _include_directive, s)

        return s

    def insert_line_comments(
        self,
        s_dict: SDict[K, V],
        s: str,
    ) -> str:
        """Replace line-comment placeholders with their original comments.

        Args:
            s_dict: Dictionary containing line comments.
            s: Formatted text containing line-comment placeholders.

        Returns:
            Text with line-comment placeholders replaced.
        """
        search_pattern: str | Pattern[str]
        for key, line_comment in s_dict.line_comments.items():
            # Search for the placeholder entry we created in _parse_tokenized_dict(),
            # and insert back the original block_comment.
            search_pattern = rf"LINECOMMENT{key:06d}\s+LINECOMMENT{key:06d};"
            s = re.sub(search_pattern, line_comment, s)

        return s

    def remove_trailing_spaces(self, s: str) -> str:
        """Remove trailing spaces from all lines.

        Args:
            s: Text whose lines should be stripped of trailing whitespace.

        Returns:
            Text with trailing spaces removed and line endings preserved.
        """
        stream = io.StringIO(newline=None)
        _ = stream.write(s)
        _ = stream.seek(0)
        ns = ""
        for line in stream.readlines():
            if match := re.search("[\r\n]*$", line):
                line_ending = match[0]
                line_without_ending = line[: len(line) - len(line_ending)]
                line_without_trailingspaces = re.sub(r"\s+$", "", line_without_ending) + line_ending
                ns += line_without_trailingspaces
        return ns


class FoamFormatter(NativeFormatter):
    """Formatter to serialize a dict into a string in OpenFOAM dictionary format."""

    def __init__(self) -> None:
        """Define default configuration for FoamFormatter."""
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        arg: MutableMapping[K, V],
    ) -> str:
        """Create a string representation of the passed in dict in OpenFOAM dictionary format.

        Args:
            arg: dict to be formatted

        Returns:
            string representation of the dict in OpenFOAM dictionary format
        """
        # Foam dicts are, in contrast to dictIO default dicts, restricted in what they may contain.
        # The dict content is hence reduced to what Foam is able to interpret.
        # Elements that Foam cannot interpret - or would misinterpret - are removed:

        # Remove all dict entries starting with underscore
        def remove_underscore_keys_recursive(
            arg: MutableMapping[K, V],
        ) -> None:
            keys = list(arg.keys())
            for key in keys:
                if self.format_key(key).startswith("_"):
                    del arg[key]
                elif isinstance(arg[key], MutableMapping):
                    remove_underscore_keys_recursive(arg[key])  # recursion
            return

        dict_adapted_for_foam = deepcopy(arg)
        remove_underscore_keys_recursive(dict_adapted_for_foam)

        # Call base class implementation (NativeFormatter)
        s = super().to_string(dict_adapted_for_foam)

        # Substitute all remeining single quotes, if any, by double quotes:
        # s = re.sub('\'', '"', s)  # noqa: ERA001

        return s

    def format_empty_string(self, arg: str) -> str:
        """Format an empty string.

        Args:
            arg: the empty string to be formatted

        Returns:
            the formatted empty string
        """
        return self.add_double_quotes(arg)

    def format_string_with_nested_string(self, arg: str) -> str:
        """Format a string that contains a nested string.

        Args:
            arg: the string with a nested string to be formatted

        Returns:
            the formatted string with a nested string

        Raises:
            ValueError: If the input does not contain a nested quote.
        """
        if re.search(r'"', arg):
            _arg: str = re.sub(r'"', '\\"', arg)
            return self.add_double_quotes(_arg)
        if re.search(r"'", arg):
            return self.add_double_quotes(arg)
        raise ValueError(f"expected a string with a nested string. However, following string was passed in: {arg}")

    def format_multi_word_string(self, arg: str) -> str:
        """Format a multi word string.

        Args:
            arg: the multi word string to be formatted

        Returns:
            the formatted multi word string
        """
        return self.add_double_quotes(arg)

    def format_expression_string(self, arg: str) -> str:
        """Format an expression.

        Args:
            arg: the expression to be formatted

        Returns:
            the formatted expression
        """
        return self.add_double_quotes(arg)

    def make_default_block_comment(self, block_comment: str = "") -> str:
        """Ensure an OpenFOAM header precedes the supplied block comment.

        Args:
            block_comment: Existing block comment. If it contains a C++ marker
                and the OpenFOAM header, leave it unchanged. If it has no C++
                marker, prepend the default OpenFOAM header. Defaults to `""`.

        Returns:
            Block comment with the OpenFOAM header prepended when needed.
        """
        # If there is no ' C++ ' and 'OpenFoam' contained in block_comment,
        # then insert the OpenFOAM default block comment in front:
        default_block_comment = (
            "/*--------------------------------*- C++ -*----------------------------------*\\\n"
            "| =========                 |                                                 |\n"
            "| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n"
            "|  \\\\    /   O peration     | Version:  dev                                   |\n"
            "|   \\\\  /    A nd           | Web:      www.OpenFOAM.com                      |\n"
            "|    \\\\/     M anipulation  |                                                 |\n"
            "\\*---------------------------------------------------------------------------*/\n"
            "FoamFile\n"
            "{\n"
            "    version                   2.0;\n"
            "    format                    ascii;\n"
            "    class                     dictionary;\n"
            "    object                    foamDict;\n"
            "}\n"
            "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //\n"
        )
        if not re.search(r"\s[Cc]\+{2}\s", block_comment):
            block_comment = default_block_comment + block_comment
        if not re.search(r"OpenFOAM", block_comment):
            block_comment = default_block_comment
        return block_comment


class JsonFormatter(Formatter):
    """Formatter to serialize a dict into a string in JSON dictionary format."""

    def __init__(self) -> None:
        """Define default configuration for JsonFormatter."""
        # Invoke base class constructor
        super().__init__()

    def to_string(
        self,
        arg: MutableMapping[K, V],
    ) -> str:
        """Create a string representation of the passed in dict in JSON dictionary format.

        Args:
            arg: dict to be formatted

        Returns:
            string representation of the dict in JSON dictionary format
        """
        import json  # noqa: PLC0415

        # Json dump
        s = json.dumps(
            obj=arg,
            skipkeys=True,
            ensure_ascii=True,
            check_circular=True,
            allow_nan=True,
            sort_keys=False,
            indent=4,
            separators=(",", ":"),
        )
        if isinstance(arg, SDict):
            s = self.insert_includes(arg, s)

        return s

    def insert_includes(
        self,
        s_dict: SDict[K, V],
        s: str,
    ) -> str:
        """Replace include placeholders with JSON include directives.

        Args:
            s_dict: Dictionary containing include metadata.
            s: JSON text containing include placeholders.

        Returns:
            JSON text with include placeholders replaced.
        """
        search_pattern: str | Pattern[str]
        for key, (_, include_file_name, _) in s_dict.includes.items():
            # Search for the placeholder key in the Json string,
            # and insert back the original include directive.
            _include_file_name = include_file_name.replace("\\", "\\\\\\\\")
            _include_directive = f'"#include{key:06d}":"{_include_file_name}"'
            search_pattern = rf'"INCLUDE{key:06d}"\s*:\s*"INCLUDE{key:06d}"'
            s = re.sub(search_pattern, _include_directive, s)

        return s


class XmlFormatter(Formatter):
    r"""Formatter to serialize a dict into a string in xml format.

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

    """ <databases>
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
    """

    def __init__(
        self,
        *,
        omit_prefix: bool = True,
        integrate_attributes: bool = True,
        remove_node_numbering: bool = True,
    ) -> None:
        """Initialize XML formatting options.

        Args:
            omit_prefix: Whether to remove namespace prefixes from serialized
                element tags. Defaults to `True`.
            integrate_attributes: Whether to serialize recognized dictionary
                attributes as XML attributes. Defaults to `True`.
            remove_node_numbering: Whether to remove generated node numbers
                from element names. Defaults to `True`.
        """
        # Invoke base class constructor
        super().__init__()
        # Save default configuration as attributes
        self.omit_prefix: bool = omit_prefix
        self.integrate_attributes: bool = integrate_attributes
        self.remove_node_numbering: bool = remove_node_numbering

    def to_string(
        self,
        arg: MutableMapping[K, V],
    ) -> str:
        """Create a string representation of the passed in dict in XML format.

        Args:
            arg: dict to be formatted

        Returns:
            string representation of the dict in XML format
        """
        # Default configuration
        namespaces: MutableMapping[str, str] = {"xs": "https://www.w3.org/2009/XMLSchema/XMLSchema.xsd"}
        root_tag: str = "NOTSPECIFIED"
        root_attributes: MutableMapping[str, str] | None = None
        indent = " " * 4

        # Check whether xml opts are contained in dict.
        # If so, read and use them
        if "_xmlOpts" in arg:
            xml_opts = cast("MutableMapping[K, V]", arg[cast("K", "_xmlOpts")])
            namespaces = (
                cast("MutableMapping[str, str]", xml_opts[cast("K", "_nameSpaces")])
                if "_nameSpaces" in xml_opts
                else namespaces
            )
            root_tag = str(xml_opts[cast("K", "_rootTag")]) if "_rootTag" in xml_opts else root_tag
            root_attributes = (
                cast("MutableMapping[str, str]", xml_opts[cast("K", "_rootAttributes")])
                if "_rootAttributes" in xml_opts
                else root_attributes
            )
            self.remove_node_numbering = (
                bool(xml_opts[cast("K", "_removeNodeNumbering")])
                if "_removeNodeNumbering" in xml_opts
                else self.remove_node_numbering
            )

        prefixes: list[str] = []
        prefix: str
        uri: str
        for prefix, uri in namespaces.items():
            prefixes.append(prefix)
            if prefix == "None":
                register_namespace("", uri)
            else:
                register_namespace(prefix, uri)
        prefix = prefixes[0]

        xsd_uri: str = namespaces[prefixes[0]]

        attributes: dict[str, str] = {}
        if root_attributes:
            for key, item in root_attributes.items():
                attributes[key] = item  # noqa: PERF403

        # @TODO: Isn't it contradictory to first pass in here the attributes to root_element
        #        but then thereafter ask whether to integrate the attributes?
        root_element = Element(f"{{{xsd_uri}}}{root_tag}", attrib=attributes)
        if self.integrate_attributes:
            # integrate attributes in root element
            root_element.attrib = {k: str(v) for k, v in attributes.items() if str(v) != ""}

        self.populate_into_element(root_element, arg, xsd_uri)

        s: str = minidom.parseString(  # noqa: S318
            tostring(
                root_element,
                encoding="UTF-8",
                method="xml",
            )
        ).toprettyxml(indent=indent)
        if self.omit_prefix:
            query = f"({'|'.join(f'{s}:' for s in prefixes)})"
            s = re.sub(query, "", s)

        return s

    def populate_into_element(
        self,
        element: Element,
        arg: object,
        xsd_uri: str | None = None,
    ) -> None:
        """Populate arg into the XML element node.

        If arg is a dict or list, method will call itself recursively until all nested content within the dict or list
        is populated into nested elements, eventually creating an XML dom.

        Args:
            element: XML element to populate.
            arg: Value or nested container to add to the element.
            xsd_uri: Namespace URI for created child elements. If `None`, use
                the namespace configured by the caller. Defaults to `None`.
        """
        # sourcery skip: merge-duplicate-blocks, remove-pass-body, remove-pass-elif, remove-redundant-pass

        # @TODO: LINECOMMENTs not handled yet

        if isinstance(arg, MutableSequence):
            arg = cast("MutableSequence[Any]", arg)
            element.text = " ".join(str(x) for x in arg)

        elif isinstance(arg, MutableMapping):
            arg = cast("MutableMapping[Any, Any]", arg)
            for key, item in arg.items():
                skey: str = self.format_key(key)
                if re.match(pattern="_content", string=skey):
                    # Write back content (from the key-value pair "_content <content>;") into xml node.text
                    # In case of multiline content, do not write it inline between opening and closing tag,
                    # but add a line ending at the beginning and at the end, so that content gets formatted
                    # as an indented text block beween the opening and closing tag.
                    text = str(item)
                    if text not in [None, ""] and len(text.splitlines()) > 1:
                        text = "\n" + text + "\n"
                    element.text = text

                elif self.integrate_attributes and re.match(pattern="_attrib", string=skey):
                    # attributes to integrate in node, otherwise leave in content
                    # correct occurence of true false -> de-pythonize for lowercase
                    if isinstance(item, Mapping):
                        attributes: dict[str, str] = {
                            k: str(v).lower()
                            if re.match(pattern="^(true|false)$", string=str(v), flags=re.IGNORECASE)
                            else str(v)
                            for k, v in item.items()
                        }
                        element.attrib = attributes

                elif re.match(pattern="^(_.*[Oo]pts|INCLUDE)", string=skey):
                    # underscore elements _opts _xmlOpts and INCLUDE are considered not being content so far
                    pass

                elif re.match(pattern="BLOCKCOMMENT[0-9]+", string=skey):
                    if re.search(pattern=".*0$", string=skey):
                        # take all except the first one as this is /* C++ dict */
                        pass
                    else:
                        # @TODO: Implement substitution of BLOCKCOMMENT
                        # cIndex = int(re.findall('(?<=BLOCKCOMMENT)[0-9]+', skey)[0])  # noqa: ERA001
                        # element.append(Comment(item))  # noqa: ERA001
                        pass

                elif re.match(pattern="LINECOMMENT[0-9]+", string=skey):
                    # @TODO: Implement substitution of LINECOMMENT
                    # cIndex = int(re.findall('(?<=LINECOMMENT)[0-9;]+', skey)[0])  # noqa: ERA001
                    # root_element.append(Comment(re.sub('/', '', self.dict.line_comments[cIndex])))  # noqa: ERA001
                    pass

                else:
                    # nested content
                    _skey = skey
                    _item = item
                    if self.remove_node_numbering:
                        _skey = re.sub(pattern=r"(^\d{1,6}_)", repl="", string=_skey)

                    # Substitute with empty string to force <NODE/> in favour of <NODE>None</NODE>
                    if _item is None:
                        _item = ""

                    child_node = SubElement(element, f"{{{xsd_uri}}}{_skey}")
                    self.populate_into_element(element=child_node, arg=_item, xsd_uri=xsd_uri)

        else:
            element.text = str(arg)

        return
