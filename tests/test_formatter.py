import re
from copy import deepcopy
from pathlib import Path

import pytest
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import create_target_file_name
from dictIO.formatter import CppFormatter, FoamFormatter, XmlFormatter
from dictIO.utils.path import silent_remove


# @TODO: To be implemented
@pytest.mark.skip(reason='To be implemented')
class TestFormatter():

    # @TODO: To be implemented
    @pytest.mark.skip(reason='To be implemented')
    def test_returned_formatter_type(self):
        pass


class TestCppFormatter():

    def test_format_type_string(self):
        formatter = CppFormatter()
        str_in = 'string'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '0.1'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '2'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '+0.1'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '+2'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '-0.1'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '-2'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '$keyword'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '$keyword1'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        str_in = '$keyword1[0]'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        str_in = '$keyword1[1][2]'
        str_assert = str_in
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '$keyword+1'
        str_assert = '"' + str_in + '"'
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '$keyword - 3.0'
        str_assert = '"' + str_in + '"'
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = '$keyword1 * $keyword2'
        str_assert = '"' + str_in + '"'
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = 'a string with spaces'
        str_assert = '\'' + str_in + '\''
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = r'C:\a\path\in\windows'
        str_assert = '\'' + str_in + '\''
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = r'C:/a/path/in/linux'
        str_assert = '\'' + str_in + '\''
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert
        str_in = ''
        str_assert = '\'' + str_in + '\''
        str_out = formatter.format_type(str_in)
        assert str_out == str_assert

    def test_insert_block_comments(self):                                                           # sourcery skip: class-extract-method
                                                                                                    # Prepare dict until and including ()
        formatter = CppFormatter()
        as_is_block_comment = (
            '/*---------------------------------*- C++ -*----------------------------------*\\\n'
            'This is a block comment; coding utf-8; version 0.1;\n'
            '\\*----------------------------------------------------------------------------*/'
        )
        default_block_comment = (
            '/*---------------------------------*- C++ -*----------------------------------*\\\n'
            'filetype dictionary; coding utf-8; version 0.1; local --; purpose --;\n'
            '\\*----------------------------------------------------------------------------*/'
        )
                                                                                                    # Prepare input templates

        TestCppFormatter.run_block_comment_tests(
            formatter,
            as_is_block_comment,
            default_block_comment,
        )

    @staticmethod
    def run_block_comment_tests(
        formatter: CppFormatter,
        as_is_block_comment: str,
        default_block_comment: str,
    ):
        dict = CppDict()
        SetupHelper.prepare_dict(dict_to_prepare=dict, file_to_read='test_formatter_dict')
        str_in_template = formatter.format_dict(
            dict.data
        )                                           # as we used test_simpleDict, str_in does not have a block comment yet
        placeholder1 = 'BLOCKCOMMENT000101            BLOCKCOMMENT000101;'
        placeholder2 = 'BLOCKCOMMENT000102            BLOCKCOMMENT000102;'
        placeholder3 = 'BLOCKCOMMENT000103            BLOCKCOMMENT000103;'

        # THE STANDARD CASE: The dictionary contains 1 (ONE) BLOCK COMMENT
        # Prepare the dict
        dict.block_comments = {101: as_is_block_comment}
        # Prepare the input
        str_in = placeholder1 + '\n' + str_in_template
        # Prepare what we expect as output
        str_assert = str_in.replace(placeholder1, as_is_block_comment)
        # Run the test
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert

        # THE FALLBACK CASE: The dictionary contains 0 (NO) BLOCK COMMENT
        # Prepare the dict
        dict.block_comments = {}
        # Prepare the input
        str_in = str_in_template
        # Prepare what we expect as output
        str_assert = default_block_comment + '\n' + str_in
        # Run the test
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert
        # but does it also work when we call insert_block_comments() the second time? Will the default block comment then still be inserted?
        str_in = str_in_template
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert

        # A NON-STANDARD CASE: The dictionary contains 3 (THREE) BLOCK COMMENTS, ALL IDENTICAL
        # Prepare the dict
        dict.block_comments = {
            101: as_is_block_comment,
            102: as_is_block_comment,
            103: as_is_block_comment,
        }

        # Prepare the input
        str_in = placeholder1 + '\n' + placeholder2 + '\n' + placeholder3 + '\n' + str_in_template
        # Prepare what we expect as output
        str_assert = (
            str_in.replace(placeholder1,
                           as_is_block_comment).replace(placeholder2,
                                                        '').replace(placeholder3, '')
        )
        # Run the test
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert

        # A NON-STANDARD CASE: The dictionary contains 3 (THREE) BLOCK COMMENTS, NON IDENTICAL
        # Prepare the dict
        dict.block_comments = {
            101: as_is_block_comment,
            102: default_block_comment,
            103: as_is_block_comment,
        }

        # Prepare the input
        str_in = placeholder1 + '\n' + placeholder2 + '\n' + placeholder3 + '\n' + str_in_template
        # Prepare what we expect as output
        str_assert = (
            str_in.replace(placeholder1,
                           as_is_block_comment).replace(placeholder2, default_block_comment
                                                        ).replace(placeholder3, '')
        )
        # Run the test
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert

        # A NON-STANDARD CASE: The dictionary contains 1 (ONE) BLOCK COMMENT, BUT IT DOES NOT CONTAIN ' C++ '
        block_comment_tampered = re.sub(r'\s[Cc]\+{2}\s', ' C# ', as_is_block_comment)
        # Prepare the dict
        dict.block_comments = {}
        dict.block_comments[101] = block_comment_tampered
        # Prepare the input
        str_in = placeholder1 + '\n' + str_in_template
        # Prepare what we expect as output
        str_assert = str_in.replace(
            placeholder1, default_block_comment + '\n' + block_comment_tampered
        )
        # Run the test
        str_out = formatter.insert_block_comments(dict, str_in)
        assert str_out == str_assert

    def test_insert_includes(self):
        # Prepare
        include_directive_in = '#include "test formatter paramDict"'
        include_file_name_in = 'test formatter paramDict'
        include_file_path_in = Path('test formatter paramDict').absolute()

        dict = CppDict()
        dict.includes[102] = (include_directive_in, include_file_name_in, include_file_path_in)

        blockcomment_placeholder = 'BLOCKCOMMENT000101            BLOCKCOMMENT000101;'
        include_placeholder = 'INCLUDE000102            INCLUDE000102;'

        str_in = blockcomment_placeholder + '\n' + include_placeholder + '\n'
        str_assert = str_in.replace(
            include_placeholder, include_directive_in.replace('"', '\'').replace('#', '')
        )

        formatter = CppFormatter()

        # Execute
        str_out = formatter.insert_includes(dict, str_in)
        # Assert
        assert str_out == str_assert

    def test_insert_line_comments(self):
        # Prepare dict until and including ()
        dict = CppDict()
        SetupHelper.prepare_dict(dict_to_prepare=dict, file_to_read='test_formatter_dict')
        line_comment_in = "// This is a line comment"
        formatter = CppFormatter()
        # Prepare input templates
        str_in_template = formatter.format_dict(dict.data)
        # as we used test_formatter_dict, str_in does not have a block comment yet
        placeholder1 = 'BLOCKCOMMENT000101            BLOCKCOMMENT000101;'
        placeholder2 = 'INCLUDE000102            INCLUDE000102;'
        placeholder3 = 'LINECOMMENT000103            LINECOMMENT000103;'
        # Prepare the dict
        dict.line_comments = {103: line_comment_in}
        # Prepare the input
        str_in = placeholder1 + '\n' + placeholder2 + '\n' + placeholder3 + '\n' + str_in_template
        # Prepare what we expect as output
        str_assert = str_in.replace(placeholder3, line_comment_in)
        # Run the test
        str_out = formatter.insert_line_comments(dict, str_in)
        assert str_out == str_assert

    def test_remove_trailing_spaces(self):
        formatter = CppFormatter()

        # Construct 7 test strings, each having a different number of leading and trailing spaces
        str_in_1 = 'a string with one trailing space '
        str_assert_1 = 'a string with one trailing space'
        str_in_2 = 'a string with five trailing spaces     '
        str_assert_2 = 'a string with five trailing spaces'
        str_in_3 = ' a string with one leading space'
        str_assert_3 = ' a string with one leading space'
        str_in_4 = '     a string with five leading spaces'
        str_assert_4 = '     a string with five leading spaces'
        str_in_5 = ' a string with one leading and one trailing space '
        str_assert_5 = ' a string with one leading and one trailing space'
        str_in_6 = '     a string with five leading and five trailing spaces     '
        str_assert_6 = '     a string with five leading and five trailing spaces'
        str_in_7 = 'a string with no leading or trailing spaces'
        str_assert_7 = 'a string with no leading or trailing spaces'

        multi_line_str_in = str()
        multi_line_str_in += str_in_1 + '\n'
        multi_line_str_in += str_in_2 + '\n'
        multi_line_str_in += str_in_3 + '\n'
        multi_line_str_in += str_in_4 + '\n'
        multi_line_str_in += str_in_5 + '\n'
        multi_line_str_in += str_in_6 + '\n'
        multi_line_str_in += str_in_7

        multi_line_str_assert = str()
        multi_line_str_assert += str_assert_1 + '\n'
        multi_line_str_assert += str_assert_2 + '\n'
        multi_line_str_assert += str_assert_3 + '\n'
        multi_line_str_assert += str_assert_4 + '\n'
        multi_line_str_assert += str_assert_5 + '\n'
        multi_line_str_assert += str_assert_6 + '\n'
        multi_line_str_assert += str_assert_7

        multi_line_str_out = formatter.remove_trailing_spaces(multi_line_str_in)
        assert multi_line_str_out == multi_line_str_assert

        # Do same test, but this time with the last line having a line ending
        multi_line_str_in += '\n'
        multi_line_str_assert += '\n'
        multi_line_str_out = formatter.remove_trailing_spaces(multi_line_str_in)
        assert multi_line_str_out == multi_line_str_assert

        # only one single line
        str_out = formatter.remove_trailing_spaces(str_in_1)
        assert str_out == str_assert_1

        # empty string
        str_in = str()
        str_out = formatter.remove_trailing_spaces(str_in)
        assert str_out == ''

    def test_list_with_nested_list(self):
        test_obj = {
            'blocks': [
                'hex', [0, 1, 2, 3, 4, 5, 6, 7], [1, 1, 2],
                'simpleGrading', [1, 1, 1],
                'hex', [10, 11, 12, 13, 14, 15, 16, 17], [1, 1, 2],
                'edgeGrading', [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ]
        }
        dict = CppDict()
        dict_in = deepcopy(dict.data)
        dict_in.update(test_obj)
        formatter = CppFormatter()
        assert test_obj == dict_in
        str_in = str()
        str_in += formatter.format_dict(test_obj)
        str_out = str()
        str_out += formatter.format_dict(dict_in)
        assert str_in == str_out


class TestFoamFormatter():

    def test_insert_block_comments(self):                                                           # sourcery skip: class-extract-method
                                                                                                    # Prepare dict until and including ()
        formatter = FoamFormatter()
        as_is_block_comment = (
            '/*--------------------------------*- C++ -*----------------------------------*\\\n'
            '| =========       This is a block comment                                     |\n'
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
            '// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //'
        )
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
            '// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //'
        )
                                                                                                    # Prepare input templates

        TestCppFormatter.run_block_comment_tests(
            formatter,
            as_is_block_comment,
            default_block_comment,
        )

    def test_insert_includes(self):
        # Prepare
        include_directive_in = "#include 'test formatter paramDict'"
        include_file_name_in = 'test formatter paramDict'
        include_file_path_in = Path('test formatter paramDict').absolute()

        dict = CppDict()
        dict.includes[102] = (include_directive_in, include_file_name_in, include_file_path_in)

        blockcomment_placeholder = 'BLOCKCOMMENT000101            BLOCKCOMMENT000101;'
        include_placeholder = 'INCLUDE000102            INCLUDE000102;'

        str_in = blockcomment_placeholder + '\n' + include_placeholder + '\n'
        str_assert = str_in.replace(include_placeholder, include_directive_in.replace('\'', '"'))

        formatter = FoamFormatter()

        # Execute
        str_out = formatter.insert_includes(dict, str_in)
        # Assert
        assert str_out == str_assert

    def test_ensure_string_does_not_contain_single_quotes(self):
        # sourcery skip: class-extract-method
        # Prepare dict until and including ()
        dict = DictReader.read(Path('test_formatter_dict'), comments=True)
        formatter = FoamFormatter()
        # Execute
        str_out = str()
        str_out += formatter.to_string(dict)
        assert re.search(r'\'', str_out) is None

    def test_ensure_string_does_not_contain_underscore_variables(self):
        # Prepare dict until and including ()
        dict = DictReader.read(Path('test_formatter_dict'), comments=False)
        formatter = FoamFormatter()
        # Execute
        str_out = str()
        str_out += formatter.to_string(dict)
        assert re.search(r'\s+_', str_out) is None


