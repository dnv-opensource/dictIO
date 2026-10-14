"""Test configuration and fixtures."""

import logging
import os
from collections.abc import Generator
from pathlib import Path
from shutil import rmtree

import pytest


@pytest.fixture(scope="session", autouse=True)
def chdir() -> Generator[None, None, None]:
    """Change to the isolated test working directory for the duration of the session.

    Yields:
        Control to the test session after changing directories; restores the original directory afterward.
    """
    original_cwd = Path.cwd()
    os.chdir(Path(__file__).parent.absolute() / "test_working_directory")
    try:
        yield
    finally:
        os.chdir(original_cwd)  # reset to original working directory after tests


@pytest.fixture(scope="session", autouse=True)
def test_dir() -> Path:
    """Provide the absolute path to the tests directory for test setup.

    Returns:
        Absolute path to the directory containing this configuration file.
    """
    return Path(__file__).parent.absolute()


output_dirs: list[str] = []
output_files: list[str] = [
    "parsed.*",
]


@pytest.fixture(autouse=True)
def default_setup_and_teardown() -> Generator[None, None, None]:
    """Remove test artifacts before and after each test function.

    Yields:
        Control to the test after removing configured artifacts, then removes them again.
    """
    _remove_output_dirs_and_files()
    yield
    _remove_output_dirs_and_files()


def _remove_output_dirs_and_files() -> None:
    """Remove configured output directories and files from the test working directory."""
    for folder in output_dirs:
        rmtree(folder, ignore_errors=True)
    for pattern in output_files:
        for file in Path.cwd().glob(pattern):
            _file = Path(file)
            if _file.is_file():
                _file.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Reset captured logging before each test function.

    Args:
        caplog: Pytest fixture used to set the log level and clear captured records.
    """
    caplog.set_level("INFO")
    caplog.clear()


@pytest.fixture(autouse=True)
def logger() -> logging.Logger:
    """Provide the root logger used by tests.

    Returns:
        Root logger for the current test process.
    """
    return logging.getLogger()
