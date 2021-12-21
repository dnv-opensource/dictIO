import os
from copy import deepcopy
from pathlib import Path, PurePath

import pytest
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name
from dictIO.parser import CppParser
from dictIO.utils.path import silent_remove


def test_merge_includes():  # sourcery skip: class-extract-method
                            # Prepare dict until and including parse_tokenized_dict()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict_to_prepare=dict)
    dict_in = deepcopy(dict.data)
                            # Preparations done.
                            # Now start the actual test
    assert dict_in['references']['reference']['value'][:10] == 'EXPRESSION'
    assert dict_in['references']['expression1']['value'][:10] == 'EXPRESSION'
    assert dict_in['references']['expression2']['value'][:10] == 'EXPRESSION'
    assert dict_in['references']['expression3']['value'][:10] == 'EXPRESSION'
    DictReader._merge_includes(dict)
    dict_out = dict.data
                            # check whether test_dictReader_paramDict has been merged
    assert len(dict_out) == len(dict_in) + 8
    assert dict_out['paramA'] == 3.0
    assert dict_out['paramB'] == 4.0
    assert dict_out['paramC'] == 7.0
    assert dict_out['paramD'] == 0.66
    assert dict_out['paramE'] == [0.1, 0.2, 0.4]
    assert dict_out['paramF'] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict_out['paramG'] == [[10, 'fancy', 3.14, 's'], ['more', 2, 'come']]


def test_resolve_reference():
    # Prepare dict until and including ()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict_to_prepare=dict, until_step=0)
    # test resolution of non-indexed references
    assert DictReader._resolve_reference('$paramA', dict) == 3.0
    assert DictReader._resolve_reference('$paramB', dict) == 4.0
    assert DictReader._resolve_reference('$paramC', dict) == 7.0
    assert DictReader._resolve_reference('$paramD', dict) == 0.66
    assert DictReader._resolve_reference('$paramE[0]', dict.variables) == 0.1

    paramE = DictReader._resolve_reference('$paramE', dict)     # noqa: N806
    assert isinstance(paramE, list)
    assert len(paramE) == 3
    assert paramE[0] == 0.1
    assert paramE[1] == 0.2
    assert paramE[2] == 0.4
    paramF = DictReader._resolve_reference('$paramF', dict)     # noqa: N806
    assert isinstance(paramF, list)
    assert len(paramF) == 2
    assert len(paramF[0]) == 2
    assert len(paramF[1]) == 2
    assert paramF[0][0] == 0.3
    assert paramF[0][1] == 0.9
    assert paramF[1][0] == 2.7
    assert paramF[1][1] == 8.1
    paramG = DictReader._resolve_reference('$paramG', dict)     # noqa: N806
    assert isinstance(paramG, list)
    assert len(paramG) == 2
    assert len(paramG[0]) == 4
    assert len(paramG[1]) == 3
    assert paramG[0][0] == 10
    assert paramG[0][1] == 'fancy'
    assert paramG[0][2] == 3.14
    assert paramG[0][3] == 's'
    assert paramG[1][0] == 'more'
    assert paramG[1][1] == 2
    assert paramG[1][2] == 'come'

    # test resolution of indexed references
    assert DictReader._resolve_reference('$paramE[0]', dict) == 0.1
    assert DictReader._resolve_reference('$paramE[1]', dict) == 0.2
    assert DictReader._resolve_reference('$paramE[2]', dict) == 0.4
    assert DictReader._resolve_reference('$paramF[0][0]', dict) == 0.3
    assert DictReader._resolve_reference('$paramF[0][1]', dict) == 0.9
    assert DictReader._resolve_reference('$paramF[1][0]', dict) == 2.7
    assert DictReader._resolve_reference('$paramF[1][1]', dict) == 8.1
    assert DictReader._resolve_reference('$paramG[0][0]', dict) == 10
    assert DictReader._resolve_reference('$paramG[0][1]', dict) == 'fancy'
    assert DictReader._resolve_reference('$paramG[0][2]', dict) == 3.14
    assert DictReader._resolve_reference('$paramG[0][3]', dict) == 's'
    assert DictReader._resolve_reference('$paramG[1][0]', dict) == 'more'
    assert DictReader._resolve_reference('$paramG[1][1]', dict) == 2
    assert DictReader._resolve_reference('$paramG[1][2]', dict) == 'come'