class TestXmlFormatter():

    def test_default_options(self):
        formatter = XmlFormatter()
        assert formatter.omit_prefix is True
        assert formatter.integrate_attributes is True
        assert formatter.remove_node_numbering is True
        # assert formatter.indent == ' ' * 4
        # assert formatter.root_tag == 'NOTSPECIFIED'
        # assert formatter.namespaces == {
        #     'xs': 'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'
        # }
        # assert formatter.root_attributes is None
        # assert len(formatter.prefixes) == 1
        # assert formatter.prefixes[0] == 'xs'
        # assert formatter.attributes == {}
        # assert formatter.root_element.tag.find(
        #     'https://www.w3.org/2009/XMLSchema/XMLSchema.xsd'
        # ) > 0

    def test_to_string(self):
        # Prepare dict until and including ()
        source_file = Path('test_formatter_dict')
        target_file = create_target_file_name(source_file, prefix='parsed', format='xml')
        silent_remove(target_file)
        dict = DictReader.read(source_file)
        xml_opts = {
            '_nameSpaces': {
                'osp': 'https://opensimulationplatform.com/xsd/OspModelDescription'
            },
            '_rootTag': 'OspModelDescription',
            '_removeNodeNumbering': True,
        }
        dict.update({'_xmlOpts': xml_opts})
        formatter = XmlFormatter()
        # Execute
        str_out = str()
        str_out += formatter.to_string(dict)
        # Assert
        # @TODO: It seems nothing is de facto tested tested (asserted) here.
        # -> Needs to checked and properly implemented. CLAROS, 2021-12-23
        with open(target_file, 'w') as f:
            f.write(str_out)
        # Clean up
        silent_remove(target_file)


class SetupHelper():

    @staticmethod
    def prepare_dict(dict_to_prepare: CppDict, file_to_read='test_formatter_dict'):

        file_name = Path.cwd() / file_to_read

        if dict_to_prepare is None:
            dict_to_prepare = DictReader.read(file_name)

        return dict_to_prepare
