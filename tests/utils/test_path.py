from pathlib import Path
from typing import List

from dictIO.utils.path import find_highest_common_root_folder
import pytest


def test_find_highest_common_root_folder():
    # Prepare
    file_01: Path = Path(r'C:/A0/A1/A2/file_01.abc')
    file_02: Path = Path(r'C:/A0/A1/A2/file_02.abc')
    file_03: Path = Path(r'C:/A0/A1/B2/file_03.abc')
    file_04: Path = Path(r'C:/A0/B1/B2/file_04.abc')
    file_05: Path = Path(r'C:/B0/B1/B2/file_05.abc')
    file_06: Path = Path(r'C:/A0/A1/file_06.abc')
    file_07: Path = Path(r'C:/A0/B1/file_07.abc')
    file_08: Path = Path(r'C:/B0/B1/file_08.abc')
    file_09: Path = Path(r'C:/A0/file_09.abc')
    file_10: Path = Path(r'C:/B0/file_10.abc')
    file_11: Path = Path(r'C:/file_11.abc')
    file_12: Path = Path(r'D:/file_12.abc')
    folder_01: Path = Path(r'C:/A0/A1/A2/')
    folder_06: Path = Path(r'C:/A0/A1/')
    folder_07: Path = Path(r'C:/A0/B1/')
    folder_08: Path = Path(r'C:/B0/B1/')
    folder_09: Path = Path(r'C:/A0/')
    folder_10: Path = Path(r'C:/B0/')
    folder_11: Path = Path(r'C:/')
    folder_12: Path = Path(r'D:/')
    # Execute and Assert
    with pytest.raises(ValueError):
        find_highest_common_root_folder([])
    assert find_highest_common_root_folder([file_01]) == folder_01
    assert find_highest_common_root_folder([file_01, file_02]) == folder_01
    assert find_highest_common_root_folder([file_01, file_02, file_03]) == folder_06
    assert find_highest_common_root_folder([file_01, file_02, file_03, file_04]) == folder_09
    assert find_highest_common_root_folder(
        [file_01, file_02, file_03, file_04, file_05]
    ) == folder_11
    assert find_highest_common_root_folder([file_01, file_06]) == folder_06
    assert find_highest_common_root_folder([file_01, file_07]) == folder_09
    assert find_highest_common_root_folder([file_01, file_08]) == folder_11
    assert find_highest_common_root_folder([file_01, file_09]) == folder_09
    assert find_highest_common_root_folder([file_01, file_10]) == folder_11
    assert find_highest_common_root_folder([file_04, file_07]) == folder_07
    assert find_highest_common_root_folder([file_05, file_08]) == folder_08
    assert find_highest_common_root_folder([file_08, file_10]) == folder_10
    assert find_highest_common_root_folder([file_11]) == folder_11
    assert find_highest_common_root_folder([file_12]) == folder_12
    with pytest.raises(ValueError):
        find_highest_common_root_folder([file_11, file_12])
    # Clean up
