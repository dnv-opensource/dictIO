# pyright: reportIncompatibleMethodOverride=false
import contextlib
import logging
import os
import re
from collections import UserDict
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    MutableSequence,
    Tuple,
    TypeVar,
    Union,
)

from dictIO.utils.counter import BorgCounter
from dictIO.utils.path import relative_path

__ALL__ = [
    "CppDict",
    "order_keys",
    "find_global_key",
    "set_global_key",
    "global_key_exists",
]

_KT = TypeVar("_KT")  # generic Type variable for keys
_VT = TypeVar("_VT")  # generic Type variable for values

logger = logging.getLogger(__name__)


class CppDict(UserDict[Any, Any]):
    """Data structure for generic dictionaries.

    CppDict inherits from UserDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    def __init__(self, file: Union[str, os.PathLike[str], None] = None):
        # At very first: Re-declare member 'data' of base class UserDict with a well defined type hint.
        # (This allows static type checkers to properly resolve the type of the 'data' member.)
        self.data: Dict[Any, Any] = {}
        # Call base class constructor
        super().__init__()

        self.counter: BorgCounter = BorgCounter()
        self.source_file: Union[Path, None] = None
        self.path: Path = Path.cwd()
        self.name: str = ""

        if file:
            # Make sure file argument is of type Path. If not, cast it to Path type.
            file = file if isinstance(file, Path) else Path(file)
            self.source_file = file.absolute()
            self.path = self.source_file.parent
            self.name = self.source_file.name

        self.line_content: List[str] = []
        self.block_content: str = ""
        self.tokens: List[Tuple[int, str]] = []
        self.string_literals: Dict[int, str] = {}

        self.line_comments: Dict[int, str] = {}
        self.block_comments: Dict[int, str] = {}
        self.expressions: Dict[int, Dict[str, str]] = {}
        self.includes: Dict[int, Tuple[str, str, Path]] = {}

        self.brackets: List[Tuple[str, str]] = [
            ("{", "}"),
            ("[", "]"),
            ("(", ")"),
            ("<", ">"),
        ]
        self.delimiters: List[str] = [
            "{",
            "}",
            "(",
            ")",
            "<",
            ">",
            ";",
            ",",
        ]
        self.openingBrackets: List[str] = [
            "{",
            "[",
            "(",
        ]  # Note: < and > are not considered brackets, but operators used in filter expressions
        self.closingBrackets: List[str] = [
            "}",
            "]",
            ")",
        ]
        return

    def include(self, dict_to_include: "CppDict"):
        """Add an include directive for the passed in dict.

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

        from dictIO import CppFormatter

        formatter = CppFormatter()
        include_file_name = str(relative_file_path)
        include_file_name = include_file_name.replace("\\", "\\\\")
        include_file_name = formatter.format_type(include_file_name)

        include_directive = f"#include {include_file_name}"

        ii: int = 0
        placeholder: str = ""
        while True:
            ii = self.counter()
            placeholder = "INCLUDE%06i" % ii
            if placeholder in self.data:
                continue
            else:
                break
        self.data[placeholder] = placeholder
        self.includes.update({ii: (include_directive, include_file_name, include_file_path)})
        return

    def update(self, __m: Mapping[Any, Any], **kwargs: Any) -> None:
        """Update top-level keys with the keys from the passed in dict.

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
        **kwargs: Any
            optional keyword arguments. These will be passed on to the update() method of the parent class.
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

    def merge(self, dict: MutableMapping[Any, Any]):
        """Merge the passed in dict into the existing CppDict instance.

        In contrast to update(), merge() works recursively. That is, it does not simply substitute top-level keys but
        recursively merges (potentially nested) content from the passed in dict into the existing.
        This prevents nested keys from being deleted.
        Further, existing keys will NOT be overwritten.

        Parameters
        ----------
        dict : MutableMapping[Any, Any]
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
        """String representation of the CppDict instance in dictIO dict file format.

        Returns
        -------
        str
            the string representation
        """  # noqa: D401
        from dictIO import (
            CppFormatter,  # __str__ shall be formatted in default dict file format
        )

        formatter = CppFormatter()
        return formatter.to_string(self)

    def __repr__(self):
        return f"CppDict({self.source_file!r})"

    def __eq__(self, other: Union[Any, "CppDict"]):
        return str(self) == str(other) if isinstance(other, CppDict) else False

    def order_keys(self):
        """alpha-numeric sorting of keys, recursively."""
        self.data = dict(order_keys(self.data))
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.expressions = order_keys(self.expressions)
        self.includes = order_keys(self.includes)

        return

    def find_global_key(self, query: str = "") -> Union[List[Any], None]:
        """Return the global key thread to the first key the value of which matches the passed in query.

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
        Union[List[Any], None]
            global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
        """
        return find_global_key(self.data, query)

    def set_global_key(self, global_key: MutableSequence[Any], value: Any = None):
        """Set the value for the passed in global key.

        The global key thread is traversed downwards until arrival at the target key,
        the value of which is then set.

        Parameters
        ----------
        global_key : MutableSequence[Any]
            list of keys defining the global key thread to the target key (such as returned by method find_global_key())
        value : Any, optional
            value the target key shall be set to, by default None
        """
        set_global_key(self.data, global_key, value)

        return

    def global_key_exists(self, global_key: MutableSequence[Any]) -> bool:
        """Check whether the specified global key exists.

        Parameters
        ----------
        global_key : MutableSequence[Any]
            global key the existence of which is checked

        Returns
        -------
        bool
            True if the specified global key exists, otherwise False
        """
        """
        probe the existence of (nested) keys in dict
        """
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
                self.data = eval("self.data['" + "']['".join(scope) + "']")
            except KeyError as e:
                logger.warning(f"CppDict.reduce_scope(): no scope '{e.args[0]}' in dictionary {self.source_file}")
        return

    @property
    def variables(self) -> Dict[str, Any]:
        """Returns a dict with all Variables currently registered.

        Returns
        -------
        Dict[str, Any]
            dict of all Variables currently registered.
        """
        variables: Dict[str, Any] = {}

        def extract_variables_from_dict(dict: MutableMapping[Any, Any]):
            for k, v in dict.items():
                if isinstance(v, MutableMapping):
                    extract_variables_from_dict(v)  # recursion
                elif isinstance(v, MutableSequence):
                    if list_contains_dict(v):
                        extract_variables_from_list(v)  # recursion
                    else:
                        # special case: item is a list, but does NOT contain a nested dict (-> e.g. a vector or matrix)
                        variables[k] = v
                else:
                    # base case: item is a single value type
                    v = _insert_expression(v, self)
                    if not _value_contains_circular_reference(k, v):
                        variables[k] = v
            return

        def extract_variables_from_list(list: MutableSequence[Any]):
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

        def list_contains_dict(list: MutableSequence[Any]) -> bool:
            # sourcery skip: merge-duplicate-blocks, use-any
            for item in list:
                if isinstance(item, MutableMapping):
                    return True
                elif isinstance(item, MutableSequence):
                    if list_contains_dict(item):
                        return True
            return False

        extract_variables_from_dict(self.data)

        variables = order_keys(variables)

        return variables

    def _clean(self, dict: Union[MutableMapping[Any, Any], None] = None):
        # sourcery skip: avoid-builtin-shadow
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within self.data:
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        """
        # START at nest level 0
        if dict is None:
            dict = self.data

        # IDENTIFY all placeholders on current level
        keys_on_this_level: List[Any] = list(dict.keys())
        block_comments_on_this_level: List[Any] = []
        includes_on_this_level: List[Any] = []
        line_comments_on_this_level: List[Any] = []
        for key in keys_on_this_level:
            if re.search(r"BLOCKCOMMENT\d{6}", key):
                block_comments_on_this_level.append(key)
            elif re.search(r"INCLUDE\d{6}", key):
                includes_on_this_level.append(key)
            elif re.search(r"LINECOMMENT\d{6}", key):
                line_comments_on_this_level.append(key)

        unique_block_comments_on_this_level: List[str] = []  # BLOCKCOMMENTs
        for key in block_comments_on_this_level:
            with contextlib.suppress(Exception):
                id: int = int(re.findall(r"\d{6}", key)[0])
                _block_comment: str = self.block_comments[id]
                if _block_comment in unique_block_comments_on_this_level:
                    # Found doublette
                    # Remove from current level in self.data (the dict)
                    del dict[key]
                    # ..AND from self.block_comments (the lookup table)
                    del self.block_comments[id]
                else:
                    # Unique
                    unique_block_comments_on_this_level.append(_block_comment)
        unique_includes_on_this_level: List[Tuple[str, str, Path]] = []  # INCLUDEs
        for key in includes_on_this_level:
            with contextlib.suppress(Exception):
                id: int = int(re.findall(r"\d{6}", key)[0])
                _include: Tuple[str, str, Path] = self.includes[id]
                if _include in unique_includes_on_this_level:
                    # Found doublette
                    # Remove from current level in self.data (the dict)
                    del dict[key]
                    # ..AND from self.includes (the lookup table)
                    del self.includes[id]
                else:
                    # Unique
                    unique_includes_on_this_level.append(_include)
        unique_line_comments_on_this_level: List[str] = []  # LINECOMMENTs
        for key in line_comments_on_this_level:
            with contextlib.suppress(Exception):
                id: int = int(re.findall(r"\d{6}", key)[0])
                _line_comment: str = self.line_comments[id]
                if _line_comment in unique_line_comments_on_this_level:
                    # Found doublette
                    # Remove from current level in self.data (the dict)
                    del dict[key]
                    # ..AND from self.line_comments (the lookup table)
                    del self.line_comments[id]
                else:
                    # Unique
                    unique_line_comments_on_this_level.append(_line_comment)
        # RECURSION for nested levels
        for key in dict.keys():
            if isinstance(dict[key], MutableMapping):
                self._clean(dict[key])  # Recursion

        return


def order_keys(arg: MutableMapping[_KT, _VT]) -> Dict[_KT, _VT]:
    """alpha-numeric sorting of keys, recursively.

    Parameters
    ----------
    arg : MutableMapping[_KT, _VT]
        dict, the keys of which shall be sorted

    Returns
    -------
    Dict[_KT, _VT]
        passed in dict with keys sorted
    """
    sorted_dict: MutableMapping[_KT, _VT] = dict(sorted(arg.items(), key=lambda x: (isinstance(x[0], str), x[0])))
    for key, value in sorted_dict.items():
        if isinstance(value, MutableMapping):
            sorted_dict[key] = order_keys(sorted_dict[key])  # type: ignore
    return sorted_dict


def find_global_key(
    arg: Union[MutableMapping[Any, Any], MutableSequence[Any]],
    query: str = "",
) -> Union[List[Any], None]:
    """Return the global key thread to the first key the value of which matches the passed in query.

    Parameters
    ----------
    arg : Union[MutableMapping[Any, Any], MutableSequence[Any]]
        dict to search in for the queried value
    query : str, optional
        query string for the value to search for, by default ''

    Returns
    -------
    Union[List, None]
        global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
    """
    global_key: List[Any] = []
    if isinstance(arg, MutableMapping):  # dict
        for key, _ in sorted(arg.items()):
            if isinstance(arg[key], (MutableMapping, MutableSequence)):
                if next_level_key := find_global_key(arg=arg[key], query=query):
                    global_key.append(key)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[key])):
                global_key.append(key)
                break
    else:  # list
        for index, _ in enumerate(arg):
            if isinstance(arg[index], (MutableMapping, MutableSequence)):
                if next_level_key := find_global_key(arg=arg[index], query=query):
                    global_key.append(index)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(arg[index])):
                global_key.append(index)
                break

    return global_key or None


def set_global_key(
    arg: MutableMapping[Any, Any],
    global_key: MutableSequence[Any],
    value: Any = None,
):
    """Set the value for the passed in global key.

    Parameters
    ----------
    arg : MutableMapping[Any, Any]
        dict the target key in which shall be set
    global_key : MutableSequence[Any], optional
        list of keys defining the global key thread to the target key (such as returned by method find_global_key())
    value : Any, optional
        value the target key shall be set to, by default None
    """
    if global_key:
        last_branch = arg
        remaining_keys = global_key
        ii = 0
        while (
            len(remaining_keys) > 1
        ):  # as long as we didn't arrive at the last branch (the one that contains the target key)..
            last_branch = last_branch[remaining_keys[0]]  # ..walk one level further down
            remaining_keys = remaining_keys[1:]
            ii += 1
            if ii == 10:
                break
        last_branch[remaining_keys[0]] = value

    return


def global_key_exists(arg: MutableMapping[Any, Any], global_key: MutableSequence[Any]) -> bool:
    """Check whether the specified global key exists in the passed in dict.

    Parameters
    ----------
    arg : MutableMapping[Any, Any]
        dict to check for existence of the specified global key
    global_key : MutableSequence[Any], optional
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


