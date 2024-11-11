# pyright: reportPrivateUsage=false
# pyright: reportUnnecessaryTypeIgnoreComment=false
# ruff: noqa: T201, E501
import re
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from dictIO import NativeParser, Parser, SDict, XmlParser
from dictIO.types import K, V
from dictIO.utils.counter import BorgCounter
from dictIO.utils.strings import string_diff


class TestParser:
    # @TODO: To be implemented
    @pytest.mark.skip(reason="To be implemented")
    def test_get_parser(self) -> None:
        pass

    def test_file_not_found_exception(self) -> None:
        # Prepare
        parser = Parser()
        source_file = Path("this_file_does_not_exist")
        # Execute and Assert
        with pytest.raises(FileNotFoundError):
            _ = parser.parse_file(source_file)

    def test_remove_quotes_from_string(self) -> None:
        str_in_1 = "'a string with single quotes'"
        str_in_2 = '"a string with double quotes"'
        str_in_3 = "'a string with 'inside' quotes'"
        str_in_4 = "'a string with \"inside\" double quotes'"
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        # Test with argument 'all' = False (default)
        str_out_1 = Parser.remove_quotes_from_string(str_in_1)
        assert str_out_1 == "a string with single quotes"
        str_out_2 = Parser.remove_quotes_from_string(str_in_2)
        assert str_out_2 == "a string with double quotes"
        str_out_3 = Parser.remove_quotes_from_string(str_in_3)
        assert str_out_3 == "a string with 'inside' quotes"
        str_out_4 = Parser.remove_quotes_from_string(str_in_4)
        assert str_out_4 == 'a string with "inside" double quotes'

        # Test with argument 'all' = True
        str_out_1 = Parser.remove_quotes_from_string(str_in_1, all_quotes=True)
        assert str_out_1 == "a string with single quotes"
        str_out_2 = Parser.remove_quotes_from_string(str_in_2, all_quotes=True)
        assert str_out_2 == "a string with double quotes"
        str_out_3 = Parser.remove_quotes_from_string(str_in_3, all_quotes=True)
        assert str_out_3 == "a string with inside quotes"
        str_out_4 = Parser.remove_quotes_from_string(str_in_4, all_quotes=True)
        assert str_out_4 == "a string with inside double quotes"

        with pytest.raises(TypeError):
            _ = Parser.remove_quotes_from_string(not_a_str_1)  # type: ignore[arg-type, reportArgumentType]
        with pytest.raises(TypeError):
            _ = Parser.remove_quotes_from_string(not_a_str_2)  # type: ignore[arg-type, reportArgumentType]
        with pytest.raises(TypeError):
            _ = Parser.remove_quotes_from_string(not_a_str_3)  # type: ignore[arg-type, reportArgumentType]

    def test_remove_quotes_from_strings(self) -> None:
        str_in_1 = "'a string with single quotes'"
        str_in_2 = '"a string with double quotes"'
        str_in_3 = "'a string with 'inside' quotes'"
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        key_1 = "key_1"
        key_2 = "key_2"
        key_3 = "key_3"
        key_n_1 = "key_n_1"
        key_n_2 = "key_n_2"
        key_n_3 = "key_n_3"
        keyd = "keyd"
        keyl = "keyl"
        d_nested = {
            key_1: str_in_1,
            key_2: str_in_2,
            key_3: str_in_3,
            key_n_1: not_a_str_1,
            key_n_2: not_a_str_2,
            key_n_3: not_a_str_3,
        }
        l_nested = [str_in_1, str_in_2, str_in_3, not_a_str_1, not_a_str_2, not_a_str_3]
        # construct a dictionary with single entries, a nested dict and a nested list
        dict_in: dict[str, Any] = {
            key_1: str_in_1,
            key_2: str_in_2,
            key_3: str_in_3,
            key_n_1: not_a_str_1,
            key_n_2: not_a_str_2,
            key_n_3: not_a_str_3,
            keyd: d_nested,
            keyl: l_nested,
        }

        str_out_1 = "a string with single quotes"
        str_out_2 = "a string with double quotes"
        str_out_3 = "a string with 'inside' quotes"

        dict_out = deepcopy(dict_in)
        _ = Parser.remove_quotes_from_strings(dict_out)
        assert dict_out[key_1] == str_out_1
        assert dict_out[key_2] == str_out_2
        # changes here parser.remove_quotes_from_string: "all" to True
        # to protect inside strings in e.g. farn filter expression "var in ['item1', 'item2']"
        assert dict_out[key_3] == str_out_3
        assert dict_out[keyd][key_1] == str_out_1
        assert dict_out[keyd][key_2] == str_out_2
        assert dict_out[keyd][key_3] == str_out_3
        assert dict_out[keyl][0] == str_out_1
        assert dict_out[keyl][1] == str_out_2
        assert dict_out[keyl][2] == str_out_3
        assert dict_out[key_n_1] == not_a_str_1
        assert dict_out[key_n_2] == not_a_str_2
        assert dict_out[key_n_3] == not_a_str_3
        assert dict_out[keyd][key_n_1] == not_a_str_1
        assert dict_out[keyd][key_n_2] == not_a_str_2
        assert dict_out[keyd][key_n_3] == not_a_str_3
        assert dict_out[keyl][3] == not_a_str_1
        assert dict_out[keyl][4] == not_a_str_2
        assert dict_out[keyl][5] == not_a_str_3

        with pytest.raises(TypeError):
            _ = Parser.remove_quotes_from_strings(str_in_1)  # type: ignore[arg-type, reportArgumentType]
        with pytest.raises(TypeError):
            _ = Parser.remove_quotes_from_strings(not_a_str_1)  # type: ignore[arg-type, reportArgumentType]

    def test_parse_value_int(self) -> None:
        parser = Parser()
        int_in = 1
        int_out = parser.parse_value(int_in)
        assert isinstance(int_out, int)
        assert int_out == int_in

    def test_parse_value_float(self) -> None:
        parser = Parser()
        float_in = 1.0
        float_out = parser.parse_value(float_in)
        assert isinstance(float_out, float)
        assert float_out == float_in

    def test_parse_value_bool(self) -> None:
        # sourcery skip: extract-duplicate-method, inline-variable
        parser = Parser()
        bool_in: str | bool
        bool_in = True
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = False
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = "True"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = "False"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = "true"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = "false"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = "  True  "
        bool_out = parser.parse_value(bool_in)
        assert bool_out is True
        bool_in = "  False  "
        bool_out = parser.parse_value(bool_in)
        assert bool_out is False
        bool_in = "ON"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = "OFF"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = "on"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = "off"
        bool_out = parser.parse_value(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False

    def test_parse_value_none(self) -> None:
        parser = Parser()
        none_in = None
        none_out = parser.parse_value(none_in)
        assert none_out is None
        none_in = "None"
        none_out = parser.parse_value(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        none_in = "none"
        none_out = parser.parse_value(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        none_in = "  None  "
        none_out = parser.parse_value(none_in)
        assert none_out is None
        none_in = "NULL"
        none_out = parser.parse_value(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        none_in = "null"
        none_out = parser.parse_value(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        assert none_out is None
        none_in = "thisisnotnull"
        none_out = parser.parse_value(none_in)
        assert isinstance(none_out, str)
        assert none_out == none_in
        none_in = "nullwithsomestuffthereafterisneithernull"
        none_out = parser.parse_value(none_in)
        assert isinstance(none_out, str)
        assert none_out == none_in

    def test_parse_value_string_numbers(self) -> None:
        # sourcery skip: extract-duplicate-method, inline-variable
        parser = Parser()
        str_in = "1234"
        int_out = parser.parse_value(str_in)
        assert isinstance(int_out, int)
        assert int_out == 1234
        str_in = "1.23"
        float_out = parser.parse_value(str_in)
        assert isinstance(float_out, float)
        assert float_out == 1.23
        str_in = "1."
        float_out = parser.parse_value(str_in)
        assert isinstance(float_out, float)
        assert float_out == 1.0

    @pytest.mark.parametrize(
        "str_in, str_expected",
        [
            ("a string", "a string"),
            ("'a string'", "a string"),
            ('"a string"', "a string"),
            ("", ""),
            ("''", ""),
            ('""', ""),
        ],
    )
    def test_parse_value_str(self, str_in: str, str_expected: str) -> None:
        """Make sure additional surrounding quotes of strings, if existing, get removed by parsing"""
        # Prepare
        parser = Parser()
        # Execute
        str_out = parser.parse_value(str_in)
        # Assert
        assert isinstance(str_out, str)
        assert str_out == str_expected

    def test_parse_list(self) -> None:
        # Prepare
        parser = Parser()
        str_1 = "string 1"
        str_2 = "string 2"
        str_3 = "string 3"
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        list_nested = [
            str_1,
            str_2,
            str_3,
            not_a_str_1,
            not_a_str_2,
            not_a_str_3,
        ]
        list_in = [
            str_1,
            str_2,
            str_3,
            list_nested,
            not_a_str_1,
            not_a_str_2,
            not_a_str_3,
        ]

        string1_expected = parser.parse_value(str_1)
        string2_expected = parser.parse_value(str_2)
        string3_expected = parser.parse_value(str_3)
        not_a_str_1_expected = parser.parse_value(not_a_str_1)
        not_a_str_2_expected = parser.parse_value(not_a_str_2)
        not_a_str_3_expected = parser.parse_value(not_a_str_3)

        list_expected_nested = [
            string1_expected,
            string2_expected,
            string3_expected,
            not_a_str_1_expected,
            not_a_str_2_expected,
            not_a_str_3_expected,
        ]
        list_expected = [
            string1_expected,
            string2_expected,
            string3_expected,
            list_expected_nested,
            not_a_str_1_expected,
            not_a_str_2_expected,
            not_a_str_3_expected,
        ]

        # Execute
        list_out = deepcopy(list_in)
        parser.parse_values(list_out)
        # Assert
        # assert list_out is list_in
        assert list_out == list_expected
        assert list_out[3] == list_expected[3]

    def test_parse_file_into_existing_dict(self) -> None:
        # Prepare
        target_dict: SDict[str, Any] = SDict()
        source_file = Path("test_parser_dict")
        parser = Parser()
        # Execute
        _ = parser.parse_file(source_file, target_dict)
        # Assert
        assert target_dict.source_file == source_file.absolute()
        assert target_dict.path == source_file.absolute().parent
        assert target_dict.name == source_file.absolute().name


class TestNativeParser:
    def test_extract_line_comments(self) -> None:
        # sourcery skip: no-loop-in-tests
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        line1 = "a line with no line comment\n"
        line2 = "//a line comment\n"
        line3 = "a line with //an inline comment\n"
        line4 = "a line with no line comment\n"
        s_dict.line_content.extend([line1, line2, line3, line4])
        assert len(s_dict.line_content) == 4
        # Execute
        parser._extract_line_comments(s_dict, comments=True)
        # Assert
        assert len(s_dict.line_content) == 4
        for line in s_dict.line_content:
            assert re.search(r"//", line) is None
        assert len(s_dict.line_comments) == 2
        for line in s_dict.line_comments.values():
            assert re.search("//", str(line)) is not None

    def test_extract_includes(self) -> None:
        # sourcery skip: no-loop-in-tests
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        line1 = "a line with no include directive\n"
        line2 = "#include testDict\n"
        line3 = "#include 'testDict'\n"
        line4 = '#include "testDict"\n'
        # line4 = '#include testDict with some dummy content thereafter\n'   # this is currently not covered by _extract_includes() and would fail
        line5 = "   #include testDict   \n"
        line6 = "   # include testDict   \n"
        line7 = "a line with no include directive\n"
        s_dict.line_content.extend([line1, line2, line3, line4, line5, line6, line7])
        assert len(s_dict.line_content) == 7
        file_name_expected = "testDict"
        file_path_expected = Path("testDict").absolute()
        # Execute
        parser._extract_includes(s_dict)
        # Assert
        assert len(s_dict.line_content) == 7
        for line in s_dict.line_content:
            assert "#include" not in line
        assert len(s_dict.includes) == 5
        for (
            include_directive,
            include_file_name,
            include_file_path,
        ) in s_dict.includes.values():
            assert bool(re.search(r"#\s*include", str(include_directive)))
            assert not bool(re.search(r"\n", str(include_directive)))
            assert include_file_name == file_name_expected
            assert include_file_path == file_path_expected

    def test_convert_line_content_to_block_content(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        # Three lines with line endings
        line1 = "line 1\n"
        line2 = "line 2\n"
        line3 = "line 3\n"
        s_dict.line_content.extend([line1, line2, line3])
        # Execute
        parser._convert_line_content_to_block_content(s_dict)
        # Assert
        assert s_dict.block_content == "line 1\nline 2\nline 3\n"

    def test_remove_line_endings_from_block_content(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        # Three lines with line endings
        line1 = "line 1\n"
        line2 = "line 2\n"
        line3 = "line 3\n"
        s_dict.line_content.extend([line1, line2, line3])
        parser._convert_line_content_to_block_content(s_dict)
        # Execute
        parser._remove_line_endings_from_block_content(s_dict)
        # Assert
        assert s_dict.block_content == "line 1 line 2 line 3"

    def test_extract_block_comments(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block_in = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are C++ block comments.\n"
            "C++ block comments have an opening line, the block comment itself, and a closing line. See following example:\n"
            "/*---------------------------------*- C++ -*----------------------------------*\\\n"
            "This is a block comment; coding utf-8; version 0.1;\n"
            "\\*----------------------------------------------------------------------------*/\n"
            "Identified block comments are extracted and replaced by a placeholder\n"
            "in the form B L O C K C O M M E N T 0 0 0 0 0 0 ."
        )
        text_block_expected = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are C++ block comments.\n"
            "C++ block comments have an opening line, the block comment itself, and a closing line. See following example:\n"
            "BLOCKCOMMENT000000\n"
            "Identified block comments are extracted and replaced by a placeholder\n"
            "in the form B L O C K C O M M E N T 0 0 0 0 0 0 ."
        )
        s_dict.block_content = text_block_in
        # Execute
        parser._extract_block_comments(s_dict, comments=True)
        # Assert
        text_block_out = re.sub(r"[0-9]{6}", "000000", s_dict.block_content)
        assert text_block_out == text_block_expected
        print(string_diff(text_block_out, text_block_expected))
        assert len(s_dict.block_comments) == 1
        assert list(s_dict.block_comments.values())[0] == (
            "/*---------------------------------*- C++ -*----------------------------------*\\\n"
            "This is a block comment; coding utf-8; version 0.1;\n"
            "\\*----------------------------------------------------------------------------*/"
        )

    def test_extract_string_literals(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block_in = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are inline substrings with single quotes.\n"
            "Such substrings we identify as string literals and substitute them with a placeholder\n"
            "in the form S T R I N G L I T E R A L 0 0 0 0 0 0.  Lets look at some examples in the following three lines:\n"
            "This is a line with 'a string literal1'\n"
            "This is a line with 'a string literal2' and some blabla thereafter.\n"
            "This is a line with ' a string literal3 with leading and trailing spaces '\n"
            "'This line starts with a string literal4' and then has some blabla thereafter.\n"
            "'This line is nothing else than a string literal5'"
            'This is a line with "a string literal6 in double quotes". Although having double quotes, it is still identified as a string literal because it does not contain a $ character.\n'
            'This is a line with an expression, e.g. "$varName2 + 4". Expressions are double quoted strings that contain minimum one $ character (denoting a reference).\n'
            "And here we close our small test with a final line with no string literal at all"
        )
        text_block_expected = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are inline substrings with single quotes.\n"
            "Such substrings we identify as string literals and substitute them with a placeholder\n"
            "in the form S T R I N G L I T E R A L 0 0 0 0 0 0.  Lets look at some examples in the following three lines:\n"
            "This is a line with STRINGLITERAL000000\n"
            "This is a line with STRINGLITERAL000000 and some blabla thereafter.\n"
            "This is a line with STRINGLITERAL000000\n"
            "STRINGLITERAL000000 and then has some blabla thereafter.\n"
            "STRINGLITERAL000000"
            "This is a line with STRINGLITERAL000000. Although having double quotes, it is still identified as a string literal because it does not contain a $ character.\n"
            'This is a line with an expression, e.g. "$varName2 + 4". Expressions are double quoted strings that contain minimum one $ character (denoting a reference).\n'
            "And here we close our small test with a final line with no string literal at all"
        )
        s_dict.block_content = text_block_in
        # Execute
        parser._extract_string_literals(s_dict)
        # Assert
        text_block_out = re.sub(r"[0-9]{6}", "000000", s_dict.block_content)
        print(string_diff(text_block_out, text_block_expected))
        assert text_block_out == text_block_expected
        assert len(s_dict.string_literals) == 6
        assert list(s_dict.string_literals.values())[0] == "a string literal1"
        assert list(s_dict.string_literals.values())[1] == "a string literal2"
        assert list(s_dict.string_literals.values())[2] == " a string literal3 with leading and trailing spaces "
        assert list(s_dict.string_literals.values())[3] == "This line starts with a string literal4"
        assert list(s_dict.string_literals.values())[4] == "This line is nothing else than a string literal5"
        assert list(s_dict.string_literals.values())[5] == "a string literal6 in double quotes"

    def test_extract_expressions(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block_in = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are key value pairs where the value\n"
            "is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n"
            "Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n"
            "The following examples will be identified as expressions:\n"
            "   reference1      $varName1\n"
            "   reference2      $varName1[0]\n"
            "   reference3      $varName1[1][2]\n"
            '   expression1     "$varName1"\n'
            '   expression2     "$varName2 + 4"\n'
            '   expression3     "4 + $varName2"\n'
            '   expression4     "$varName2 + $varName3" and some blabla thereafter\n'
            '   expression5     "$varName1 + $varName2 + $varName3" and some blabla thereafter\n'
            '   expression6     "$varName2 + $varName3 + $varName1" and some blabla thereafter\n'
            "The following example will NOT be identified as expression but as string literal:\n"
            "   string1         '$varName1 is not an expression but a string literal because it is in single instead of double quotes'\n"
            '   string2         "not an expression but a string literal as it does not contain a Dollar character"\n'
            "_extract_expressions() will extract expressions and substitute them with a placeholder\n"
            "in the form E X P R E S S I O N 0 0 0 0 0 0."
            "The actual evaluation of an expression is not part of _extract_expressions(). The evaluation is done within ()."
        )
        text_block_expected = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are key value pairs where the value\n"
            "is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n"
            "Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n"
            "The following examples will be identified as expressions:\n"
            "   reference1      EXPRESSION000000\n"
            "   reference2      EXPRESSION000000\n"
            "   reference3      EXPRESSION000000\n"
            "   expression1     EXPRESSION000000\n"
            "   expression2     EXPRESSION000000\n"
            "   expression3     EXPRESSION000000\n"
            "   expression4     EXPRESSION000000 and some blabla thereafter\n"
            "   expression5     EXPRESSION000000 and some blabla thereafter\n"
            "   expression6     EXPRESSION000000 and some blabla thereafter\n"
            "The following example will NOT be identified as expression but as string literal:\n"
            "   string1         STRINGLITERAL000000\n"
            "   string2         STRINGLITERAL000000\n"
            "_extract_expressions() will extract expressions and substitute them with a placeholder\n"
            "in the form E X P R E S S I O N 0 0 0 0 0 0."
            "The actual evaluation of an expression is not part of _extract_expressions(). The evaluation is done within ()."
        )
        s_dict.block_content = text_block_in
        parser._extract_string_literals(s_dict)
        # Execute
        parser._extract_expressions(s_dict)
        # Assert
        text_block_out = re.sub(r"[0-9]{6}", "000000", s_dict.block_content)
        assert text_block_out == text_block_expected
        print(string_diff(text_block_out, text_block_expected))
        assert len(s_dict.expressions) == 9

        assert list(s_dict.expressions.values())[0]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[0]["expression"] == "$varName1"

        assert list(s_dict.expressions.values())[1]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[1]["expression"] == "$varName2 + 4"

        assert list(s_dict.expressions.values())[2]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[2]["expression"] == "4 + $varName2"

        assert list(s_dict.expressions.values())[3]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[3]["expression"] == "$varName2 + $varName3"

        assert list(s_dict.expressions.values())[4]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[4]["expression"] == "$varName1 + $varName2 + $varName3"

        assert list(s_dict.expressions.values())[5]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[5]["expression"] == "$varName2 + $varName3 + $varName1"

        assert list(s_dict.expressions.values())[6]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[6]["expression"] == "$varName1"

        assert list(s_dict.expressions.values())[7]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[7]["expression"] == "$varName1[0]"

        assert list(s_dict.expressions.values())[8]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[8]["expression"] == "$varName1[1][2]"

    def test_extract_single_character_expressions(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block_in = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are key value pairs where the value\n"
            "is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n"
            "Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n"
            "The following examples will be identified as expressions:\n"
            "   reference1      $a\n"
            "   reference2      $a[0]\n"
            "   reference3      $a[1][2]\n"
            '   expression1     "$a"\n'
            '   expression2     "$b + 4"\n'
            '   expression3     "4 + $b"\n'
            '   expression4     "$b + $c" and some blabla thereafter\n'
            '   expression5     "$a + $b + $c" and some blabla thereafter\n'
            '   expression6     "$b + $c + $a" and some blabla thereafter\n'
            "The following example will NOT be identified as expression but as string literal:\n"
            "   string1         '$a is not an expression but a string literal because it is in single instead of double quotes'\n"
            '   string2         "not an expression but a string literal as it does not contain a Dollar character"\n'
            "_extract_expressions() will extract expressions and substitute them with a placeholder\n"
            "in the form E X P R E S S I O N 0 0 0 0 0 0."
            "The actual evaluation of an expression is not part of _extract_expressions(). The evaluation is done within ()."
        )
        text_block_expected = (
            "This is a text block\n"
            "with multiple lines. Within this text block, there are key value pairs where the value\n"
            "is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n"
            "Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n"
            "The following examples will be identified as expressions:\n"
            "   reference1      EXPRESSION000000\n"
            "   reference2      EXPRESSION000000\n"
            "   reference3      EXPRESSION000000\n"
            "   expression1     EXPRESSION000000\n"
            "   expression2     EXPRESSION000000\n"
            "   expression3     EXPRESSION000000\n"
            "   expression4     EXPRESSION000000 and some blabla thereafter\n"
            "   expression5     EXPRESSION000000 and some blabla thereafter\n"
            "   expression6     EXPRESSION000000 and some blabla thereafter\n"
            "The following example will NOT be identified as expression but as string literal:\n"
            "   string1         STRINGLITERAL000000\n"
            "   string2         STRINGLITERAL000000\n"
            "_extract_expressions() will extract expressions and substitute them with a placeholder\n"
            "in the form E X P R E S S I O N 0 0 0 0 0 0."
            "The actual evaluation of an expression is not part of _extract_expressions(). The evaluation is done within ()."
        )
        s_dict.block_content = text_block_in
        parser._extract_string_literals(s_dict)
        # Execute
        parser._extract_expressions(s_dict)
        # Assert
        text_block_out = re.sub(r"[0-9]{6}", "000000", s_dict.block_content)
        assert text_block_out == text_block_expected
        print(string_diff(text_block_out, text_block_expected))
        assert len(s_dict.expressions) == 9

        assert list(s_dict.expressions.values())[0]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[0]["expression"] == "$a"

        assert list(s_dict.expressions.values())[1]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[1]["expression"] == "$b + 4"

        assert list(s_dict.expressions.values())[2]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[2]["expression"] == "4 + $b"

        assert list(s_dict.expressions.values())[3]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[3]["expression"] == "$b + $c"

        assert list(s_dict.expressions.values())[4]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[4]["expression"] == "$a + $b + $c"

        assert list(s_dict.expressions.values())[5]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[5]["expression"] == "$b + $c + $a"

        assert list(s_dict.expressions.values())[6]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[6]["expression"] == "$a"

        assert list(s_dict.expressions.values())[7]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[7]["expression"] == "$a[0]"

        assert list(s_dict.expressions.values())[8]["name"][:10] == "EXPRESSION"
        assert list(s_dict.expressions.values())[8]["expression"] == "$a[1][2]"

    def test_separate_delimiters(self) -> None:
        # sourcery skip: no-loop-in-tests
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block_in = (
            "This is a text block\n"
            "with multiple lines. Within this text block there are distinct chars that shall be identified as delimiters.\n"
            "All chars that shall be identified delimiters are passed to _separate_delimiters as a list of chars.\n"
            "_separate_delimiters parses .block_content for occurences of these delimiters and strips any spaces surrounding the\n"
            "delimiter to exactly one single space before and one single space after the delimiter.\n"
            "It further removes all line endings from .block_content and eventually replaces them with single spaces.\n"
            "This is a preparatory step to ensure proper splitting at the delimiters when decomposing .block_content into tokens.\n"
            "Lets look at some examples in the following lines:\n"
            "These chars are identified as delimiters:{}()<>;,\n"
            "These chars are not identified as delimiters: .:-_|#+*\n"
            "Some delimiters with lots of spaces before and after:    {    }    (    )    <    >    ;    ,    \n"
            "delimiters burried between other text: bla{bla}bla(bla)bla<bla>bla;bla,bla\n"
            "And here we close our small test with a final line with no delimiter at all"
        )
        text_block_expected = (
            "This is a text block "
            "with multiple lines. Within this text block there are distinct chars that shall be identified as delimiters. "
            "All chars that shall be identified delimiters are passed to _separate_delimiters as a list of chars. "
            "_separate_delimiters parses .block_content for occurences of these delimiters and strips any spaces surrounding the "
            "delimiter to exactly one single space before and one single space after the delimiter. "
            "It further removes all line endings from .block_content and eventually replaces them with single spaces. "
            "This is a preparatory step to ensure proper splitting at the delimiters when decomposing .block_content into tokens. "
            "Lets look at some examples in the following lines: "
            "These chars are identified as delimiters: { } ( ) < > ; , "
            "These chars are not identified as delimiters: .:-_|#+* "
            "Some delimiters with lots of spaces before and after: { } ( ) < > ; , "
            "delimiters burried between other text: bla { bla } bla ( bla ) bla < bla > bla ; bla , bla "
            "And here we close our small test with a final line with no delimiter at all"
        )
        s_dict.block_content = text_block_in
        # Execute
        parser._separate_delimiters(s_dict, s_dict.delimiters)
        # Assert
        assert s_dict.block_content == text_block_expected
        print(string_diff(s_dict.block_content, text_block_expected))
        # In addition, test whether re.split('\s', block_content) results in tokens containing one single word each
        # because this exactly is what _separate_delimiters() is meant to ensure
        s_dict.tokens = [(0, i) for i in re.split(r"\s", s_dict.block_content)]
        assert len(s_dict.tokens) == 184
        for _, token in s_dict.tokens:
            assert len(token) > 0

    def test_determine_token_hierarchy(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        parser = NativeParser()
        text_block = (
            "level0 { level1 { level2 { level3 } level2 } level1 } level0\n"
            "level0 [ level1 [ level2 [ level3 ] level2 ] level1 ] level0\n"
            "level0 ( level1 ( level2 ( level3 ) level2 ) level1 ) level0"
        )
        tokens: list[str] = re.split(r"\s", text_block)
        tokens_in: list[tuple[int, str]] = [(0, token) for token in tokens]
        levels_expected = [0, 0, 1, 1, 2, 2, 3, 2, 2, 1, 1, 0, 0] * 3
        tokens_expected = list(zip(levels_expected, tokens, strict=False))
        s_dict.tokens = tokens_in
        # Execute
        parser._determine_token_hierarchy(s_dict)
        # Assert
        assert s_dict.tokens == tokens_expected

    def test_parse_tokenized_dict(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out: dict[str, Any] = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out) == 13
        keys: list[str] = list(dict_out.keys())
        assert type(keys[0]) is str
        assert keys[0][:12] == "BLOCKCOMMENT"
        assert type(keys[1]) is str
        assert keys[1][:7] == "INCLUDE"
        assert type(keys[2]) is str
        assert keys[2][:11] == "LINECOMMENT"
        assert keys[3] == "emptyDict"
        assert keys[4] == "emptyList"
        assert keys[5] == "booleans"
        assert keys[6] == "numbers"
        assert keys[7] == "nones"
        assert keys[8] == "strings"
        assert keys[9] == "invalid"
        assert keys[10] == "nesting"
        assert keys[11] == "expressions"
        assert keys[12] == "theDictInAListPitfall"

    def test_parse_tokenized_dict_booleans(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["booleans"]) == 8  # bool1, bool2, ..., bool8
        assert isinstance(dict_out["booleans"]["bool1"], bool)
        assert isinstance(dict_out["booleans"]["bool2"], bool)
        assert isinstance(dict_out["booleans"]["bool3"], bool)
        assert isinstance(dict_out["booleans"]["bool4"], bool)
        assert isinstance(dict_out["booleans"]["bool5"], bool)
        assert isinstance(dict_out["booleans"]["bool6"], bool)
        assert isinstance(dict_out["booleans"]["bool7"], bool)
        assert isinstance(dict_out["booleans"]["bool8"], bool)
        assert dict_out["booleans"]["bool1"] is True
        assert dict_out["booleans"]["bool2"] is False
        assert dict_out["booleans"]["bool3"] is True
        assert dict_out["booleans"]["bool4"] is False
        assert dict_out["booleans"]["bool5"] is True
        assert dict_out["booleans"]["bool6"] is False
        assert dict_out["booleans"]["bool7"] is True
        assert dict_out["booleans"]["bool8"] is False

    def test_parse_tokenized_dict_numbers(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["numbers"]) == 3  # int1,int2,float1
        assert isinstance(dict_out["numbers"]["int1"], int)
        assert isinstance(dict_out["numbers"]["int2"], int)
        assert isinstance(dict_out["numbers"]["float1"], float)
        assert dict_out["numbers"]["int1"] == 0
        assert dict_out["numbers"]["int2"] == 120
        assert dict_out["numbers"]["float1"] == 3.5

    def test_parse_tokenized_dict_nones(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["nones"]) == 4  # none1, none2, none3, none4
        assert dict_out["nones"]["none1"] is None
        assert dict_out["nones"]["none2"] is None
        assert dict_out["nones"]["none3"] is None
        assert dict_out["nones"]["none4"] is None

    def test_parse_tokenized_dict_strings(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["strings"]) == 7
        assert dict_out["strings"]["string1"][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["string2"][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["string3"][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["string4"] == "singleWordsWithoutSpacesCanAlsoBeDeclaredWithoutQuotes"
        assert dict_out["strings"]["string5"][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["string6"][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["listWithStrings"][0][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["listWithStrings"][1][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["listWithStrings"][2][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["listWithStrings"][3][:13] == "STRINGLITERAL"
        assert dict_out["strings"]["listWithStrings"][4][:13] == "STRINGLITERAL"

    def test_parse_tokenized_dict_invalid(self, caplog: pytest.LogCaptureFixture) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        log_level_expected = "WARNING"
        log_message_0_expected = (
            "NativeParser._parse_tokenized_dict(): tokens skipped: "
            "[(1, 'this'), (1, 'is'), (1, 'not'), (1, 'a'), (1, 'valid'), (1, 'key'), (1, 'value'), (1, 'pair'),"
            " (1, 'because'), (1, 'the'), (1, 'number'), (1, 'of'), (1, 'tokens'), (1, 'is'), (1, 'larger'), (1, 'than'), (1, 'two'), (1, ';')] "
            "inside /this is not a valid key value pair because the number of tokens is larger than two ; thisIsNeitherAValidKeyValuePairBecuaseThisIsOnlyOneToken ;/"
        )
        log_message_1_expected = (
            "NativeParser._parse_tokenized_dict(): tokens skipped: "
            "[(1, 'thisIsNeitherAValidKeyValuePairBecuaseThisIsOnlyOneToken'), (1, ';')] "
            "inside /this is not a valid key value pair because the number of tokens is larger than two ; thisIsNeitherAValidKeyValuePairBecuaseThisIsOnlyOneToken ;/"
        )
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["invalid"]) == 0
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == log_level_expected
        assert caplog.records[0].message == log_message_0_expected
        assert caplog.records[1].message == log_message_1_expected

    def test_parse_tokenized_dict_nesting(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["nesting"]) == 5
        # Assert emptyNestedDict
        assert len(dict_out["nesting"]["emptyNestedDict"]) == 0
        # Assert emptyNestedList
        assert len(dict_out["nesting"]["emptyNestedList"]) == 0
        # Assert nested dict with nested list
        assert len(dict_out["nesting"]["nestedDictWithNestedList"]) == 3
        assert isinstance(dict_out["nesting"]["nestedDictWithNestedList"]["list1"], list)
        assert isinstance(dict_out["nesting"]["nestedDictWithNestedList"]["list2"], list)
        assert isinstance(dict_out["nesting"]["nestedDictWithNestedList"]["list3"], list)
        assert len(dict_out["nesting"]["nestedDictWithNestedList"]["list1"]) == 3
        assert len(dict_out["nesting"]["nestedDictWithNestedList"]["list2"]) == 3
        assert len(dict_out["nesting"]["nestedDictWithNestedList"]["list3"]) == 3
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list1"][0] == 1.00000000e00
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list1"][1] == 2.20972831e-17
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list1"][2] == 3.15717747e-18
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list2"][0] == 2.20972831e-17
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list2"][1] == 1.00000000e00
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list2"][2] == -7.07290050e-18
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list3"][0] == 3.15717747e-18
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list3"][1] == -7.07290050e-18
        assert dict_out["nesting"]["nestedDictWithNestedList"]["list3"][2] == 1.00000000e00
        # Assert nested list with nested list
        assert len(dict_out["nesting"]["nestedListWithNestedList"]) == 3
        assert isinstance(dict_out["nesting"]["nestedListWithNestedList"][0], list)
        assert isinstance(dict_out["nesting"]["nestedListWithNestedList"][1], list)
        assert isinstance(dict_out["nesting"]["nestedListWithNestedList"][2], list)
        assert len(dict_out["nesting"]["nestedListWithNestedList"][0]) == 3
        assert len(dict_out["nesting"]["nestedListWithNestedList"][1]) == 3
        assert len(dict_out["nesting"]["nestedListWithNestedList"][2]) == 3
        assert dict_out["nesting"]["nestedListWithNestedList"][0][0] == 1.00000000e00
        assert dict_out["nesting"]["nestedListWithNestedList"][0][1] == 2.20972831e-17
        assert dict_out["nesting"]["nestedListWithNestedList"][0][2] == 3.15717747e-18
        assert dict_out["nesting"]["nestedListWithNestedList"][1][0] == 2.20972831e-17
        assert dict_out["nesting"]["nestedListWithNestedList"][1][1] == 1.00000000e00
        assert dict_out["nesting"]["nestedListWithNestedList"][1][2] == -7.07290050e-18
        assert dict_out["nesting"]["nestedListWithNestedList"][2][0] == 3.15717747e-18
        assert dict_out["nesting"]["nestedListWithNestedList"][2][1] == -7.07290050e-18
        assert dict_out["nesting"]["nestedListWithNestedList"][2][2] == 1.00000000e00
        # Assert nested list with nested dict
        assert len(dict_out["nesting"]["nestedListWithNestedDict"]) == 3
        assert isinstance(dict_out["nesting"]["nestedListWithNestedDict"][0], list)
        assert isinstance(dict_out["nesting"]["nestedListWithNestedDict"][1], dict)
        assert isinstance(dict_out["nesting"]["nestedListWithNestedDict"][2], list)
        assert len(dict_out["nesting"]["nestedListWithNestedDict"][0]) == 3
        assert len(dict_out["nesting"]["nestedListWithNestedDict"][1]) == 3
        assert len(dict_out["nesting"]["nestedListWithNestedDict"][2]) == 3
        assert dict_out["nesting"]["nestedListWithNestedDict"][0][0] == 11
        assert dict_out["nesting"]["nestedListWithNestedDict"][0][1] == 12
        assert dict_out["nesting"]["nestedListWithNestedDict"][0][2] == 13
        assert dict_out["nesting"]["nestedListWithNestedDict"][1]["value21"] == 21
        assert dict_out["nesting"]["nestedListWithNestedDict"][1]["value22"] == 22
        assert dict_out["nesting"]["nestedListWithNestedDict"][1]["value23"] == 23
        assert dict_out["nesting"]["nestedListWithNestedDict"][2][0] == 31
        assert dict_out["nesting"]["nestedListWithNestedDict"][2][1] == 32
        assert dict_out["nesting"]["nestedListWithNestedDict"][2][2] == 33

    def test_parse_tokenized_dict_expressions(self) -> None:
        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["expressions"]) == 13  # reference..G3 (level 2)
        assert len(dict_out["expressions"]["reference"]) == 3  # name,value,COMMENT (level 3)
        assert len(dict_out["expressions"]["expression1"]) == 3
        assert len(dict_out["expressions"]["expression2"]) == 3
        assert len(dict_out["expressions"]["expression3"]) == 3
        assert len(dict_out["expressions"]["expressionE"]) == 3
        assert len(dict_out["expressions"]["expressionF"]) == 3
        assert len(dict_out["expressions"]["expressionG1"]) == 3
        assert len(dict_out["expressions"]["expressionG2"]) == 3
        assert len(dict_out["expressions"]["expressionG3"]) == 3
        assert dict_out["expressions"]["reference"]["name"][:13] == "STRINGLITERAL"
        assert dict_out["expressions"]["expression1"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expression2"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expression3"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expressionE"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expressionF"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expressionG1"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expressionG2"]["value"][:10] == "EXPRESSION"
        assert dict_out["expressions"]["expressionG3"]["value"][:10] == "EXPRESSION"

    def test_parse_tokenized_dict_theDictInAListPitfall(self) -> None:
        # This test case adresses issue #6 that Frank raised on Github
        # https://github.com/MaritimeOSPx/ModelVerification/issues/6

        # sourcery skip: extract-duplicate-method

        # Prepare
        dict_in: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9, comments=False)
        parser = NativeParser()
        # Execute
        dict_out = parser._parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # Assert
        assert len(dict_out["theDictInAListPitfall"]) == 1
        assert len(dict_out["theDictInAListPitfall"]["keyToADict"]) == 1  # list
        assert (
            len(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"]) == 7
        )  # 'notAKey', {}, 'notAKey', 'notAKey', 'notAKey', 'notAKey', {}
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][0], str)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1], dict)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][2], str)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][3], str)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][4], str)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][5], str)
        assert isinstance(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6], dict)
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][0] == "notAKey"
        assert len(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1]) == 2  # key1, key2
        assert list(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1].keys())[0] == "key1"
        assert list(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1].keys())[1] == "key2"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1]["key1"] == "value1"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][1]["key2"] == "value2"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][2] == "notAKey"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][3] == "notAKey"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][4] == "notAKey"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][5] == "notAKey"
        assert len(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6]) == 2  # key1, key2
        assert list(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6].keys())[0] == "key1"
        assert list(dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6].keys())[1] == "key2"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6]["key1"] == "value1"
        assert dict_out["theDictInAListPitfall"]["keyToADict"]["keyToAList"][6]["key2"] == "value2"

    def test_insert_string_literals(self) -> None:
        # Prepare
        s_dict: SDict[str, Any] = SDict()
        SetupHelper.prepare_dict_until(dict_to_prepare=s_dict, until_step=10)
        parser = NativeParser()
        # Execute
        parser._insert_string_literals(s_dict)
        # Assert
        dict_out = s_dict
        assert dict_out["strings"]["listWithStrings"][0] == "string1"
        assert dict_out["strings"]["listWithStrings"][1] == "string2 has spaces"
        assert dict_out["strings"]["listWithStrings"][2] == "string3"
        assert dict_out["strings"]["listWithStrings"][3] == "string4 is ok but note that string5 is empty"
        assert dict_out["strings"]["listWithStrings"][4] == ""


