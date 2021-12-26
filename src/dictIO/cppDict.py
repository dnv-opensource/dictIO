import re
import os
from collections import UserDict
from pathlib import Path
from typing import (Any, Mapping, MutableMapping, MutableSequence, Sequence, TypeVar, Union)
import logging


__ALL__ = ['CppDict', 'verify_dict_content']

_KT = TypeVar('_KT')    # generic Type variable for keys
_VT = TypeVar('_VT')    # generic Type variable for values

logger = logging.getLogger(__name__)


class CppDict(UserDict):
    """Data structure for generic C++ dictionaries

    CppDict inherits from UserDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    def __init__(self, file: Union[str, os.PathLike[str]] = None):
        super().__init__()  # call base class constructor

        self.source_file = None
        self.path = Path.cwd()
        self.name = ''

        if file:
            # Make sure file argument is of type Path. If not, cast it to Path type.
            file = file if isinstance(file, Path) else Path(file)
            self.source_file = file.absolute()
            self.path = self.source_file.parent
            self.name = self.source_file.name

        self.line_content = []
        self.block_content = ''
        self.tokens = []
        self.string_literals = {}

        self.line_comments = {}
        self.block_comments: MutableMapping[int, str] = {}
        self.expressions = {}
        self.includes = {}

        self.brackets = [('{', '}'), ('[', ']'), ('(', ')'), ('<', '>')]
        self.delimiters = ['{', '}', '(', ')', '<', '>', ';', ',']
        self.openingBrackets = [
            '{', '[', '('
        ]                           # Note: < and > are not considered brackets, but operators used in filter expressions
        self.closingBrackets = ['}', ']', ')']
        return

    # Override the update() method of UserDict class to include updating CppDict attributes
    def update(self, __m: Mapping, **kwargs) -> None:
        # sourcery skip: class-extract-method
        # call base class method. This takes care of updating self.data
        super().update(__m, **kwargs)
        # update attributes
        if isinstance(__m, CppDict):
            self.line_comments.update(__m.line_comments)
            self.block_comments.update(__m.block_comments)
            self.expressions.update(__m.expressions)
            self.includes.update(__m.includes)
        self.clean()

        return

    def merge(self, dict: MutableMapping):
        '''
        Merges the passed in dict into the CppDict instance.
        In contrast to update(), merge() works recursively. That is, it does not only update the top-level keys of the Cpp instance,
        but also nested dicts, given they are also present in the dict to be merged
        '''
        # merge dict into self (=into self.data)
        merge_dicts(self, dict)
        # mergedeep behaves like merge with less (visible) code
        # no clue how merge works in detail without return value...
        # from mergedeep import merge
        # self.data = merge(self.data, dict)
        # merge attributes
        if isinstance(dict, CppDict):
            merge_dicts(self.line_comments, dict.line_comments)
            merge_dicts(self.block_comments, dict.block_comments)
            merge_dicts(self.expressions, dict.expressions)
            merge_dicts(self.includes, dict.includes)
        self.clean()

        return

    def clean(self, dict: MutableMapping = None):
        '''
        Finds and removes doublettes of following PLACEHOLDER keys within self.data
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        '''
        # START at nest level 0
        if dict is None:
            dict = self.data

        # IDENTIFY all placeholders on current level
        keys_on_this_level = list(dict.keys())
        block_comments_on_this_level = []
        includes_on_this_level = []
        line_comments_on_this_level = []
        for key in keys_on_this_level:
            if re.search(r'BLOCKCOMMENT\d{6}', key):
                block_comments_on_this_level.append(key)
            elif re.search(r'INCLUDE\d{6}', key):
                includes_on_this_level.append(key)
            elif re.search(r'LINECOMMENT\d{6}', key):
                line_comments_on_this_level.append(key)

        unique_block_comments_on_this_level = []                    # BLOCKCOMMENTs
        for key in block_comments_on_this_level:
            try:
                id = int(re.findall(r'\d{6}', key)[0])
                value = str(self.block_comments[id])
                if value in unique_block_comments_on_this_level:    # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.block_comments[id]                     # ..AND from self.block_comments (the lookup table)
                else:                                               # Unique
                    unique_block_comments_on_this_level.append(value)
            except Exception:
                pass
        unique_includes_on_this_level = []                          # INCLUDEs
        for key in includes_on_this_level:
            try:
                id = int(re.findall(r'\d{6}', key)[0])
                value = self.includes[id]
                if value in unique_includes_on_this_level:          # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.includes[id]                           # ..AND from self.includes (the lookup table)
                else:                                               # Unique
                    unique_includes_on_this_level.append(value)
            except Exception:
                pass
        unique_line_comments_on_this_level = []                     # LINECOMMENTs
        for key in line_comments_on_this_level:
            try:
                id = int(re.findall(r'\d{6}', key)[0])
                value = self.line_comments[id]
                if value in unique_line_comments_on_this_level:     # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.line_comments[id]                      # ..AND from self.line_comments (the lookup table)
                else:                                               # Unique
                    unique_line_comments_on_this_level.append(value)
            except Exception:
                pass

        # RECURSION for nested levels
        for key in dict.keys():
            if isinstance(dict[key], MutableMapping):
                self.clean(dict[key])   # Recursion

        return

    def __str__(self):
        '''
        string representation of the dictionary in C++ dictionary format
        '''
        from dictIO.formatter import \
            CppFormatter  # __str__ shall be formatted in default C++ dictionary format
        formatter = CppFormatter()
        return formatter.to_string(self)

    def __repr__(self):
        return f'CppDict({self.source_file!r})'

    def __eq__(self, other):
        if isinstance(other, CppDict):
            return str(self) == str(other)
        else:
            return False

    def order_keys(self):
        '''
        alpha-numeric sorting of keys
        '''
        self.data = dict(order_keys(self.data))
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.expressions = order_keys(self.expressions)
        self.includes = order_keys(self.includes)

        return

    def iter_find_key(self, query: str = '') -> Union[MutableSequence, None]:
        '''
        Returns the global key thread to the first value matching the passed in query.
        '''
        return iter_find_key(self.data, query)

    def iter_set_key(self, global_key: MutableSequence, value: Any = None):
        '''
        Sets the value for the passed in global key.
        '''
        iter_set_key(self.data, global_key, value)

        return

    def iter_key_exists(self, global_key: MutableSequence):
        '''
        probe the existence of (nested) keys in dict
        '''
        return iter_key_exists(self.data, global_key)

    def reduce_scope(self, scope: Sequence = None):
        '''
        Reduces self.data to the keys defined in scope
        '''
        if (scope is not None) and (len(scope) > 0):
            try:
                self.data = eval('self.data[\'' + '\'][\''.join(scope) + '\']')
            except KeyError as e:
                logger.warning(
                    'CppDict.reduce_scope(): no scope \'%s\' in dictionary %s' %
                    (e.args[0], self.source_file)
                )
        return

    @property
    def variables(self):
        variables = {}

        def extract_variables_from_dict(dict: MutableMapping):
            for k, v in dict.items():
                if isinstance(v, MutableMapping):
                    extract_variables_from_dict(v)      # recursion
                elif isinstance(v, MutableSequence):
                    if list_contains_dict(v):
                        extract_variables_from_list(v)  # recursion
                    else:
                                                        # special case: item is a list, but does NOT contain a nested dict (-> e.g. a vector or matrix)
                        variables.update({k: v})
                else:
                                                        # base case: item is a single value type
                    v = insert_expression(v, self)
                    if not value_contains_circular_reference(k, v):
                        variables.update({k: v})
            return

        def extract_variables_from_list(list: MutableSequence):
            # sourcery skip: remove-redundant-pass
            for v in list:
                if isinstance(v, MutableMapping):
                    extract_variables_from_dict(v)  # recursion
                elif isinstance(v, MutableSequence):
                    extract_variables_from_list(v)  # recursion
                else:
                                                    # By convention, list items are NOT added to the variables lookup table
                                                    # as they only have an index but no key
                                                    # (which we need, though, to serve as variable name)
                    pass
            return

        def list_contains_dict(list: MutableSequence) -> bool:
            # sourcery skip: merge-duplicate-blocks, use-any
            for item in list:
                if isinstance(item, MutableMapping):
                    return True
                elif isinstance(item, MutableSequence):
                    if list_contains_dict(item):
                        return True
            return False

        extract_variables_from_dict(self.data)

        order_keys(variables)

        return variables


def order_keys(arg: MutableMapping[_KT, _VT]) -> MutableMapping[_KT, _VT]:
    '''
    alpha-numeric sorting of keys, recursively
    '''
    if isinstance(arg, dict):
        sorted_dict = dict(sorted(arg.items(), key=lambda x: (isinstance(x[0], str), x[0])))
        for key, value in sorted_dict.items():
            if isinstance(value, dict):
                sorted_dict[key] = order_keys(sorted_dict[key])
        return sorted_dict
    else:
        logger.warning(
            'dict.order_keys(): no alpha-numeric sorting of keys possible because of \'argument not a dict\', returning same.'
        )
        return arg


def iter_find_key(arg: Union[MutableMapping, MutableSequence],
                  query: str = '') -> Union[MutableSequence, None]:
    '''
    Returns the global key thread to the first value matching the passed in query.
    Function works recursively on nested dicts and is non-greedy: The key of the first match is returned.
    Return value is a sequence of keys: The 'global key thread'.
    It represents the sequence of keys that one needs to traverse downwards
    in order to arrive at the target key found.
    '''
    global_key = []
    if isinstance(arg, MutableMapping):                                         # dict
        for key, _ in sorted(arg.items()):
            if isinstance(arg[key], (MutableMapping, MutableSequence)):
                next_level_key = iter_find_key(arg=arg[key], query=query)       # Recursion
                if next_level_key:
                    global_key.append(key)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[key])):
                global_key.append(key)
                break
    elif isinstance(arg, MutableSequence):                                      # list
        for index, _ in enumerate(arg):
            if isinstance(arg[index], (MutableMapping, MutableSequence)):
                next_level_key = iter_find_key(arg=arg[index], query=query)     # Recursion
                if next_level_key:
                    global_key.append(index)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[index])):
                global_key.append(index)
                break
    else:
        logger.warning('Run into not implemented alternative')

    return global_key or None


def iter_set_key(
    arg: MutableMapping, global_key: MutableSequence = None, value: Any = None
) -> MutableMapping:
    '''
    Sets the value for the passed in global key.
    Parameter global_key is expected to be a list of keys defining a global key thread to the target key.
    (Such as returned by corresponding function iter_find_key())
    The global key thread is traversed downwards until arrival at the target key,
    the value of which is then set.
    '''
    if isinstance(global_key, MutableSequence) and (global_key):
        last_branch = arg
        remaining_keys = global_key
        ii = 0
        while len(
            remaining_keys
        ) > 1:                                              # as long as we didn't arrive at the last branch (the one that contains the target key)..
            last_branch = last_branch[remaining_keys[0]]    # ..walk one level further down
            remaining_keys = remaining_keys[1:]
            ii += 1
            if ii == 10: break
        last_branch[remaining_keys[0]] = value

    return arg


def iter_key_exists(arg: MutableMapping, global_key: MutableSequence = None):
    '''
    Check if (nested) global_key (nested) exists in dict
    '''
    global_key = global_key or []
    _arg = arg
    for key in global_key:
        try:
            _arg = _arg[key]
        except KeyError:
            return False
    return True


def verify_dict_content(dict: MutableMapping) -> MutableMapping:
    '''
    check, if there is dict and there are entries
    '''
    if not isinstance(dict, MutableMapping):
        logger.error('verifyContent: consider providing a postDict with reasonable entries')
    if len(dict.keys()) <= 0:
        logger.error('verifyContent: consider providing a postDict with reasonable entries')
    return dict


def insert_expression(value: str, dict: CppDict) -> str:
    if isinstance(value, str) and isinstance(dict,
                                             CppDict) and re.search(r'EXPRESSION\d{6}', value):
        match_index = re.search(r'\d{6}', value)
        if match_index:
            index = int(match_index[0])
            value = dict.expressions[index]['expression'] if index in dict.expressions else value
    return value


def value_contains_circular_reference(key: str, value: str) -> bool:
    if isinstance(key, str) and isinstance(value, str):
        return key in value
    return False


def merge_dicts(target_dict: MutableMapping, dict_to_merge: MutableMapping, overwrite=False):
    '''
    Merges dict_to_merge into a target_dict.
    In contrast to dict.update(), merge_dicts() does not only update the top-level keys of target_dict,
    but also nested dicts, given they are also present in dict_to_merge.
    Doing so, it prevents keys in any nested dicts from being deleted.
    '''
    for key in dict_to_merge.keys():
        if (key in target_dict.keys()) and isinstance(
            target_dict[key], MutableMapping
        ) and isinstance(dict_to_merge[key], MutableMapping):                                           # dict
            merge_dicts(target_dict[key], dict_to_merge[key])                                           # Recursion
        else:
            value_in_target_dict_contains_circular_reference = False
            if key in target_dict and isinstance(target_dict, CppDict):
                value = insert_expression(target_dict[key], target_dict)
                value_in_target_dict_contains_circular_reference = value_contains_circular_reference(
                    key, value
                )
            if overwrite or key not in target_dict or value_in_target_dict_contains_circular_reference:
                target_dict[key] = dict_to_merge[key]                                                   # Update

    return
