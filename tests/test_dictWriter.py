import os
import re
from copy import deepcopy
from pathlib import Path, PurePath

import pytest
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name
from dictIO.parser import FoamParser
from dictIO.utils.counter import BorgCounter
from dictIO.utils.path import silent_remove


def test_write_and_reread_dict_target_file_given_as_str():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    target_file_as_path = Path('parsed.test_dictWriter_dict')
    target_file_as_str = str(target_file_as_path.absolute())
    DictWriter.write(dict_read, target_file_as_str)
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert dict_read == dict_reread


def test_write_and_reread_dict_target_file_given_as_purepath():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    target_file_as_path = Path('parsed.test_dictWriter_dict')
    target_file_as_purepath = PurePath(str(target_file_as_path))
    DictWriter.write(dict_read, target_file_as_purepath)
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert dict_read == dict_reread


def test_write_and_reread_dict_target_file_given_as_path():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    target_file_as_path = Path('parsed.test_dictWriter_dict')
    DictWriter.write(dict_read, target_file_as_path)
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert dict_read == dict_reread


def test_write_dict_filetype_abc():
    # sourcery skip: class-extract-method
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    target_file_abc = Path('parsed.test_dictWriter_dict.abc')
    silent_remove(target_file)
    silent_remove(target_file_abc)
    dict_read = DictReader.read(source_file, includes=False)
    assert not target_file.exists()
    assert not target_file_abc.exists()
    DictWriter.write(dict_read, target_file)
    assert target_file.exists()
    assert not target_file_abc.exists()
    silent_remove(target_file)
    DictWriter.write(dict_read, target_file_abc)
    assert not target_file.exists()
    assert target_file_abc.exists()
    dict_reread = DictReader.read(target_file_abc, includes=False)
    assert dict_read == dict_reread
    silent_remove(target_file)
    silent_remove(target_file_abc)


def test_file_ending_abc():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    target_file_abc = Path('parsed.test_dictWriter_dict.abc')
    silent_remove(target_file)
    silent_remove(target_file_abc)
    dict_read = DictReader.read(source_file, includes=False)
    # Execute
    DictWriter.write(dict_read, target_file_abc)
    # Assert
    assert not target_file.exists()
    assert target_file_abc.exists()
    dict_reread = DictReader.read(target_file_abc)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)
    silent_remove(target_file_abc)


def test_file_ending_cpp():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    target_file_cpp = Path('parsed.test_dictWriter_dict.cpp')
    silent_remove(target_file)
    silent_remove(target_file_cpp)
    dict_read = DictReader.read(source_file, includes=False)
    # Execute
    DictWriter.write(dict_read, target_file_cpp)
    # Assert
    assert not target_file.exists()
    assert target_file_cpp.exists()
    dict_reread = DictReader.read(target_file_cpp)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)
    silent_remove(target_file_cpp)


def test_file_ending_xml():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    target_file_xml = Path('parsed.test_dictWriter_dict.xml')
    silent_remove(target_file)
    silent_remove(target_file_xml)
    dict_read = DictReader.read(source_file, includes=False)
    # Execute
    DictWriter.write(dict_read, target_file_xml)
    # Assert
    assert not target_file.exists()
    assert target_file_xml.exists()
    # Clean up
    silent_remove(target_file)
    silent_remove(target_file_xml)


def test_read_cpp_write_cpp():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_cpp_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=True)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_foam_write_foam():
    # Prepare
    source_file = Path('test_dictWriter_foam')
    target_file = Path('parsed.test_dictWriter_foam.foam')
    silent_remove(target_file)
    parser = FoamParser()
    dict_read = DictReader.read(source_file, includes=False, parser=parser)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_foam_write_foam_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_foam')
    target_file = Path('parsed.test_dictWriter_foam.foam')
    silent_remove(target_file)
    parser = FoamParser()
    dict_read = DictReader.read(source_file, includes=True, parser=parser)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_xml_write_xml():
    # Prepare
    source_file = Path('test_dictWriter_xml.xml')
    target_file = Path('parsed.test_dictWriter_xml.xml')
    silent_remove(target_file)
    BorgCounter.reset()
    dict_read = DictReader.read(source_file, includes=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    BorgCounter.reset()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_xml_write_xml_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_xml.xml')
    target_file = Path('parsed.test_dictWriter_xml.xml')
    silent_remove(target_file)
    BorgCounter.reset()
    dict_read = DictReader.read(source_file, includes=True)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    BorgCounter.reset()
    dict_reread = DictReader.read(target_file)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_foam():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.foam')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=False, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=False, comments=False)
    # (The 'FoamFile' element is foam dicts specific. Before comparison with the original cpp dict, we need to delete it.)
    del dict_reread['FoamFile']
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_foam_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.foam')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=True, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=True, comments=False)
    # (The 'FoamFile' element is foam dicts specific. Before comparison with the original cpp dict, we need to delete it.)
    del dict_reread['FoamFile']
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_json():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.json')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=False, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=False, comments=False)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_json_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.json')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=True, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=True, comments=False)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


