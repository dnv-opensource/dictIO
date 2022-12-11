import re
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Any, Dict

import pytest

from dictIO import CppDict, DictReader, DictWriter, FoamParser, create_target_file_name
from dictIO.utils.counter import BorgCounter


def test_write_dict():
    # Prepare
    target_file: Path = Path("temp_file_test_write_dict")
    test_dict: Dict[str, Any] = {
        "param1": -10.0,
        "param2": 0.0,
        "param3": 0.0,
        "_case": {
            "_layer": "lhsvar",
            "_level": 1,
            "_no_of_samples": 108,
            "_index": 0,
            "_path": r"C:\Users\CLAROS\Documents\SystemSimulation\ModelVerification\tools\farn\test\cases\gp_0\lhsvar_000",
            "_key": "lhsvar_000",
            "_is_leaf": False,
            "_condition": None,
            "_names": ["param1", "param2", "param3"],
            "_values": [-10.0, 0.0, 0.0],
            "_commands": {"ls": ["echo %PATH%", "dir"]},
        },
    }
    test_str: str = r"/*---------------------------------*- C++ -*----------------------------------*\ filetype dictionary; coding utf-8; version 0.1; local --; purpose --; \*----------------------------------------------------------------------------*/ param1 -10.0; param2 0.0; param3 0.0; _case { _layer lhsvar; _level 1; _no_of_samples 108; _index 0; _path 'C:\Users\CLAROS\Documents\SystemSimulation\ModelVerification\tools\farn\test\cases\gp_0\lhsvar_000'; _key lhsvar_000; _is_leaf false; _condition NULL; _names ( param1 param2 param3 ); _values ( -10.0 0.0 0.0 ); _commands { ls ( 'echo %PATH%' dir ); } } "
    test_cpp_dict: CppDict = CppDict()
    test_cpp_dict.update(test_dict)

    # Execute 1.1: Write as CppDict completely new
    target_file.unlink(missing_ok=True)
    DictWriter.write(test_cpp_dict, target_file, mode="w")
    # Assert 1.1
    assert target_file.exists()
    parsed_str = re.sub(r"[\r\n\s]+", " ", str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # Execute 1.2: Write as CppDict on top of existing
    DictWriter.write(test_cpp_dict, target_file, mode="a")
    # Assert 1.2
    assert target_file.exists()
    parsed_str = re.sub(r"[\r\n\s]+", " ", str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # Execute 2.1: Write as dict completely new
    target_file.unlink()
    DictWriter.write(test_dict, target_file, mode="w")
    # Assert 2.1
    assert target_file.exists()
    parsed_str = re.sub(r"[\r\n\s]+", " ", str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # Execute 2.2: Write as dict on top of existent
    DictWriter.write(test_dict, target_file, mode="a")
    # Assert 2.2
    assert target_file.exists()
    parsed_str = re.sub(r"[\r\n\s]+", " ", str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # Clean up
    target_file.unlink()


def test_write_mode():
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file}")
    target_file.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=False)
    DictWriter.write(dict_read, target_file)
    # delete one element (parameterD) in the dict to have a test case for the write mode
    dict_read_modified = deepcopy(dict_read)
    del dict_read_modified["parameters"]["parameterD"]

    # Execute mode 'a'
    # -> parameterD should still exist after writing (as the existing file was not overwritten but only appended to)
    DictWriter.write(dict_read_modified, target_file, mode="a")
    dict_reread = DictReader.read(target_file, includes=False)
    # Assert mode 'a'
    assert target_file.exists()
    assert "parameterD" in dict_reread["parameters"]

    # Execute mode 'w'
    # -> parameterD should NOT exist after writing (as the existing file was overwritten)
    DictWriter.write(dict_read_modified, target_file, mode="w")
    dict_reread = DictReader.read(target_file, includes=False)
    # Assert mode 'w'
    assert target_file.exists()
    assert "parameterD" not in dict_reread["parameters"]

    # Clean up
    target_file.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_dict(includes: bool):
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes)
    # Execute
    DictWriter.write(dict_read, target_file)
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


def test_read_dict_write_dict_target_file_given_as_str():
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path.cwd().absolute() / "parsed.test_dictWriter_dict"
    target_file_as_str = str(target_file.absolute())
    target_file.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file)
    # Execute
    DictWriter.write(dict_read, target_file_as_str)
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


def test_read_dict_write_dict_target_file_given_as_purepath():
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path.cwd().absolute() / "parsed.test_dictWriter_dict"
    target_file_as_purepath = PurePath(str(target_file.absolute()))
    target_file.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file)
    # Execute
    DictWriter.write(dict_read, target_file_as_purepath)
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_abc(includes: bool):
    # sourcery skip: class-extract-method
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file_abc = Path(f"{target_file.name}.abc")
    target_file.unlink(missing_ok=True)
    target_file_abc.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes)
    # Execute
    DictWriter.write(dict_read, target_file_abc)
    dict_reread = DictReader.read(target_file_abc)
    # Assert
    assert not target_file.exists()
    assert target_file_abc.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file_abc.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_cpp(includes: bool):
    # sourcery skip: class-extract-method
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file_cpp = Path(f"{target_file.name}.cpp")
    target_file.unlink(missing_ok=True)
    target_file_cpp.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes)
    # Execute
    DictWriter.write(dict_read, target_file_cpp)
    dict_reread = DictReader.read(target_file_cpp)
    # Assert
    assert not target_file.exists()
    assert target_file_cpp.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file_cpp.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_foam(includes: bool):
    # sourcery skip: class-extract-method
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file_foam = Path(f"{target_file.name}.foam")
    target_file.unlink(missing_ok=True)
    target_file_foam.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file_foam)
    dict_reread = DictReader.read(target_file_foam, includes=includes, comments=False)
    # Assert
    # (The 'FoamFile' element is foam dicts specific. Before comparison with the original cpp dict, we need to delete it.)
    del dict_reread["FoamFile"]
    assert not target_file.exists()
    assert target_file_foam.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file_foam.unlink()