class TestXmlParser:
    def test_default_options(self) -> None:
        # Execute
        parser = XmlParser()
        # Assert
        assert parser.add_node_numbering is True
        # assert parser.namespaces == {'xs': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'}
        # assert parser.xsd_uri == 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'
        # assert parser.root_tag == 'NOTSPECIFIED'

    def test_parse_generic_xml_without_node_numbering(self) -> None:
        # Prepare XML string to be parsed
        file_name = Path("test_parser_xml.xml")
        str_in = ""
        with Path.open(file_name) as f:
            str_in = f.read()
        dict_out: SDict[str, Any] = SDict(file_name)
        parser = XmlParser(add_node_numbering=False)
        content_TAG00_expected = (  # noqa: N806
            "Extensible Markup Language (XML) is a markup language that defines a set of rules for encoding documents in a format that is both human-readable and machine-readable.\n"
            "Mapping the basic tree model of XML to type systems of programming languages or databases can be difficult, especially when XML is used for exchanging highly structured data between applications, which was not its primary design goal.\n"
            "JSON, YAML, and S-Expressions are frequently proposed as simpler alternatives that focus on representing highly structured data rather than documents, which may contain both highly structured and relatively unstructured content."
        )
        # Execute
        dict_out = parser.parse_string(str_in, dict_out)
        # Assert
        assert dict_out["TAG00"]["_content"] == content_TAG00_expected
        assert dict_out["TAG01"] == {}
        assert dict_out["TAG02"] == {}
        assert dict_out["TAG03"] == {}
        assert dict_out["TAG04"] == {}
        assert dict_out["TAG05"]["_attributes"]["ATTR0"] == 0
        assert dict_out["TAG06"] == {"_attributes": {"ATTR0": 0, "ATTR1": 1}}
        assert dict_out["TAG07"] == {"_attributes": {"ATTR0": 0, "ATTR1": 1}}
        assert dict_out["TAG08"] == {
            "_content": "TEXT",
            "_attributes": {"ATTR0": 0, "ATTR1": 1},
        }
        assert dict_out["TAG09"]["TAG91"] == {}
        assert dict_out["TAG09"]["TAG92"] == {}
        assert dict_out["TAG09"]["TAG93"] == {}
        assert dict_out["TAG09"]["TAG94"]["_attributes"]["ATTR0"] == 0
        assert dict_out["TAG09"]["TAG95"]["_content"] == "TEXT"
        assert dict_out["TAG09"]["TAG96"] == {
            "_content": "TEXT",
            "_attributes": {"ATTR0": 0, "ATTR1": 1},
        }

    def test_parse_generic_xml_with_node_numbering(self) -> None:
        # Prepare XML string to be parsed
        file_name = Path("test_parser_xml.xml")
        str_in = ""
        with Path.open(file_name) as f:
            str_in = f.read()
        dict_out: SDict[str, Any] = SDict(file_name)
        parser = XmlParser(add_node_numbering=True)
        content_TAG00_expected = (  # noqa: N806
            "Extensible Markup Language (XML) is a markup language that defines a set of rules for encoding documents in a format that is both human-readable and machine-readable.\n"
            "Mapping the basic tree model of XML to type systems of programming languages or databases can be difficult, especially when XML is used for exchanging highly structured data between applications, which was not its primary design goal.\n"
            "JSON, YAML, and S-Expressions are frequently proposed as simpler alternatives that focus on representing highly structured data rather than documents, which may contain both highly structured and relatively unstructured content."
        )
        BorgCounter.reset()
        # Execute
        dict_out = parser.parse_string(str_in, dict_out)
        # Assert
        assert dict_out["000000_TAG00"]["_content"] == content_TAG00_expected
        assert dict_out["000001_TAG01"] == {}
        assert dict_out["000002_TAG02"] == {}
        assert dict_out["000003_TAG03"] == {}
        assert dict_out["000004_TAG04"] == {}
        assert dict_out["000005_TAG05"]["_attributes"]["ATTR0"] == 0
        assert dict_out["000006_TAG06"] == {"_attributes": {"ATTR0": 0, "ATTR1": 1}}
        assert dict_out["000007_TAG07"] == {"_attributes": {"ATTR0": 0, "ATTR1": 1}}
        assert dict_out["000008_TAG08"] == {
            "_content": "TEXT",
            "_attributes": {"ATTR0": 0, "ATTR1": 1},
        }
        assert dict_out["000009_TAG09"]["000010_TAG91"] == {}
        assert dict_out["000009_TAG09"]["000011_TAG92"] == {}
        assert dict_out["000009_TAG09"]["000012_TAG93"] == {}
        assert dict_out["000009_TAG09"]["000013_TAG94"]["_attributes"]["ATTR0"] == 0
        assert dict_out["000009_TAG09"]["000014_TAG95"]["_content"] == "TEXT"
        assert dict_out["000009_TAG09"]["000015_TAG96"] == {
            "_content": "TEXT",
            "_attributes": {"ATTR0": 0, "ATTR1": 1},
        }

    def test_parse_xml_namespace_explicit(self) -> None:
        # Prepare XML string to be parsed
        file_name = Path("test_xml_namespace_explicit.xml")
        str_in = ""
        with Path.open(file_name) as f:
            str_in = f.read()
        dict_out: SDict[str, Any] = SDict(file_name)
        parser = XmlParser()
        # Execute
        dict_out = parser.parse_string(str_in, dict_out)
        namespaces: dict[str, str] = dict_out["_xmlOpts"]["_nameSpaces"]
        # Assert
        assert len(namespaces) == 1
        assert "xs" in namespaces
        assert namespaces["xs"] == "http://www.w3.org/2001/XMLSchema"

    def test_parse_xml_namespace_default(self) -> None:
        # Prepare XML string to be parsed
        file_name = Path("test_xml_namespace_default.xml")
        str_in = ""
        with Path.open(file_name) as f:
            str_in = f.read()
        dict_out: SDict[str, Any] = SDict(file_name)
        parser = XmlParser()
        # Execute
        dict_out = parser.parse_string(str_in, dict_out)
        namespaces: dict[str, str] = dict_out["_xmlOpts"]["_nameSpaces"]
        # Assert
        assert len(namespaces) == 1
        assert "None" in namespaces
        assert namespaces["None"] == "http://www.w3.org/2001/XMLSchema"