# @TODO: The XML tests expectedly fail as our XML parser and formatter
#        do not support yet the full breadth of dicts.
#        However, the tests mark a good goal. We can improve the
#        XML parser and formatter one day to the point these tests pass.
#        CLAROS, 2021-12-22
def test_read_cpp_write_xml():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.xml')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=False, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=False, comments=False)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_read_cpp_write_xml_with_includes():
    # Prepare
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict.xml')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=True, comments=False)
    # Execute
    DictWriter.write(dict_read, target_file)
    # Assert
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=True, comments=False)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)
    # Clean up
    silent_remove(target_file)


def test_write_mode():
    source_file = Path('test_dictWriter_dict')
    target_file = Path('parsed.test_dictWriter_dict')
    silent_remove(target_file)
    dict_read = DictReader.read(source_file, includes=False)
    assert not target_file.exists()
    DictWriter.write(dict_read, target_file)
    assert target_file.exists()

    # delete one element (parameterD) in the dict to have a test case for the write mode
    dict_read_modified = deepcopy(dict_read)
    del dict_read_modified['parameters']['parameterD']
    # Write with mode 'a': -> parameterD should still exist after writing (as the existing file was not overwritten but only appended to)
    DictWriter.write(dict_read_modified, target_file, mode='a')
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(target_file, includes=False)
    assert 'parameterD' in dict_reread['parameters']
    # Write with mode 'w': -> parameterD should not exist after writing (as the existing file was overwritten)
    DictWriter.write(dict_read_modified, target_file, mode='w')
    assert target_file.exists()
    dict_reread = DictReader.read(target_file, includes=False)
    assert 'parameterD' not in dict_reread['parameters']
    silent_remove(target_file)


def test_write_farn_param_dict():
    target_file = Path('test_farn_paramDict')
    test_dict = dict(
        {
            'param1': -10.0,
            'param2': 0.0,
            'param3': 0.0,
            '_case': {
                '_layer': 'lhsvar',
                '_level': 1,
                '_no_of_samples': 108,
                '_index': 0,
                '_path':
                r'C:\Users\CLAROS\Documents\SystemSimulation\ModelVerification\tools\farn\test\cases\gp_0\lhsvar_000',
                '_key': 'lhsvar_000',
                '_is_leaf': False,
                '_condition': None,
                '_names': ['param1', 'param2', 'param3'],
                '_values': [-10.0, 0.0, 0.0],
                '_commands': {
                    'ls': ['echo %PATH%', 'dir']
                },
            }
        }
    )
    test_str = r"/*---------------------------------*- C++ -*----------------------------------*\ filetype dictionary; coding utf-8; version 0.1; local --; purpose --; \*----------------------------------------------------------------------------*/ param1 -10.0; param2 0.0; param3 0.0; _case { _layer lhsvar; _level 1; _no_of_samples 108; _index 0; _path 'C:\Users\CLAROS\Documents\SystemSimulation\ModelVerification\tools\farn\test\cases\gp_0\lhsvar_000'; _key lhsvar_000; _is_leaf False; _condition None; _names ( param1 param2 param3 ); _values ( -10.0 0.0 0.0 ); _commands { ls ( 'echo %PATH%' dir ); } } "

    # write as CppDict completely new
    silent_remove(target_file)
    test_cpp_dict = CppDict()
    test_cpp_dict.update(test_dict)
    DictWriter.write(test_cpp_dict, target_file)
    assert target_file.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # write as CppDict on top of existing
    test_cpp_dict = CppDict()
    test_cpp_dict.update(test_dict)
    DictWriter.write(test_cpp_dict, target_file)
    assert target_file.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # write as dict completely new
    silent_remove(target_file)
    DictWriter.write(test_dict, target_file)
    assert target_file.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # write as dict on top of existent
    DictWriter.write(test_dict, target_file)
    assert target_file.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(target_file)))
    assert parsed_str == test_str

    # clean up
    silent_remove(target_file)


class TestCreateTargetFileName():

    @pytest.mark.parametrize(
        'file_ending',
        [
            '',
            'abc',
            'cpp',
            'foam',
            'json',
            'xml',
        ],
    )
    def test_file_ending(self, file_ending):
        file_name = 'someDictFile' if not file_ending else 'someDictFile.' + file_ending
        source_file = Path(file_name)
        assert_file = Path(file_name)
        target_file = create_target_file_name(source_file)
        assert target_file == assert_file

    @pytest.mark.parametrize(
        ('output_format', 'file_ending'),
        [
            ('cpp', ''),
            ('foam', 'foam'),
            ('json', 'json'),
            ('xml', 'xml'),
            ('', ''),
            ('notdefinedformat', ''),
        ],
    )
    def test_output_format_file_ending(self, output_format, file_ending):
        source_file = Path('someDictFile')
        assert_file_name = 'someDictFile' if not file_ending else 'someDictFile.' + file_ending
        assert_file = Path(assert_file_name)
        target_file = create_target_file_name(source_file, format=output_format)
        assert target_file == assert_file

    def test_target_file_does_not_contain_double_prefix(self):
        # Prepare
        source_file = Path('test_dictWriter_dict')
        target_file_assert = Path('prefix.test_dictWriter_dict')
        # Execute
        target_file_first_call = create_target_file_name(source_file, 'prefix')
        target_file_second_call = create_target_file_name(target_file_first_call, 'prefix')
        # Assert
        assert target_file_first_call == target_file_assert
        assert target_file_second_call == target_file_assert