# @TODO: The read_cpp_write_xml test fails as XmlParser and XmlFormatter
#        do not support yet all dict elements.
#        We might want to improve the XML parser and formatter
#        one day to the point these tests pass.
#        CLAROS, 2021-12-22
@pytest.mark.skip(
    reason=(
        "XmlParser and XmlFormatter do not support yet all dict elements.\n"
        "E.g. the XMLFormatter does currently not support writing None / NULL values. This causes this test to fail,\n"
        "as the None values in the source file (test_dictWriter_dict) are not persisted in XML and get hence lost on rereading."
    )
)
@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_xml(includes: bool):
    # sourcery skip: class-extract-method
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file_xml = Path(f"{target_file.name}.xml")
    target_file.unlink(missing_ok=True)
    target_file_xml.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file_xml)
    dict_reread = DictReader.read(target_file_xml)
    # Assert
    assert not target_file.exists()
    assert target_file_xml.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file_xml.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_dict_write_json(includes: bool):
    # sourcery skip: class-extract-method
    # Prepare
    source_file = Path("test_dictWriter_dict")
    target_file = Path(f"parsed.{source_file.name}")
    target_file_json = Path(f"{target_file.name}.json")
    target_file.unlink(missing_ok=True)
    target_file_json.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file_json)
    dict_reread = DictReader.read(target_file_json)
    # Assert
    assert not target_file.exists()
    assert target_file_json.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file_json.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_foam_write_foam(includes: bool):
    # Prepare
    source_file = Path("test_dictWriter_foam")
    target_file = Path(f"parsed.{source_file}.foam")
    target_file.unlink(missing_ok=True)
    parser = FoamParser()
    dict_read = DictReader.read(source_file, includes=includes, parser=parser)
    # Execute
    DictWriter.write(dict_read, target_file)
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_xml_write_xml(includes: bool):
    # Prepare
    source_file = Path("test_dictWriter_xml.xml")
    target_file = Path(f"parsed.{source_file}")
    target_file.unlink(missing_ok=True)
    BorgCounter.reset()
    dict_read = DictReader.read(source_file, includes=includes)
    # Execute
    DictWriter.write(dict_read, target_file)
    BorgCounter.reset()
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


@pytest.mark.parametrize("includes", [False, True])
def test_read_json_write_json(includes: bool):
    # Prepare
    source_file = Path("test_dictWriter_json.json")
    target_file = Path(f"parsed.{source_file}")
    target_file.unlink(missing_ok=True)
    dict_read = DictReader.read(source_file, includes=includes)
    # Execute
    DictWriter.write(dict_read, target_file)
    dict_reread = DictReader.read(target_file)
    # Assert
    assert target_file.exists()
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    target_file.unlink()


class TestCreateTargetFileName:
    @pytest.mark.parametrize(
        "file_ending",
        [
            "",
            "abc",
            "cpp",
            "foam",
            "json",
            "xml",
        ],
    )
    def test_file_ending(self, file_ending: str):
        # Prepare
        file_name = f"someDictFile.{file_ending}" if file_ending else "someDictFile"
        source_file = Path(file_name)
        assert_file = Path(file_name)
        # Execute
        target_file = create_target_file_name(source_file)
        # Assert
        assert target_file == assert_file

    @pytest.mark.parametrize(
        ("output_format", "file_ending"),
        [
            ("cpp", ""),
            ("foam", "foam"),
            ("json", "json"),
            ("xml", "xml"),
            ("", ""),
            ("notdefinedformat", ""),
        ],
    )
    def test_output_format_file_ending(self, output_format: str, file_ending: str):
        # Prepare
        source_file = Path("someDictFile")
        assert_file_name = f"someDictFile.{file_ending}" if file_ending else "someDictFile"
        assert_file = Path(assert_file_name)
        # Execute
        target_file = create_target_file_name(source_file, format=output_format)
        # Assert
        assert target_file == assert_file

    def test_target_file_does_not_contain_double_prefix(self):
        # Prepare
        source_file = Path("test_dictWriter_dict")
        target_file_expected = Path("prefix.test_dictWriter_dict")
        # Execute
        target_file_first_call = create_target_file_name(source_file, "prefix")
        target_file_second_call = create_target_file_name(target_file_first_call, "prefix")
        # Assert
        assert target_file_first_call == target_file_expected
        assert target_file_second_call == target_file_expected