def test_eval_expressions():
    # Prepare dict until and including ()
    dict = CppDict()
    SetupHelper.prepare_dict_until(dict_to_prepare=dict, until_step=0)
    dict_in = deepcopy(dict.data)
    assert dict_in['references']['reference']['value'][:10] == 'EXPRESSION'             # $paramA
    assert dict_in['references']['expression1']['value'][:10] == 'EXPRESSION'           # "$paramB"
    assert dict_in['references']['expression2']['value'][:10] == 'EXPRESSION'           # "$paramC + 4"
    assert dict_in['references']['expression3']['value'][:10] == 'EXPRESSION'           # "$paramC + $paramD"
    assert dict_in['references']['expressionE']['value'][:10] == 'EXPRESSION'           # $paramE[0]
    assert dict_in['references']['expressionF']['value'][:10] == 'EXPRESSION'           # $paramF[0][0]
    assert dict_in['references']['expressionG1']['value'][:10] == 'EXPRESSION'          # "$paramG"
    assert dict_in['references']['expressionG2']['value'][:10] == 'EXPRESSION'          # "$paramG[0]"
    assert dict_in['references']['expressionG3']['value'][:10] == 'EXPRESSION'          # "$paramG[1][2]"
                                                                                        # Preparations done.
    DictReader._eval_expressions(dict)
    dict_out = dict.data
                                                                                        # check whether references have been resolved
    assert dict_out['references']['reference']['value'] == 3.0                          # 3.0
    assert dict_out['references']['expression1']['value'] == 4.0                        # 4.0
    assert dict_out['references']['expression2']['value'] == 11.0                       # 7.0 + 4
    assert dict_out['references']['expression3']['value'] == 7.66                       # 7.0 + 0.66
    assert dict_out['references']['expressionE']['value'] == 0.1                        # paramE[0]
    assert dict_out['references']['expressionF']['value'] == 0.3                        # paramF[0][0]
    assert dict_out['references']['expressionG1']['value'] == [
        [10, 'fancy', 3.14, 's'], ['more', 2, 'come']
    ]                                                                                   # paramG
    assert dict_out['references']['expressionG2']['value'] == [10, 'fancy', 3.14, 's']  # paramG[0]
    assert dict_out['references']['expressionG3']['value'] == 'come'                    # paramG[1][2]


