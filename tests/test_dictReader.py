# pyright: reportPrivateUsage=false
import os
import re
import sys
from copy import deepcopy
from pathlib import Path, PurePath
from typing import Any, Dict, List, Union

import pytest
from numpy.testing import assert_array_equal
from pytest import LogCaptureFixture

from dictIO import CppDict, CppParser, DictReader, DictWriter

WindowsOnly: pytest.MarkDecorator = pytest.mark.skipif(not sys.platform.startswith("win"), reason="windows only test")


def test_file_not_found_exception():
    # Prepare
    source_file = Path("this_file_does_not_exist")
    # Execute and Assert
    with pytest.raises(FileNotFoundError):
        _ = DictReader.read(source_file)


def test_merge_includes():
    # sourcery skip: avoid-builtin-shadow, class-extract-method
    # Prepare dict until and including _parse_tokenized_dict()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict, until_step=-1)
    dict_in = deepcopy(dict.data)
    # Assert dict_in
    assert dict_in["expressions"]["reference"]["value"][:10] == "EXPRESSION"
    assert dict_in["expressions"]["expression1"]["value"][:10] == "EXPRESSION"
    assert dict_in["expressions"]["expression2"]["value"][:10] == "EXPRESSION"
    assert dict_in["expressions"]["expression3"]["value"][:10] == "EXPRESSION"
    # Execute
    DictReader._merge_includes(dict)
    dict_out = dict.data
    # Assert
    assert len(dict_out) == len(dict_in) + 8
    assert dict_out["paramA"] == 3.0
    assert dict_out["paramB"] == 4.0
    assert dict_out["paramC"] == 7.0
    assert dict_out["paramD"] == 0.66
    assert dict_out["paramE"] == [0.1, 0.2, 0.4]
    assert dict_out["paramF"] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict_out["paramG"] == [[10, "fancy", 3.14, "s"], ["more", 2, "come"]]


def test_resolve_reference():
    # sourcery skip: avoid-builtin-shadow
    # Prepare dict until and including ()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict, until_step=0)
    # Assert non-indexed references have been resolved
    assert DictReader._resolve_reference("$paramA", dict) == 3.0
    assert DictReader._resolve_reference("$paramB", dict) == 4.0
    assert DictReader._resolve_reference("$paramC", dict) == 7.0
    assert DictReader._resolve_reference("$paramD", dict) == 0.66
    assert DictReader._resolve_reference("$paramE[0]", dict.variables) == 0.1

    paramE = DictReader._resolve_reference("$paramE", dict)  # noqa: N806
    assert isinstance(paramE, list)
    assert len(paramE) == 3
    assert paramE[0] == 0.1
    assert paramE[1] == 0.2
    assert paramE[2] == 0.4
    paramF = DictReader._resolve_reference("$paramF", dict)  # noqa: N806
    assert isinstance(paramF, list)
    assert len(paramF) == 2
    assert len(paramF[0]) == 2
    assert len(paramF[1]) == 2
    assert paramF[0][0] == 0.3
    assert paramF[0][1] == 0.9
    assert paramF[1][0] == 2.7
    assert paramF[1][1] == 8.1
    paramG = DictReader._resolve_reference("$paramG", dict)  # noqa: N806
    assert isinstance(paramG, list)
    assert len(paramG) == 2
    assert len(paramG[0]) == 4
    assert len(paramG[1]) == 3
    assert paramG[0][0] == 10
    assert paramG[0][1] == "fancy"
    assert paramG[0][2] == 3.14
    assert paramG[0][3] == "s"
    assert paramG[1][0] == "more"
    assert paramG[1][1] == 2
    assert paramG[1][2] == "come"

    # Assert indexed references have been resolved
    assert DictReader._resolve_reference("$paramE[0]", dict) == 0.1
    assert DictReader._resolve_reference("$paramE[1]", dict) == 0.2
    assert DictReader._resolve_reference("$paramE[2]", dict) == 0.4
    assert DictReader._resolve_reference("$paramF[0][0]", dict) == 0.3
    assert DictReader._resolve_reference("$paramF[0][1]", dict) == 0.9
    assert DictReader._resolve_reference("$paramF[1][0]", dict) == 2.7
    assert DictReader._resolve_reference("$paramF[1][1]", dict) == 8.1
    assert DictReader._resolve_reference("$paramG[0][0]", dict) == 10
    assert DictReader._resolve_reference("$paramG[0][1]", dict) == "fancy"
    assert DictReader._resolve_reference("$paramG[0][2]", dict) == 3.14
    assert DictReader._resolve_reference("$paramG[0][3]", dict) == "s"
    assert DictReader._resolve_reference("$paramG[1][0]", dict) == "more"
    assert DictReader._resolve_reference("$paramG[1][1]", dict) == 2
    assert DictReader._resolve_reference("$paramG[1][2]", dict) == "come"


