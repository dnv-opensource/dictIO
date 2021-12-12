import os
import re
from copy import deepcopy
from difflib import ndiff
from pathlib import Path, PurePath

import pytest
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name
from dictIO.formatter import CppFormatter, XmlFormatter
from dictIO.utils.counter import BorgCounter
from dictIO.utils.path import silent_remove


def test_write_and_reread_dict_without_includes():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict'))
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert dict_read == dict_reread
    assert str(dict_read) == str(dict_reread)


def test_write_and_reread_dict_with_includes():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'))
    assert not os.path.exists('parsed.test_dictWriter_dict')
    # silentRemove('parsed.test_dictWriter_dict')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict'))
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'))
    # why is assert here failing???
    # because of insert includes with re.escape on a whole string for include_directive
    # yielding a  \#include\ 'test_paramDict' and not a #include 'test_paramDict'
    assert dict_read == dict_reread

    formatter = CppFormatter()
    liste1 = re.split('[\r\n]+', formatter.to_string(dict_read))
    liste2 = re.split('[\r\n]+', formatter.to_string(dict_reread))

    liste = [item for item in ndiff(liste1, liste2) if not re.search(r'^\s*$', item)]
    diff_list = []
    for index, item in enumerate(liste):
        if re.match(r'^[+\-]', item):
            print('diff in line %4i:' % index, item)
            diff_list.append((item))

    count = len(diff_list)
    print(
        'there %s %i difference%s between test_dictWriter_dict and parsed.test_dictWriter_dict' %
        (('are' if count > 1 else 'is'), count, ('s' if count > 1 else ''))
    )


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
    silent_remove(Path('parsed.test_dictWriter_dict'))
    silent_remove(Path('parsed.test_dictWriter_dict.abc'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert not os.path.exists('parsed.test_dictWriter_dict.abc')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict.abc'))
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert os.path.exists('parsed.test_dictWriter_dict.abc')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict.abc'), includes=False)
    assert dict_read == dict_reread


def test_write_dict_filetype_cpp():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    silent_remove(Path('parsed.test_dictWriter_dict.cpp'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert not os.path.exists('parsed.test_dictWriter_dict.cpp')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict'))
    assert os.path.exists('parsed.test_dictWriter_dict')
    assert not os.path.exists('parsed.test_dictWriter_dict.cpp')
    silent_remove(Path('parsed.test_dictWriter_dict'))
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict.cpp'))
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert os.path.exists('parsed.test_dictWriter_dict.cpp')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict.cpp'), includes=False)
    assert dict_read == dict_reread


def test_write_dict_filetype_xml():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    silent_remove(Path('parsed.test_dictWriter_dict.xml'))
    formatter = XmlFormatter()
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert not os.path.exists('parsed.test_dictWriter_dict.xml')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict'), formatter=formatter)
    assert os.path.exists('parsed.test_dictWriter_dict')
    assert not os.path.exists('parsed.test_dictWriter_dict.xml')
    silent_remove(Path('parsed.test_dictWriter_dict'))
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict.xml'))
    assert not os.path.exists('parsed.test_dictWriter_dict')
    assert os.path.exists('parsed.test_dictWriter_dict.xml')
    # @TODO: Rereading xml doesn't work yet 1:1
    # dict_reread = DictReader.read('parsed.test_dictWriter_dict.xml', includes=False)
    # assert dict == dict_reread  # Rereading xml doesn't work yet 1:1


def test_read_write_foam_dict():
    file_name_in = Path('test_foamDict')
    file_name_out = Path('reread.test_foamDict.foam')
    silent_remove(file_name_out)
    dict_read = DictReader.read(file_name_in)
    assert not os.path.exists(file_name_out)
    DictWriter.write(dict_read, file_name_out)
    assert os.path.exists(file_name_out)
    dict_reread = DictReader.read(file_name_out)
    # @TODO: failing under linux: CRLF !== LF
    assert dict_read == dict_reread
    # @TODO: test env setup function for something like this...
    #        os.system('. .OFdev ; cd $TESTFOLDER ; blockMesh')


def test_write_mode():
    silent_remove(Path('parsed.test_dictWriter_dict'))
    dict_read = DictReader.read(Path('test_dictWriter_dict'), includes=False)
    assert not os.path.exists('parsed.test_dictWriter_dict')
    DictWriter.write(dict_read, Path('parsed.test_dictWriter_dict'))
    assert os.path.exists('parsed.test_dictWriter_dict')

    # delete one element (parameterD) in the dict to have a test case for the write mode
    dict_read_modified = deepcopy(dict_read)
    del dict_read_modified['parameters']['parameterD']
    # Write with mode 'a': -> parameterD should still exist after writing (as the existing file was not overwritten but only appended to)
    DictWriter.write(dict_read_modified, Path('parsed.test_dictWriter_dict'), mode='a')
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert 'parameterD' in dict_reread['parameters']
    # Write with mode 'w': -> parameterD should not exist after writing (as the existing file was overwritten)
    DictWriter.write(dict_read_modified, Path('parsed.test_dictWriter_dict'), mode='w')
    assert os.path.exists('parsed.test_dictWriter_dict')
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_dict'), includes=False)
    assert 'parameterD' not in dict_reread['parameters']


def test_write_farn_param_dict():
    file_name = Path('test_farnParamDict')
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
    silent_remove(file_name)
    test_cpp_dict = CppDict()
    test_cpp_dict.update(test_dict)
    DictWriter.write(test_cpp_dict, file_name)
    assert file_name.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(file_name)))
    assert parsed_str == test_str

    # write CppDict on top of existing
    test_cpp_dict = CppDict()
    test_cpp_dict.update(test_dict)
    DictWriter.write(test_cpp_dict, file_name)
    assert file_name.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(file_name)))
    assert parsed_str == test_str

    # write as dict completely new
    silent_remove(file_name)
    DictWriter.write(test_dict, file_name)
    assert file_name.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(file_name)))
    assert parsed_str == test_str

    # write as dict on top of existent
    DictWriter.write(test_dict, file_name)
    assert file_name.exists()
    parsed_str = re.sub(r'[\r\n\s]+', ' ', str(DictReader.read(file_name)))
    assert parsed_str == test_str

    # clean up
    silent_remove(file_name)


def test_write_xml():
    silent_remove(Path('parsed.test_dictWriter_xml'))
    silent_remove(Path('parsed.test_dictWriter_xml.xml'))
    BorgCounter.reset()
    dict_read = DictReader.read(Path('test_dictWriter_xml.xml'))

    parsed_file = Path('parsed.test_dictWriter_xml')
    DictWriter.write(dict_read, parsed_file)
    assert os.path.exists('parsed.test_dictWriter_xml')
    assert not os.path.exists('parsed.test_dictWriter_xml.xml')
    silent_remove(Path('parsed.test_dictWriter_xml'))

    parsed_file = Path('parsed.test_dictWriter_xml.xml')
    DictWriter.write(dict_read, parsed_file)
    assert not os.path.exists('parsed.test_dictWriter_xml')
    assert os.path.exists('parsed.test_dictWriter_xml.xml')
    # silentRemove(Path('parsed.test_dictWriter_xml.xml'))

    BorgCounter.reset()
    dict_reread = DictReader.read(Path('parsed.test_dictWriter_xml.xml'))
    assert dict_read == dict_reread


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
