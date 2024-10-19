from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from dictIO import (
    CppDict,
    CppParser,
    DictParser,
    DictReader,
    DictWriter,
    find_global_key,
    order_keys,
    set_global_key,
)
from dictIO.cppDict import ComposableDict

if TYPE_CHECKING:
    from dictIO.types import TValue


@pytest.fixture
def test_dict() -> CppDict:
    parser = CppParser()
    return parser.parse_file(Path("test_dict_dict"))


def test_init() -> None:
    test_dict = CppDict()
    assert test_dict.source_file is None
    assert test_dict.path == Path.cwd()
    assert test_dict.name == ""
    assert test_dict.line_content == []
    assert test_dict.line_comments == {}
    assert test_dict.includes == {}
    assert test_dict.block_content == ""
    assert test_dict.block_comments == {}
    assert test_dict.string_literals == {}
    assert test_dict.expressions == {}
    assert test_dict.delimiters == ["{", "}", "(", ")", "<", ">", ";", ","]


def test_init_with_file() -> None:
    test_dict = CppDict("someDict")
    assert test_dict.source_file == Path.cwd() / "someDict"
    assert test_dict.path == Path.cwd()
    assert test_dict.name == "someDict"
    assert test_dict.line_content == []
    assert test_dict.line_comments == {}
    assert test_dict.includes == {}
    assert test_dict.block_content == ""
    assert test_dict.block_comments == {}
    assert test_dict.string_literals == {}
    assert test_dict.expressions == {}
    assert test_dict.delimiters == ["{", "}", "(", ")", "<", ">", ";", ","]


def test_init_with_base_dict() -> None:
    base_dict: dict[str, TValue] = {
        "key1": "value1",
        "key2": "value2",
    }
    test_dict = CppDict(base_dict)
    assert test_dict.data == base_dict
    assert test_dict.source_file is None
    assert test_dict.path == Path.cwd()
    assert test_dict.name == ""
    assert test_dict.line_content == []
    assert test_dict.line_comments == {}
    assert test_dict.includes == {}
    assert test_dict.block_content == ""
    assert test_dict.block_comments == {}
    assert test_dict.string_literals == {}
    assert test_dict.expressions == {}
    assert test_dict.delimiters == ["{", "}", "(", ")", "<", ">", ";", ","]