def test_eval_expressions():
    # sourcery skip: avoid-builtin-shadow
    # Prepare dict until and including ()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict, until_step=0)
    dict_in = deepcopy(dict.data)
    # Assert dict_in
    assert dict_in["expressions"]["reference"]["value"][:10] == "EXPRESSION"  # $paramA
    assert dict_in["expressions"]["expression1"]["value"][:10] == "EXPRESSION"  # "$paramB"
    assert dict_in["expressions"]["expression2"]["value"][:10] == "EXPRESSION"  # "$paramC + 4"
    assert dict_in["expressions"]["expression3"]["value"][:10] == "EXPRESSION"  # "$paramC + $paramD"
    assert dict_in["expressions"]["expressionE"]["value"][:10] == "EXPRESSION"  # $paramE[0]
    assert dict_in["expressions"]["expressionF"]["value"][:10] == "EXPRESSION"  # $paramF[0][0]
    assert dict_in["expressions"]["expressionG1"]["value"][:10] == "EXPRESSION"  # "$paramG"
    assert dict_in["expressions"]["expressionG2"]["value"][:10] == "EXPRESSION"  # "$paramG[0]"
    assert dict_in["expressions"]["expressionG3"]["value"][:10] == "EXPRESSION"  # "$paramG[1][2]"

    # Execute
    DictReader._eval_expressions(dict)
    dict_out = dict.data

    # Assert references have been resolved
    assert dict_out["expressions"]["reference"]["value"] == 3.0  # 3.0
    assert dict_out["expressions"]["expression1"]["value"] == 4.0  # 4.0
    assert dict_out["expressions"]["expression2"]["value"] == 11.0  # 7.0 + 4
    assert dict_out["expressions"]["expression3"]["value"] == 7.66  # 7.0 + 0.66
    assert dict_out["expressions"]["expressionE"]["value"] == 0.1  # paramE[0]
    assert dict_out["expressions"]["expressionF"]["value"] == 0.3  # paramF[0][0]
    assert dict_out["expressions"]["expressionG1"]["value"] == [
        [10, "fancy", 3.14, "s"],
        ["more", 2, "come"],
    ]  # paramG
    assert dict_out["expressions"]["expressionG2"]["value"] == [
        10,
        "fancy",
        3.14,
        "s",
    ]  # paramG[0]
    assert dict_out["expressions"]["expressionG3"]["value"] == "come"  # paramG[1][2]


