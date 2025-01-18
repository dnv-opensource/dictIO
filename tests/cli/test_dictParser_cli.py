# pyright: reportPrivateUsage=false
import sys
from argparse import ArgumentError
from collections.abc import MutableSequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from dictIO.cli import dict_parser
from dictIO.cli.dict_parser import _argparser, _validate_scope, main
from dictIO.dict_parser import DictParser

# *****Test commandline interface (CLI)************************************************************


@dataclass()
class CliArgs:
    # Expected default values for the CLI arguments when dictParser gets called via the commandline
    quiet: bool = False
    verbose: bool = False
    log: str | None = None
    log_level: str = field(default_factory=lambda: "WARNING")
    dict: str | None = field(default_factory=lambda: "test_dictParser_dict")
    ignore_includes: bool = False
    mode: str = "w"
    order: bool = False
    ignore_comments: bool = False
    scope: str | None = None
    output: str = "cpp"


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ([], ArgumentError),
        (["test_dictParser_dict"], CliArgs()),
        (["test_dictParser_dict", "-q"], CliArgs(quiet=True)),
        (["test_dictParser_dict", "--quiet"], CliArgs(quiet=True)),
        (["test_dictParser_dict", "-v"], CliArgs(verbose=True)),
        (["test_dictParser_dict", "--verbose"], CliArgs(verbose=True)),
        (["test_dictParser_dict", "-qv"], ArgumentError),
        (["test_dictParser_dict", "--log", "logFile"], CliArgs(log="logFile")),
        (["test_dictParser_dict", "--log"], ArgumentError),
        (["test_dictParser_dict", "--log-level", "INFO"], CliArgs(log_level="INFO")),
        (["test_dictParser_dict", "--log-level"], ArgumentError),
        (["test_dictParser_dict", "-I"], CliArgs(ignore_includes=True)),
        (["test_dictParser_dict", "--ignore-includes"], CliArgs(ignore_includes=True)),
        (["test_dictParser_dict", "--mode", "a"], CliArgs(mode="a")),
        (["test_dictParser_dict", "--mode"], ArgumentError),
        (["test_dictParser_dict", "--order"], CliArgs(order=True)),
        (["test_dictParser_dict", "-o"], ArgumentError),
        (["test_dictParser_dict", "-C"], CliArgs(ignore_comments=True)),
        (["test_dictParser_dict", "--ignore-comments"], CliArgs(ignore_comments=True)),
        (["test_dictParser_dict", "--scope", ""], CliArgs(scope="")),
        (["test_dictParser_dict", "--scope", "key"], CliArgs(scope="key")),
        (
            ["test_dictParser_dict", "--scope", "[key1,key2]"],
            CliArgs(scope="[key1,key2]"),
        ),
        (
            ["test_dictParser_dict", "--scope", "[key1, key2]"],
            CliArgs(scope="[key1, key2]"),
        ),
        (
            ["test_dictParser_dict", "--scope", "['key1', 'key2']"],
            CliArgs(scope="['key1', 'key2']"),
        ),
        (["test_dictParser_dict", "--scope", "key1", "key2"], ArgumentError),
        (["test_dictParser_dict", "--scope"], ArgumentError),
        (["test_dictParser_dict", "--output", "cpp"], CliArgs(output="cpp")),
        (["test_dictParser_dict", "--output", "foam"], CliArgs(output="foam")),
        (["test_dictParser_dict", "--output", "xml"], CliArgs(output="xml")),
        (["test_dictParser_dict", "--output", "json"], CliArgs(output="json")),
        (["test_dictParser_dict", "--output", ""], ArgumentError),
        (["test_dictParser_dict", "--output"], ArgumentError),
    ],
)
def test_cli(
    inputs: list[str],
    expected: CliArgs | type,
    monkeypatch: pytest.MonkeyPatch,
):
    # sourcery skip: no-conditionals-in-tests
    # sourcery skip: no-loop-in-tests
    # Prepare
    monkeypatch.setattr(sys, "argv", ["dictParser", *inputs])
    parser = _argparser()
    # Execute
    if isinstance(expected, CliArgs):
        args_expected: CliArgs = expected
        args = parser.parse_args()
        # Assert args
        for key in args_expected.__dataclass_fields__:
            assert args.__getattribute__(key) == args_expected.__getattribute__(key)
    elif issubclass(expected, Exception):
        exception: type = expected
        # Assert that expected exception is raised
        with pytest.raises((exception, SystemExit)):
            args = parser.parse_args()
    else:
        raise TypeError


