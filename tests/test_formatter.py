import re
from copy import copy, deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from dictIO import DictReader, FoamFormatter, NativeFormatter, SDict, XmlFormatter

if TYPE_CHECKING:
    from dictIO.types import TKey, TValue


class TestFormatter:
    # @TODO: To be implemented
    @pytest.mark.skip(reason="To be implemented")
    def test_returned_formatter_type(self) -> None:
        pass


class TestNativeFormatter:
    @pytest.mark.parametrize(
        "str_in",
        [
            "string",
            "0.1",
            "2",
            "+0.1" "+2",
            "-0.1",
            "-2",
            "$keyword",
            "$keyword1",
            "$keyword1[0]",
            "$keyword1[1][2]",
        ],
    )
    def test_format_type_string_no_additional_quotes_expected(self, str_in: str) -> None:
        # Prepare
        formatter = NativeFormatter()
        str_expected = str_in
        # Execute
        str_out = formatter.format_value(str_in)
        # Assert
        assert str_out == str_expected

    @pytest.mark.parametrize(
        "str_in",
        [
            "a string with spaces",
            r"C:\a\path\in\windows",
            r"C:/a/path/in/linux",
            "",
            r'contains a "nested string" literal with double quotes',
            r"contains a \"nested string\" literal with escaped double quotes",
        ],
    )
    def test_format_type_string_additional_single_quotes_expected(self, str_in: str) -> None:
        # Prepare
        formatter = NativeFormatter()
        str_expected = f"'{str_in}'"
        # Execute
        str_out = formatter.format_value(str_in)
        # Assert
        assert str_out == str_expected

    @pytest.mark.parametrize(
        "str_in",
        [
            "$keyword+1",
            "$keyword - 3.0",
            "$keyword1 * $keyword2",
            r"contains a 'nested string' literal with single quotes",
            r"contains a \'nested string\' literal with escaped single quotes",
        ],
    )
    def test_format_type_string_additional_double_quotes_expected(self, str_in: str) -> None:
        # Prepare
        formatter = NativeFormatter()
        str_expected = f'"{str_in}"'
        # Execute
        str_out = formatter.format_value(str_in)
        # Assert
        assert str_out == str_expected

    def test_format_type_float(self) -> None:
        # sourcery skip: extract-duplicate-method, inline-variable
        formatter = NativeFormatter()
        float_in = 1.23
        str_out = formatter.format_value(float_in)
        assert isinstance(str_out, str)
        assert str_out == "1.23"
        float_in = 1.0
        str_out = formatter.format_value(float_in)
        assert isinstance(str_out, str)
        assert str_out == "1.0"
        float_in = 0.0
        str_out = formatter.format_value(float_in)
        assert isinstance(str_out, str)
        assert str_out == "0.0"

    def test_insert_block_comments(self) -> None:
        # sourcery skip: class-extract-method
        # Prepare
        formatter = NativeFormatter()
        as_is_block_comment = (
            "/*---------------------------------*- C++ -*----------------------------------*\\\n"
            "This is a block comment; coding utf-8; version 0.1;\n"
            "\\*----------------------------------------------------------------------------*/"
        )
        default_block_comment = (
            "/*---------------------------------*- C++ -*----------------------------------*\\\n"
            "filetype dictionary; coding utf-8; version 0.1; local --; purpose --;\n"
            "\\*----------------------------------------------------------------------------*/"
        )
        # Execute and Assert
        # (dispatch to run_block_comment_tests())
        TestNativeFormatter.run_block_comment_tests(
            formatter,
            as_is_block_comment,
            default_block_comment,
        )

    @staticmethod
    def run_block_comment_tests(
        formatter: NativeFormatter,
        as_is_block_comment: str,
        default_block_comment: str,
    ) -> None:
        s_dict: SDict[TKey, TValue] = SDict()
        # as we used test_simpleDict, str_in does not have a block comment yet
        str_in_template = formatter.format_dict(s_dict)
        placeholder1 = "BLOCKCOMMENT000101            BLOCKCOMMENT000101;"
        placeholder2 = "BLOCKCOMMENT000102            BLOCKCOMMENT000102;"
        placeholder3 = "BLOCKCOMMENT000103            BLOCKCOMMENT000103;"

        # STANDARD CASE: The dictionary contains 1 (ONE) BLOCK COMMENT
        # Prepare
        s_dict.block_comments = {101: as_is_block_comment}
        str_in = placeholder1 + "\n" + str_in_template
        str_expected = str_in.replace(placeholder1, as_is_block_comment)
        # Execute
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

        # FALLBACK CASE: The dictionary contains 0 (NO) BLOCK COMMENT
        # Prepare
        s_dict.block_comments = {}
        str_in = str_in_template
        str_expected = default_block_comment + "\n" + str_in
        # Execute
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected
        # Execute a second time:
        #   Does it still work when we call insert_block_comments() the second time?
        #   Will the default block comment then still be inserted?
        str_in = str_in_template
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

        # NON-STANDARD CASE 1: The dictionary contains 3 (THREE) BLOCK COMMENTS, ALL IDENTICAL
        # Prepare
        s_dict.block_comments = {
            101: as_is_block_comment,
            102: as_is_block_comment,
            103: as_is_block_comment,
        }
        str_in = placeholder1 + "\n" + placeholder2 + "\n" + placeholder3 + "\n" + str_in_template
        str_expected = (
            str_in.replace(placeholder1, as_is_block_comment).replace(placeholder2, "").replace(placeholder3, "")
        )
        # Execute
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

        # NON-STANDARD CASE 2: The dictionary contains 3 (THREE) BLOCK COMMENTS, NON IDENTICAL
        # Prepare
        s_dict.block_comments = {
            101: as_is_block_comment,
            102: default_block_comment,
            103: as_is_block_comment,
        }
        str_in = placeholder1 + "\n" + placeholder2 + "\n" + placeholder3 + "\n" + str_in_template
        str_expected = (
            str_in.replace(placeholder1, as_is_block_comment)
            .replace(placeholder2, default_block_comment)
            .replace(placeholder3, "")
        )
        # Execute
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

        # NON-STANDARD CASE 3: The dictionary contains 1 (ONE) BLOCK COMMENT, BUT IT DOES NOT CONTAIN ' C++ '
        # Prepare
        block_comment_tampered = re.sub(r"\s[Cc]\+{2}\s", " C# ", as_is_block_comment)
        s_dict.block_comments = {101: block_comment_tampered}
        str_in = placeholder1 + "\n" + str_in_template
        str_expected = str_in.replace(placeholder1, default_block_comment + "\n" + block_comment_tampered)
        # Execute
        str_out = formatter.insert_block_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

    def test_insert_includes(self) -> None:
        # Prepare
        include_directive_in = '#include "test formatter paramDict"'
        include_file_name_in = "test formatter paramDict"
        include_file_path_in = Path("test formatter paramDict").absolute()
        s_dict: SDict[TKey, TValue] = SDict()
        s_dict.includes[102] = (
            include_directive_in,
            include_file_name_in,
            include_file_path_in,
        )
        blockcomment_placeholder = "BLOCKCOMMENT000101            BLOCKCOMMENT000101;"
        include_placeholder = "INCLUDE000102            INCLUDE000102;"
        str_in = blockcomment_placeholder + "\n" + include_placeholder + "\n"
        str_expected = str_in.replace(include_placeholder, include_directive_in.replace('"', "'"))
        formatter = NativeFormatter()
        # Execute
        str_out = formatter.insert_includes(s_dict, str_in)
        # Assert
        assert str_out == str_expected

    def test_insert_line_comments(self) -> None:
        # Prepare
        s_dict: SDict[TKey, TValue] = SDict()
        line_comment_in = "// This is a line comment"
        formatter = NativeFormatter()
        str_in_template = formatter.format_dict(s_dict)
        s_dict.line_comments = {103: line_comment_in}
        placeholder1 = "BLOCKCOMMENT000101            BLOCKCOMMENT000101;"
        placeholder2 = "INCLUDE000102            INCLUDE000102;"
        placeholder3 = "LINECOMMENT000103            LINECOMMENT000103;"
        str_in = placeholder1 + "\n" + placeholder2 + "\n" + placeholder3 + "\n" + str_in_template
        str_expected = str_in.replace(placeholder3, line_comment_in)
        # Execute
        str_out = formatter.insert_line_comments(s_dict, str_in)
        # Assert
        assert str_out == str_expected

    def test_remove_trailing_spaces(self) -> None:
        # sourcery skip: extract-duplicate-method, move-assign-in-block
        # Prepare
        # Construct 7 test strings, each having a different number of leading and trailing spaces
        str_in_1 = "a string with one trailing space "
        str_expected_1 = "a string with one trailing space"
        str_in_2 = "a string with five trailing spaces     "
        str_expected_2 = "a string with five trailing spaces"
        str_in_3 = " a string with one leading space"
        str_expected_3 = " a string with one leading space"
        str_in_4 = "     a string with five leading spaces"
        str_expected_4 = "     a string with five leading spaces"
        str_in_5 = " a string with one leading and one trailing space "
        str_expected_5 = " a string with one leading and one trailing space"
        str_in_6 = "     a string with five leading and five trailing spaces     "
        str_expected_6 = "     a string with five leading and five trailing spaces"
        str_in_7 = "a string with no leading or trailing spaces"
        str_expected_7 = "a string with no leading or trailing spaces"

        multi_line_str_in = ""
        multi_line_str_in += str_in_1 + "\n"
        multi_line_str_in += str_in_2 + "\n"
        multi_line_str_in += str_in_3 + "\n"
        multi_line_str_in += str_in_4 + "\n"
        multi_line_str_in += str_in_5 + "\n"
        multi_line_str_in += str_in_6 + "\n"
        multi_line_str_in += str_in_7

        multi_line_str_expected = ""
        multi_line_str_expected += str_expected_1 + "\n"
        multi_line_str_expected += str_expected_2 + "\n"
        multi_line_str_expected += str_expected_3 + "\n"
        multi_line_str_expected += str_expected_4 + "\n"
        multi_line_str_expected += str_expected_5 + "\n"
        multi_line_str_expected += str_expected_6 + "\n"
        multi_line_str_expected += str_expected_7

        formatter = NativeFormatter()

        # Execute 1
        multi_line_str_out = formatter.remove_trailing_spaces(multi_line_str_in)
        # Assert 1
        assert multi_line_str_out == multi_line_str_expected

        # Execute 2: Same test, but this time with the last line having a line ending
        multi_line_str_in += "\n"
        multi_line_str_expected += "\n"
        multi_line_str_out = formatter.remove_trailing_spaces(multi_line_str_in)
        # Assert 2
        assert multi_line_str_out == multi_line_str_expected

        # Execute 3: Only one single line
        str_out = formatter.remove_trailing_spaces(str_in_1)
        # Assert 3
        assert str_out == str_expected_1

        # Execute 4: Empty string
        str_in = ""
        str_out = formatter.remove_trailing_spaces(str_in)
        # Assert 4
        assert str_out == ""

    def test_list_with_nested_list(self) -> None:
        # Prepare
        test_obj: dict[TKey, TValue] = {
            "blocks": [
                "hex",
                [0, 1, 2, 3, 4, 5, 6, 7],
                [1, 1, 2],
                "simpleGrading",
                [1, 1, 1],
                "hex",
                [10, 11, 12, 13, 14, 15, 16, 17],
                [1, 1, 2],
                "edgeGrading",
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ]
        }
        s_dict: SDict[TKey, TValue] = SDict()
        dict_in = deepcopy(s_dict)
        dict_in.update(test_obj)
        formatter = NativeFormatter()
        assert test_obj == dict_in
        # Execute
        str_in: str = formatter.format_dict(test_obj)
        str_out: str = formatter.format_dict(dict_in)
        # Assert
        assert str_in == str_out

    def test_to_string_does_not_alter_original(self) -> None:
        # Prepare
        dict_in = DictReader.read(Path("test_formatter_dict"))
        formatter = NativeFormatter()
        dict_in_reference = dict_in
        dict_in_shallowcopy = copy(dict_in)
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert isinstance(str_out, str)
        # Make sure that the original dictionary is not modified
        assert dict_in == dict_in_reference
        assert dict_in is dict_in_reference
        for key in dict_in:
            assert dict_in[key] == dict_in_reference[key]
            assert dict_in[key] is dict_in_reference[key]
        assert dict_in == dict_in_shallowcopy
        assert dict_in is not dict_in_shallowcopy
        for key in dict_in:
            assert dict_in[key] == dict_in_shallowcopy[key]
            assert dict_in[key] is dict_in_shallowcopy[key]


