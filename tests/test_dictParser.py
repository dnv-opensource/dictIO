import os
from pathlib import Path

from dictIO.dictParser import DictParser
from dictIO.cli.dictParser import _validate_scope
from dictIO.dictReader import DictReader
from dictIO.dictWriter import create_target_file_name
from dictIO.utils.path import silent_remove


def test_validate_scope():
    # Vary scope to different types and each time test whether setOptions works as expected

    # None
    scope_in = None
    scope_out = _validate_scope(scope_in)   # type: ignore
    assert scope_out is None

    # (single) string -> should not be stored as a raw string, but as a one-element list
    scope_in = 'strings'
    scope_out = _validate_scope(scope_in)
    assert isinstance(scope_out, list)
    assert len(scope_out) == 1
    assert list(scope_out)[0] == 'strings'

    # list
    scope_in = ['input', 'time']
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == 'input'
    assert list(scope_out)[1] == 'time'

    # list in string format (= string, which LOOKS like a list)
    scope_in = "['input','time']"
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == 'input'
    assert list(scope_out)[1] == 'time'

    # int  -> should not be accepted and result in None
    scope_in = 1
    scope_out = _validate_scope(scope_in)   # type: ignore
    assert scope_out is None


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
    silent_remove(Path('parsed.test_dictParser_paramDict'))
    silent_remove(Path('parsed.test_dictParser_dict'))
    silent_remove(Path('parsed.test_dictParser_dict.foam'))
    silent_remove(Path('parsed.parsed.test_dictParser_paramDict'))
    silent_remove(Path('parsed.parsed.test_dictParser_dict'))
    silent_remove(Path('parsed.parsed.test_dictParser_dict.foam'))
    file_name = Path('test_dictParser_dict')
    DictParser.parse(file_name, output='foam')
    assert not os.path.exists('parsed.test_dictParser_paramDict')
    assert not os.path.exists('parsed.test_dictParser_dict')
    assert os.path.exists('parsed.test_dictParser_dict.foam')

    # parsed_file_name = create_target_file_name(file_name, 'parsed')
    # dict_reread = DictReader.read(parsed_file_name)
    # assert dict == dict_reread