def test_find_global_key() -> None:
    # sourcery skip: no-loop-in-tests
    # Prepare
    str_in_1 = "PLACEHOLDER000001"
    str_in_2 = "PLACEHOLDER000002"
    str_in_3 = "PLACEHOLDER000003"
    not_a_str_1 = 1234
    not_a_str_2 = 1.23
    not_a_str_3 = False

    key_1 = "key_1"
    key_2 = "key_2"
    key_3 = "key_3"
    key_n_1 = "key_n_1"
    key_n_2 = "key_n_2"
    key_n_3 = "key_n_3"
    keyd = "keyd"
    keyl = "keyl"
    keydl = "keydl"
    keyld = "keyld"
    keydld = "keydld"
    keyldl = "keyldl"
    d_nested = {
        key_1: str_in_1,
        key_2: str_in_2,
        key_3: str_in_3,
        key_n_1: not_a_str_1,
        key_n_2: not_a_str_2,
        key_n_3: not_a_str_3,
    }
    l_nested = [
        str_in_1,
        str_in_2,
        str_in_3,
        not_a_str_1,
        not_a_str_2,
        not_a_str_3,
    ]
    dl_nested = {keyl: deepcopy(l_nested)}
    ld_nested = [deepcopy(d_nested)]
    dld_nested = {keyld: deepcopy(ld_nested)}
    ldl_nested = [deepcopy(dl_nested)]

    # Construct a dictionary dict_in with single entries, nested dicts and nested lists
    dict_in: dict[str, TValue] = {
        key_1: str_in_1,
        key_2: str_in_2,
        key_3: str_in_3,
        key_n_1: not_a_str_1,
        key_n_2: not_a_str_2,
        key_n_3: not_a_str_3,
        keyd: d_nested,
        keyl: l_nested,
        keydl: dl_nested,
        keyld: ld_nested,
        keydld: dld_nested,
        keyldl: ldl_nested,
    }

    # Assert structure of dict_in
    assert len(dict_in) == 12
    assert len(dict_in[keyd]) == 6
    assert len(dict_in[keyl]) == 6
    assert len(dict_in[keydl]) == 1
    assert len(dict_in[keydl][keyl]) == 6
    assert len(dict_in[keyld]) == 1
    assert len(dict_in[keyld][0]) == 6
    assert len(dict_in[keydld]) == 1
    assert len(dict_in[keydld][keyld]) == 1
    assert len(dict_in[keydld][keyld][0]) == 6
    assert len(dict_in[keyldl]) == 1
    assert len(dict_in[keyldl][0]) == 1
    assert len(dict_in[keyldl][0][keyl]) == 6

    # Assert content of dict_in
    assert dict_in[key_1] == str_in_1
    assert dict_in[key_2] == str_in_2
    assert dict_in[key_3] == str_in_3
    assert dict_in[keyd][key_1] == str_in_1
    assert dict_in[keyd][key_2] == str_in_2
    assert dict_in[keyd][key_3] == str_in_3
    assert dict_in[keyl][0] == str_in_1
    assert dict_in[keyl][1] == str_in_2
    assert dict_in[keyl][2] == str_in_3
    assert dict_in[keydl][keyl][0] == str_in_1
    assert dict_in[keydl][keyl][1] == str_in_2
    assert dict_in[keydl][keyl][2] == str_in_3
    assert dict_in[keyld][0][key_1] == str_in_1
    assert dict_in[keyld][0][key_2] == str_in_2
    assert dict_in[keyld][0][key_3] == str_in_3
    assert dict_in[keydld][keyld][0][key_1] == str_in_1
    assert dict_in[keydld][keyld][0][key_2] == str_in_2
    assert dict_in[keydld][keyld][0][key_3] == str_in_3
    assert dict_in[keyldl][0][keyl][0] == str_in_1
    assert dict_in[keyldl][0][keyl][1] == str_in_2
    assert dict_in[keyldl][0][keyl][2] == str_in_3

    # Execute find_global_key and set_global_key
    dict_out = deepcopy(dict_in)
    str_out_1 = "string 1"
    str_out_2 = "string 2"
    str_out_3 = "string 3"
    global_key = find_global_key(arg=dict_out, query=str_in_1)
    i = 0
    while global_key:
        i += 1
        # Substitute str_in_1 with str_out_1
        set_global_key(arg=dict_out, global_key=global_key, value=str_out_1)
        global_key = find_global_key(arg=dict_out, query=str_in_1)
    assert i == 7
    global_key = find_global_key(arg=dict_out, query=str_in_2)
    i = 0
    while global_key:
        i += 1
        # Substitute str_in_2 with str_out_2
        set_global_key(arg=dict_out, global_key=global_key, value=str_out_2)
        global_key = find_global_key(arg=dict_out, query=str_in_2)
    assert i == 7
    global_key = find_global_key(arg=dict_out, query=str_in_3)
    i = 0
    while global_key:
        i += 1
        # Substitute str_in_3 with str_out_3
        set_global_key(arg=dict_out, global_key=global_key, value=str_out_3)
        global_key = find_global_key(arg=dict_out, query=str_in_3)
    assert i == 7

    # Assert structure of dict_out
    assert len(dict_out) == 12
    assert len(dict_out[keyd]) == 6
    assert len(dict_out[keyl]) == 6
    assert len(dict_out[keydl]) == 1
    assert len(dict_out[keydl][keyl]) == 6
    assert len(dict_out[keyld]) == 1
    assert len(dict_out[keyld][0]) == 6
    assert len(dict_out[keydld]) == 1
    assert len(dict_out[keydld][keyld]) == 1
    assert len(dict_out[keydld][keyld][0]) == 6
    assert len(dict_out[keyldl]) == 1
    assert len(dict_out[keyldl][0]) == 1
    assert len(dict_out[keyldl][0][keyl]) == 6

    # Assert content of dict_out
    assert dict_out[key_1] == str_out_1
    assert dict_out[key_2] == str_out_2
    assert dict_out[key_3] == str_out_3
    assert dict_out[keyd][key_1] == str_out_1
    assert dict_out[keyd][key_2] == str_out_2
    assert dict_out[keyd][key_3] == str_out_3
    assert dict_out[keyl][0] == str_out_1
    assert dict_out[keyl][1] == str_out_2
    assert dict_out[keyl][2] == str_out_3
    assert dict_out[keydl][keyl][0] == str_out_1
    assert dict_out[keydl][keyl][1] == str_out_2
    assert dict_out[keydl][keyl][2] == str_out_3
    assert dict_out[keyld][0][key_1] == str_out_1
    assert dict_out[keyld][0][key_2] == str_out_2
    assert dict_out[keyld][0][key_3] == str_out_3
    assert dict_out[keydld][keyld][0][key_1] == str_out_1
    assert dict_out[keydld][keyld][0][key_2] == str_out_2
    assert dict_out[keydld][keyld][0][key_3] == str_out_3
    assert dict_out[keyldl][0][keyl][0] == str_out_1
    assert dict_out[keyldl][0][keyl][1] == str_out_2
    assert dict_out[keyldl][0][keyl][2] == str_out_3