class SetupHelper:
    @staticmethod
    def prepare_dict_until(
        dict_to_prepare: SDict[K, V],
        until_step: int = -1,
        file_to_read: str = "test_parser_dict",
        *,
        comments: bool = True,
    ) -> None:
        source_file = Path.cwd() / file_to_read

        dict_to_prepare.source_file = source_file.absolute()

        with Path.open(source_file) as f:
            file_content = f.read()
        dict_to_prepare.line_content = file_content.splitlines(keepends=True)

        parser = NativeParser()

        funcs = [
            partial(
                parser._extract_line_comments,  # Step 00
                dict_to_prepare,
                comments=comments,
            ),
            partial(
                parser._extract_includes,  # Step 01
                dict_to_prepare,
            ),
            partial(
                parser._convert_line_content_to_block_content,  # Step 02
                dict_to_prepare,
            ),
            partial(
                parser._extract_block_comments,  # Step 03
                dict_to_prepare,
                comments=comments,
            ),
            partial(
                parser._remove_line_endings_from_block_content,  # Step 04
                dict_to_prepare,
            ),
            partial(
                parser._extract_string_literals,  # Step 05
                dict_to_prepare,
            ),
            partial(
                parser._extract_expressions,  # Step 06
                dict_to_prepare,
            ),
            partial(
                parser._separate_delimiters,  # Step 07
                dict_to_prepare,
            ),
            partial(
                parser._convert_block_content_to_tokens,  # Step 08
                dict_to_prepare,
            ),
            partial(
                parser._determine_token_hierarchy,  # Step 09
                dict_to_prepare,
            ),
            partial(
                parser._convert_tokens_to_dict,  # Step 10
                dict_to_prepare,
            ),
            partial(
                parser._insert_string_literals,  # Step 11
                dict_to_prepare,
            ),
        ]

        for i in range(until_step + 1):
            funcs[i]()
        return