def test_eval_expressions_with_included_keys():
    # sourcery skip: avoid-builtin-shadow
    # test keys with the same name as included keys
    # Prepare
    source_file = Path("test_dictReader_dict")

    # Execute
    dict = DictReader.read(source_file, includes=True)
    dict_out = dict.data

    # Assert root keys
    assert dict_out["keyA"] == 3.0  # $paramA
    assert dict_out["keyB"] == 4.0  # "$paramB"
    assert dict_out["keyC"] == 7.0  # "$paramC"
    assert dict_out["keyD"] == 4.16  # "$paramD+$paramC/2"
    assert dict_out["keyE"] == 6.67  # "$paramC-$paramD/2"
    assert dict_out["keyF"] == 8.98  # "3 * $paramD + $paramC"
    assert dict_out["keyG"] == 20.34  # "3 * $paramC - $paramD"
    assert dict_out["keyH"] == 0.2  # "$paramE[1]"
    assert dict_out["keyI"] == [0.1, 0.2, 0.4]  # "$paramE"
    assert dict_out["keyJ"] == 8.1  # "$paramF[1][1]"
    assert dict_out["keyK"] == [2.7, 8.1]  # "$paramF[1]"
    assert dict_out["keyL"] == [[0.3, 0.9], [2.7, 8.1]]  # "$paramF"
    assert dict_out["keyM"] == 9.0  # "3 * $paramA"
    assert dict_out["keyN"] == 7.0  # "$paramA + $paramB"

    # Assert different key names
    assert dict_out["differentKeyNames"]["keyA"] == 3.0  # $paramA
    assert dict_out["differentKeyNames"]["keyB"] == 4.0  # "$paramB"
    assert dict_out["differentKeyNames"]["keyC"] == 7.0  # "$paramC"
    assert dict_out["differentKeyNames"]["keyD"] == 4.16  # "$paramD+$paramC/2"
    assert dict_out["differentKeyNames"]["keyE"] == 6.67  # "$paramC-$paramD/2"
    assert dict_out["differentKeyNames"]["keyF"] == 8.98  # "3 * $paramD + $paramC"
    assert dict_out["differentKeyNames"]["keyG"] == 20.34  # "3 * $paramC - $paramD"
    assert dict_out["differentKeyNames"]["keyH"] == 0.2  # "$paramE[1]"
    assert dict_out["differentKeyNames"]["keyI"] == [0.1, 0.2, 0.4]  # "$paramE"
    assert dict_out["differentKeyNames"]["keyJ"] == 8.1  # "$paramF[1][1]"
    assert dict_out["differentKeyNames"]["keyK"] == [2.7, 8.1]  # "$paramF[1]"
    assert dict_out["differentKeyNames"]["keyL"] == [
        [0.3, 0.9],
        [2.7, 8.1],
    ]  # "$paramF"
    assert dict_out["differentKeyNames"]["keyM"] == 9.0  # "3 * $paramA"
    assert dict_out["differentKeyNames"]["keyN"] == 7.0  # "$paramA + $paramB"

    # Assert same key name as reference name
    # Be aware that in the nested dict 'sameKeyNames', paramD becomes reaasigned.
    # This overwrites paramD from included dict due to the flat lookup table provided through dict.variables
    assert dict_out["sameKeyNames"]["paramA"] == 3.0  # $paramA;
    assert dict_out["sameKeyNames"]["paramB"] == 4.0  # "$paramB";
    assert dict_out["sameKeyNames"]["paramC"] == 7.0  # "$paramC";
    assert dict_out["sameKeyNames"]["paramD"] == 10.5  # "$paramC+$paramC/2";
    assert dict_out["sameKeyNames"]["paramE"] == 0.2  # "$paramE[1]";
    assert dict_out["sameKeyNames"]["paramF"] == [[0.3, 0.9], [2.7, 8.1]]  # "$paramF";

    # Assert references to variables in deeper structure of the included dict
    assert dict_out["keysWithNestedRefs"]["nestKeyA"] == 3.0  # $paramA;
    assert dict_out["keysWithNestedRefs"]["nestKeyB"] == 4.0  # "$paramB";
    assert dict_out["keysWithNestedRefs"]["nestKeyC"] == 12.0  # "$paramA * $paramB";
    assert dict_out["keysWithNestedRefs"]["nestKeyD"] == 35.4  # "$paramC / $paramE[1] + $paramE[2]";
    assert dict_out["keysWithNestedRefs"]["nestKeyE"] == 0.4  # "$paramE[2]";
    assert dict_out["keysWithNestedRefs"]["nestKeyF"] == [
        [0.3, 0.9],
        [2.7, 8.1],
    ]  # "$paramF";
    assert dict_out["keysWithNestedRefs"]["nestKeyH"] == 1.2  # "$paramH";
    assert dict_out["keysWithNestedRefs"]["nestKeyI"] == 3.4  # "$paramI[1]";
    assert dict_out["keysWithNestedRefs"]["nestKeyJ"] == 5.6  # "$paramJ[0][1]";
    assert dict_out["keysWithNestedRefs"]["nestParamA"] == 3.0  # "$paramA";
    assert dict_out["keysWithNestedRefs"]["nestParamB"] == 4.0  # "$paramB";
    assert dict_out["keysWithNestedRefs"]["nestParamC"] == 7.0  # "$paramC";
    assert dict_out["keysWithNestedRefs"]["nestParamD"] == 0.66  # "$paramD";
    assert dict_out["keysWithNestedRefs"]["nestParamE"] == [0.1, 0.2, 0.4]  # "$paramE";
    assert dict_out["keysWithNestedRefs"]["nestParamF"] == 0.3  # "$paramF[0][0]";
    assert dict_out["keysWithNestedRefs"]["nestParamH"] == 1.2  # "$paramH";
    assert dict_out["keysWithNestedRefs"]["nestParamI"] == [2.3, 3.4]  # "$paramI";
    assert dict_out["keysWithNestedRefs"]["nestParamJ"] == [
        [4.5, 5.6],
        [6.7, 7.8],
    ]  # "$paramJ";
    assert dict_out["keysWithNestedRefs"]["nestParamK"] == 0.4  # "$nestKeyE" == "$paramE[2]";
    assert dict_out["keysWithNestedRefs"]["nestParamL"] == 7.0  # "$paramE[2] * 10 + $paramA";
    assert dict_out["keysWithNestedRefs"]["nestParamM"] == 14.8  # "$nestParamJ[1][1] + $paramC";

    # Assert keys that do not point to a single expression, but a list of expressions
    assert dict_out["keysPointingToAListOfExpressions"]["keyToListA"][0] == 3.0  # $paramA;
    assert dict_out["keysPointingToAListOfExpressions"]["keyToListA"][1] == 1
    assert dict_out["keysPointingToAListOfExpressions"]["keyToListA"][2] == 2
    assert dict_out["keysPointingToAListOfExpressions"]["keyToListB"][0] == 4.0  # "$paramB";
    assert dict_out["keysPointingToAListOfExpressions"]["keyToListL"][0] == 14.8  # "$nestParamJ[1][1] + $paramC";


