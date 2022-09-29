from pathlib import Path
from typing import List

from dictIO.utils.path import highest_common_root_folder, relative_path
import pytest


def test_highest_common_root_folder():
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
        highest_common_root_folder([])
    assert highest_common_root_folder([file_01]) == folder_01
    assert highest_common_root_folder([file_01, file_02]) == folder_01
    assert highest_common_root_folder([file_01, file_02, file_03]) == folder_06
    assert highest_common_root_folder([file_01, file_02, file_03, file_04]) == folder_09
    assert highest_common_root_folder([file_01, file_02, file_03, file_04, file_05]) == folder_11
    assert highest_common_root_folder([file_01, file_06]) == folder_06
    assert highest_common_root_folder([file_01, file_07]) == folder_09
    assert highest_common_root_folder([file_01, file_08]) == folder_11
    assert highest_common_root_folder([file_01, file_09]) == folder_09
    assert highest_common_root_folder([file_01, file_10]) == folder_11
    assert highest_common_root_folder([file_04, file_07]) == folder_07
    assert highest_common_root_folder([file_05, file_08]) == folder_08
    assert highest_common_root_folder([file_08, file_10]) == folder_10
    assert highest_common_root_folder([file_11]) == folder_11
    assert highest_common_root_folder([file_12]) == folder_12
    with pytest.raises(ValueError):
        highest_common_root_folder([file_11, file_12])
    # Clean up


def test_relative_path():
    # Prepare
    file_01: Path = Path(r'C:/A0/A1/A2/file_01.abc')
    file_06: Path = Path(r'C:/A0/A1/file_06.abc')
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

    relative_path_folder_06_folder_01 = Path(r'A2/')
    relative_path_folder_01_folder_06 = Path(r'../')

    relative_path_folder_09_folder_01 = Path(r'A1/A2/')
    relative_path_folder_01_folder_09 = Path(r'../../')

    relative_path_folder_11_folder_01 = Path(r'A0/A1/A2/')
    relative_path_folder_01_folder_11 = Path(r'../../../')

    relative_path_folder_09_folder_06 = Path(r'A1/')
    relative_path_folder_06_folder_09 = Path(r'../')

    relative_path_folder_11_folder_06 = Path(r'A0/A1/')
    relative_path_folder_06_folder_11 = Path(r'../../')

    relative_path_folder_11_folder_09 = Path(r'A0/')
    relative_path_folder_09_folder_11 = Path(r'../')

    relative_path_folder_07_folder_01 = Path(r'../A1/A2/')
    relative_path_folder_01_folder_07 = Path(r'../../B1/')

    relative_path_folder_08_folder_01 = Path(r'../../A0/A1/A2/')
    relative_path_folder_01_folder_08 = Path(r'../../../B0/B1/')

    relative_path_folder_10_folder_01 = Path(r'../A0/A1/A2/')
    relative_path_folder_01_folder_10 = Path(r'../../../B0/')

    relative_path_folder_06_file_01 = Path(r'A2/file_01.abc')
    relative_path_folder_01_file_06 = Path(r'../file_06.abc')

    relative_path_file_06_folder_01 = Path(r'../A2/')
    relative_path_file_01_folder_06 = Path(r'../../')

    relative_path_file_06_file_01 = Path(r'../A2/file_01.abc')
    relative_path_file_01_file_06 = Path(r'../../file_06.abc')

    # Execute and Assert
    assert relative_path(folder_06, folder_01) == relative_path_folder_06_folder_01
    assert relative_path(folder_01, folder_06) == relative_path_folder_01_folder_06

    assert relative_path(folder_09, folder_01) == relative_path_folder_09_folder_01
    assert relative_path(folder_01, folder_09) == relative_path_folder_01_folder_09

    assert relative_path(folder_11, folder_01) == relative_path_folder_11_folder_01
    assert relative_path(folder_01, folder_11) == relative_path_folder_01_folder_11

    assert relative_path(folder_09, folder_06) == relative_path_folder_09_folder_06
    assert relative_path(folder_06, folder_09) == relative_path_folder_06_folder_09

    assert relative_path(folder_11, folder_06) == relative_path_folder_11_folder_06
    assert relative_path(folder_06, folder_11) == relative_path_folder_06_folder_11

    assert relative_path(folder_11, folder_09) == relative_path_folder_11_folder_09
    assert relative_path(folder_09, folder_11) == relative_path_folder_09_folder_11

    assert relative_path(folder_07, folder_01) == relative_path_folder_07_folder_01
    assert relative_path(folder_01, folder_07) == relative_path_folder_01_folder_07

    assert relative_path(folder_08, folder_01) == relative_path_folder_08_folder_01
    assert relative_path(folder_01, folder_08) == relative_path_folder_01_folder_08

    assert relative_path(folder_10, folder_01) == relative_path_folder_10_folder_01
    assert relative_path(folder_01, folder_10) == relative_path_folder_01_folder_10

    assert relative_path(folder_06, file_01) == relative_path_folder_06_file_01
    assert relative_path(folder_01, file_06) == relative_path_folder_01_file_06

    assert relative_path(file_06, folder_01) == relative_path_file_06_folder_01
    assert relative_path(file_01, folder_06) == relative_path_file_01_folder_06

    assert relative_path(file_06, file_01) == relative_path_file_06_file_01
    assert relative_path(file_01, file_06) == relative_path_file_01_file_06

    with pytest.raises(ValueError):
        relative_path(folder_11, folder_12)
    with pytest.raises(ValueError):
        relative_path(folder_11, file_12)
    with pytest.raises(ValueError):
        relative_path(file_11, folder_12)
    with pytest.raises(ValueError):
        relative_path(file_11, file_12)
