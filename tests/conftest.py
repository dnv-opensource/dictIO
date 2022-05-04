import os
from glob import glob
from pathlib import Path

import pytest


@pytest.fixture(scope='package', autouse=True)
def chdir():
    os.chdir(Path(__file__).parent.absolute() / 'test_dicts')


parsed_files = ['parsed.*']


@pytest.fixture(autouse=True)
def default_setup_and_teardown():
    _remove_parsed_files()
    yield
    _remove_parsed_files()


def _remove_parsed_files():
    for pattern in parsed_files:
        for file in glob(pattern):
            file = Path(file)
            file.unlink(missing_ok=True)