class TestFoamFormatter:
    def test_insert_block_comments(self) -> None:
        # sourcery skip: class-extract-method
        # Prepare
        formatter = FoamFormatter()
        as_is_block_comment = (
            "/*--------------------------------*- C++ -*----------------------------------*\\\n"
            "| =========       This is a block comment                                     |\n"
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
            "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"
        )
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
            "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"
        )
        # Execute and Assert
        # (dispatch to TestNativeFormatter as, apart from the block comment itself, the tests are identical)
        TestNativeFormatter.run_block_comment_tests(
            formatter,
            as_is_block_comment,
            default_block_comment,
        )

    def test_insert_includes(self) -> None:
        # Prepare
        include_directive_in = "#include 'test formatter paramDict'"
        include_file_name_in = "test formatter paramDict"
        include_file_path_in = Path("test formatter paramDict").absolute()
        s_dict: SDict[TKey, TValue] = SDict()
        s_dict.includes[102] = (
            include_directive_in,
            include_file_name_in,
            include_file_path_in,
        )
        blockcomment_placeholder = "BLOCKCOMMENT000101            BLOCKCOMMENT000101;"
        include_placeholder = "INCLUDE000102            INCLUDE000102;"
        str_in = blockcomment_placeholder + "\n" + include_placeholder + "\n"
        str_expected = str_in.replace(include_placeholder, include_directive_in.replace("'", '"'))
        formatter = FoamFormatter()
        # Execute
        str_out: str = formatter.insert_includes(s_dict, str_in)
        # Assert
        assert str_out == str_expected

    def test_ensure_string_does_not_contain_single_quotes(self) -> None:
        # Prepare dict until and including ()
        dict_in = DictReader.read(Path("test_formatter_dict"), comments=True)
        formatter = FoamFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert re.search(r"\'", str_out) is None

    def test_ensure_string_does_not_contain_underscore_variables(self) -> None:
        # Prepare dict until and including ()
        dict_in = DictReader.read(Path("test_formatter_dict"), comments=False)
        formatter = FoamFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert re.search(r"\s+_", str_out) is None

    def test_to_string_does_not_alter_original(self) -> None:
        # Prepare
        dict_in = DictReader.read(Path("test_formatter_dict"))
        formatter = FoamFormatter()
        dict_in_reference = dict_in
        dict_in_shallowcopy = copy(dict_in)
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert isinstance(str_out, str)
        # Make sure that the original dictionary is not modified
        assert dict_in == dict_in_reference
        assert dict_in is dict_in_reference
        for key in dict_in:
            assert dict_in[key] == dict_in_reference[key]
            assert dict_in[key] is dict_in_reference[key]
        assert dict_in == dict_in_shallowcopy
        assert dict_in is not dict_in_shallowcopy
        for key in dict_in:
            assert dict_in[key] == dict_in_shallowcopy[key]
            assert dict_in[key] is dict_in_shallowcopy[key]