def test_order_keys() -> None:
    # sourcery skip: no-loop-in-tests
    # Prepare
    str_1 = "string 1"
    str_2 = "string 2"
    str_3 = "string 3"
    not_a_str_1 = 1234
    not_a_str_2 = 1.23
    not_a_str_3 = False

    key_1 = "key_1"
    key_2 = "key_2"
    key_3 = "key_3"
    key_n_1 = "key_n_1"
    key_n_2 = "key_n_2"
    key_n_3 = "key_n_3"
    key_4 = "key_4"

    d_nested = {
        key_3: str_3,
        key_1: str_1,
        key_2: str_2,
        key_n_3: not_a_str_3,
        key_n_1: not_a_str_1,
        key_n_2: not_a_str_2,
    }
    dict_in: dict[str, TValue] = {
        key_3: str_3,
        key_1: str_1,
        key_2: str_2,
        key_n_3: not_a_str_3,
        key_n_2: not_a_str_2,
        key_4: d_nested,
        key_n_1: not_a_str_1,
    }
    keys_expected = [key_1, key_2, key_3, key_4, key_n_1, key_n_2, key_n_3]
    keys_expected_nested = [key_1, key_2, key_3, key_n_1, key_n_2, key_n_3]

    cpp_dict = CppDict()
    cpp_dict.data.update(deepcopy(dict_in))

    # 1. negative test: assert dict_in is not alphanumerically ordered
    for index, key in enumerate(dict_in):
        assert key != keys_expected[index]
    for index, key in enumerate(dict_in[key_4]):
        assert key != keys_expected_nested[index]

    # 2. negative test: assert dict is not alphanumerically ordered
    for index, key in enumerate(cpp_dict.data):
        assert key != keys_expected[index]
    for index, key in enumerate(cpp_dict.data[key_4]):
        assert key != keys_expected_nested[index]

    dict_out = order_keys(dict_in)  # order_keys function defined in dict.py module
    cpp_dict.order_keys()  # order_keys instance method of CppDict class

    # 1. positive test for dict_out: assert dict_out is alphanumerically ordered
    for index, key in enumerate(dict_out):
        assert key == keys_expected[index]
    for index, key in enumerate(dict_out[key_4]):
        assert key == keys_expected_nested[index]

    # 2. positive test for dict: assert dict.data is alphanumerically ordered
    for index, key in enumerate(cpp_dict.data):
        assert key == keys_expected[index]
    for index, key in enumerate(cpp_dict.data[key_4]):
        assert key == keys_expected_nested[index]


def test_order_keys_of_test_dict(test_dict: CppDict) -> None:
    # Prepare
    # Execute
    test_dict.order_keys()
    # Assert
    assert str(test_dict.data["unordered"]) == str(test_dict.data["ordered"])


def test_reduce_scope_of_test_dict(test_dict: CppDict) -> None:
    # Prepare
    scope = ["scope", "subscope1"]
    # Execute
    test_dict.reduce_scope(scope)
    # Assert
    dict_out = test_dict.data
    assert len(dict_out) == 2  # subscope11, subscope12
    assert dict_out["subscope11"]["name"] == "subscope11"
    assert dict_out["subscope12"]["name"] == "subscope12"


def test_include() -> None:
    # Prepare
    source_dict_file = Path("test_dict_add_include")
    param_dict_file = Path("test_dict_paramDict")
    temp_dict_file = Path(f"{source_dict_file.name}_temp")
    parsed_dict_file = Path(f"parsed.{temp_dict_file.name}")
    temp_dict_file.unlink(missing_ok=True)
    parsed_dict_file.unlink(missing_ok=True)
    source_dict = DictReader.read(source_dict_file)
    param_dict = DictReader.read(param_dict_file)
    # Execute
    source_dict.include(param_dict)
    # Assert
    DictWriter.write(source_dict, temp_dict_file)
    parsed_dict = DictParser.parse(temp_dict_file)
    assert parsed_dict is not None
    assert parsed_dict["valueA"] == 1
    # Clean up
    temp_dict_file.unlink(missing_ok=True)
    parsed_dict_file.unlink(missing_ok=True)