def test_eval_expressions_with_included_keys():
    # test keys with the same name as included keys
    file_name = Path('test_dictReader_dict')
    dict = DictReader.read(file_name, includes=True)
    dict_out = dict.data

    # root keys
    assert dict_out['keyA'] == 3.0                          # $paramA
    assert dict_out['keyB'] == 4.0                          # "$paramB"
    assert dict_out['keyC'] == 7.0                          # "$paramC"
    assert dict_out['keyD'] == 4.16                         # "$paramD+$paramC/2"
    assert dict_out['keyE'] == 6.67                         # "$paramC-$paramD/2"
    assert dict_out['keyF'] == 8.98                         # "3 * $paramD + $paramC"
    assert dict_out['keyG'] == 20.34                        # "3 * $paramC - $paramD"
    assert dict_out['keyH'] == 0.2                          # "$paramE[1]"
    assert dict_out['keyI'] == [0.1, 0.2, 0.4]              # "$paramE"
    assert dict_out['keyJ'] == 8.1                          # "$paramF[1][1]"
    assert dict_out['keyK'] == [2.7, 8.1]                   # "$paramF[1]"
    assert dict_out['keyL'] == [[0.3, 0.9], [2.7, 8.1]]     # "$paramF"
    assert dict_out['keyM'] == 9.0                          # "3 * $paramA"
    assert dict_out['keyN'] == 7.0                          # "$paramA + $paramB"

    # different key names
    assert dict_out['differentKeyNames']['keyA'] == 3.0                         # $paramA
    assert dict_out['differentKeyNames']['keyB'] == 4.0                         # "$paramB"
    assert dict_out['differentKeyNames']['keyC'] == 7.0                         # "$paramC"
    assert dict_out['differentKeyNames']['keyD'] == 4.16                        # "$paramD+$paramC/2"
    assert dict_out['differentKeyNames']['keyE'] == 6.67                        # "$paramC-$paramD/2"
    assert dict_out['differentKeyNames']['keyF'] == 8.98                        # "3 * $paramD + $paramC"
    assert dict_out['differentKeyNames']['keyG'] == 20.34                       # "3 * $paramC - $paramD"
    assert dict_out['differentKeyNames']['keyH'] == 0.2                         # "$paramE[1]"
    assert dict_out['differentKeyNames']['keyI'] == [0.1, 0.2, 0.4]             # "$paramE"
    assert dict_out['differentKeyNames']['keyJ'] == 8.1                         # "$paramF[1][1]"
    assert dict_out['differentKeyNames']['keyK'] == [2.7, 8.1]                  # "$paramF[1]"
    assert dict_out['differentKeyNames']['keyL'] == [[0.3, 0.9], [2.7, 8.1]]    # "$paramF"
    assert dict_out['differentKeyNames']['keyM'] == 9.0                         # "3 * $paramA"
    assert dict_out['differentKeyNames']['keyN'] == 7.0                         # "$paramA + $paramB"

    # same key name as reference name
    # Be aware that in the nested dict 'sameKeyNames', paramD becomes reaasigned.
    # This overwrites paramD from included dict due to the flat lookup table provided through dict.variables
    assert dict_out['sameKeyNames']['paramA'] == 3.0                        # $paramA;
    assert dict_out['sameKeyNames']['paramB'] == 4.0                        # "$paramB";
    assert dict_out['sameKeyNames']['paramC'] == 7.0                        # "$paramC";
    assert dict_out['sameKeyNames']['paramD'] == 10.5                       # "$paramC+$paramC/2";
    assert dict_out['sameKeyNames']['paramE'] == 0.2                        # "$paramE[1]";
    assert dict_out['sameKeyNames']['paramF'] == [[0.3, 0.9], [2.7, 8.1]]   # "$paramF";

    # here comes the test for references, what are in a deeper structure of the included dict
    assert dict_out['keysWithNestedRefs']['nestKeyA'] == 3.0                            # $paramA;
    assert dict_out['keysWithNestedRefs']['nestKeyB'] == 4.0                            # "$paramB";
    assert dict_out['keysWithNestedRefs']['nestKeyC'] == 12.0                           # "$paramA * $paramB";
    assert dict_out['keysWithNestedRefs']['nestKeyD'] == 35.4                           # "$paramC / $paramE[1] + $paramE[2]";
    assert dict_out['keysWithNestedRefs']['nestKeyE'] == 0.4                            # "$paramE[2]";
    assert dict_out['keysWithNestedRefs']['nestKeyF'] == [[0.3, 0.9], [2.7, 8.1]]       # "$paramF";
    assert dict_out['keysWithNestedRefs']['nestKeyH'] == 1.2                            # "$paramH";
    assert dict_out['keysWithNestedRefs']['nestKeyI'] == 3.4                            # "$paramI[1]";
    assert dict_out['keysWithNestedRefs']['nestKeyJ'] == 5.6                            # "$paramJ[0][1]";
    assert dict_out['keysWithNestedRefs']['nestParamA'] == 3.0                          # "$paramA";
    assert dict_out['keysWithNestedRefs']['nestParamB'] == 4.0                          # "$paramB";
    assert dict_out['keysWithNestedRefs']['nestParamC'] == 7.0                          # "$paramC";
    assert dict_out['keysWithNestedRefs']['nestParamD'] == 0.66                         # "$paramD";
    assert dict_out['keysWithNestedRefs']['nestParamE'] == [0.1, 0.2, 0.4]              # "$paramE";
    assert dict_out['keysWithNestedRefs']['nestParamF'] == 0.3                          # "$paramF[0][0]";
    assert dict_out['keysWithNestedRefs']['nestParamH'] == 1.2                          # "$paramH";
    assert dict_out['keysWithNestedRefs']['nestParamI'] == [2.3, 3.4]                   # "$paramI";
    assert dict_out['keysWithNestedRefs']['nestParamJ'] == [[4.5, 5.6], [6.7, 7.8]]     # "$paramJ";
    assert dict_out['keysWithNestedRefs']['nestParamK'] == 0.4                          # "$nestKeyE" == "$paramE[2]";
    assert dict_out['keysWithNestedRefs']['nestParamL'] == 7.0                          # "$paramE[2] * 10 + $paramA";
    assert dict_out['keysWithNestedRefs']['nestParamM'] == 14.8                         # "$nestParamJ[1][1] + $paramC";

    # keys that do not point to a single expression, but a list of expressions
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][0] == 3.0     # $paramA;
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][1] == 1
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][2] == 2
    assert dict_out['keysPointingToAListOfExpressions']['keyToListB'][0] == 4.0     # "$paramB";
    assert dict_out['keysPointingToAListOfExpressions']['keyToListL'][
        0] == 14.8                                                                  # "$nestParamJ[1][1] + $paramC";