def _merge_dicts(
    target_dict: MutableMapping[Any, Any],
    dict_to_merge: MutableMapping[Any, Any],
    overwrite: bool = False,
):
    """Merge dict_to_merge into target_dict.

    In contrast to dict.update(), _merge_dicts() works recursively. That is, it does not simply substitute top-level keys
    in target_dict but recursively merges (potentially nested) content from dict_to_merge into target_dict.
    This prevents nested keys from being deleted.

    Parameters
    ----------
    target_dict : MutableMapping[Any, Any]
        target dict
    dict_to_merge : MutableMapping[Any, Any]
        dict to be merged into target dict
    overwrite : bool, optional
        if True, existing keys will be overwritten, by default False
    """
    for key in dict_to_merge.keys():
        if (
            (key in target_dict.keys())
            and isinstance(target_dict[key], MutableMapping)
            and isinstance(dict_to_merge[key], MutableMapping)
        ):  # dict
            _merge_dicts(target_dict[key], dict_to_merge[key], overwrite)  # Recursion
        else:
            value_in_target_dict_contains_circular_reference = False
            if key in target_dict and isinstance(target_dict, CppDict):
                value = _insert_expression(target_dict[key], target_dict)
                value_in_target_dict_contains_circular_reference = _value_contains_circular_reference(key, value)
            if overwrite or key not in target_dict or value_in_target_dict_contains_circular_reference:
                target_dict[key] = dict_to_merge[key]  # Update

    return


def _insert_expression(value: Any, dict: CppDict) -> str:
    if isinstance(value, str) and re.search(r"EXPRESSION\d{6}", value):
        if match_index := re.search(r"\d{6}", value):
            index = int(match_index[0])
            value = dict.expressions[index]["expression"] if index in dict.expressions else value
    return value


def _value_contains_circular_reference(key: Any, value: Any) -> bool:
    if isinstance(key, str) and isinstance(value, str):
        return key in value
    return False
