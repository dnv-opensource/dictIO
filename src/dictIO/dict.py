# pyright: reportIncompatibleMethodOverride=false
# pyright: reportUnnecessaryTypeIgnoreComment=false
# ruff: noqa: ERA001
from __future__ import annotations

import contextlib
import logging
import os
import re
import warnings
from _collections_abc import Iterable, Mapping, MutableMapping, MutableSequence
from copy import copy
from pathlib import Path
from types import NoneType
from typing import (
    TypeVar,
    cast,
    overload,
)

from dictIO.types import TKey, TValue
from dictIO.utils.counter import BorgCounter
from dictIO.utils.dict import (
    find_global_key,
    global_key_exists,
    order_keys,
    set_global_key,
)
from dictIO.utils.path import relative_path

__ALL__ = [
    "SDict",
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


class SDict(dict[_KT, _VT]):
    """Data structure for generic dictionaries.

    SDict inherits from UserDict. It can hence be used transparently also in a context
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

        if base_dict is None:
            super().__init__()
        else:
            super().__init__(base_dict)

        if kwargs:
            self.update(**kwargs)

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
        self.line_comments: dict[int, str] = {}
        self.block_comments: dict[int, str] = {}
        self.includes: dict[int, tuple[str, str, Path]] = {}

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

        return

    @overload
    def __or__(
        self,
        other: dict[_KT, _VT],
    ) -> SDict[_KT, _VT]:
        pass

    @overload
    def __or__(
        self,
        other: dict[_KT_local, _VT_local],
    ) -> SDict[_KT | _KT_local, _VT | _VT_local]:
        pass

    def __or__(
        self,
        other: dict[_KT, _VT] | dict[_KT_local, _VT_local],
    ) -> SDict[_KT, _VT] | SDict[_KT | _KT_local, _VT | _VT_local]:
        """left `or` operation: `self | other`.

        The `__or__()` method is called by the ` | ` operator when it is used with `self` on the left-hand side.

        Parameters
        ----------
        other : MutableMapping[_KT, _VT]
            The other dictionary

        Returns
        -------
        SDict[_KT, _VT]
            A new SDict instance containing the content of `self` updated with the content of `other`.
        """
        new_dict: SDict[_KT | _KT_local, _VT | _VT_local]
        new_dict = cast(
            SDict[_KT | _KT_local, _VT | _VT_local],
            self.__class__(super().__or__(other)),
        )
        # update attributes
        new_dict._post_update(other)
        new_dict._clean()
        return new_dict

    @overload
    def __ror__(
        self,
        other: dict[_KT, _VT],
    ) -> SDict[_KT, _VT]:
        pass

    @overload
    def __ror__(
        self,
        other: dict[_KT_local, _VT_local],
    ) -> SDict[_KT | _KT_local, _VT | _VT_local]:
        pass

    def __ror__(
        self,
        other: dict[_KT, _VT] | dict[_KT_local, _VT_local],
    ) -> SDict[_KT, _VT] | SDict[_KT | _KT_local, _VT | _VT_local]:
        """right `or` operation: `other | self`.

        The `__ror__()` method is called by the ` | ` operator when it is used with `self` on the right-hand side.
        This method is only called if `other` and `self` are of different types
        and `other` does not implement `__or__()`, i.e. other.__or__() returns `NotImplemented`.

        Parameters
        ----------
        other : MutableMapping[_KT, _VT]
            The other dictionary

        Returns
        -------
        SDict[_KT, _VT]
            A new SDict instance containing the content of `other` updated with the content of `self`.
        """
        new_dict: SDict[_KT | _KT_local, _VT | _VT_local]
        new_dict = cast(
            SDict[_KT | _KT_local, _VT | _VT_local],
            self.__class__(super().__ror__(other)),
        )
        # update attributes
        new_dict._post_update(self)
        new_dict._clean()
        return new_dict

    @overload  # type: ignore[override]
    def __ior__(
        self,
        other: Mapping[_KT, _VT],
    ) -> SDict[_KT, _VT]:
        pass

    @overload
    def __ior__(
        self,
        other: Iterable[tuple[_KT, _VT]],
    ) -> SDict[_KT, _VT]:
        pass

    # TODO @CLAROS: Change return type to `Self` (from `typing`module)
    #      once we drop support for Python 3.10
    #      (see https://docs.python.org/3/library/typing.html#typing.Self)
    #      CLAROS, 2024-10-15
    def __ior__(  # noqa: PYI034
        self,
        other: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]],
    ) -> SDict[_KT, _VT]:
        # def __ior__(self, other: MutableMapping[_KT, _VT]) -> SDict[_KT, _VT]:
        """augmented `or` operation: `self |= other`.

        The `__ior__()` method is called by the ` |= ` operator with `self` on the left-hand side.
        The content of `self` gets updated with the content of `other`.

        Parameters
        ----------
        other : MutableMapping[_KT, _VT]
            The other dictionary

        Returns
        -------
        SDict[_KT, _VT]
            Reference to `self`.
        """
        should_be_self = super().__ior__(other)
        assert should_be_self is self
        # update attributes
        self._post_update(other)
        self._clean()
        return self

    def __copy__(self) -> SDict[_KT, _VT]:
        copied_dict = self.__class__.__new__(self.__class__)
        copied_dict.__dict__.update(self.__dict__)
        copied_dict.update(super().copy())
        return copied_dict

    def copy(self) -> SDict[_KT, _VT]:
        copied_dict = copy(self)  # calls __copy__()
        return copied_dict

    @overload
    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_KT_local],
        value: None = None,
    ) -> SDict[_KT_local, TValue | None]:
        pass

    @overload
    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_KT_local],
        value: _VT_local,
    ) -> SDict[_KT_local, _VT_local]:
        pass

    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_KT_local],
        value: _VT_local | None = None,
    ) -> SDict[_KT_local, _VT_local] | SDict[_KT_local, TValue | None]:
        new_dict: SDict[_KT_local, _VT_local] = cast(SDict[_KT_local, _VT_local], cls())
        for key in iterable:
            new_dict[key] = cast(_VT_local, value)  # cast is safe, as `None` is within the type bounds of _VT
        return new_dict

    @overload  # type: ignore[override]
    def update(
        self,
        m: Mapping[_KT, _VT],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def update(
        self,
        m: Iterable[tuple[_KT, _VT]],
        **kwargs: _VT,
    ) -> None:
        pass

    @overload
    def update(
        self,
        **kwargs: _VT,
    ) -> None:
        pass

    def update(
        self,
        m: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]] | None = None,
        **kwargs: _VT,
    ) -> None:
        """Update top-level keys with the keys from the passed in dict.

        Overrides the update() method of UserDict base class in order to include also SDict
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
        if m is None:
            super().update(**kwargs)
        else:
            super().update(m, **kwargs)
        # update attributes
        self._post_update(m, **kwargs)
        self._clean()
        return

    def _post_update(
        self,
        m: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]] | None = None,
        **kwargs: _VT,  # noqa: ARG002
    ) -> None:
        # update attributes
        if isinstance(m, SDict):
            self.expressions.update(m.expressions)
            self.line_comments.update(m.line_comments)
            self.block_comments.update(m.block_comments)
            self.includes.update(m.includes)
        return

    def merge(self, other: Mapping[_KT, _VT]) -> None:
        """Merge the passed in dict into the existing SDict instance.

        In contrast to update(), merge() works recursively. That is, it does not simply substitute top-level keys but
        recursively merges (potentially nested) content from the passed in dict into the existing.
        This prevents nested keys from being deleted.
        Further, existing keys will NOT be overwritten.

        Parameters
        ----------
        other : MutableMapping[TKey, TValue]
            dict to be merged
        """
        # merge other dict into self (=into self)

        self._recursive_merge(self, other)
        # @TODO: An alternative we might test one day is the mergedeep module from the Python standard library:
        #        from mergedeep import merge
        #        self = merge(self, dict)
        #        CLAROS (FRALUM), 2022-01-05

        # merge SDict attributes
        self._post_merge(other)
        self._clean()

        return

    def _recursive_merge(
        self,
        target_dict: MutableMapping[_KT_local, _VT_local],
        dict_to_merge: Mapping[_KT_local, _VT_local],
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
        dict_to_merge : Mapping[TKey, TValue]
            dict to be merged into target dict
        overwrite : bool, optional
            if True, existing keys will be overwritten, by default False
        """
        for key in dict_to_merge:
            if (
                key in target_dict
                and isinstance(target_dict[key], MutableMapping)
                and isinstance(dict_to_merge[key], Mapping)
            ):  # dict
                self._recursive_merge(  # Recursion
                    target_dict=cast(MutableMapping[TKey, TValue], target_dict[key]),
                    dict_to_merge=cast(Mapping[TKey, TValue], dict_to_merge[key]),
                    overwrite=overwrite,
                )
            else:
                value_in_target_dict_contains_circular_reference = False
                if isinstance(target_dict, SDict) and key in target_dict:
                    value = _insert_expression(target_dict[key], target_dict)
                    value_in_target_dict_contains_circular_reference = _value_contains_circular_reference(key, value)
                if overwrite or key not in target_dict or value_in_target_dict_contains_circular_reference:
                    target_dict[key] = dict_to_merge[key]  # Update

        return

    def _post_merge(self, other: Mapping[_KT, _VT]) -> None:
        # merge SDict attributes
        if isinstance(other, SDict):
            self._recursive_merge(self.expressions, other.expressions)
            self._recursive_merge(self.line_comments, other.line_comments)
            self._recursive_merge(self.block_comments, other.block_comments)
            self._recursive_merge(self.includes, other.includes)
        return

    def include(self, dict_to_include: SDict[_KT_local, _VT_local]) -> None:
        """Add an include directive for the passed in dict.

        Parameters
        ----------
        dict_to_include : SDict
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
            if placeholder in self:
                continue
            break
        # cast is safe, as `str` is within the type bounds of both _KT and _VT
        self[cast(_KT, placeholder)] = cast(_VT, placeholder)
        self.includes.update({ii: (include_directive, include_file_name, include_file_path)})
        return

    def __str__(self) -> str:
        """String representation of the SDict instance in dictIO dict file format.

        Returns
        -------
        str
            the string representation
        """
        from dictIO import (
            CppFormatter,  # __str__ shall be formatted in default dict file format
        )

        formatter = CppFormatter()
        return formatter.to_string(cast(SDict[TKey, TValue], self))

    def __repr__(self) -> str:
        return f"SDict({self.source_file!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SDict):
            return str(self) == str(other)
        return super().__eq__(other)

    def order_keys(self) -> None:
        """alpha-numeric sorting of keys, recursively."""
        _ = order_keys(self)
        self.expressions = order_keys(self.expressions)
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.includes = order_keys(self.includes)
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
        return find_global_key(self, query)

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
            arg=cast(MutableMapping[TKey, TValue], self),
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
            dict_in=cast(MutableMapping[TKey, TValue], self),
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
                reduced_dict = eval("self['" + "']['".join(_scope) + "']")  # noqa: S307
                self.clear()
                self.update(reduced_dict)
            except KeyError as e:
                logger.warning(f"SDict.reduce_scope(): no scope '{e.args[0]}' in dictionary {self.source_file}")
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
            dict_in=self,
        )

        variables = order_keys(variables)

        return variables

    def _clean(self) -> None:
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within self:
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

        _recursive_clean(data=self)

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
        # IDENTIFY all placeholders on current level
        _keys_on_this_level: list[_KT_local] = list(branch.keys())
        key_type_on_this_level: type[_KT_local | None] = NoneType
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

    # The `data` property is added for backwards compatibility
    # with CppDict class from dictIO <= v0.3.4
    # It is marked as deprecated and will be removed in a future release.
    @property
    def data(self) -> dict[_KT, _VT]:
        warnings.warn(
            f"`{self.__class__.__name__}.data` is deprecated. Use `SDict` directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    @data.setter
    def data(self, data: dict[_KT, _VT]) -> None:
        warnings.warn(
            f"`{self.__class__.__name__}.data` is deprecated. Use `SDict.update()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.clear()
        self.update(data)
        return


class CppDict(SDict[TKey, TValue]):
    #     """Data structure for C++ dictionaries.

    #     CppDict inherits from SDict. It can hence be used transparently also in a context
    #     where a dict or any other MutableMapping type is expected.
    #     """
    @overload
    def __init__(
        self,
        **kwargs: TValue,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[TKey, TValue],
        **kwargs: TValue,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[TKey, TValue]],
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
        arg: Mapping[TKey, TValue] | Iterable[tuple[TKey, TValue]] | str | os.PathLike[str] | None = None,
        **kwargs: TValue,
    ) -> None:
        warnings.warn(
            "`CppDict` is deprecated. Use `SDict[TKey, TValue]` instead.",
            DeprecationWarning,
            stacklevel=1,
        )
        super().__init__(arg, **kwargs)  # type: ignore[arg-type, reportArgumentType, reportCallIssue]
        return


def _insert_expression(value: TValue, s_dict: SDict[_KT, _VT]) -> TValue:
    if not isinstance(value, str):
        return value
    if not re.search(r"EXPRESSION\d{6}", value):
        return value
    if match_index := re.search(r"\d{6}", value):
        index = int(match_index[0])
        return s_dict.expressions[index]["expression"] if index in s_dict.expressions else value
    return value


def _value_contains_circular_reference(key: TKey, value: TValue) -> bool:
    if isinstance(key, str) and isinstance(value, str):
        return key in value
    return False
