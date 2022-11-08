import contextlib
import re
import os
from collections import UserDict
from pathlib import Path
from typing import (Any, Dict, Mapping, MutableMapping, MutableSequence, TypeVar, Union)
import logging
import dictIO
from dictIO.utils.counter import BorgCounter
from dictIO.utils.path import relative_path


__ALL__ = ['CppDict', 'order_keys', 'find_global_key', 'set_global_key', 'global_key_exists']

_KT = TypeVar('_KT')    # generic Type variable for keys
_VT = TypeVar('_VT')    # generic Type variable for values

logger = logging.getLogger(__name__)


class CppDict(UserDict):
    """Data structure for generic dictionaries

    CppDict inherits from UserDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    def __init__(self, file: Union[str, os.PathLike[str], None] = None):
        super().__init__()  # call base class constructor

        self.counter = BorgCounter()
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
        self.expressions: Dict[int, Dict[str, Any]] = {}
        self.includes = {}

        self.brackets = [('{', '}'), ('[', ']'), ('(', ')'), ('<', '>')]
        self.delimiters = ['{', '}', '(', ')', '<', '>', ';', ',']
        self.openingBrackets = [
            '{', '[', '('
        ]                           # Note: < and > are not considered brackets, but operators used in filter expressions
        self.closingBrackets = ['}', ']', ')']
        return

    def include(self, dict_to_include: 'CppDict'):
        """Adds an include directive for the passed in dict

        Parameters
        ----------
        dict_to_include : CppDict
            The dict to be included via an include directive

        Raises
        ------
        AttributeError
            If dict_to_include.source_file is None
        ValueError
            If no relative path in between the current dict and the included dict can be resolved
        """
        if not dict_to_include.source_file:
            raise AttributeError(
                f"Cannot include {dict_to_include.name}. Attribute '.source_file' of {dict_to_include.name} is None."
            )
        if not self.source_file:
            raise AttributeError(
                f"Cannot include {dict_to_include.name}. Attribute '.source_file' of {self.name} is None."
            )

        include_file_path = dict_to_include.source_file
        relative_file_path: Path
        try:
            relative_file_path = relative_path(
                from_path=self.source_file.parent,
                to_path=dict_to_include.source_file,
            )
        except ValueError as e:
            raise ValueError(
                f"Cannot include {dict_to_include.name}. Relative path to {dict_to_include.name} could not be resolved."
            ) from e

        formatter = dictIO.formatter.CppFormatter()
        include_file_name = str(relative_file_path)
        include_file_name = include_file_name.replace('\\', '\\\\')
        include_file_name = formatter.format_type(include_file_name)

        include_directive = f'#include {include_file_name}'

        ii: int = 0
        placeholder: str = ''
        while True:
            ii = self.counter()
            placeholder = 'INCLUDE%06i' % ii
            if placeholder in self.data:
                continue
            else:
                break
        self.data[placeholder] = placeholder
        self.includes.update({ii: (include_directive, include_file_name, include_file_path)})
        return

    def update(self, __m: Mapping, **kwargs) -> None:
        """Updates top-level keys with the keys from the passed in dict.

        Overrides the update() method of UserDict base class in order to include also CppDict class attributes in the update.

        If a key already exists, it will be substituted by the key from the passed in dict.
        In order to not substitute top-level keys but recursively merge (potentially nested) content from passed in dict into the existing, use merge() instead.

        Note:

        The behaviour of update() corresponds with default mode '-w' in the dictParser command line interface.

        The behaviour of merge() corresponds with mode '-a' in the dictParser command line interface. See also CLI Documentation.

        Parameters
        ----------
        __m : Mapping
            dict containing the keys to be updated and its new values
        """
        # sourcery skip: class-extract-method
        # call base class method. This takes care of updating self.data
        super().update(__m, **kwargs)
        # update attributes
        if isinstance(__m, CppDict):
            self.line_comments.update(__m.line_comments)
            self.block_comments.update(__m.block_comments)
            self.expressions.update(__m.expressions)
            self.includes.update(__m.includes)
        self._clean()

        return

    def merge(self, dict: MutableMapping):
        """Merges the passed in dict into the existing CppDict instance.

        In contrast to update(), merge() works recursively. That is, it does not simply substitute top-level keys but
        recursively merges (potentially nested) content from the passed in dict into the existing.
        This prevents nested keys from being deleted.
        Further, existing keys will NOT be overwritten.

        Parameters
        ----------
        dict : MutableMapping
            dict to be merged
        """
        # merge dict into self (=into self.data)
        _merge_dicts(self, dict)
        # @TODO: An alternative we might test one day is the mergedeep module from the Python standard library:
        #        from mergedeep import merge
        #        self.data = merge(self.data, dict)
        #        CLAROS (FRALUM), 2022-01-05

        # merge CppDict attributes
        if isinstance(dict, CppDict):
            _merge_dicts(self.line_comments, dict.line_comments)
            _merge_dicts(self.block_comments, dict.block_comments)
            _merge_dicts(self.expressions, dict.expressions)
            _merge_dicts(self.includes, dict.includes)
        self._clean()

        return

    def __str__(self):
        """string representation of the CppDict instance in dictIO dict file format

        Returns
        -------
        str
            the string representation
        """
        from dictIO import \
            CppFormatter  # __str__ shall be formatted in default dict file format
        formatter = CppFormatter()
        return formatter.to_string(self)

    def __repr__(self):
        return f'CppDict({self.source_file!r})'

    def __eq__(self, other):
        return str(self) == str(other) if isinstance(other, CppDict) else False

    def order_keys(self):
        """alpha-numeric sorting of keys, recursively
        """
        self.data = dict(order_keys(self.data))
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.expressions = order_keys(self.expressions)
        self.includes = order_keys(self.includes)

        return

    def find_global_key(self, query: str = '') -> Union[MutableSequence, None]:
        """Returns the global key thread to the first key the value of which matches the passed in query.

        Function works recursively on nested dicts and is non-greedy: The key of the first match is returned.
        Return value is a sequence of keys: The 'global key thread'.
        It represents the sequence of keys that one needs to traverse downwards
        in order to arrive at the target key found.

        Parameters
        ----------
        query : str, optional
            query string for the value to search for by default ''

        Returns
        -------
        Union[MutableSequence, None]
            global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
        """
        return find_global_key(self.data, query)

    def set_global_key(self, global_key: MutableSequence, value: Any = None):
        """Sets the value for the passed in global key.

        The global key thread is traversed downwards until arrival at the target key,
        the value of which is then set.

        Parameters
        ----------
        global_key : MutableSequence
            list of keys defining the global key thread to the target key (such as returned by method find_global_key())
        value : Any, optional
            value the target key shall be set to, by default None
        """
        set_global_key(self.data, global_key, value)

        return

    def global_key_exists(self, global_key: MutableSequence) -> bool:
        """Checks whether the specified global key exists.

        Parameters
        ----------
        global_key : MutableSequence
            global key the existence of which is checked

        Returns
        -------
        bool
            True if the specified global key exists, otherwise False
        """
        '''
        probe the existence of (nested) keys in dict
        '''
        return global_key_exists(self.data, global_key)

    def reduce_scope(self, scope: MutableSequence[str]):
        """Reduces the dict to the keys defined in scope.

        Parameters
        ----------
        scope : MutableSequence[str]
            scope the dict shall be reduced to
        """
        if scope:
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
                    v = _insert_expression(v, self)
                    if not _value_contains_circular_reference(k, v):
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

    def _clean(self, dict: Union[MutableMapping, None] = None):
        # sourcery skip: avoid-builtin-shadow
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
            with contextlib.suppress(Exception):
                id = int(re.findall(r'\d{6}', key)[0])
                value = str(self.block_comments[id])
                if value in unique_block_comments_on_this_level:    # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.block_comments[id]                     # ..AND from self.block_comments (the lookup table)
                else:                                               # Unique
                    unique_block_comments_on_this_level.append(value)
        unique_includes_on_this_level = []                          # INCLUDEs
        for key in includes_on_this_level:
            with contextlib.suppress(Exception):
                id = int(re.findall(r'\d{6}', key)[0])
                value = self.includes[id]
                if value in unique_includes_on_this_level:          # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.includes[id]                           # ..AND from self.includes (the lookup table)
                else:                                               # Unique
                    unique_includes_on_this_level.append(value)
        unique_line_comments_on_this_level = []                     # LINECOMMENTs
        for key in line_comments_on_this_level:
            with contextlib.suppress(Exception):
                id = int(re.findall(r'\d{6}', key)[0])
                value = self.line_comments[id]
                if value in unique_line_comments_on_this_level:     # Found doublette
                    del dict[key]                                   # remove from current level in self.data (the dict)
                    del self.line_comments[id]                      # ..AND from self.line_comments (the lookup table)
                else:                                               # Unique
                    unique_line_comments_on_this_level.append(value)
                                                                    # RECURSION for nested levels
        for key in dict.keys():
            if isinstance(dict[key], MutableMapping):
                self._clean(dict[key])                              # Recursion

        return


def order_keys(arg: MutableMapping[_KT, _VT]) -> MutableMapping[_KT, _VT]:
    """alpha-numeric sorting of keys, recursively

    Parameters
    ----------
    arg : MutableMapping[_KT, _VT]
        dict, the keys of which shall be sorted

    Returns
    -------
    MutableMapping[_KT, _VT]
        passed in dict with keys sorted
    """
    if isinstance(arg, MutableMapping):
        sorted_dict: MutableMapping[_KT, _VT] = dict(
            sorted(arg.items(), key=lambda x: (isinstance(x[0], str), x[0]))
        )
        for key, value in sorted_dict.items():
            if isinstance(value, dict):
                sorted_dict[key] = order_keys(sorted_dict[key])                                                                # type: ignore
        return sorted_dict
    else:
        logger.warning(
            'dict.order_keys(): no alpha-numeric sorting of keys possible because of \'argument not a dict\', returning same.'
        )
        return arg


def find_global_key(arg: Union[MutableMapping, MutableSequence],
                    query: str = '') -> Union[MutableSequence, None]:
    """Returns the global key thread to the first key the value of which matches the passed in query.

    Parameters
    ----------
    arg : Union[MutableMapping, MutableSequence]
        dict to search in for the queried value
    query : str, optional
        query string for the value to search for, by default ''

    Returns
    -------
    Union[MutableSequence, None]
        global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
    """
    global_key = []
    if isinstance(arg, MutableMapping):     # dict
        for key, _ in sorted(arg.items()):
            if isinstance(arg[key], (MutableMapping, MutableSequence)):
                if next_level_key := find_global_key(arg=arg[key], query=query):
                    global_key.append(key)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[key])):
                global_key.append(key)
                break
    elif isinstance(arg, MutableSequence):  # list
        for index, _ in enumerate(arg):
            if isinstance(arg[index], (MutableMapping, MutableSequence)):
                if next_level_key := find_global_key(arg=arg[index], query=query):
                    global_key.append(index)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[index])):
                global_key.append(index)
                break
    else:
        logger.warning('Run into not implemented alternative')

    return global_key or None


def set_global_key(arg: MutableMapping, global_key: MutableSequence, value: Any = None):
    """Sets the value for the passed in global key.

    Parameters
    ----------
    arg : MutableMapping
        dict the target key in which shall be set
    global_key : MutableSequence, optional
        list of keys defining the global key thread to the target key (such as returned by method find_global_key())
    value : Any, optional
        value the target key shall be set to, by default None
    """
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

    return


def global_key_exists(arg: MutableMapping, global_key: MutableSequence) -> bool:
    """Checks whether the specified global key exists in the passed in dict.

    Parameters
    ----------
    arg : MutableMapping
        dict to check for existence of the specified global key
    global_key : MutableSequence, optional
        global key the existence of which is checked in the passed in dict

    Returns
    -------
    bool
        True if the specified global key exists, otherwise False
    """
    global_key = global_key or []
    _arg = arg
    for key in global_key:
        try:
            _arg = _arg[key]
        except KeyError:
            return False
    return True


def _merge_dicts(target_dict: MutableMapping, dict_to_merge: MutableMapping, overwrite=False):
    """Merges dict_to_merge into target_dict.

    In contrast to dict.update(), _merge_dicts() works recursively. That is, it does not simply substitute top-level keys
    in target_dict but recursively merges (potentially nested) content from dict_to_merge into target_dict.
    This prevents nested keys from being deleted.

    Parameters
    ----------
    target_dict : MutableMapping
        target dict
    dict_to_merge : MutableMapping
        dict to be merged into target dict
    overwrite : bool, optional
        if True, existing keys will be overwritten, by default False
    """
    for key in dict_to_merge.keys():
        if (key in target_dict.keys()) and isinstance(
            target_dict[key], MutableMapping
        ) and isinstance(dict_to_merge[key], MutableMapping):                                           # dict
            _merge_dicts(target_dict[key], dict_to_merge[key], overwrite)                               # Recursion
        else:
            value_in_target_dict_contains_circular_reference = False
            if key in target_dict and isinstance(target_dict, CppDict):
                value = _insert_expression(target_dict[key], target_dict)
                value_in_target_dict_contains_circular_reference = _value_contains_circular_reference(
                    key, value
                )
            if overwrite or key not in target_dict or value_in_target_dict_contains_circular_reference:
                target_dict[key] = dict_to_merge[key]                                                   # Update

    return


def _insert_expression(value: str, dict: CppDict) -> str:
    if isinstance(value, str) and isinstance(dict,
                                             CppDict) and re.search(r'EXPRESSION\d{6}', value):
        if match_index := re.search(r'\d{6}', value):
            index = int(match_index[0])
            value = dict.expressions[index]['expression'] if index in dict.expressions else value
    return value


def _value_contains_circular_reference(key: str, value: str) -> bool:
    if isinstance(key, str) and isinstance(value, str):
        return key in value
    return False
