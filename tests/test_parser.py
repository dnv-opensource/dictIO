import re
from copy import deepcopy
from pathlib import Path

import pytest
from dictIO.cppDict import CppDict
from dictIO.parser import CppParser, Parser, XmlParser
from dictIO.utils.counter import BorgCounter
from dictIO.utils.strings import string_diff


class TestParser():

    # @TODO: To be implemented
    def test_getParser(self):
        pass

    def test_remove_quotes_from_string(self):
        str_in_1 = '\'a string with single quotes\''
        str_in_2 = '\"a string with double quotes\"'
        str_in_3 = '\'a string with \'inside\' quotes\''
        str_in_4 = '\'a string with \"inside\" double quotes\''
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        # Test with argument 'all' = True (default)
        str_out_1 = Parser.remove_quotes_from_string(str_in_1)
        assert str_out_1 == 'a string with single quotes'
        str_out_2 = Parser.remove_quotes_from_string(str_in_2)
        assert str_out_2 == 'a string with double quotes'
        str_out_3 = Parser.remove_quotes_from_string(str_in_3)
        assert str_out_3 == 'a string with inside quotes'
        str_out_4 = Parser.remove_quotes_from_string(str_in_4)
        assert str_out_4 == 'a string with inside double quotes'

        # Test with argument 'all' = False
        str_out_1 = Parser.remove_quotes_from_string(str_in_1, all=False)
        assert str_out_1 == 'a string with single quotes'
        str_out_2 = Parser.remove_quotes_from_string(str_in_2, all=False)
        assert str_out_2 == 'a string with double quotes'
        str_out_3 = Parser.remove_quotes_from_string(str_in_3, all=False)
        assert str_out_3 == 'a string with \'inside\' quotes'
        str_out_4 = Parser.remove_quotes_from_string(str_in_4, all=False)
        assert str_out_4 == 'a string with \"inside\" double quotes'

        with pytest.raises(TypeError):
            Parser.remove_quotes_from_string(not_a_str_1)   # type: ignore
        with pytest.raises(TypeError):
            Parser.remove_quotes_from_string(not_a_str_2)   # type: ignore
        with pytest.raises(TypeError):
            Parser.remove_quotes_from_string(not_a_str_3)   # type: ignore

    def test_remove_quotes_from_strings(self):
        str_in_1 = '\'a string with single quotes\''
        str_in_2 = '\"a string with double quotes\"'
        str_in_3 = '\'a string with \'inside\' quotes\''
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        key_1 = 'key_1'
        key_2 = 'key_2'
        key_3 = 'key_3'
        key_n_1 = 'key_n_1'
        key_n_2 = 'key_n_2'
        key_n_3 = 'key_n_3'
        keyd = 'keyd'
        keyl = 'keyl'
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
        dict_in = {
            key_1: str_in_1,
            key_2: str_in_2,
            key_3: str_in_3,
            key_n_1: not_a_str_1,
            key_n_2: not_a_str_2,
            key_n_3: not_a_str_3,
            keyd: d_nested,
            keyl: l_nested,
        }

        str_out_1 = 'a string with single quotes'
        str_out_2 = 'a string with double quotes'
        str_out_3 = 'a string with inside quotes'

        dict_out = deepcopy(dict_in)
        Parser.remove_quotes_from_strings(dict_out)
        assert dict_out[key_1] == str_out_1
        assert dict_out[key_2] == str_out_2
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
            Parser.remove_quotes_from_strings(str_in_1)     # type: ignore
        with pytest.raises(TypeError):
            Parser.remove_quotes_from_strings(not_a_str_1)  # type: ignore

    def test_parse_type_int(self):
        parser = Parser()
        int_in = 1
        int_out = parser.parse_type(int_in)
        assert isinstance(int_out, int)
        assert int_out == int_in

    def test_parse_type_float(self):
        parser = Parser()
        float_in = 1.0
        float_out = parser.parse_type(float_in)
        assert isinstance(float_out, float)
        assert float_out == float_in

    def test_parse_type_bool(self):
        parser = Parser()
        bool_in = True
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = False
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = 'True'
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = 'False'
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = 'true'
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is True
        bool_in = 'false'
        bool_out = parser.parse_type(bool_in)
        assert isinstance(bool_out, bool)
        assert bool_out is False
        bool_in = '  True  '
        bool_out = parser.parse_type(bool_in)
        assert bool_out is True
        bool_in = '  False  '
        bool_out = parser.parse_type(bool_in)
        assert bool_out is False

    def test_parse_type_none(self):
        parser = Parser()
        none_in = None
        none_out = parser.parse_type(none_in)
        assert none_out is None
        none_in = 'None'
        none_out = parser.parse_type(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        none_in = 'none'
        none_out = parser.parse_type(none_in)
        assert not isinstance(none_out, str)
        assert none_out is None
        none_in = '  None  '
        none_out = parser.parse_type(none_in)
        assert none_out is None

    def test_parse_type_string_numerals(self):
        parser = Parser()
        str_in = '1234'
        int_out = parser.parse_type(str_in)
        assert isinstance(int_out, int)
        assert int_out == 1234
        str_in = '1.23'
        float_out = parser.parse_type(str_in)
        assert isinstance(float_out, float)
        assert float_out == 1.23

    def test_parse_type_str(self):
        parser = Parser()
        str_in = 'a string'
        str_out = parser.parse_type(str_in)
        assert isinstance(str_out, str)
        assert str_out == str_in
        str_in_with_single_quotes = '\'' + str_in + '\''
        str_out = parser.parse_type(str_in_with_single_quotes)
        assert isinstance(str_out, str)
        assert str_out == str_in
        str_in_with_double_quotes = '\"' + str_in + '\"'
        str_out = parser.parse_type(str_in_with_double_quotes)
        assert isinstance(str_out, str)
        assert str_out == str_in

    def test_parse_type_empty_str(self):
        parser = Parser()
        str_in = ''
        str_out = parser.parse_type(str_in)
        assert isinstance(str_out, str)
        assert str_out == str_in
        str_in_with_single_quotes = '\'' + str_in + '\''
        str_out = parser.parse_type(str_in_with_single_quotes)
        assert isinstance(str_out, str)
        assert str_out == str_in
        str_in_with_double_quotes = '\"' + str_in + '\"'
        str_out = parser.parse_type(str_in_with_double_quotes)
        assert isinstance(str_out, str)
        assert str_out == str_in

    def test_parse_list(self):
        parser = Parser()
        str_1 = 'string 1'
        str_2 = 'string 2'
        str_3 = 'string 3'
        not_a_str_1 = 1234
        not_a_str_2 = 1.23
        not_a_str_3 = False

        string1_eval = parser.parse_type(str_1)
        string2_eval = parser.parse_type(str_2)
        string3_eval = parser.parse_type(str_3)
        not_a_str_1_eval = parser.parse_type(not_a_str_1)
        not_a_str_2_eval = parser.parse_type(not_a_str_2)
        not_a_str_3_eval = parser.parse_type(not_a_str_3)

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
        list_assert_nested = [
            string1_eval,
            string2_eval,
            string3_eval,
            not_a_str_1_eval,
            not_a_str_2_eval,
            not_a_str_3_eval,
        ]
        list_assert = [
            string1_eval,
            string2_eval,
            string3_eval,
            list_assert_nested,
            not_a_str_1_eval,
            not_a_str_2_eval,
            not_a_str_3_eval,
        ]

        list_out = parser.parse_types(list_in)

        assert list_out is list_in
        assert list_out == list_assert
        assert list_out[3] == list_assert[3]


class TestCppParser():

    def test_convert_line_content_to_block_content(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        # Three lines with line endings
        line1 = 'line 1\n'
        line2 = 'line 2\n'
        line3 = 'line 3\n'
        assert dict.line_content == []
        dict.line_content.extend([line1, line2, line3])
        assert dict.block_content == ''
        parser.convert_line_content_to_block_content(dict)
        assert dict.block_content == 'line 1\nline 2\nline 3\n'

    def test_remove_line_endings_from_block_content(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        # Three lines with line endings
        line1 = 'line 1\n'
        line2 = 'line 2\n'
        line3 = 'line 3\n'
        assert dict.line_content == []
        dict.line_content.extend([line1, line2, line3])
        assert dict.block_content == ''
        parser.convert_line_content_to_block_content(dict)
        parser.remove_line_endings_from_block_content(dict)
        assert dict.block_content == 'line 1 line 2 line 3'

    def test_extract_line_comments(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        line1 = 'a line with no line comment\n'
        line2 = '//a line comment\n'
        line3 = 'a line with //an inline comment\n'
        line4 = 'a line with no line comment\n'
        assert dict.line_content == []
        assert dict.line_comments == {}
        dict.line_content.extend([line1, line2, line3, line4])
        assert len(dict.line_content) == 4
        parser.extract_line_comments(dict, comments=True)
        assert len(dict.line_content) == 4
        for line in dict.line_content:
            assert re.search(r'//', line) is None
        assert len(dict.line_comments) == 2
        for line in dict.line_comments.values():
            assert re.search(str(r'//'), str(line)) is not None

    def test_extract_includes(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        line1 = 'a line with no include directive\n'
        line2 = '#include testDict\n'
        line3 = '#include \'testDict\'\n'
        # line4 = '#include testDict with some dummy content thereafter\n'   # this is currently not covered by extract_includes and would fail
        line4 = '   #include testDict   \n'
        line5 = '   # include testDict   \n'
        line6 = 'a line with no include directive\n'
        assert dict.line_content == []
        assert dict.includes == {}
        dict.line_content.extend([line1, line2, line3, line4, line5, line6])
        assert len(dict.line_content) == 6
        parser.extract_includes(dict)
        assert len(dict.line_content) == 6
        for line in dict.line_content:
            assert bool(re.search(
                r'#include',
                line,
            )) is False
        assert len(dict.includes) == 4
        path_assert = Path('testDict').absolute()
        for include_directive, path in dict.includes.values():
            assert bool(re.search(str(r'#\s*include'), str(include_directive))) is True
            assert bool(re.search(str(r'\n'), str(include_directive))) is False
            assert path == path_assert

    def test_extract_string_literals(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        text_block_in = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are inline substrings with single quotes.\n'
            'Such substrings we identify as string literals and substitute them with a placeholder\n'
            'in the form S T R I N G L I T E R A L 0 0 0 0 0 0.  Lets look at some examples in the following three lines:\n'
            'This is a line with \'a string literal1\'\n'
            'This is a line with \'a string literal2\' and some blabla thereafter.\n'
            'This is a line with \' a string literal3 with leading and trailing spaces \'\n'
            '\'This line starts with a string literal4\' and then has some blabla thereafter.\n'
            '\'This line is nothing else than a string literal5\''
            'This line has a \"substring that is not a string literal because it got double quotes\" instead of single quotes\n'
            'And here we close our small test with a final line with no string literal at all'
        )

        text_block_assert = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are inline substrings with single quotes.\n'
            'Such substrings we identify as string literals and substitute them with a placeholder\n'
            'in the form S T R I N G L I T E R A L 0 0 0 0 0 0.  Lets look at some examples in the following three lines:\n'
            'This is a line with STRINGLITERAL000000\n'
            'This is a line with STRINGLITERAL000000 and some blabla thereafter.\n'
            'This is a line with STRINGLITERAL000000\n'
            'STRINGLITERAL000000 and then has some blabla thereafter.\n'
            'STRINGLITERAL000000'
            'This line has a \"substring that is not a string literal because it got double quotes\" instead of single quotes\n'
            'And here we close our small test with a final line with no string literal at all'
        )

        assert dict.block_content == ''
        assert dict.string_literals == {}
        dict.block_content = text_block_in
        parser.extract_string_literals(dict)
        text_block_out = re.sub(r'[0-9]{6}', '000000', dict.block_content)
        string_diff(text_block_out, text_block_assert)
        assert text_block_out == text_block_assert
        assert len(dict.string_literals) == 5
        assert list(dict.string_literals.values())[0] == 'a string literal1'
        assert list(dict.string_literals.values())[1] == 'a string literal2'
        assert list(dict.string_literals.values()
                    )[2] == ' a string literal3 with leading and trailing spaces '
        assert list(dict.string_literals.values())[3] == 'This line starts with a string literal4'
        assert list(dict.string_literals.values()
                    )[4] == 'This line is nothing else than a string literal5'

    def test_extract_block_comments(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        text_block_in = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are C++ block comments.\n'
            'C++ block comments have an opening line, the block comment itself, and a closing line. See following example:\n'
            '/*---------------------------------*- C++ -*----------------------------------*\\\n'
            'This is a block comment; coding utf-8; version 0.1;\n'
            '\\*----------------------------------------------------------------------------*/\n'
            'Identified block comments are extracted and replaced by a placeholder\n'
            'in the form B L O C K C O M M E N T 0 0 0 0 0 0 .'
        )

        text_block_assert = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are C++ block comments.\n'
            'C++ block comments have an opening line, the block comment itself, and a closing line. See following example:\n'
            'BLOCKCOMMENT000000\n'
            'Identified block comments are extracted and replaced by a placeholder\n'
            'in the form B L O C K C O M M E N T 0 0 0 0 0 0 .'
        )

        assert dict.block_content == ''
        assert dict.block_comments == {}
        dict.block_content = text_block_in
        parser.extract_block_comments(dict, comments=True)
        text_block_out = re.sub(r'[0-9]{6}', '000000', dict.block_content)
        assert text_block_out == text_block_assert
        string_diff(text_block_out, text_block_assert)
        assert len(dict.block_comments) == 1
        assert list(dict.block_comments.values())[0] == (
            '/*---------------------------------*- C++ -*----------------------------------*\\\n'
            'This is a block comment; coding utf-8; version 0.1;\n'
            '\\*----------------------------------------------------------------------------*/'
        )

    def test_extract_expressions(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        # key_8 is unfortunately not recogniset as string in this test here,
        # for dictionary with given
        # key '$bvalue';
        # it works properly
        text_block_in = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are key value pairs where the value\n'
            'is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n'
            'Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n'
            'The following examples will be identified as expressions:\n'
            'key_1    "$varName1"\n'
            '   key_2                        \"$varName2 + 4\"\n'
            '   key_3                        \"4 + $varName2\"\n'
            '   key_4                        \"$varName2 + $varName3\" and some blabla thereafter\n'
            '   key_5                        \"$varName1 + $varName2 + $varName3\" and some blabla thereafter\n'
            '   key_6                        \"$varName2 + $varName3 + $varName1\" and some blabla thereafter\n'
            'key_7    \"not_a_nExpression4\"\n'
            'extract_expressions() will extract such expressions and substitute them with a placeholder\n'
            'in the form E X P R E S S I O N 0 0 0 0 0 0.'
            'The actual evaluation of an expression is not part of extract_expressions(). The evaluation is done within ().'
        )
        # '   key_5                        \"REFERENCE000001 + $varName3\" and some blabla thereafter\n'
        # '   key_6                        \"REFERENCE000001 + REFERENCE000002\" and some blabla thereafter\n'
        # 'key_8    \'$not_a_nExpression5\'\n'

        text_block_assert = (
            'This is a text block\n'
            'with multiple lines. Within this text block, there are key value pairs where the value\n'
            'is a string surrounded by double quotes and containing at least one reference to a variable starting with $.\n'
            'Such strings are identified as expressions. Expressions will be evaluated by DictReader.\n'
            'The following examples will be identified as expressions:\n'
            'key_1    EXPRESSION000000\n'
            '   key_2                        EXPRESSION000000\n'
            '   key_3                        EXPRESSION000000\n'
            '   key_4                        EXPRESSION000000 and some blabla thereafter\n'
            '   key_5                        EXPRESSION000000 and some blabla thereafter\n'
            '   key_6                        EXPRESSION000000 and some blabla thereafter\n'
            'key_7    \"not_a_nExpression4\"\n'
            'extract_expressions() will extract such expressions and substitute them with a placeholder\n'
            'in the form E X P R E S S I O N 0 0 0 0 0 0.'
            'The actual evaluation of an expression is not part of extract_expressions(). The evaluation is done within ().'
        )
        # '   key_5                        EXPRESSION000000 and some blabla thereafter\n'
        # '   key_6                        EXPRESSION000000 and some blabla thereafter\n'
        # 'key_8    \'$not_a_nExpression5\'\n'

        assert dict.block_content == ''
        assert dict.expressions == {}
        dict.block_content = text_block_in
        parser.extract_string_literals(dict)
        parser.extract_expressions(dict)
        text_block_out = re.sub(r'[0-9]{6}', '000000', dict.block_content)
        assert text_block_out == text_block_assert
        string_diff(text_block_out, text_block_assert)
        assert len(dict.expressions) == 6

        assert list(dict.expressions.values())[0]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values())[0]['expression'] == '$varName1'

        assert list(dict.expressions.values())[1]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values())[1]['expression'] == '$varName2 + 4'

        assert list(dict.expressions.values())[2]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values())[2]['expression'] == '4 + $varName2'

        assert list(dict.expressions.values())[3]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values())[3]['expression'] == '$varName2 + $varName3'

        assert list(dict.expressions.values())[4]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values()
                    )[4]['expression'] == '$varName1 + $varName2 + $varName3'

        assert list(dict.expressions.values())[5]['name'][:10] == 'EXPRESSION'
        assert list(dict.expressions.values()
                    )[5]['expression'] == '$varName2 + $varName3 + $varName1'

    def test_separate_delimiters(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        text_block_in = (
            'This is a text block\n'
            'with multiple lines. Within this text block there are distinct chars that shall be identified as delimiters.\n'
            'All chars that shall be identified delimiters are passed to separate_delimiters as a list of chars.\n'
            'separate_delimiters parses .block_content for occurences of these delimiters and strips any spaces surrounding the\n'
            'delimiter to exactly one single space before and one single space after the delimiter.\n'
            'It further removes all line endings from .block_content and eventually replaces them with single spaces.\n'
            'This is a preparatory step to ensure proper splitting at the delimiters when decomposing .block_content into tokens.\n'
            'Lets look at some examples in the following lines:\n'
            'These chars are identified as delimiters:{}()<>;,\n'
            'These chars are not identified as delimiters: .:-_|#+*\n'
            'Some delimiters with lots of spaces before and after:    {    }    (    )    <    >    ;    ,    \n'
            'delimiters burried between other text: bla{bla}bla(bla)bla<bla>bla;bla,bla\n'
            'And here we close our small test with a final line with no delimiter at all'
        )

        text_block_assert = (
            'This is a text block '
            'with multiple lines. Within this text block there are distinct chars that shall be identified as delimiters. '
            'All chars that shall be identified delimiters are passed to separate_delimiters as a list of chars. '
            'separate_delimiters parses .block_content for occurences of these delimiters and strips any spaces surrounding the '
            'delimiter to exactly one single space before and one single space after the delimiter. '
            'It further removes all line endings from .block_content and eventually replaces them with single spaces. '
            'This is a preparatory step to ensure proper splitting at the delimiters when decomposing .block_content into tokens. '
            'Lets look at some examples in the following lines: '
            'These chars are identified as delimiters: { } ( ) < > ; , '
            'These chars are not identified as delimiters: .:-_|#+* '
            'Some delimiters with lots of spaces before and after: { } ( ) < > ; , '
            'delimiters burried between other text: bla { bla } bla ( bla ) bla < bla > bla ; bla , bla '
            'And here we close our small test with a final line with no delimiter at all'
        )

        assert dict.block_content == ''
        # assert dict.delimiters == ['{','}','[',']','(',')','<','>',';',',']
        assert dict.delimiters == ['{', '}', '(', ')', '<', '>', ';', ',']
        dict.block_content = text_block_in
        parser.separate_delimiters(dict, dict.delimiters)
        assert dict.block_content == text_block_assert
        string_diff(dict.block_content, text_block_assert)
        # In addition, test whether re.split('\s', block_content) results in tokens containing one single word each
        # because this exactly is what separate_delimiters() is meant to ensure
        dict.tokens = [(0, i) for i in re.split(r'\s', dict.block_content)]
        assert len(dict.tokens) == 184
        for _, token in dict.tokens:
            assert len(token) > 0

    def test_determine_token_hierarchy(self):
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        text_block = (
            'level0 { level1 { level2 { level3 } level2 } level1 } level0\n'
            'level0 [ level1 [ level2 [ level3 ] level2 ] level1 ] level0\n'
            'level0 ( level1 ( level2 ( level3 ) level2 ) level1 ) level0'
        )
        tokens = re.split(r'\s', text_block)
        tokens_in = [(0, token) for token in tokens]

        levels_assert = [0, 0, 1, 1, 2, 2, 3, 2, 2, 1, 1, 0, 0] * 3
        tokens_assert = list(zip(levels_assert, tokens))

        dict.tokens = tokens_in
        parser.determine_token_hierarchy(dict)
        assert dict.tokens == tokens_assert

    def test_parse_tokenized_dict_simple_dict(self):
        # Prepare dict until and including determine_token_hierarchy()
        dict = CppDict(Path('testDict'))
        parser = CppParser()
        SetupHelper.prepare_dict_until(
            dict_to_prepare=dict, until_step=9, file_to_read='test_simpleDict'
        )
        # Preparations done.
        # Now start the actual test
        dict_out = parser.parse_tokenized_dict(dict, dict.tokens, level=0)
        # check structure of the dict
        assert len(dict_out) == 1                               # parameters (level 0)
        assert len(dict_out['parameters']) == 4                 # parameterA,B,C,D (level 1)
        assert len(dict_out['parameters']['parameterA']) == 2   # name,value (level 2)
        assert len(dict_out['parameters']['parameterB']) == 2
        assert len(dict_out['parameters']['parameterC']) == 2
        assert len(dict_out['parameters']['parameterD']) == 2
                                                                # check some selected keys
        assert dict_out['parameters']['parameterA']['name'][:13] == 'STRINGLITERAL'
        assert dict_out['parameters']['parameterB']['value'] == 2.0
        assert dict_out['parameters']['parameterC']['value'][:10] == 'EXPRESSION'
        assert dict_out['parameters']['parameterD']['value'][:10] == 'EXPRESSION'

    def test_parse_tokenized_dict_config_dict(self):
        # Prepare dict until and including determine_token_hierarchy()
        dict_in = CppDict(Path('testDict'))
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = CppParser()
        # Preparations done.
        # Now start the actual test
        dict_out = parser.parse_tokenized_dict(dict_in, dict_in.tokens, level=0)

        # check structure of the dict
        assert len(dict_out) == 10
        assert list(dict_out.keys())[0][:12] == 'BLOCKCOMMENT'
        assert list(dict_out.keys())[1][:7] == 'INCLUDE'
        assert list(dict_out.keys())[2][:11] == 'LINECOMMENT'
        assert list(dict_out.keys())[3] == 'emptyDict'
        assert list(dict_out.keys())[4] == 'emptyList'
        assert list(dict_out.keys())[5] == 'exampleDict'
        assert list(dict_out.keys())[6] == 'numerals'
        assert list(dict_out.keys())[7] == 'strings'
        assert list(dict_out.keys())[8] == 'references'
        assert list(dict_out.keys())[9] == 'scope'
        assert len(dict_out['references']) == 13                # parameterA..G3 (level 2)
        assert len(dict_out['references']['parameterA']) == 3   # name,value,COMMENT (level 3)
        assert len(dict_out['references']['parameterB']) == 3
        assert len(dict_out['references']['parameterC']) == 3
        assert len(dict_out['references']['parameterD']) == 3
        assert len(dict_out['references']['parameterE']) == 3
        assert len(dict_out['references']['parameterF']) == 3
        assert len(dict_out['references']['parameterG1']) == 3
        assert len(dict_out['references']['parameterG2']) == 3
        assert len(dict_out['references']['parameterG3']) == 3

        assert len(dict_out['numerals']) == 3   # int1,int2,float1
        assert len(dict_out['emptyDict']) == 0
        assert len(dict_out['exampleDict']['emptyNestedDict']) == 0

        # nested list with nested list
        assert len(dict_out['exampleDict']['nestedListWithNestedList']) == 3
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedList'][0], list)
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedList'][1], list)
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedList'][2], list)
        assert len(dict_out['exampleDict']['nestedListWithNestedList'][0]) == 3
        assert len(dict_out['exampleDict']['nestedListWithNestedList'][1]) == 3
        assert len(dict_out['exampleDict']['nestedListWithNestedList'][2]) == 3

        # nested list with nested dict
        assert len(dict_out['exampleDict']['nestedListWithNestedDict']) == 3
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedDict'][0], list)
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedDict'][1], dict)
        assert isinstance(dict_out['exampleDict']['nestedListWithNestedDict'][2], list)
        assert len(dict_out['exampleDict']['nestedListWithNestedDict'][0]) == 3
        assert len(dict_out['exampleDict']['nestedListWithNestedDict'][1]) == 3
        assert len(dict_out['exampleDict']['nestedListWithNestedDict'][2]) == 3
        # check some selected keys
        assert dict_out['references']['parameterA']['name'][:13] == 'STRINGLITERAL'
        assert dict_out['references']['parameterC']['value'][:10] == 'EXPRESSION'
        assert dict_out['references']['parameterD']['value'][:10] == 'EXPRESSION'
        assert dict_out['numerals']['int2'] == 120
        # check that also lists are parsed correctly
        assert len(dict_out['emptyList']) == 0
        assert len(dict_out['exampleDict']['emptyNestedList']) == 0
        assert len(dict_out['strings']['listWithStrings']) == 5
        assert dict_out['strings']['listWithStrings'][0][:13] == 'STRINGLITERAL'
        assert dict_out['strings']['listWithStrings'][1][:13] == 'STRINGLITERAL'
        assert dict_out['strings']['listWithStrings'][2][:13] == 'STRINGLITERAL'
        assert dict_out['strings']['listWithStrings'][3][:13] == 'STRINGLITERAL'
        assert dict_out['strings']['listWithStrings'][4][:13] == 'STRINGLITERAL'

        # nested list with nested list
        assert dict_out['exampleDict']['nestedListWithNestedList'][0][0] == 1.00000000e+00
        assert dict_out['exampleDict']['nestedListWithNestedList'][0][1] == 2.20972831e-17
        assert dict_out['exampleDict']['nestedListWithNestedList'][0][2] == 3.15717747e-18
        assert dict_out['exampleDict']['nestedListWithNestedList'][1][0] == 2.20972831e-17
        assert dict_out['exampleDict']['nestedListWithNestedList'][1][1] == 1.00000000e+00
        assert dict_out['exampleDict']['nestedListWithNestedList'][1][2] == -7.07290050e-18
        assert dict_out['exampleDict']['nestedListWithNestedList'][2][0] == 3.15717747e-18
        assert dict_out['exampleDict']['nestedListWithNestedList'][2][1] == -7.07290050e-18
        assert dict_out['exampleDict']['nestedListWithNestedList'][2][2] == 1.00000000e+00

        # nested list with nested dict
        assert dict_out['exampleDict']['nestedListWithNestedDict'][0][0] == 11
        assert dict_out['exampleDict']['nestedListWithNestedDict'][0][1] == 12
        assert dict_out['exampleDict']['nestedListWithNestedDict'][0][2] == 13
        assert dict_out['exampleDict']['nestedListWithNestedDict'][1]['value21'] == 21
        assert dict_out['exampleDict']['nestedListWithNestedDict'][1]['value22'] == 22
        assert dict_out['exampleDict']['nestedListWithNestedDict'][1]['value23'] == 23
        assert dict_out['exampleDict']['nestedListWithNestedDict'][2][0] == 31
        assert dict_out['exampleDict']['nestedListWithNestedDict'][2][1] == 32
        assert dict_out['exampleDict']['nestedListWithNestedDict'][2][2] == 33

    def test_parse_tokenized_dict_sub_dict(self):
        # This test case adresses issue #6 that Frank raised on Github
        # https://github.com/MaritimeOSPx/ModelVerification/issues/6
        # Prepare dict until and including determine_token_hierarchy()
        dict_in = CppDict(Path('testDict'))
        SetupHelper.prepare_dict_until(dict_to_prepare=dict_in, until_step=9)
        parser = CppParser()
        # Preparations done.
        # Now start the actual test
        dict_out = parser.parse_tokenized_dict(dict_in, dict_in.tokens, level=0)
        # check structure of subdict1
        assert len(dict_out['exampleDict']['subdict']) == 1             # list
        assert len(dict_out['exampleDict']['subdict']['list']) == 4     # 'subdict2', (dict object)
        assert isinstance(dict_out['exampleDict']['subdict']['list'][0], str)
        assert dict_out['exampleDict']['subdict']['list'][0] == 'subdict1'
        assert dict_out['exampleDict']['subdict']['list'][2] == 'subdict2'
        assert isinstance(dict_out['exampleDict']['subdict']['list'][1], dict)
        assert len(dict_out['exampleDict']['subdict']['list'][1]) == 2  # key1, key2
        assert list(dict_out['exampleDict']['subdict']['list'][1].keys())[0] == 'key1'
        assert list(dict_out['exampleDict']['subdict']['list'][1].keys())[1] == 'key2'
        assert dict_out['exampleDict']['subdict']['list'][1]['key1'] == 'value1'
        assert dict_out['exampleDict']['subdict']['list'][1]['key2'] == 'value2'

    def test_insert_string_literals(self):
        # Prepare dict until and including convert_tokens_to_dict()
        dict = CppDict(Path('testDict'))
        SetupHelper.prepare_dict_until(dict_to_prepare=dict, until_step=10)
        parser = CppParser()
        dict_in = deepcopy(dict.data)
        # Preparations done.
        # Now start the actual test
        assert dict_in['references']['parameterA']['name'][:13] == 'STRINGLITERAL'
        assert dict_in['strings']['listWithStrings'][0][:13] == 'STRINGLITERAL'
        assert dict_in['strings']['listWithStrings'][1][:13] == 'STRINGLITERAL'
        assert dict_in['strings']['listWithStrings'][2][:13] == 'STRINGLITERAL'
        assert dict_in['strings']['listWithStrings'][3][:13] == 'STRINGLITERAL'
        assert dict_in['strings']['listWithStrings'][4][:13] == 'STRINGLITERAL'
        parser.insert_string_literals(dict)
        dict_out = dict.data
        # check whether string literals have been inserted
        assert dict_out['references']['parameterA']['name'] == 'parameterA'
        assert dict_out['strings']['listWithStrings'][0] == 'string1'
        assert dict_out['strings']['listWithStrings'][1] == 'string2 has spaces'
        assert dict_out['strings']['listWithStrings'][2] == 'string3'
        assert dict_out['strings']['listWithStrings'][
            3] == 'string4 is ok but note that string5 is empty'
        assert dict_out['strings']['listWithStrings'][4] == ''


class TestXmlParser():

    def test_default_options(self):
        parser = XmlParser()
        assert parser.add_node_numbering is True
        # assert parser.namespaces == {'xs': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'}
        # assert parser.xsd_uri == 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'
        # assert parser.root_tag == 'NOTSPECIFIED'

    def test_parse_generic_xml_without_node_numbering(self):
        # Prepare XML string to be parsed
        file_name = Path('test_generic.xml')
        # Read file content
        str_in = ''
        with open(file_name, 'r') as f:
            str_in = f.read()
        # Preparations done.
        # Now start the actual test
        dict_out = CppDict(file_name)
        parser = XmlParser(add_node_numbering=False)
        dict_out = parser.parse_string(str_in, dict_out)

        content_TAG00_assert = (  # noqa: N806
            'Extensible Markup Language (XML) is a markup language that defines a set of rules for encoding documents in a format that is both human-readable and machine-readable.\n'
            'Mapping the basic tree model of XML to type systems of programming languages or databases can be difficult, especially when XML is used for exchanging highly structured data between applications, which was not its primary design goal.\n'
            'JSON, YAML, and S-Expressions are frequently proposed as simpler alternatives that focus on representing highly structured data rather than documents, which may contain both highly structured and relatively unstructured content.'
        )

        assert dict_out['TAG00']['_content'] == content_TAG00_assert
        assert dict_out['TAG01'] is None
        assert dict_out['TAG02'] is None
        assert dict_out['TAG03'] is None
        assert dict_out['TAG04'] is None
        assert dict_out['TAG05']['_attributes']['ATTR0'] == 0
        assert dict_out['TAG06'] == {'_attributes': {'ATTR0': 0, 'ATTR1': 1}}
        assert dict_out['TAG07'] == {'_attributes': {'ATTR0': 0, 'ATTR1': 1}}
        assert dict_out['TAG08'] == {'_content': 'TEXT', '_attributes': {'ATTR0': 0, 'ATTR1': 1}}
        assert dict_out['TAG09']['TAG91'] is None
        assert dict_out['TAG09']['TAG92'] is None
        assert dict_out['TAG09']['TAG93'] is None
        assert dict_out['TAG09']['TAG94']['_attributes']['ATTR0'] == 0
        assert dict_out['TAG09']['TAG95']['_content'] == 'TEXT'
        assert dict_out['TAG09']['TAG96'] == {
            '_content': 'TEXT', '_attributes': {
                'ATTR0': 0, 'ATTR1': 1
            }
        }

    def test_parse_generic_xml_with_node_numbering(self):
        # Prepare XML string to be parsed
        file_name = Path('test_generic.xml')
        # Read file content
        str_in = ''
        with open(file_name, 'r') as f:
            str_in = f.read()
        # Preparations done.
        # Now start the actual test
        dict_out = CppDict(file_name)
        parser = XmlParser(add_node_numbering=True)
        BorgCounter.reset()
        dict_out = parser.parse_string(str_in, dict_out)

        content_TAG00_assert = (  # noqa: N806
            'Extensible Markup Language (XML) is a markup language that defines a set of rules for encoding documents in a format that is both human-readable and machine-readable.\n'
            'Mapping the basic tree model of XML to type systems of programming languages or databases can be difficult, especially when XML is used for exchanging highly structured data between applications, which was not its primary design goal.\n'
            'JSON, YAML, and S-Expressions are frequently proposed as simpler alternatives that focus on representing highly structured data rather than documents, which may contain both highly structured and relatively unstructured content.'
        )

        assert dict_out['000000_TAG00']['_content'] == content_TAG00_assert
        assert dict_out['000001_TAG01'] is None
        assert dict_out['000002_TAG02'] is None
        assert dict_out['000003_TAG03'] is None
        assert dict_out['000004_TAG04'] is None
        assert dict_out['000005_TAG05']['_attributes']['ATTR0'] == 0
        assert dict_out['000006_TAG06'] == {'_attributes': {'ATTR0': 0, 'ATTR1': 1}}
        assert dict_out['000007_TAG07'] == {'_attributes': {'ATTR0': 0, 'ATTR1': 1}}
        assert dict_out['000008_TAG08'] == {
            '_content': 'TEXT', '_attributes': {
                'ATTR0': 0, 'ATTR1': 1
            }
        }
        assert dict_out['000009_TAG09']['000010_TAG91'] is None
        assert dict_out['000009_TAG09']['000011_TAG92'] is None
        assert dict_out['000009_TAG09']['000012_TAG93'] is None
        assert dict_out['000009_TAG09']['000013_TAG94']['_attributes']['ATTR0'] == 0
        assert dict_out['000009_TAG09']['000014_TAG95']['_content'] == 'TEXT'
        assert dict_out['000009_TAG09']['000015_TAG96'] == {
            '_content': 'TEXT', '_attributes': {
                'ATTR0': 0, 'ATTR1': 1
            }
        }


class SetupHelper():

    @staticmethod
    def prepare_dict_until(
        dict_to_prepare: CppDict,
        until_step=-1,
        file_to_read='test_dict',
    ):

        file_name = Path.cwd() / file_to_read

        if dict_to_prepare is None:
            dict_to_prepare = CppDict(file_name)

        with open(file_name, 'r') as f:
            file_content = f.read()
        dict_to_prepare.line_content = file_content.splitlines(keepends=True)

        parser = CppParser()

        comments: bool = True

        funcs = [
            (parser.extract_line_comments, dict_to_prepare, comments),          # Step 00
            (parser.extract_includes, dict_to_prepare),                         # Step 01
            (parser.convert_line_content_to_block_content, dict_to_prepare),    # Step 02
            (parser.extract_block_comments, dict_to_prepare, comments),         # Step 03
            (parser.remove_line_endings_from_block_content, dict_to_prepare),   # Step 04
            (parser.extract_string_literals, dict_to_prepare),                  # Step 05
            (parser.extract_expressions, dict_to_prepare),                      # Step 06
            (parser.separate_delimiters, dict_to_prepare),                      # Step 07
            (parser.convert_block_content_to_tokens, dict_to_prepare),          # Step 08
            (parser.determine_token_hierarchy, dict_to_prepare),                # Step 09
            (parser.convert_tokens_to_dict, dict_to_prepare),                   # Step 10
            (parser.insert_string_literals, dict_to_prepare),                   # Step 11
        ]

        for i in range(until_step + 1):
            funcs[i][0](*funcs[i][1:])
        return dict_to_prepare