def test_reread_string_literals():
    # test keys with the same name as imported keys
    file_name = Path('test_dictReader_dict')
    dict = DictReader.read(file_name, includes=True)
    parsed_file_name = create_target_file_name(file_name, 'parsed')
    silent_remove(parsed_file_name)
    DictWriter.write(dict, parsed_file_name)
    assert os.path.exists(parsed_file_name)
    # Assure that string literals that contain the '$' character are written back and reread with surrounding single quotes.
    # This to avoid that a string literal with single quotes that contains a '$' character gets unintentionally evaluated as expression
    # when rereading a parsed dict.
    parsed_dict = DictReader.read(Path(parsed_file_name))
    assert dict.data['differentKeyNames'] == parsed_dict.data['differentKeyNames']
    assert dict.data['sameKeyNames'] == parsed_dict.data['sameKeyNames']
    silent_remove(parsed_file_name)


# @TODO: To be implemented
def test_remove_comment_keys():
    pass


# @TODO: To be implemented
def test_remove_include_keys():
    pass


# def test_read_config_dict():
#     silentRemove('parsed.test_dictReader_paramDict')
#     silentRemove('parsed.test_dict')
#     file_name = Path('test_dict')
#     dict = DictReader.read(file_name)
#     assert not os.path.exists('parsed.test_dictReader_paramDict')
#     assert not os.path.exists('parsed.test_dict')
#     dict = DictReader.read(file_name)
#     assert not os.path.exists('parsed.test_dictReader_paramDict')
#     assert os.path.exists('parsed.test_dict')


def test_reread_parsed_dict():
    # Prepare
    source_file = Path('test_dictReader_dict')
    parsed_file = Path('parsed.test_dictReader_dict')
    parsed_file_paramDict = Path('parsed.test_dictReader_Paramdict')
    parsed_file_wrong = Path('parsed.parsed.test_dictReader_dict')
    parsed_file_paramDict_wrong = Path('parsed.parsed.test_dictReader_Paramdict')
    silent_remove(parsed_file)
    silent_remove(parsed_file_paramDict)
    silent_remove(parsed_file_wrong)
    silent_remove(parsed_file_paramDict_wrong)

    dict = DictReader.read(source_file)
    parsed_file_name = create_target_file_name(source_file, 'parsed')
    silent_remove(parsed_file_name)
    DictWriter.write(dict, parsed_file_name)
    assert parsed_file.exists()
    assert not parsed_file_paramDict.exists()
    source_file = parsed_file
    dict = DictReader.read(source_file)
    assert parsed_file.exists()
    assert not parsed_file_paramDict.exists()
    # no piping parsed prefix anymore: parsed.parsed.test_dictReader_dict
    assert not os.path.exists('parsed.parsed.test_dictReader_dict')
    assert not os.path.exists('parsed.parsed.test_dictReader_Paramdict')
    silent_remove(parsed_file_name)