def test_merge_does_not_overwrite_existing_keys() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "B": 21,
            "C": 21.0,
            "D": True,
            "E": {
                "A": "string 22",
                "B": 22,
                "C": 22.0,
                "D": False,
            },
            "F": [
                "string 23",
                23,
                23.0,
                True,
            ],
        }
    )
    dict_1_original = deepcopy(dict_1)
    # merge dict_2 into dict_1
    dict_1.merge(dict_2)
    # assert that no entry in dict_1 has been overwritten
    # (because dict_2 contains only keys that are already present in dict_1)
    assert dict_1 == dict_1_original


def test_merge_does_not_delete_existing_keys() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "E": {},
            "F": [],
        }
    )
    dict_1_original = deepcopy(dict_1)
    # merge dict_2 into dict_1
    dict_1.merge(dict_2)
    # assert that no entry in dict_1 has been deleted
    assert dict_1 == dict_1_original


def test_merge_does_add_new_keys() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "E": {
                "E": "string 24",
            },
            "G": "string 26",
        }
    )
    # merge dict_2 into dict_1
    dict_1.merge(dict_2)
    # assert dict_1 contains the new keys and values from dict_2
    assert dict_1["A"] == "string 11"
    assert dict_1["B"] == 11
    assert dict_1["C"] == 11.0
    assert dict_1["D"] is False
    assert dict_1["E"]["A"] == "string 12"
    assert dict_1["E"]["B"] == 12
    assert dict_1["E"]["C"] == 12.0
    assert dict_1["E"]["D"] is True
    assert dict_1["E"]["E"] == "string 24"
    assert dict_1["F"][0] == "string 13"
    assert dict_1["F"][1] == 13
    assert dict_1["F"][2] == 13.0
    assert dict_1["F"][3] is False
    assert dict_1["G"] == "string 26"


def test_merge_does_not_change_existings_lists() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "F": [
                "string 23",
                23,
                23.0,
                True,
                "string 25",
            ],
        }
    )
    # merge dict_2 into dict_1
    dict_1.merge(dict_2)
    # assert that list "F" remained unchanged and
    # that the additional element in list "F" has NOT been added to the list.
    assert dict_1["F"][0] == "string 13"
    assert dict_1["F"][1] == 13
    assert dict_1["F"][2] == 13.0
    assert dict_1["F"][3] is False
    assert len(dict_1["F"]) == 4
    with pytest.raises(IndexError):
        _ = dict_1["F"][4]


def test_update_does_overwrite_existing_keys() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "B": 21,
            "C": 21.0,
            "D": True,
            "E": {
                "A": "string 22",
                "B": 22,
                "C": 22.0,
                "D": False,
            },
            "F": [
                "string 23",
                23,
                23.0,
                True,
            ],
        }
    )
    # update dict_1 with dict_2
    dict_1.update(dict_2)
    # assert âll elements in dict_1 have been overwritten with the elements from dict_2
    assert dict_1["A"] == "string 21"
    assert dict_1["B"] == 21
    assert dict_1["C"] == 21.0
    assert dict_1["D"] is True
    assert dict_1["E"]["A"] == "string 22"
    assert dict_1["E"]["B"] == 22
    assert dict_1["E"]["C"] == 22.0
    assert dict_1["E"]["D"] is False
    assert dict_1["F"][0] == "string 23"
    assert dict_1["F"][1] == 23
    assert dict_1["F"][2] == 23.0
    assert dict_1["F"][3] is True


def test_update_does_delete_nested_elements() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "E": {},
            "F": [],
        }
    )
    # update dict_1 with dict_2
    dict_1.update(dict_2)
    # assert that formerly existing nested elements have been deleted,
    # because they are not present in dict_2
    assert dict_1["A"] == "string 21"  # overwritten by dict_2
    assert dict_1["B"] == 11  # not deleted by dict_2
    assert dict_1["C"] == 11.0  # not deleted by dict_2
    assert dict_1["D"] is False  # not deleted by dict_2
    assert dict_1["E"] == {}  # overwritten by dict_2, and hence all nested elements have been deleted
    assert dict_1["F"] == []  # overwritten by dict_2, and hence all nested elements have been deleted


