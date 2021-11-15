import os
from copy import deepcopy
from pathlib import Path, PurePath

import pytest
from dictIO.cppDict import CppDict
from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name
from dictIO.parser import CppParser
from dictIO.utils.path import silent_remove


@pytest.fixture()
def parsed_dict():
    # remove if exists
    silent_remove(Path('parsed.test_mergeDict'))
    # generate one with certain key in it
    parsed_dict = {'key00': {'key10': {'key20': 'val20'}}}
    DictWriter.write(parsed_dict, Path('parsed.test_mergeDict'))
    return


def test_merge_includes():  # sourcery skip: class-extract-method
                            # Prepare dict until and including parse_tokenized_dict()
    dict = CppDict(Path('testDict'))
    SetupHelper.prepare_dict_until(dict_to_prepare=dict)
    dict_in = deepcopy(dict.data)
                            # Preparations done.
                            # Now start the actual test
    assert dict_in['input']['parameterObjects']['parameterA']['value'][:10] == 'EXPRESSION'
    assert dict_in['input']['parameterObjects']['parameterB']['value'][:10] == 'EXPRESSION'
    assert dict_in['input']['parameterObjects']['parameterC']['value'][:10] == 'EXPRESSION'
    assert dict_in['input']['parameterObjects']['parameterD']['value'][:10] == 'EXPRESSION'
    DictReader._merge_includes(dict)
    dict_out = dict.data
                            # check whether test_paramDict has been merged
    assert len(dict_out) == len(dict_in) + 16
    assert dict_out['paramA'] == 4.0
    assert dict_out['paramB'] == 6.0
    assert dict_out['paramC'] == 8.0
    assert dict_out['paramD'] == 0.72
    assert dict_out['paramE'] == [0.1, 0.2, 0.4]
    assert dict_out['paramF'] == [[0.3, 0.9], [2.7, 8.1]]
    assert dict_out['paramG'] == [[10, 'fancy', 3.14, 's'], ['more', 2, 'come']]


def test_resolve_reference():
    # Prepare dict until and including ()
    dict = CppDict(Path('testDict'))
    SetupHelper.prepare_dict_until(dict_to_prepare=dict, until_step=0)
    # test resolution of non-indexed references
    assert DictReader._resolve_reference('$paramA', dict) == 4.0
    assert DictReader._resolve_reference('$paramB', dict) == 6.0
    assert DictReader._resolve_reference('$paramC', dict) == 8.0
    assert DictReader._resolve_reference('$paramD', dict) == 0.72
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
    dict = CppDict(Path('testDict'))
    SetupHelper.prepare_dict_until(dict_to_prepare=dict, until_step=0)
    dict_in = deepcopy(dict.data)
    assert dict_in['input']['parameterObjects']['parameterA']['value'][:10] == 'EXPRESSION'     # $paramA
    assert dict_in['input']['parameterObjects']['parameterB']['value'][:10
                                                                       ] == 'EXPRESSION'        # "$paramB"
    assert dict_in['input']['parameterObjects']['parameterC']['value'
                                                              ][:10] == 'EXPRESSION'            # "$paramC + 4"
    assert dict_in['input']['parameterObjects']['parameterD'][
        'value'][:10] == 'EXPRESSION'                                                           # "$paramC + $paramD"
    assert dict_in['input']['parameterObjects']['parameterE']['value'
                                                              ][:10] == 'EXPRESSION'            # $paramE[0]
    assert dict_in['input']['parameterObjects']['parameterF']['value'
                                                              ][:10] == 'EXPRESSION'            # $paramF[0][0]
    assert dict_in['input']['parameterObjects']['parameterG1'][
        'value'][:10] == 'EXPRESSION'                                                           # "$paramG[1][2]"
    assert dict_in['input']['parameterObjects']['parameterG2']['value'
                                                               ][:10] == 'EXPRESSION'           # "$paramG[0]"
    assert dict_in['input']['parameterObjects']['parameterG3']['value'
                                                               ][:10] == 'EXPRESSION'           # "$paramG"
                                                                                                # Preparations done.
    DictReader._eval_expressions(dict)
    dict_out = dict.data
                                                                                                # check whether references have been resolved
    assert dict_out['input']['parameterObjects']['parameterA']['value'] == 4.0                  # 4.0
    assert dict_out['input']['parameterObjects']['parameterB']['value'] == 6.0                  # 6.0
    assert dict_out['input']['parameterObjects']['parameterC']['value'] == 12.0                 # 8.0 + 4
    assert dict_out['input']['parameterObjects']['parameterD']['value'] == 8.72                 # 8.0 + 0.72
    assert dict_out['input']['parameterObjects']['parameterE']['value'] == 0.1                  # paramE[0]
    assert dict_out['input']['parameterObjects']['parameterF']['value'] == 0.3                  # paramF[0][0]
    assert dict_out['input']['parameterObjects']['parameterG1']['value'] == 'come'              # paramG[1][2]
    assert dict_out['input']['parameterObjects']['parameterG2']['value'] == [
        10, 'fancy', 3.14, 's'
    ]                                                                                           # paramG[0]
    assert dict_out['input']['parameterObjects']['parameterG3']['value'] == [
        [10, 'fancy', 3.14, 's'], ['more', 2, 'come']
    ]                                                                                           # paramG