def test_read_foam():
    # Prepare
    source_file = Path('test_dictReader_foam')
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert dict['Re_profile'] == 1000000.0
    assert dict['mag_U_infty'] == 1.004


def test_read_xml():
    # Prepare
    source_file = Path('test_dictReader_xml.xml')
    # Execute
    dict = DictReader.read(source_file)
    # Assert
    assert '_xmlOpts' in dict
    assert len(dict['_xmlOpts']['_nameSpaces']) == 1
    assert dict['_xmlOpts']['_nameSpaces']['xs'] == 'http://www.w3.org/2001/XMLSchema'
    assert len(dict['_xmlOpts']['_rootAttributes']) == 1
    assert dict['_xmlOpts']['_rootTag'] == 'ROOT'
    assert dict['_xmlOpts']['_rootAttributes']['version'] == '0.1'
    assert dict['_xmlOpts']['_addNodeNumbering'] is True


def test_read_dict_in_subfolder():
    source_file = Path.cwd() / 'subfolder' / 'test_subfolder_dict'
    dict_in = DictReader.read(source_file)
    assert dict_in['valueA'] == 1
    assert dict_in['valueB'] == 2


def test_read_dict_in_subfolder_source_file_given_as_str():
    source_file_as_path = Path.cwd() / 'subfolder' / 'test_subfolder_dict'
    source_file_as_str = str(source_file_as_path)
    dict_in = DictReader.read(source_file_as_str)
    assert dict_in['valueA'] == 1
    assert dict_in['valueB'] == 2


def test_read_dict_in_subfolder_source_file_given_as_purepath():
    source_file_as_path = Path.cwd() / 'subfolder' / 'test_subfolder_dict'
    source_file_as_purepath = PurePath(str(source_file_as_path))
    dict_in = DictReader.read(source_file_as_purepath)
    assert dict_in['valueA'] == 1
    assert dict_in['valueB'] == 2


def test_read_dict_in_subfolder_parsed_via_dictparser_cli():
    file_name = 'subfolder/test_subfolder_dict'
    silent_remove(Path('subfolder/parsed.test_subfolder_dict'))
    silent_remove(Path('subfolder/parsed.test_subfolder_dict.foam'))
    # os.system(f'..\\src\\dictIO\\cli\\dictParser.py --quiet {file_name}')
    os.system(f' python -m dictIO.cli.dictParser --quiet {file_name}')
    assert os.path.exists('subfolder/parsed.test_subfolder_dict')
    assert not os.path.exists('subfolder/parsed.test_subfolder_dict.foam')
    silent_remove(Path('subfolder/parsed.test_subfolder_dict'))
    # os.system(f'..\\src\\dictIO\\cli\\dictParser.py --quiet --output=foam {file_name}')
    os.system(f' python -m dictIO.cli.dictParser --quiet --output=foam {file_name}')
    assert not os.path.exists('subfolder/parsed.test_subfolder_dict')
    assert os.path.exists('subfolder/parsed.test_subfolder_dict.foam')
    silent_remove(Path('subfolder/parsed.test_subfolder_dict.foam'))


class SetupHelper():

    @staticmethod
    def prepare_dict_until(
        dict_to_prepare: CppDict,
        until_step=-1,
        file_to_read='test_dictReader_dict',
    ):

        file_name = Path.cwd() / file_to_read

        parser = CppParser()
        parser.parse_file(file_name, dict_to_prepare)

        funcs = [
            (DictReader._merge_includes, dict_to_prepare),      # Step 00
            (DictReader._eval_expressions, dict_to_prepare),    # Step 01
        ]

        for i in range(until_step + 1):
            funcs[i][0](*funcs[i][1:])
        return dict_to_prepare
