import os
import sys
from argparse import ArgumentError
from dataclasses import dataclass
from pathlib import Path
from typing import List, MutableSequence, Union

import pytest
from dictIO.cli import dictParser
from dictIO.cli.dictParser import _argparser, _main, _validate_scope, main
from dictIO.utils.path import silent_remove


@dataclass()
class CliArgs():
    quiet: bool = False
    verbose: bool = False
    log: Union[str, None] = None
    log_level: str = 'WARNING'

    dict: Union[str, None] = 'myDict'
    ignore_includes: bool = False
    mode: str = 'w'
    order: bool = False
    ignore_comments: bool = False
    scope: Union[str, None] = None
    output: str = 'cpp'


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ([], ArgumentError),
        (['myDict'], CliArgs()),
        (['myDict', '-q'], CliArgs(quiet=True)),
        (['myDict', '--quiet'], CliArgs(quiet=True)),
        (['myDict', '-v'], CliArgs(verbose=True)),
        (['myDict', '--verbose'], CliArgs(verbose=True)),
        (['myDict', '-qv'], ArgumentError),
        (['myDict', '--log', 'logFile'], CliArgs(log='logFile')),
        (['myDict', '--log'], ArgumentError),
        (['myDict', '--log-level', 'INFO'], CliArgs(log_level='INFO')),
        (['myDict', '--log-level'], ArgumentError),
        (['myDict', '-I'], CliArgs(ignore_includes=True)),
        (['myDict', '--ignore-includes'], CliArgs(ignore_includes=True)),
        (['myDict', '--mode', 'a'], CliArgs(mode='a')),
        (['myDict', '--mode'], ArgumentError),
        (['myDict', '--order'], CliArgs(order=True)),
        (['myDict', '-o'], ArgumentError),
        (['myDict', '-C'], CliArgs(ignore_comments=True)),
        (['myDict', '--ignore-comments'], CliArgs(ignore_comments=True)),
        (['myDict', '--scope', ''], CliArgs(scope='')),
        (['myDict', '--scope', 'key'], CliArgs(scope='key')),
        (['myDict', '--scope', '[key1,key2]'], CliArgs(scope='[key1,key2]')),
        (['myDict', '--scope', '[key1, key2]'], CliArgs(scope='[key1, key2]')),
        (['myDict', '--scope', "['key1', 'key2']"], CliArgs(scope="['key1', 'key2']")),
        (['myDict', '--scope', 'key1', 'key2'], ArgumentError),
        (['myDict', '--scope'], ArgumentError),
        (['myDict', '--output', 'cpp'], CliArgs(output='cpp')),
        (['myDict', '--output', 'foam'], CliArgs(output='foam')),
        (['myDict', '--output', 'xml'], CliArgs(output='xml')),
        (['myDict', '--output', 'json'], CliArgs(output='json')),
        (['myDict', '--output', ''], ArgumentError),
        (['myDict', '--output'], ArgumentError),
    ]
)
def test_argparser(
    inputs: List[str],
    expected: Union[CliArgs, type],
    monkeypatch,
):
    # Prepare
    monkeypatch.setattr(sys, "argv", ["dictParser"] + inputs)
    parser = _argparser()
    # Execute
    if isinstance(expected, CliArgs):
        args_assert: CliArgs = expected
        args = parser.parse_args()
        # Assert args
        for key in args_assert.__dataclass_fields__:
            assert args.__getattribute__(key) == args_assert.__getattribute__(key)
    elif issubclass(expected, Exception):
        exception: type = expected
        # Assert that expected exception is raised
        with pytest.raises((exception, SystemExit)):
            args = parser.parse_args()
    else:
        assert False