def test_eval_expressions_with_included_keys():
    # test keys with the same name as included keys
    file_name = Path('test_exprsDict')
    dict = DictReader.read(file_name, includes=True)
    dict_out = dict.data

    # root keys
    assert dict_out['keyA'] == 3.0                          # $paramA
    assert dict_out['keyB'] == 4.0                          # $paramB
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
    assert dict_out['differentKeyNames']['keyB'] == '$paramB'                   # '$paramB'
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
    assert dict_out['sameKeyNames']['paramB'] == '$paramB'                  # '$paramB';
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
    assert dict_out['keysWithNestedRefs']['nestKeyG'] == 1.2                            # "$paramG";
    assert dict_out['keysWithNestedRefs']['nestKeyH'] == 3.4                            # "$paramH[1]";
    assert dict_out['keysWithNestedRefs']['nestKeyI'] == 5.6                            # "$paramI[0][1]";
    assert dict_out['keysWithNestedRefs']['nestParamA'] == 3.0                          # "$paramA";
    assert dict_out['keysWithNestedRefs']['nestParamB'] == 4.0                          # "$paramB";
    assert dict_out['keysWithNestedRefs']['nestParamC'] == 7.0                          # "$paramC";
    assert dict_out['keysWithNestedRefs']['nestParamD'] == 0.66                         # "$paramD";
    assert dict_out['keysWithNestedRefs']['nestParamE'] == [0.1, 0.2, 0.4]              # "$paramE";
    assert dict_out['keysWithNestedRefs']['nestParamF'] == 0.3                          # "$paramF[0][0]";
    assert dict_out['keysWithNestedRefs']['nestParamG'] == 1.2                          # "$paramG";
    assert dict_out['keysWithNestedRefs']['nestParamH'] == [2.3, 3.4]                   # "$paramH";
    assert dict_out['keysWithNestedRefs']['nestParamI'] == [[4.5, 5.6], [6.7, 7.8]]     # "$paramI";
    assert dict_out['keysWithNestedRefs']['nestParamJ'] == 0.4                          # "$nestKeyE" == "$paramE[2]";
    assert dict_out['keysWithNestedRefs']['nestParamK'] == 7.0                          # "$paramE[2] * 10 + $paramA";
    assert dict_out['keysWithNestedRefs']['nestParamL'] == 14.8                         # "$nestParamI[1][1] + $paramC";

    # keys that do not point to a single expression, but a list of expressions
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][0] == 3.0     # $paramA;
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][1] == 1
    assert dict_out['keysPointingToAListOfExpressions']['keyToListA'][2] == 2
    assert dict_out['keysPointingToAListOfExpressions']['keyToListB'][0] == 4.0     # "$paramB";
    assert dict_out['keysPointingToAListOfExpressions']['keyToListL'][
        0] == 14.8                                                                  # "$nestParamI[1][1] + $paramC";


