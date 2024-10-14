# pyright: reportIncompatibleMethodOverride=false
# pyright: reportUnnecessaryTypeIgnoreComment=false
# ruff: noqa: ERA001
import contextlib
import logging
import os
import re
from _collections_abc import Iterable, Iterator, Mapping, MutableMapping, MutableSequence
from copy import deepcopy
from pathlib import Path
from types import NoneType
from typing import (
    Self,
    TypeVar,
    cast,
    overload,
)

from dictIO.types import TKey, TValue
from dictIO.utils.counter import BorgCounter
from dictIO.utils.path import relative_path

__ALL__ = [
    "ParsableDict",
    "ComposableDict",
    "CppDict",
    "order_keys",
    "find_global_key",
    "set_global_key",
    "global_key_exists",
]


# Type variables for keys and values
_KT = TypeVar("_KT", bound=TKey)
_VT = TypeVar("_VT", bound=TValue)
_KT_local = TypeVar("_KT_local", bound=TKey)
_VT_local = TypeVar("_VT_local", bound=TValue)


logger = logging.getLogger(__name__)


class ParsableDict(MutableMapping[_KT, _VT]):
    """Data structure for generic dictionaries.

    ParsableDict inherits from UserDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    @overload
    def __init__(
        self,
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[_KT, _VT],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[_KT, _VT]],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: str | os.PathLike[str],
        **kwargs: _VT,
    ) -> None:
        pass

    def __init__(
        self,
        arg: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]] | str | os.PathLike[str] | None = None,
        **kwargs: _VT,
    ) -> None:
        file: str | os.PathLike[str] | None = None
        base_dict: MutableMapping[_KT, _VT] | None = None
        if isinstance(arg, Mapping):
            base_dict = dict(cast(Mapping[_KT, _VT], arg))
        elif isinstance(arg, str | os.PathLike):
            file = arg
        elif isinstance(arg, Iterable):
            base_dict = dict(cast(Iterable[tuple[_KT, _VT]], arg))  # type: ignore[reportUnnecessaryCast]

        self.data: dict[_KT, _VT] = {}

        self.counter: BorgCounter = BorgCounter()
        self.source_file: Path | None = None
        self.path: Path = Path.cwd()
        self.name: str = ""

        if file:
            # Make sure file argument is of type Path. If not, cast it to Path type.
            file = file if isinstance(file, Path) else Path(file)
            self.source_file = file.absolute()
            self.path = self.source_file.parent
            self.name = self.source_file.name

        self.line_content: list[str] = []
        self.block_content: str = ""
        self.tokens: list[tuple[int, str]] = []
        self.string_literals: dict[int, str] = {}

        self.expressions: dict[int, dict[str, str]] = {}

        self.brackets: list[tuple[str, str]] = [
            ("{", "}"),
            ("[", "]"),
            ("(", ")"),
            ("<", ">"),
        ]
        self.delimiters: list[str] = [
            "{",
            "}",
            "(",
            ")",
            "<",
            ">",
            ";",
            ",",
        ]
        self.openingBrackets: list[str] = [
            "{",
            "[",
            "(",
        ]  # Note: < and > are not considered brackets, but operators used in filter expressions
        self.closingBrackets: list[str] = [
            "}",
            "]",
            ")",
        ]

        if base_dict is not None:
            self.update(base_dict)
        if kwargs:
            self.update(cast(Mapping[_KT, _VT], kwargs))

        return

    # Implementations of the abstract methods of collections.abc.MutableMapping
    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, key: _KT) -> _VT:
        if key in self.data:
            return self.data[key]
        # if hasattr(self.__class__, "__missing__"):
        #     return self.__class__.__missing__(self, key)
        raise KeyError(key)

    def __setitem__(self, key: _KT, item: _VT) -> None:
        self.data[key] = item

    def __delitem__(self, key: _KT) -> None:
        del self.data[key]

    def __iter__(self) -> Iterator[_KT]:
        return iter(self.data)

    # Modify __contains__ and get() to work like dict
    # does when __missing__ is present.
    def __contains__(self, key: object) -> bool:
        return key in self.data

    def get(self, key: _KT, default: _VT | None = None) -> _VT | None:  # type: ignore[override]
        return self[key] if key in self else default  # noqa: SIM401

    # Implementation of additional methods in ParsableDict
    # independent of collections.abc.MutableMapping
    def __or__(self, other: MutableMapping[_KT, _VT]) -> "ParsableDict[_KT, _VT]":
        if isinstance(other, ParsableDict):
            return self.__class__(self.data | other.data)  # type(other) is ParsableDict
        return self.__class__(self.data | dict(other))  # type(other) is MutableMapping

    def __ror__(self, other: MutableMapping[_KT, _VT]) -> "ParsableDict[_KT, _VT]":
        if isinstance(other, ParsableDict):
            return self.__class__(other.data | self.data)  # type(other) is ParsableDict
        return self.__class__(dict(other) | self.data)  # type(other) is MutableMapping

    def __ior__(self, other: MutableMapping[_KT, _VT]) -> Self:
        if isinstance(other, ParsableDict):
            self.data |= other.data  # type(other) is ParsableDict
        else:
            self.data |= dict(other)  # type(other) is MutableMapping
        return self

    def __copy__(self) -> "ParsableDict[_KT, _VT]":
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"].copy()
        return inst

    def copy(self) -> "ParsableDict[_KT, _VT]":
        if self.__class__ is ParsableDict:
            return ParsableDict(self.data.copy())
        import copy

        data = self.data
        copied_cpp_dict: ParsableDict[_KT, _VT]
        try:
            self.data = {}
            copied_cpp_dict = copy.copy(self)
        finally:
            self.data = data
        copied_cpp_dict.update(self)
        return copied_cpp_dict

    @classmethod
    def fromkeys(cls, iterable: Iterable[_KT], value: _VT | None = None) -> "ParsableDict[_KT, _VT]":
        new_dict: ParsableDict[_KT, _VT] = cls()
        for key in iterable:
            new_dict[key] = cast(_VT, value)  # safe, as _VT_co can be None
        return new_dict

    def update(  # type: ignore[override]
        self,
        __m: Mapping[_KT, _VT],
        **kwargs: _VT,
    ) -> None:
        """Update top-level keys with the keys from the passed in dict.

        Overrides the update() method of UserDict base class in order to include also ParsableDict
        class attributes in the update.

        If a key already exists, it will be substituted by the key from the passed in dict.
        In order to not substitute top-level keys but recursively merge (potentially nested) content
        from passed in dict into the existing, use merge() instead.

        Note:

        The behaviour of update() corresponds with default mode '-w' in the dictParser command line interface.

        The behaviour of merge() corresponds with mode '-a' in the dictParser command line interface.
        See also CLI Documentation.

        Parameters
        ----------
        __m : Mapping[TKey, TValue]
            dict containing the keys to be updated and its new values
        **kwargs: TValue
            optional keyword arguments. These will be passed on to the update() method of the parent class.
        """
        # sourcery skip: class-extract-method
        # call base class method. This takes care of updating self.data
        super().update(__m, **kwargs)
        # update attributes
        self._post_update(__m, **kwargs)
        self._clean()

        return

    def _post_update(
        self,
        __m: Mapping[_KT, _VT],
        **kwargs: _VT,  # noqa: ARG002
    ) -> None:
        # update attributes
        if isinstance(__m, ParsableDict):
            self.expressions.update(__m.expressions)
        return

    def merge(self, other: MutableMapping[_KT, _VT]) -> None:
        """Merge the passed in dict into the existing ParsableDict instance.

        In contrast to update(), merge() works recursively. That is, it does not simply substitute top-level keys but
        recursively merges (potentially nested) content from the passed in dict into the existing.
        This prevents nested keys from being deleted.
        Further, existing keys will NOT be overwritten.

        Parameters
        ----------
        other : MutableMapping[TKey, TValue]
            dict to be merged
        """
        # merge other dict into self (=into self.data)

        self._recursive_merge(self, other)
        # @TODO: An alternative we might test one day is the mergedeep module from the Python standard library:
        #        from mergedeep import merge
        #        self.data = merge(self.data, dict)
        #        CLAROS (FRALUM), 2022-01-05

        # merge ParsableDict attributes
        self._post_merge(other)
        self._clean()

        return

    def _recursive_merge(
        self,
        target_dict: MutableMapping[_KT_local, _VT_local],
        dict_to_merge: MutableMapping[_KT_local, _VT_local],
        *,
        overwrite: bool = False,
    ) -> None:
        """Merge dict_to_merge into target_dict.

        In contrast to dict.update(), _merge_dicts() works recursively.
        That is, it does not just substitute top-level keys in target_dict
        but recursively merges (potentially nested) content from dict_to_merge into target_dict.
        This prevents nested keys from being deleted.

        Parameters
        ----------
        target_dict : MutableMapping[TKey, TValue]
            target dict
        dict_to_merge : MutableMapping[TKey, TValue]
            dict to be merged into target dict
        overwrite : bool, optional
            if True, existing keys will be overwritten, by default False
        """
        for key in dict_to_merge:
            if (
                key in target_dict
                and isinstance(target_dict[key], MutableMapping)
                and isinstance(dict_to_merge[key], MutableMapping)
            ):  # dict
                self._recursive_merge(  # Recursion
                    target_dict=cast(MutableMapping[TKey, TValue], target_dict[key]),
                    dict_to_merge=cast(MutableMapping[TKey, TValue], dict_to_merge[key]),
                    overwrite=overwrite,
                )
            else:
                value_in_target_dict_contains_circular_reference = False
                if isinstance(target_dict, ParsableDict) and key in target_dict:
                    value = _insert_expression(target_dict[key], target_dict)
                    value_in_target_dict_contains_circular_reference = _value_contains_circular_reference(key, value)
                if overwrite or key not in target_dict or value_in_target_dict_contains_circular_reference:
                    target_dict[key] = dict_to_merge[key]  # Update

        return

    def _post_merge(self, other: MutableMapping[_KT, _VT]) -> None:
        # merge ParsableDict attributes
        if isinstance(other, ParsableDict):
            self._recursive_merge(self.expressions, other.expressions)
        return

    def __str__(self) -> str:
        """String representation of the ParsableDict instance in dictIO dict file format.

        Returns
        -------
        str
            the string representation
        """
        from dictIO import (
            CppFormatter,  # __str__ shall be formatted in default dict file format
        )

        formatter = CppFormatter()
        return formatter.to_string(cast(ParsableDict[TKey, TValue], self))

    def __repr__(self) -> str:
        return f"ParsableDict({self.source_file!r})"

    def __eq__(self, other: object) -> bool:
        return str(self) == str(other) if isinstance(other, ParsableDict) else False

    def order_keys(self) -> None:
        """alpha-numeric sorting of keys, recursively."""
        self.data = order_keys(self.data)
        self.expressions = order_keys(self.expressions)
        return

    def find_global_key(self, query: str = "") -> list[TKey] | None:
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
        Union[list[TKey], None]
            global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
        """
        return find_global_key(self.data, query)

    def set_global_key(self, global_key: MutableSequence[TKey], value: TValue = None) -> None:
        """Set the value for the passed in global key.

        The global key thread is traversed downwards until arrival at the target key,
        the value of which is then set.

        Parameters
        ----------
        global_key : MutableSequence[TValue]
            list of keys defining the global key thread to the target key (such as returned by method find_global_key())
        value : TValue, optional
            value the target key shall be set to, by default None
        """
        set_global_key(
            arg=cast(MutableMapping[TKey, TValue], self.data),
            global_key=global_key,
            value=value,
        )

        return

    def global_key_exists(self, global_key: MutableSequence[TKey]) -> bool:
        """Check whether the specified global key exists.

        Parameters
        ----------
        global_key : MutableSequence[TValue]
            global key the existence of which is checked

        Returns
        -------
        bool
            True if the specified global key exists, otherwise False
        """
        """
        probe the existence of (nested) keys in dict
        """
        return global_key_exists(
            dict_in=cast(MutableMapping[TKey, TValue], self.data),
            global_key=global_key,
        )

    def reduce_scope(self, scope: MutableSequence[TKey]) -> None:
        """Reduces the dict to the keys defined in scope.

        Parameters
        ----------
        scope : MutableSequence[str]
            scope the dict shall be reduced to
        """
        if scope:
            _scope: list[str] = [str(key) for key in scope]
            try:
                self.data = eval("self.data['" + "']['".join(_scope) + "']")  # noqa: S307
            except KeyError as e:
                logger.warning(f"ParsableDict.reduce_scope(): no scope '{e.args[0]}' in dictionary {self.source_file}")
        return

    @property
    def variables(self) -> dict[str, TValue]:
        """Returns a dict with all Variables currently registered.

        Returns
        -------
        Dict[str, TValue]
            dict of all Variables currently registered.
        """
        variables: dict[str, TValue] = {}

        def extract_variables_from_dict(dict_in: MutableMapping[_KT_local, _VT]) -> None:
            for key, value in dict_in.items():
                if isinstance(value, MutableMapping):
                    extract_variables_from_dict(value)  # recursion
                elif isinstance(value, MutableSequence):
                    if list_contains_dict(value):
                        extract_variables_from_list(value)  # recursion
                    else:
                        # special case: item is a list, but does NOT contain a nested dict (-> e.g. a vector or matrix)
                        variables[str(key)] = value
                else:
                    # base case: item is a single value type
                    _value = _insert_expression(value, self)
                    if not _value_contains_circular_reference(key, _value):
                        variables[str(key)] = _value
            return

        def extract_variables_from_list(list_in: MutableSequence[TValue]) -> None:
            # sourcery skip: remove-redundant-pass
            for value in list_in:
                if isinstance(value, MutableMapping):
                    extract_variables_from_dict(value)  # recursion
                elif isinstance(value, MutableSequence):
                    extract_variables_from_list(value)  # recursion
                else:
                    # By convention, list items are NOT added to the variables lookup table
                    # as they only have an index but no key
                    # (which we need, though, to serve as variable name)
                    pass
            return

        def list_contains_dict(list_in: MutableSequence[TValue]) -> bool:
            # sourcery skip: merge-duplicate-blocks, use-any
            for value in list_in:
                if isinstance(value, MutableMapping):
                    return True
                if isinstance(value, MutableSequence) and list_contains_dict(value):
                    return True
            return False

        extract_variables_from_dict(
            dict_in=self.data,
        )

        variables = order_keys(variables)

        return variables

    def _clean(self) -> None:
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within self.data:
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        """

        def _recursive_clean(data: MutableMapping[_KT_local, _VT]) -> None:
            self._clean_branch(
                branch=data,
            )
            # Recursion for nested levels
            for value in list(data.values()):
                if isinstance(value, MutableMapping):
                    _recursive_clean(value)  # Recursion

            return

        _recursive_clean(data=self.data)

        return

    def _clean_branch(self, branch: MutableMapping[_KT_local, _VT_local]) -> None:  # noqa: ARG002
        return


class ComposableDict(ParsableDict[TKey, _VT]):
    """Data structure for composable dictionaries.

    ComposableDict inherits from ParsableDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    @overload
    def __init__(
        self,
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[TKey, _VT],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[TKey, _VT]],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: str | os.PathLike[str],
        **kwargs: _VT,
    ) -> None:
        pass

    def __init__(
        self,
        arg: Mapping[TKey, _VT] | Iterable[tuple[TKey, _VT]] | str | os.PathLike[str] | None = None,
        **kwargs: _VT,
    ) -> None:
        super().__init__(arg, **kwargs)  # type: ignore[arg-type, reportArgumentType, reportCallIssue]
        self.line_comments: dict[int, str] = {}
        self.block_comments: dict[int, str] = {}
        self.includes: dict[int, tuple[str, str, Path]] = {}
        return

    def _post_update(
        self,
        __m: Mapping[str, _VT],
        **kwargs: _VT,
    ) -> None:
        super()._post_update(__m, **kwargs)
        # update attributes
        if isinstance(__m, ComposableDict):
            self.line_comments.update(__m.line_comments)
            self.block_comments.update(__m.block_comments)
            self.includes.update(__m.includes)
        return

    def _post_merge(self, other: MutableMapping[str, _VT]) -> None:
        super()._post_merge(other)
        # merge ComposableDict attributes
        if isinstance(other, ComposableDict):
            self._recursive_merge(self.line_comments, other.line_comments)
            self._recursive_merge(self.block_comments, other.block_comments)
            self._recursive_merge(self.includes, other.includes)
        return

    def order_keys(self) -> None:
        """alpha-numeric sorting of keys, recursively."""
        super().order_keys()
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.includes = order_keys(self.includes)
        return

    def include(self, dict_to_include: ParsableDict[_KT_local, _VT_local]) -> None:
        """Add an include directive for the passed in dict.

        Parameters
        ----------
        dict_to_include : ParsableDict
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
            break
        self.data[placeholder] = cast(_VT, placeholder)  # safe, as _VT_co can be str
        self.includes.update({ii: (include_directive, include_file_name, include_file_path)})
        return

    def _clean_branch(self, branch: MutableMapping[_KT_local, _VT_local]) -> None:
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within data:
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        """
        super()._clean_branch(branch)
        # IDENTIFY all placeholders on current level
        _keys_on_this_level: list[TKey] = list(branch.keys())
        key_type_on_this_level: type[TKey | None] = NoneType
        if _keys_on_this_level:
            key_type_on_this_level = type(_keys_on_this_level[0])
        if key_type_on_this_level is not str:
            return
        _branch: MutableMapping[str, _VT_local] = cast(MutableMapping[str, _VT_local], branch)
        keys_on_this_level: list[str] = list(_branch)
        block_comments_on_this_level: list[str] = []
        includes_on_this_level: list[str] = []
        line_comments_on_this_level: list[str] = []
        for key in keys_on_this_level:
            if re.search(r"BLOCKCOMMENT\d{6}", key):
                block_comments_on_this_level.append(key)
            elif re.search(r"INCLUDE\d{6}", key):
                includes_on_this_level.append(key)
            elif re.search(r"LINECOMMENT\d{6}", key):
                line_comments_on_this_level.append(key)
        _id: int
        unique_block_comments_on_this_level: list[str] = []  # BLOCKCOMMENTs
        for _block_comment in block_comments_on_this_level:
            with contextlib.suppress(Exception):
                _id = int(re.findall(r"\d{6}", _block_comment)[0])
                block_comment: str = self.block_comments[_id]
                if block_comment in unique_block_comments_on_this_level:
                    # Found doublette
                    # Remove from current level in data (the dict)
                    del _branch[_block_comment]
                    # ..AND from self.block_comments (the lookup table)
                    del self.block_comments[_id]
                else:
                    # Unique
                    unique_block_comments_on_this_level.append(block_comment)
        unique_includes_on_this_level: list[tuple[str, str, Path]] = []  # INCLUDEs
        for _include in includes_on_this_level:
            with contextlib.suppress(Exception):
                _id = int(re.findall(r"\d{6}", str(_include))[0])
                include: tuple[str, str, Path] = self.includes[_id]
                if include in unique_includes_on_this_level:
                    # Found doublette
                    # Remove from current level in data (the dict)
                    del _branch[_include]
                    # ..AND from self.includes (the lookup table)
                    del self.includes[_id]
                else:
                    # Unique
                    unique_includes_on_this_level.append(include)
        unique_line_comments_on_this_level: list[str] = []  # LINECOMMENTs
        for _line_comment in line_comments_on_this_level:
            with contextlib.suppress(Exception):
                _id = int(re.findall(r"\d{6}", str(_line_comment))[0])
                line_comment: str = self.line_comments[_id]
                if line_comment in unique_line_comments_on_this_level:
                    # Found doublette
                    # Remove from current level in data (the dict)
                    del _branch[_line_comment]
                    # ..AND from self.line_comments (the lookup table)
                    del self.line_comments[_id]
                else:
                    # Unique
                    unique_line_comments_on_this_level.append(line_comment)
        return


