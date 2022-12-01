import os
from glob import glob
from pathlib import Path

import pytest


@pytest.fixture(scope="package", autouse=True)
def chdir():
    os.chdir(Path(__file__).parent.absolute() / "test_dicts")


dictIO_files = ["parsed.*"]  # noqa


@pytest.fixture(autouse=True)
def default_setup_and_teardown():
    _remove_dictIO_files()
    yield
    _remove_dictIO_files()


def _remove_dictIO_files():  # noqa
    for pattern in dictIO_files:
        for file in glob(pattern):
            file = Path(file)
            file.unlink(missing_ok=True)
