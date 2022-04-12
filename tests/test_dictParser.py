import os
from pathlib import Path

from dictIO.dictParser import DictParser
from dictIO.dictReader import DictReader
from dictIO.dictWriter import create_target_file_name
from dictIO.utils.path import silent_remove


def test_parse_dict():  # sourcery skip: class-extract-method
    silent_remove(Path('parsed.test_dictParser_paramDict'))
    silent_remove(Path('parsed.test_dictParser_dict'))
    silent_remove(Path('parsed.parsed.test_dictParser_paramDict'))
    silent_remove(Path('parsed.parsed.test_dictParser_dict'))
    file_name = Path('test_dictParser_dict')
    dict = DictParser.parse(file_name)
    assert not os.path.exists('parsed.test_dictParser_paramDict')
    assert os.path.exists('parsed.test_dictParser_dict')

    parsed_file_name = create_target_file_name(file_name, 'parsed')
    dict_reread = DictReader.read(parsed_file_name)
    assert dict == dict_reread
    # no piping parsed prefix anymore: parsed.parsed.test_dictParser_dict
    assert not os.path.exists('parsed.parsed.test_dictParser_dict')
    assert not os.path.exists('parsed.parsed.test_dictParser_paramDict')


def test_parse_dict_foam_format():
    # Prepare
    source_file = Path('test_dictParser_dict')
    parsed_file = Path('parsed.test_dictParser_dict')
    parsed_file_foam = Path('parsed.test_dictParser_dict.foam')
    parsed_file_param_dict = Path('parsed.test_dictParser_paramDict')
    silent_remove(parsed_file)
    silent_remove(parsed_file_foam)
    silent_remove(parsed_file_param_dict)
    # Execute
    DictParser.parse(source_file, output='foam')
    # Assert
    assert not parsed_file.exists()
    assert not parsed_file_param_dict.exists()
    assert parsed_file_foam.exists()
    # Clean up
    silent_remove(parsed_file_foam)