def test_update_does_add_new_keys_by_overwrite() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "E": {
                "E": "string 24",
            },
            "G": "string 26",
        }
    )
    # update dict_1 with dict_2
    dict_1.update(dict_2)
    # assert dict_1 contains the new keys, but nested keys which do not exist in dict_2 have been deleted
    assert dict_1["A"] == "string 11"
    assert dict_1["B"] == 11
    assert dict_1["C"] == 11.0
    assert dict_1["D"] is False
    with pytest.raises(KeyError):
        _ = dict_1["E"]["A"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["B"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["C"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["D"]
    assert dict_1["E"]["E"] == "string 24"
    assert dict_1["F"][0] == "string 13"
    assert dict_1["F"][1] == 13
    assert dict_1["F"][2] == 13.0
    assert dict_1["F"][3] is False
    assert dict_1["G"] == "string 26"


def test_update_does_change_existings_lists_by_overwrite() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "F": [
                "string 23",
                23,
                23.0,
                True,
                "string 25",
            ],
        }
    )
    # update dict_1 with dict_2
    dict_1.update(dict_2)
    # assert that list "F" is overwritten with list "F" from dict_2
    assert dict_1["F"][0] == "string 23"
    assert dict_1["F"][1] == 23
    assert dict_1["F"][2] == 23.0
    assert dict_1["F"][3] is True
    assert dict_1["F"][4] == "string 25"


def test_inner_or_does_overwrite_existing_keys() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "B": 21,
            "C": 21.0,
            "D": True,
            "E": {
                "A": "string 22",
                "B": 22,
                "C": 22.0,
                "D": False,
            },
            "F": [
                "string 23",
                23,
                23.0,
                True,
            ],
        }
    )
    # execute inner or operation
    dict_1 |= dict_2
    # assert âll elements in dict_1 have been overwritten with the elements from dict_2
    assert dict_1["A"] == "string 21"
    assert dict_1["B"] == 21
    assert dict_1["C"] == 21.0
    assert dict_1["D"] is True
    assert dict_1["E"]["A"] == "string 22"
    assert dict_1["E"]["B"] == 22
    assert dict_1["E"]["C"] == 22.0
    assert dict_1["E"]["D"] is False
    assert dict_1["F"][0] == "string 23"
    assert dict_1["F"][1] == 23
    assert dict_1["F"][2] == 23.0
    assert dict_1["F"][3] is True


def test_inner_or_does_delete_nested_elements() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 21",
            "E": {},
            "F": [],
        }
    )
    # execute inner or operation
    dict_1 |= dict_2
    # assert that formerly existing nested elements have been deleted,
    # because they are not present in dict_2
    assert dict_1["A"] == "string 21"  # overwritten by dict_2
    assert dict_1["B"] == 11  # not deleted by dict_2
    assert dict_1["C"] == 11.0  # not deleted by dict_2
    assert dict_1["D"] is False  # not deleted by dict_2
    assert dict_1["E"] == {}  # overwritten by dict_2, and hence all nested elements have been deleted
    assert dict_1["F"] == []  # overwritten by dict_2, and hence all nested elements have been deleted


def test_inner_or_does_add_new_keys_by_overwrite() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "E": {
                "E": "string 24",
            },
            "G": "string 26",
        }
    )
    # execute inner or operation
    dict_1 |= dict_2
    # assert dict_1 contains the new keys, but nested keys which do not exist in dict_2 have been deleted
    assert dict_1["A"] == "string 11"
    assert dict_1["B"] == 11
    assert dict_1["C"] == 11.0
    assert dict_1["D"] is False
    with pytest.raises(KeyError):
        _ = dict_1["E"]["A"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["B"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["C"]
    with pytest.raises(KeyError):
        _ = dict_1["E"]["D"]
    assert dict_1["E"]["E"] == "string 24"
    assert dict_1["F"][0] == "string 13"
    assert dict_1["F"][1] == 13
    assert dict_1["F"][2] == 13.0
    assert dict_1["F"][3] is False
    assert dict_1["G"] == "string 26"


def test_inner_or_does_change_existings_lists_by_overwrite() -> None:
    # construct two dicts with single entries, a nested dict and a nested list
    dict_1: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "A": "string 11",
            "B": 11,
            "C": 11.0,
            "D": False,
            "E": {
                "A": "string 12",
                "B": 12,
                "C": 12.0,
                "D": True,
            },
            "F": [
                "string 13",
                13,
                13.0,
                False,
            ],
        }
    )
    dict_2: ComposableDict[str, TValue | dict[str | int, TValue]] = ComposableDict(
        {
            "F": [
                "string 23",
                23,
                23.0,
                True,
                "string 25",
            ],
        }
    )
    # execute inner or operation
    dict_1 |= dict_2
    # assert that list "F" is overwritten with list "F" from dict_2
    assert dict_1["F"][0] == "string 23"
    assert dict_1["F"][1] == 23
    assert dict_1["F"][2] == 23.0
    assert dict_1["F"][3] is True
    assert dict_1["F"][4] == "string 25"
