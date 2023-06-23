from copy import deepcopy
from pathlib import Path

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


@pytest.fixture()
def test_dict():
    parser = CppParser()
    return parser.parse_file(Path("test_dict_dict"))


def test_init():  # sourcery skip: avoid-builtin-shadow
    dict = CppDict()
    assert dict.source_file is None
    assert dict.path == Path.cwd()
    assert dict.name == ""
    assert dict.line_content == []
    assert dict.line_comments == {}
    assert dict.includes == {}
    assert dict.block_content == ""
    assert dict.block_comments == {}
    assert dict.string_literals == {}
    assert dict.expressions == {}
    # assert dict.delimiters == ['{','}','[',']','(',')','<','>',';',',']
    assert dict.delimiters == ["{", "}", "(", ")", "<", ">", ";", ","]


def test_init_with_file():  # sourcery skip: avoid-builtin-shadow
    dict = CppDict("someDict")
    assert dict.path == Path.cwd()
    assert dict.source_file == Path.cwd() / "someDict"


def test_find_global_key():
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
    dict_in = {
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


def test_order_keys():  # sourcery skip: avoid-builtin-shadow
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
    dict_in = {
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

    dict = CppDict()
    dict.data.update(deepcopy(dict_in))

    # 1. negative test: assert dict_in is not alphanumerically ordered
    for index, key in enumerate(dict_in):
        assert key != keys_expected[index]
    for index, key in enumerate(dict_in[key_4]):
        assert key != keys_expected_nested[index]

    # 2. negative test: assert dict is not alphanumerically ordered
    for index, key in enumerate(dict.data):
        assert key != keys_expected[index]
    for index, key in enumerate(dict.data[key_4]):
        assert key != keys_expected_nested[index]

    dict_out = order_keys(dict_in)  # order_keys function defined in dict.py module
    dict.order_keys()  # order_keys instance method of CppDict class

    # 1. positive test for dict_out: assert dict_out is alphanumerically ordered
    for index, key in enumerate(dict_out):
        assert key == keys_expected[index]
    for index, key in enumerate(dict_out[key_4]):
        assert key == keys_expected_nested[index]

    # 2. positive test for dict: assert dict.data is alphanumerically ordered
    for index, key in enumerate(dict.data):
        assert key == keys_expected[index]
    for index, key in enumerate(dict.data[key_4]):
        assert key == keys_expected_nested[index]


def test_order_keys_of_test_dict(test_dict: CppDict):
    # Prepare
    # Execute
    test_dict.order_keys()
    # Assert
    assert str(test_dict.data["unordered"]) == str(test_dict.data["ordered"])


def test_reduce_scope_of_test_dict(test_dict: CppDict):
    # Prepare
    scope = ["scope", "subscope1"]
    # Execute
    test_dict.reduce_scope(scope)
    # Assert
    dict_out = test_dict.data
    assert len(dict_out) == 2  # subscope11, subscope12
    assert dict_out["subscope11"]["name"] == "subscope11"
    assert dict_out["subscope12"]["name"] == "subscope12"


def test_include():
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