# *****Ensure the CLI correctly configures logging*************************************************


@dataclass()
class ConfigureLoggingArgs:
    # Values that main() is expected to pass to ConfigureLogging() by default when configuring the logging
    log_level_console: str = field(default_factory=lambda: "WARNING")
    log_file: Path | None = None
    log_level_file: str = field(default_factory=lambda: "WARNING")


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ([], ArgumentError),
        (["test_dictParser_dict"], ConfigureLoggingArgs()),
        (["test_dictParser_dict", "-q"], ConfigureLoggingArgs(log_level_console="ERROR")),
        (["test_dictParser_dict", "--quiet"], ConfigureLoggingArgs(log_level_console="ERROR")),
        (["test_dictParser_dict", "-v"], ConfigureLoggingArgs(log_level_console="INFO")),
        (
            ["test_dictParser_dict", "--verbose"],
            ConfigureLoggingArgs(log_level_console="INFO"),
        ),
        (["test_dictParser_dict", "-qv"], ArgumentError),
        (
            ["test_dictParser_dict", "--log", "logFile"],
            ConfigureLoggingArgs(log_file=Path("logFile")),
        ),
        (["test_dictParser_dict", "--log"], ArgumentError),
        (
            ["test_dictParser_dict", "--log-level", "INFO"],
            ConfigureLoggingArgs(log_level_file="INFO"),
        ),
        (["test_dictParser_dict", "--log-level"], ArgumentError),
    ],
)
def test_logging_configuration(
    inputs: list[str],
    expected: ConfigureLoggingArgs | type,
    monkeypatch: pytest.MonkeyPatch,
):
    # sourcery skip: no-conditionals-in-tests
    # sourcery skip: no-loop-in-tests
    # Prepare
    monkeypatch.setattr(sys, "argv", ["dictParser", *inputs])
    args: ConfigureLoggingArgs = ConfigureLoggingArgs()

    def fake_configure_logging(
        log_level_console: str,
        log_file: Path | None,
        log_level_file: str,
    ):
        args.log_level_console = log_level_console
        args.log_file = log_file
        args.log_level_file = log_level_file

    def fake_parse(
        source_file: Path,
        *,
        includes: bool = True,
        mode: str = "w",
        order: bool = False,
        comments: bool = True,
        scope: MutableSequence[Any] | None = None,
        output: str | None = None,
    ):
        pass

    monkeypatch.setattr(dict_parser, "configure_logging", fake_configure_logging)
    monkeypatch.setattr(DictParser, "parse", fake_parse)
    # Execute
    if isinstance(expected, ConfigureLoggingArgs):
        args_expected: ConfigureLoggingArgs = expected
        main()
        # Assert args
        for key in args_expected.__dataclass_fields__:
            assert args.__getattribute__(key) == args_expected.__getattribute__(key)
    elif issubclass(expected, Exception):
        exception: type = expected
        # Assert that expected exception is raised
        with pytest.raises((exception, SystemExit)):
            main()
    else:
        raise TypeError


# *****Ensure the CLI correctly invokes the API****************************************************