def test_reparse_string_literals():
    # test keys with the same name as imported keys
    file_name = Path('test_exprsDict')
    dict = DictReader.read(file_name, includes=True)
    parsed_file_name = create_target_file_name(file_name, 'parsed')
    silent_remove(parsed_file_name)
    DictWriter.write(dict, parsed_file_name)
    assert os.path.exists(parsed_file_name)
    # Assure that string literals that contain the '$' character are written back and reparsed with surrounding single quotes.
    # This to avoid that a string literal with single quotes that contains a '$' character gets unintentionally evaluated as expression
    # when rereading a parsed dict.
    parsed_dict = DictReader.read(Path(parsed_file_name))
    assert dict.data['differentKeyNames'] == parsed_dict.data['differentKeyNames']
    assert dict.data['sameKeyNames'] == parsed_dict.data['sameKeyNames']


# @TODO: To be implemented
def test_remove_comment_keys():
    pass


# @TODO: To be implemented
def test_remove_include_keys():
    pass


# def test_read_config_dict():
#     silentRemove('parsed.test_paramDict')
#     silentRemove('parsed.test_configDict')
#     file_name = Path('test_configDict')
#     dict = DictReader.read(file_name)
#     assert not os.path.exists('parsed.test_paramDict')
#     assert not os.path.exists('parsed.test_configDict')
#     dict = DictReader.read(file_name)
#     assert not os.path.exists('parsed.test_paramDict')
#     assert os.path.exists('parsed.test_configDict')


def test_reread_parsed_dict():
    silent_remove(Path('parsed.test_paramDict'))
    silent_remove(Path('parsed.test_configDict'))
    silent_remove(Path('parsed.parsed.test_paramDict'))
    silent_remove(Path('parsed.parsed.test_configDict'))
    file_name = Path('test_configDict')
    dict = DictReader.read(file_name)
    parsed_file_name = create_target_file_name(file_name, 'parsed')
    silent_remove(parsed_file_name)
    DictWriter.write(dict, parsed_file_name)
    assert not os.path.exists('parsed.test_paramDict')
    assert os.path.exists('parsed.test_configDict')
    file_name = Path('parsed.test_configDict')
    dict = DictReader.read(file_name)
    assert not os.path.exists('parsed.test_paramDict')
    assert os.path.exists('parsed.test_configDict')
    # no piping parsed prefix anymore: parsed.parsedtest_paramDict
    assert not os.path.exists('parsed.parsed.test_paramDict')
    assert not os.path.exists('parsed.parsed.test_configDict')


def test_dict_from_xml():
    silent_remove(Path('parsed.test_generic.xml'))
    file_name = Path('test_generic.xml')
    dict = DictReader.read(file_name)
    assert '_xmlOpts' in dict
    assert len(dict['_xmlOpts']['_nameSpaces']) == 1
    assert dict['_xmlOpts']['_nameSpaces']['xs'] == 'http://www.w3.org/2001/XMLSchema'
    assert len(dict['_xmlOpts']['_rootAttributes']) == 1
    assert dict['_xmlOpts']['_rootTag'] == 'ROOT'
    assert dict['_xmlOpts']['_rootAttributes']['version'] == '0.1'
    assert dict['_xmlOpts']['_addNodeNumbering'] is True


def test_read_dict_in_subfolder_with_includes():
    dict = CppDict(Path.cwd() / 'include' / 'initialConditions')
    silent_remove(Path('include\\parsed.initialConditions'))
    dict_in = DictReader.read(dict.source_file)
    assert dict_in['Re_profile'] == 1000000.0
    assert dict_in['mag_U_infty'] == 1.004