class CppDict(ComposableDict[TValue]):
    """Data structure for C++ dictionaries.

    CppDict inherits from ParsableDict. It can hence be used transparently also in a context
    where a dict or any other MutableMapping type is expected.
    """

    @overload
    def __init__(
        self,
        **kwargs: TValue,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[str, TValue],
        **kwargs: TValue,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[str, TValue]],
        **kwargs: TValue,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: str | os.PathLike[str],
        **kwargs: TValue,
    ) -> None:
        pass

    def __init__(
        self,
        arg: Mapping[str, TValue] | Iterable[tuple[str, TValue]] | str | os.PathLike[str] | None = None,
        **kwargs: TValue,
    ) -> None:
        super().__init__(arg, **kwargs)  # type: ignore[arg-type, reportArgumentType, reportCallIssue]
        return


def order_keys(arg: MutableMapping[_KT, _VT]) -> dict[_KT, _VT]:
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
    sorted_dict: dict[_KT, _VT] = dict(sorted(arg.items(), key=lambda x: (isinstance(x[0], str), x[0])))
    for key, value in deepcopy(sorted_dict).items():
        if isinstance(value, MutableMapping):
            sorted_dict[key] = order_keys(value)  # type: ignore[assignment]  # Recursion
    return sorted_dict


def find_global_key(
    arg: MutableMapping[_KT, _VT] | MutableSequence[_VT],
    query: str = "",
) -> list[TKey] | None:
    """Return the global key thread to the first key the value of which matches the passed in query.

    Parameters
    ----------
    arg : Union[MutableMapping[TKey, TValue], MutableSequence[TValue]]
        dict to search in for the queried value
    query : str, optional
        query string for the value to search for, by default ''

    Returns
    -------
    Union[List, None]
        global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
    """
    global_key: list[TKey] = []
    if isinstance(arg, MutableMapping):  # dict
        for key, value in sorted(arg.items()):
            if isinstance(value, MutableMapping | MutableSequence):
                if next_level_key := find_global_key(arg=value, query=query):
                    global_key.append(key)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(value)):
                global_key.append(key)
                break
    else:  # list
        for index, value in enumerate(arg):
            if isinstance(value, MutableMapping | MutableSequence):
                if next_level_key := find_global_key(arg=value, query=query):
                    global_key.append(index)
                    global_key.extend(next_level_key)
                    break
            elif re.search(query, str(value)):
                global_key.append(index)
                break

    return global_key or None


