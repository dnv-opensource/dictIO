import os
from pathlib import Path

import pytest


@pytest.fixture(scope='package', autouse=True)
def chdir():
    os.chdir(Path(__file__).parent.absolute() / 'test_dicts')