def test_read_dict_in_subfolder_with_includes_source_file_given_as_str():
    source_file_as_path = Path.cwd() / 'include' / 'initialConditions'
    source_file_as_str = str(source_file_as_path)
    silent_remove(Path('include\\parsed.initialConditions'))
    dict_in = DictReader.read(source_file_as_str)
    assert dict_in['Re_profile'] == 1000000.0
    assert dict_in['mag_U_infty'] == 1.004


def test_read_dict_in_subfolder_with_includes_source_file_given_as_purepath():
    source_file_as_path = Path.cwd() / 'include' / 'initialConditions'
    source_file_as_purepath = PurePath(str(source_file_as_path))
    silent_remove(Path('include\\parsed.initialConditions'))
    dict_in = DictReader.read(source_file_as_purepath)
    assert dict_in['Re_profile'] == 1000000.0
    assert dict_in['mag_U_infty'] == 1.004


def test_read_dict_in_subfolder_with_includes_source_file_given_as_path():
    source_file_as_path = Path.cwd() / 'include' / 'initialConditions'
    silent_remove(Path('include\\parsed.initialConditions'))
    dict_in = DictReader.read(source_file_as_path)
    assert dict_in['Re_profile'] == 1000000.0
    assert dict_in['mag_U_infty'] == 1.004


def test_read_dict_in_subfolder_with_includes_no_order():
    dict = CppDict(Path.cwd() / 'include' / 'initialConditions')
    silent_remove(Path('include\\parsed.initialConditions'))
    dict_in = DictReader.read(dict.source_file)
    assert dict_in['Re_profile'] == 1000000.0
    assert dict_in['mag_U_infty'] == 1.004


def test_read_dict_in_subfolder_with_includes_no_order_called_via_dictparser_script():
    file_name = 'include\\initialConditions'
    silent_remove(Path('include\\parsed.initialConditions'))
    silent_remove(Path('include\\parsed.initialConditions.foam'))
    os.system(f'..\\src\\dictIO\\cli\\dictParser.py --quiet {file_name}')
    assert os.path.exists('include\\parsed.initialConditions')
    assert not os.path.exists('include\\parsed.initialConditions.foam')
    silent_remove(Path('include\\parsed.initialConditions'))
    os.system(f'..\\src\\dictIO\\cli\\dictParser.py --quiet --output=foam {file_name}')
    assert not os.path.exists('include\\parsed.initialConditions')
    assert os.path.exists('include\\parsed.initialConditions.foam')


def test_merge_opts(parsed_dict):

    dict_in = DictReader.read(Path('test_mergeDict'))

    # add key in level 0
    dict_in.update({'key01': 'val01'})

    # add key in level 1
    dict_in.update({'key00': {'key11': 'val11'}})

    # add to key in level 1
    dict_in['key00'].update({'key10': {'key21': 'val21'}})

    dict_out = deepcopy(dict_in)

    # test a (before test w because otherwise w removes content in level 1)
    DictWriter.write(dict_out, Path('parsed.test_mergeDict'), 'a')
    test_dict = DictReader.read(Path('parsed.test_mergeDict'))
    assert test_dict.data == {
        'BLOCKCOMMENT000000': 'BLOCKCOMMENT000000',
        'key00': {
            'key10': {
                'key20': 'val20', 'key21': 'val21'
            }, 'key11': 'val11'
        },
        'key01': 'val01'
    }

    # test w
    DictWriter.write(dict_out, Path('parsed.test_mergeDict'), 'w', order=True)
    test_dict = DictReader.read(Path('parsed.test_mergeDict'))
    assert test_dict.data == {
        'BLOCKCOMMENT000000': 'BLOCKCOMMENT000000',
        'key00': {
            'key10': {
                'key21': 'val21'
            }, 'key11': 'val11'
        },
        'key01': 'val01'
    }


class SetupHelper():

    @staticmethod
    def prepare_dict_until(
        dict_to_prepare: CppDict,
        until_step=-1,
        file_to_read='test_configDict',
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