@dataclass()
class ApiArgs:
    # Values that main() is expected to pass to DictParser.parse() by default when invoking the API
    source_file: Path = field(default_factory=lambda: Path("test_dictParser_dict"))
    includes: bool = True
    mode: str = "w"
    order: bool = False
    comments: bool = True
    scope: MutableSequence[Any] | None = None
    output: str | None = "cpp"


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ([], ArgumentError),
        (["test_dictParser_dict"], ApiArgs()),
        (["test_dictParser_dict", "-I"], ApiArgs(includes=False)),
        (["test_dictParser_dict", "--ignore-includes"], ApiArgs(includes=False)),
        (["test_dictParser_dict", "--mode", "a"], ApiArgs(mode="a")),
        (["test_dictParser_dict", "--mode"], ArgumentError),
        (["test_dictParser_dict", "--order"], ApiArgs(order=True)),
        (["test_dictParser_dict", "-o"], ArgumentError),
        (["test_dictParser_dict", "-C"], ApiArgs(comments=False)),
        (["test_dictParser_dict", "--ignore-comments"], ApiArgs(comments=False)),
        (["test_dictParser_dict", "--scope", ""], ApiArgs(scope=[""])),
        (["test_dictParser_dict", "--scope", "key"], ApiArgs(scope=["key"])),
        (
            ["test_dictParser_dict", "--scope", "[key1,key2]"],
            ApiArgs(scope=["key1", "key2"]),
        ),
        (
            ["test_dictParser_dict", "--scope", "[key1, key2]"],
            ApiArgs(scope=["key1", "key2"]),
        ),
        (
            ["test_dictParser_dict", "--scope", "['key1', 'key2']"],
            ApiArgs(scope=["key1", "key2"]),
        ),
        (["test_dictParser_dict", "--scope", "key1", "key2"], ArgumentError),
        (["test_dictParser_dict", "--scope"], ArgumentError),
        (["test_dictParser_dict", "--output", "cpp"], ApiArgs(output="cpp")),
        (["test_dictParser_dict", "--output", "foam"], ApiArgs(output="foam")),
        (["test_dictParser_dict", "--output", "xml"], ApiArgs(output="xml")),
        (["test_dictParser_dict", "--output", "json"], ApiArgs(output="json")),
        (["test_dictParser_dict", "--output", ""], ArgumentError),
        (["test_dictParser_dict", "--output"], ArgumentError),
    ],
)
def test_api_invokation(
    inputs: list[str],
    expected: ApiArgs | type,
    monkeypatch: pytest.MonkeyPatch,
):
    # sourcery skip: no-conditionals-in-tests
    # sourcery skip: no-loop-in-tests
    # Prepare
    monkeypatch.setattr(sys, "argv", ["dictParser", *inputs])
    args: ApiArgs = ApiArgs()

    def fake_parse(
        source_file: Path,
        *,
        includes: bool = True,
        mode: str = "w",
        order: bool = False,
        comments: bool = True,
        scope: MutableSequence[Any] | None = None,
        output: str | None = None,
    ):
        args.source_file = source_file
        args.includes = includes
        args.mode = mode
        args.order = order
        args.comments = comments
        args.scope = scope
        args.output = output

    monkeypatch.setattr(target=DictParser, name="parse", value=fake_parse)
    # Execute
    if isinstance(expected, ApiArgs):
        args_expected: ApiArgs = expected
        main()
        # Assert args
        for key in args_expected.__dataclass_fields__:
            assert args.__getattribute__(key) == args_expected.__getattribute__(key)
    elif issubclass(expected, Exception):
        exception: type = expected
        # Assert that expected exception is raised
        with pytest.raises((exception, SystemExit)):
            main()
    else:
        raise TypeError


# *****Test _validate_scope() helper function******************************************************


def test_validate_scope() -> None:
    # Vary scope to different types and each time test whether setOptions works as expected
    scope_in: str | list[str] | int | None
    # None
    scope_in = None
    scope_out: list[str] | list[str | int] | list[int] | None = _validate_scope(scope_in)
    assert scope_out is None

    # empty string -> should be returned as a one-element list
    scope_in = ""
    scope_out = _validate_scope(scope_in)
    assert isinstance(scope_out, list)
    assert len(scope_out) == 1
    assert list(scope_out)[0] == ""

    # (single) string -> should be returned as a one-element list
    scope_in = "strings"
    scope_out = _validate_scope(scope_in)
    assert isinstance(scope_out, list)
    assert len(scope_out) == 1
    assert list(scope_out)[0] == "strings"

    # list
    scope_in = ["input", "time"]
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == "input"
    assert list(scope_out)[1] == "time"

    # list in string format (= string, which LOOKS like a list)
    scope_in = "['input','time']"
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == "input"
    assert list(scope_out)[1] == "time"

    # list in string format (= string, which LOOKS like a list)
    scope_in = "[input,time]"
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == "input"
    assert list(scope_out)[1] == "time"

    # list in string format (= string, which LOOKS like a list)
    scope_in = " [ input , time ] "
    scope_out = _validate_scope(scope_in)
    assert scope_out is not None
    assert isinstance(scope_out, list)
    assert len(scope_out) == 2
    assert list(scope_out)[0] == "input"
    assert list(scope_out)[1] == "time"

    # int  -> should not be accepted and result in None
    scope_in = 1
    scope_out = _validate_scope(scope_in)
    assert scope_out is None