def test_eval_expressions_with_included_numpy_expressions():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_dict")

    # Execute
    dict = DictReader.read(source_file, includes=True)
    dict_out = dict.data
    assert dict_out["keysContainingNumpyExpressions"]["npKeyA"] == 2

    assert_array_equal(dict_out["keysContainingNumpyExpressions"]["npKeyB"], [[1, 1], [1, 1]])

    assert_array_equal(dict_out["keysContainingNumpyExpressions"]["npKeyC"], [2, 2, 2])

    assert_array_equal(
        dict_out["keysContainingNumpyExpressions"]["npKeyD"],
        [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
    )

    assert_array_equal(
        dict_out["keysContainingNumpyExpressions"]["npKeyE"],
        [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
    )

    assert_array_equal(dict_out["keysContainingNumpyExpressions"]["npKeyZ"], [[0, 0, 0, 0]])


def test_reread_string_literals():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_dict")
    parsed_file = Path(f"parsed.{source_file.name}")
    parsed_file.unlink(missing_ok=True)
    dict = DictReader.read(source_file, includes=True)
    DictWriter.write(dict, parsed_file)
    assert parsed_file.exists()
    # Execute
    reread_dict = DictReader.read(parsed_file)
    # Asset that string literals containing the '$' character are written back and reread with surrounding single quotes.
    # This to avoid that a string literal with single quotes that contains a '$' character gets unintentionally evaluated as expression
    # when rereading a parsed dict.
    assert dict.data["differentKeyNames"] == reread_dict.data["differentKeyNames"]
    assert dict.data["sameKeyNames"] == reread_dict.data["sameKeyNames"]
    # Clean up
    parsed_file.unlink()


# @TODO: To be implemented
@pytest.mark.skip(reason="To be implemented")
def test_remove_comment_keys():
    pass


# @TODO: To be implemented
@pytest.mark.skip(reason="To be implemented")
def test_remove_include_keys():
    pass


def test_read_dict():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_dict")
    # Execute
    dict = DictReader.read(source_file)
    # Assert included dict has been merged
    assert dict["paramA"] == 3.0
    assert dict["paramB"] == 4.0
    assert dict["paramC"] == 7.0
    assert dict["paramD"] == 0.66
    assert dict["paramE"] == [0.1, 0.2, 0.4]
    assert dict["paramF"] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict["paramG"] == [[10, "fancy", 3.14, "s"], ["more", 2, "come"]]
    # Assert references and expressions have been resolved
    assert dict["keyA"] == 3.0
    assert dict["keyB"] == 4.0
    assert dict["keyC"] == 7.0
    assert dict["keyD"] == 4.16
    assert dict["keyE"] == 6.67
    assert dict["keyF"] == 8.98
    assert dict["keyG"] == 20.34
    assert dict["keyH"] == 0.2
    assert dict["keyI"] == [0.1, 0.2, 0.4]
    assert dict["keyJ"] == 8.1
    assert dict["keyK"] == [2.7, 8.1]
    assert dict["keyL"] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict["keyM"] == 9.0
    assert dict["keyN"] == 7.0


def test_read_json():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_json.json")
    # Execute
    dict = DictReader.read(source_file)
    # Assert included dict has been merged
    assert dict["paramA"] == 3.0
    assert dict["paramB"] == 4.0
    assert dict["paramC"] == 7.0
    assert dict["paramD"] == 0.66
    assert dict["paramE"] == [0.1, 0.2, 0.4]
    assert dict["paramF"] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict["paramG"] == [[10, "fancy", 3.14, "s"], ["more", 2, "come"]]
    # Assert references and expressions have been resolved
    assert dict["keyA"] == 3.0
    assert dict["keyB"] == 4.0
    assert dict["keyC"] == 7.0
    assert dict["keyD"] == 4.16
    assert dict["keyE"] == 6.67
    assert dict["keyF"] == 8.98
    assert dict["keyG"] == 20.34
    assert dict["keyH"] == 0.2
    assert dict["keyI"] == [0.1, 0.2, 0.4]
    assert dict["keyJ"] == 8.1
    assert dict["keyK"] == [2.7, 8.1]
    assert dict["keyL"] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict["keyM"] == 9.0
    assert dict["keyN"] == 7.0


def test_compare_expressions_in_dict_format_with_expressions_in_json_format():
    # sourcery skip: no-loop-in-tests
    # Prepare
    source_file_dict = Path("test_dictReader_dict")
    source_file_json = Path("test_dictReader_json.json")
    # Execute
    dict_dict = DictReader.read(source_file_dict)
    dict_json = DictReader.read(source_file_json)
    # Assert
    assert dict_dict.expressions == dict_json.expressions
    # Collect all references contained in expressions
    references_dict: List[str] = _get_references_in_expressions(dict_dict)
    references_json: List[str] = _get_references_in_expressions(dict_json)
    assert references_dict == references_json
    references_resolved_dict = _resolve_references(dict_dict, references_dict)
    references_resolved_json = _resolve_references(dict_json, references_json)
    assert references_resolved_dict == references_resolved_json
    # assert dict_dict.variables == dict_json.variables
    for dvs, jvs in zip(dict_dict.variables, dict_json.variables):
        assert_array_equal(dvs, jvs)


def _get_references_in_expressions(dict: CppDict) -> List[str]:
    references: List[str] = []
    for item in dict.expressions.values():
        _refs: List[str] = re.findall(r"\$\w[\w\[\]]+", item["expression"])
        references.extend(_refs)
    return references


def _resolve_references(dict: CppDict, references: List[str]) -> Dict[str, Union[Any, None]]:
    # Resolve references
    variables: Dict[str, Any] = dict.variables
    references_resolved = {ref: DictReader._resolve_reference(ref, variables) for ref in references}

    return {
        ref: value
        for ref, value in references_resolved.items()
        if (value is not None) and (not re.search(r"EXPRESSION|\$", str(value)))
    }


def test_read_foam():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_foam")
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert dict["Re_profile"] == 1000000.0
    assert dict["mag_U_infty"] == 1.004


def test_read_xml():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("test_dictReader_xml.xml")
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert "_xmlOpts" in dict
    assert len(dict["_xmlOpts"]["_nameSpaces"]) == 1
    assert dict["_xmlOpts"]["_nameSpaces"]["xs"] == "http://www.w3.org/2001/XMLSchema"
    assert len(dict["_xmlOpts"]["_rootAttributes"]) == 1
    assert dict["_xmlOpts"]["_rootTag"] == "ROOT"
    assert dict["_xmlOpts"]["_rootAttributes"]["version"] == "0.1"
    assert dict["_xmlOpts"]["_addNodeNumbering"] is True


@WindowsOnly
def test_read_dict_in_subfolder_bsl():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path.cwd() / "subfolder" / "test_subfolder_dict_bsl"
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert dict["valueA"] == 1  # paramA is defined in paramDict_bsl
    assert dict["valueB"] == "$paramB"  # paramB is defined in paramDict_fsl


def test_read_dict_in_subfolder_fsl():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path.cwd() / "subfolder" / "test_subfolder_dict_fsl"
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert dict["valueA"] == "$paramA"  # paramA is defined in paramDict_bsl
    assert dict["valueB"] == 2  # paramB is defined in paramDict_fsl


def test_read_dict_in_subfolder_source_file_given_as_str():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path.cwd().absolute() / "subfolder" / "test_subfolder_dict_fsl"
    source_file_as_str = str(source_file)
    # Execute
    dict = DictReader.read(source_file_as_str)
    # Assert
    assert dict["valueB"] == 2


def test_read_dict_in_subfolder_source_file_given_as_purepath():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path.cwd().absolute() / "subfolder" / "test_subfolder_dict_fsl"
    source_file_as_purepath = PurePath(str(source_file))
    # Execute
    dict = DictReader.read(source_file_as_purepath)
    # Assert
    assert dict["valueB"] == 2  # paramB is defined in paramDict_fsl


def test_read_dict_in_subfolder_parsed_via_dictparser_cli():
    # Prepare
    source_file = "subfolder/test_subfolder_dict_fsl"
    parsed_file = Path("subfolder/parsed.test_subfolder_dict_fsl")
    parsed_file_foam = Path("subfolder/parsed.test_subfolder_dict_fsl.foam")
    parsed_file.unlink(missing_ok=True)
    parsed_file_foam.unlink(missing_ok=True)
    # Execute
    _ = os.system(f"python -m dictIO.cli.dictParser --quiet {source_file}")
    # Assert
    assert parsed_file.exists()
    assert not parsed_file_foam.exists()
    # Clean up
    parsed_file.unlink()
    # Execute
    _ = os.system(f"python -m dictIO.cli.dictParser --quiet --output=foam {source_file}")
    # Assert
    assert not parsed_file.exists()
    assert parsed_file_foam.exists()
    # Clean up
    parsed_file_foam.unlink()


def test_read_circular_includes():
    # sourcery skip: avoid-builtin-shadow
    # Prepare
    source_file = Path("circular_include/test_base_dict")
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert dict["baseSubDict"]["baseVar1"] == 2
    assert dict["baseSubDict"]["baseVar2"] == 2
    assert dict["baseSubDict"]["baseVar3"] == 4
    assert dict["baseSubDict"]["baseVar4"] == 8
    assert dict["baseSubDict"]["baseVar5"] == 8


def test_read_circular_includes_log_warning(caplog: LogCaptureFixture):
    # Prepare
    source_file = Path("circular_include/test_base_dict")
    log_level_expected = "WARNING"
    log_message_expected = "Recursive include detected. Merging of test_ref1_dict->test_ref2_dict->test_base_dict->test_ref1_dict into test_base_dict aborted."
    # Execute
    _ = DictReader.read(source_file)
    # Assert
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == log_level_expected
    assert caplog.records[0].message == log_message_expected


class SetupHelper:
    @staticmethod
    def prepare_dict_until(
        dict_to_prepare: CppDict,
        until_step: int = -1,
        file_to_read: str = "test_dictReader_dict",
    ):
        file_name = Path.cwd() / file_to_read

        parser = CppParser()
        _ = parser.parse_file(file_name, dict_to_prepare)

        funcs = [
            (DictReader._merge_includes, dict_to_prepare),  # Step 00
            (DictReader._eval_expressions, dict_to_prepare),  # Step 01
        ]

        for i in range(until_step + 1):
            funcs[i][0](*funcs[i][1:])
        return