def set_global_key(
    arg: MutableMapping[TKey, TValue],
    global_key: MutableSequence[TKey],
    value: TValue | None = None,
) -> None:
    """Set the value for the passed in global key.

    Parameters
    ----------
    arg : MutableMapping[TKey, TValue]
        dict the target key in which shall be set
    global_key : MutableSequence[TValue], optional
        list of keys defining the global key thread to the target key (such as returned by method find_global_key())
    value : TValue, optional
        value the target key shall be set to, by default None
    """
    if not global_key:
        return

    last_branch: MutableMapping[TKey, TValue] | MutableSequence[TValue]
    next_branch: MutableMapping[TKey, TValue] | MutableSequence[TValue] | TValue
    remaining_keys: MutableSequence[TKey]

    last_branch = arg
    next_branch = None
    remaining_keys = global_key
    ii: int = 0
    while len(remaining_keys) > 1:
        # as long as we didn't arrive at the last branch (the one that contains the target key)..
        next_branch = last_branch[remaining_keys[0]]  # ..walk one level further down
        if not isinstance(next_branch, MutableMapping | MutableSequence):
            raise KeyError(f"KeyError: {global_key} not found in {arg}")
        last_branch = next_branch
        remaining_keys = remaining_keys[1:]
        ii += 1
        if ii == 10:  # noqa: PLR2004
            raise RecursionError(
                "RecursionError: Maximum recursion depth exceeded in set_global_key()."
                "set_global_key() is not designed to handle more than 10 levels of nested keys."
            )
    last_branch[remaining_keys[0]] = value

    return