class TestXmlFormatter:
    def test_default_options(self) -> None:
        # Execute
        formatter = XmlFormatter()
        # Assert
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

    def test_to_string(self) -> None:
        # Prepare
        source_file = Path("test_formatter_dict")
        target_file = Path(f"parsed.{source_file}.xml")
        target_file.unlink(missing_ok=True)
        dict_in = DictReader.read(source_file)
        xml_opts = {
            "_nameSpaces": {"osp": "https://opensimulationplatform.com/xsd/OspModelDescription"},
            "_rootTag": "OspModelDescription",
            "_removeNodeNumbering": True,
        }
        dict_in.update({"_xmlOpts": xml_opts})
        formatter = XmlFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        # @TODO: Nothing is de facto asserted here. By intention?
        # -> Needs to checked and properly implemented. CLAROS, 2021-12-23
        with Path.open(target_file, "w") as f:
            _ = f.write(str_out)
        # Clean up
        target_file.unlink()

    def test_parse_format_reparse(self) -> None:
        # Prepare XML string to be parsed
        from dictIO import XmlParser

        file_name = Path("test_parser_xml.xml")
        str_in = ""
        with Path.open(file_name) as f:
            str_in = f.read()
        parser = XmlParser(add_node_numbering=False)
        formatter = XmlFormatter()
        dict_parsed: SDict[TKey, TValue] = SDict()
        dict_reparsed: SDict[TKey, TValue] = SDict()
        # Execute
        dict_parsed = parser.parse_string(str_in, dict_parsed)
        str_out: str = formatter.to_string(dict_parsed)
        dict_reparsed = parser.parse_string(str_out, dict_reparsed)
        # Assert
        assert dict_reparsed == dict_parsed

    def test_format_xml_namespace_explicit(self) -> None:
        # sourcery skip: class-extract-method
        # Prepare
        source_file = Path("test_formatter_dict")
        dict_in = DictReader.read(source_file)
        xml_opts = {
            "_nameSpaces": {"osp": "https://opensimulationplatform.com/xsd/OspModelDescription"},
            "_rootTag": "OspModelDescription",
            "_removeNodeNumbering": True,
        }
        dict_in.update({"_xmlOpts": xml_opts})
        formatter = XmlFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert 'xmlns:osp="https://opensimulationplatform.com/xsd/OspModelDescription"' in str_out
        assert 'xmlns="https://opensimulationplatform.com/xsd/OspModelDescription"' not in str_out

    def test_format_xml_namespace_default(self) -> None:
        # Prepare
        source_file = Path("test_formatter_dict")
        dict_in = DictReader.read(source_file)
        xml_opts = {
            "_nameSpaces": {"None": "https://opensimulationplatform.com/xsd/OspModelDescription"},
            "_rootTag": "OspModelDescription",
            "_removeNodeNumbering": True,
        }
        dict_in.update({"_xmlOpts": xml_opts})
        formatter = XmlFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert 'xmlns="https://opensimulationplatform.com/xsd/OspModelDescription"' in str_out
        assert 'xmlns:None="https://opensimulationplatform.com/xsd/OspModelDescription"' not in str_out

    @pytest.mark.skip(reason="XML pretty printing is not solved yet. The root attribute for encoding still gets lost.")
    def test_format_xml_root_attributes(self) -> None:
        # Prepare
        source_file = Path("test_formatter_dict")
        dict_in = DictReader.read(source_file)
        xml_opts = {
            "_nameSpaces": {"xs": "http://www.w3.org/2001/XMLSchema"},
            "_rootTag": "ROOT",
            "_rootAttributes": {
                "version": 0.1,
                "encoding": "UTF-8",
            },
            "_removeNodeNumbering": True,
        }
        dict_in.update({"_xmlOpts": xml_opts})
        formatter = XmlFormatter()
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert '?xml version="1.0" encoding="UTF-8"?' in str_out
        assert '?xml version="1.0"?' not in str_out

    def test_to_string_does_not_alter_original(self) -> None:
        # Prepare
        dict_in = DictReader.read(Path("test_formatter_dict"))
        formatter = XmlFormatter()
        dict_in_reference = dict_in
        dict_in_shallowcopy = copy(dict_in)
        # Execute
        str_out: str = formatter.to_string(dict_in)
        # Assert
        assert isinstance(str_out, str)
        # Make sure that the original dictionary is not modified
        assert dict_in == dict_in_reference
        assert dict_in is dict_in_reference
        for key in dict_in:
            assert dict_in[key] == dict_in_reference[key]
            assert dict_in[key] is dict_in_reference[key]
        assert dict_in == dict_in_shallowcopy
        assert dict_in is not dict_in_shallowcopy
        for key in dict_in:
            assert dict_in[key] == dict_in_shallowcopy[key]
            assert dict_in[key] is dict_in_shallowcopy[key]