@dataclass()
class MainArgs():
    source_file: Path = Path('myDict')
    includes: bool = True
    mode: str = 'w'
    order: bool = False
    comments: bool = True
    scope: Union[MutableSequence[str], None] = None
    output: Union[str, None] = 'cpp'


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ([], ArgumentError),
        (['myDict'], MainArgs()),
        (['myDict', '-I'], MainArgs(includes=False)),
        (['myDict', '--ignore-includes'], MainArgs(includes=False)),
        (['myDict', '--mode', 'a'], MainArgs(mode='a')),
        (['myDict', '--mode'], ArgumentError),
        (['myDict', '--order'], MainArgs(order=True)),
        (['myDict', '-o'], ArgumentError),
        (['myDict', '-C'], MainArgs(comments=False)),
        (['myDict', '--ignore-comments'], MainArgs(comments=False)),
        (['myDict', '--scope', ''], MainArgs(scope=[''])),
        (['myDict', '--scope', 'key'], MainArgs(scope=['key'])),
        (['myDict', '--scope', '[key1,key2]'], MainArgs(scope=['key1', 'key2'])),
        (['myDict', '--scope', '[key1, key2]'], MainArgs(scope=['key1', 'key2'])),
        (['myDict', '--scope', "['key1', 'key2']"], MainArgs(scope=['key1', 'key2'])),
        (['myDict', '--scope', 'key1', 'key2'], ArgumentError),
        (['myDict', '--scope'], ArgumentError),
        (['myDict', '--output', 'cpp'], MainArgs(output='cpp')),
        (['myDict', '--output', 'foam'], MainArgs(output='foam')),
        (['myDict', '--output', 'xml'], MainArgs(output='xml')),
        (['myDict', '--output', 'json'], MainArgs(output='json')),
        (['myDict', '--output', ''], ArgumentError),
        (['myDict', '--output'], ArgumentError),
    ]
)
def test_main(
    inputs: List[str],
    expected: Union[MainArgs, type],
    monkeypatch,
):
    # Prepare
    monkeypatch.setattr(sys, 'argv', ['dictParser'] + inputs)
    args: MainArgs = MainArgs()

    def fake_main(
        source_file: Path,
        includes: bool = True,
        mode: str = 'w',
        order: bool = False,
        comments: bool = True,
        scope: MutableSequence[str] = None,
        output: str = None,
    ):
        args.source_file = source_file
        args.includes = includes
        args.mode = mode
        args.order = order
        args.comments = comments
        args.scope = scope
        args.output = output

    monkeypatch.setattr(dictParser, '_main', fake_main)
    # Execute
    if isinstance(expected, MainArgs):
        args_assert: MainArgs = expected
        main()
        # Assert args
        for key in args_assert.__dataclass_fields__:
            assert args.__getattribute__(key) == args_assert.__getattribute__(key)
    elif issubclass(expected, Exception):
        exception: type = expected
        # Assert that expected exception is raised
        with pytest.raises((exception, SystemExit)):
            main()
    else:
        assert False


def test_invoke_api():
    # Prepare
    silent_remove(Path('parsed.test_dictParser_paramDict'))
    silent_remove(Path('parsed.test_dictParser_dict'))
    source_file = Path('test_dictParser_dict')
    # Execute
    _main(source_file)
    # Assert
    assert not os.path.exists('parsed.test_dictParser_paramDict')
    assert os.path.exists('parsed.test_dictParser_dict')


def test_validate_scope():
    # Vary scope to different types and each time test whether setOptions works as expected

    # None
    scope_in = None
    scope_out = _validate_scope(scope_in)   # type: ignore
    assert scope_out is None

    # empty string -> should be returned as a one-element list
    scope_in = ''
    scope_out = _validate_scope(scope_in)
    assert isinstance(scope_out, list)
    assert len(scope_out) == 1
    assert list(scope_out)[0] == ''

    # (single) string -> should be returned as a one-element list
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

    # list in string format (= string, which LOOKS like a list)
    scope_in = '[input,time]'
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == 'input'
    assert list(scope_out)[1] == 'time'

    # list in string format (= string, which LOOKS like a list)
    scope_in = ' [ input , time ] '
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