def global_key_exists(
    dict_in: MutableMapping[TKey, TValue],
    global_key: MutableSequence[TKey],
) -> bool:
    """Check whether the specified global key exists in the passed in dict.

    Parameters
    ----------
    dict_in : MutableMapping[TKey, TValue]
        dict to check for existence of the specified global key
    global_key : MutableSequence[TKey]
        global key the existence of which is checked in the passed in dict

    Returns
    -------
    bool
        True if the specified global key exists, otherwise False
    """
    _last_branch: MutableMapping[TKey, TValue] = dict_in
    _next_branch: MutableMapping[TKey, TValue] | TValue
    try:
        for key in global_key:
            _next_branch = _last_branch[key]
            if not isinstance(_next_branch, MutableMapping):
                return False
            _last_branch = _next_branch
    except KeyError:
        return False
    return True


def _insert_expression(value: TValue, cpp_dict: ParsableDict[_KT, _VT]) -> TValue:
    if not isinstance(value, str):
        return value
    if not re.search(r"EXPRESSION\d{6}", value):
        return value
    if match_index := re.search(r"\d{6}", value):
        index = int(match_index[0])
        return cpp_dict.expressions[index]["expression"] if index in cpp_dict.expressions else value
    return value


def _value_contains_circular_reference(key: TKey, value: TValue) -> bool:
    if isinstance(key, str) and isinstance(value, str):
        return key in value
    return False
