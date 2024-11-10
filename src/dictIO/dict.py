"""SDict class definition."""

# pyright: reportIncompatibleMethodOverride=false
# pyright: reportUnnecessaryTypeIgnoreComment=false
from __future__ import annotations

import contextlib
import logging
import os
import re
import warnings
from _collections_abc import Iterable, Mapping, MutableMapping, MutableSequence
from copy import copy
from pathlib import Path
from typing import (
    TypeVar,
    cast,
    overload,
)

from dictIO.types import K, TGlobalKey, TKey, TValue, V
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
]


# Private versions of the generic type variables for keys and values.
# These are used in local scopes, where there is a need to define new type variables
# with the same constraints as the global ones, yet without being bound to them.
_K = TypeVar("_K", bound=TKey)
_V = TypeVar("_V", bound=TValue)

logger = logging.getLogger(__name__)


class SDict(dict[K, V]):
    """Generic data structure for serializable dictionaries. Core class in dictIO.

    SDict inherits from dict. It can hence be used transparently in any context
    where a dict or any other MutableMapping type is expected.
    """

    @overload
    def __init__(
        self,
        **kwargs: V,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[K, V],
        **kwargs: V,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[K, V]],
        **kwargs: V,
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: str | os.PathLike[str],
        **kwargs: V,
    ) -> None:
        pass

    def __init__(
        self,
        arg: Mapping[K, V] | Iterable[tuple[K, V]] | str | os.PathLike[str] | None = None,
        **kwargs: V,
    ) -> None:
        source_file: str | os.PathLike[str] | None = None
        base_dict: MutableMapping[K, V] | None = None

        if isinstance(arg, Mapping):
            base_dict = dict(cast(Mapping[K, V], arg))
        elif isinstance(arg, str | os.PathLike):
            source_file = arg
        elif isinstance(arg, Iterable):
            base_dict = dict(cast(Iterable[tuple[K, V]], arg))  # type: ignore[reportUnnecessaryCast]

        if base_dict:
            super().__init__(base_dict)
        else:
            super().__init__()

        self.counter: BorgCounter = BorgCounter()
        self._source_file: Path | None = None
        self._path: Path = Path.cwd()
        self._name: str = ""

        if source_file:
            # Make sure source_file is of type Path. If not, cast it to Path type.
            source_file = source_file if isinstance(source_file, Path) else Path(source_file)
            self._set_source_file(source_file)
        else:
            self._set_source_file(None)

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

        if kwargs:
            self.update(**kwargs)

        return

    @overload  # type: ignore[override]
    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_K],
        value: None = None,
    ) -> SDict[_K, TValue | None]:
        pass

    @overload
    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_K],
        value: _V,
    ) -> SDict[_K, _V]:
        pass

    @classmethod
    def fromkeys(
        cls,
        iterable: Iterable[_K],
        value: _V | None = None,
    ) -> SDict[_K, _V] | SDict[_K, TValue | None]:
        """Create a new SDict instance from the keys of an iterable.

        Parameters
        ----------
        iterable : Iterable[_K]
            An iterable with keys
        value : _V | None, optional
            The value to be assigned to the passed in keys, by default None

        Returns
        -------
        SDict[_K, _V] | SDict[_K, TValue | None]
            The created SDict instance.
        """
        new_dict: SDict[_K, _V] = cast(SDict[_K, _V], cls())
        for key in iterable:
            new_dict[key] = cast(_V, value)  # cast is safe, as `None` is within the type bounds of V
        return new_dict

    # TODO @CLAROS: Change return type to `Self` (from `typing`module)
    #      once we drop support for Python 3.10
    #      (see https://docs.python.org/3/library/typing.html#typing.Self)
    #      CLAROS, 2024-10-15
    def load(
        self,
        source_file: str | os.PathLike[str],
    ) -> SDict[K, V]:
        """Load a dict file into this SDict instance.

        Reads a dict file and loads its content into the current SDict instance.
        The content of the current SDict instance will be overwritten.

        Following file formats are supported and interpreted through source_file's file ending:
        no file ending   ->   dictIO native dict file
        '.cpp'           ->   dictIO native dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file

        Parameters
        ----------
        source_file : Union[str, os.PathLike[str]]
            dict file to be loaded

        Returns
        -------
        SDict[K, V]
            self

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f"source_file not found: {source_file}")
            raise FileNotFoundError(source_file)

        # Log a warning in case the current SDict instance is not empty,
        # as the load() method will overwrite the current content.
        if self:
            logger.warning("SDict instance is not empty. `load()` will overwrite current content will.")

        from dictIO.dict_reader import DictReader

        loaded_dict: SDict[TKey, TValue] = DictReader.read(
            source_file=source_file,
        )
        self.reset()
        # TODO @CLAROS: Improve type hinting for `loaded_dict`. Currently, it is cast to `SDict[K, V]`,
        #      which is not correct, as we do not know upfront the type of keys and values in `loaded_dict`.
        #      Maybe this method needs to be refactored to a factory function, returning a new `SDict` instance
        #      with the actual types of `loaded_dict`.
        #      CLAROS, 2024-11-06
        self.update(cast(SDict[K, V], loaded_dict))
        self._set_source_file(source_file)
        return self

    def dump(
        self,
        target_file: str | os.PathLike[str] | None = None,
    ) -> Path:
        """Dump the content of the current SDict instance into a dict file.

        Following file formats are supported and interpreted through target_file's file ending:
        no file ending   ->   dictIO native dict file
        '.cpp'           ->   dictIO native dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file

        Parameters
        ----------
        target_file : Union[str, os.PathLike[str], None], optional
            target dict file name, by default None

        Returns
        -------
        Path
            target dict file

        Raises
        ------
        ValueError
            if target_file was not specified while the current SDict instance has no source file set
            (and hence the target file cannot be inferred).
        """
        if target_file is None and self._source_file is None:
            raise ValueError("target_file must be specified if the current SDict instance has no source file set.")
        if target_file is None:
            target_file = self._source_file
        assert target_file is not None

        # Make sure target_file argument is of type Path. If not, cast it to Path type.
        target_file = target_file if isinstance(target_file, Path) else Path(target_file)

        from dictIO.dict_writer import DictWriter

        DictWriter.write(
            source_dict=cast(SDict[TKey, TValue], self),
            target_file=target_file,
        )
        self._set_source_file(target_file)

        return target_file

    @property
    def source_file(self) -> Path | None:
        """Return the source file of the SDict instance.

        Returns
        -------
        Path or None
            source file of the SDict instance
        """
        return self._source_file

    @source_file.setter
    def source_file(self, source_file: Path | None) -> None:
        """Set the source file of the SDict instance."""
        self._set_source_file(source_file)
        return

    def _set_source_file(self, source_file: Path | None) -> None:
        if source_file is None:
            self._reset_source_file()
            return
        self._source_file = source_file.absolute()
        self._path = self._source_file.parent
        self._name = self._source_file.name
        return

    @property
    def path(self) -> Path:
        """Return the path of the source file of the SDict instance.

        Returns
        -------
        Path
            path of the source file of the SDict instance
        """
        return self._path

    @property
    def name(self) -> str:
        """Return the name of the source file of the SDict instance.

        Returns
        -------
        str
            name of the source file of the SDict instance
        """
        return self._name

    @property
    def variables(self) -> dict[str, TValue]:
        """Returns a dict with all Variables currently registered.

        Returns
        -------
        Dict[str, TValue]
            dict of all Variables currently registered.
        """
        variables: MutableMapping[str, TValue] = {}

        def extract_variables_from_dict(dict_in: MutableMapping[_K, V]) -> None:
            for key, value in dict_in.items():
                # 1: Check for value types that trigger recursion
                #    (dict  or  list of dicts)
                if isinstance(value, MutableMapping):
                    extract_variables_from_dict(dict_in=value)  # recursion
                elif isinstance(value, MutableSequence) and list_contains_dict(list_in=value):
                    extract_variables_from_list(list_in=value)  # recursion
                # 2: All other value types are considered variables, given that their key is of type string
                #    (by convention, only strings are allowed as variable names)
                if type(key) is not str:
                    continue
                if isinstance(value, MutableSequence):
                    # special case: item is a list, but does NOT contain a nested dict (-> e.g. a vector or matrix)
                    variables[key] = value
                else:
                    # base case: item is a single value type
                    _value = _insert_expression(value, self)
                    if not _value_contains_circular_reference(key, _value):
                        variables[key] = _value
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

        return dict(variables)

    @overload  # type: ignore[override]
    def update(
        self,
        m: Mapping[K, V],
        **kwargs: V,
    ) -> None:
        pass

    @overload
    def update(
        self,
        m: Iterable[tuple[K, V]],
        **kwargs: V,
    ) -> None:
        pass

    @overload
    def update(
        self,
        **kwargs: V,
    ) -> None:
        pass

    def update(
        self,
        m: Mapping[K, V] | Iterable[tuple[K, V]] | None = None,
        **kwargs: V,
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
        m: Mapping[K, V] | Iterable[tuple[K, V]] | None = None,
        **kwargs: V,  # noqa: ARG002
    ) -> None:
        # update attributes
        if isinstance(m, SDict):
            self.expressions.update(m.expressions)
            self.line_comments.update(m.line_comments)
            self.block_comments.update(m.block_comments)
            self.includes.update(m.includes)
        return

    def merge(self, other: Mapping[K, V]) -> None:
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
        # merge SDict attributes
        self._post_merge(other)
        self._clean()

        return

    def _recursive_merge(
        self,
        target_dict: MutableMapping[_K, _V],
        dict_to_merge: Mapping[_K, _V],
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
        target_dict : MutableMapping[TKey, TValue] | MutableMapping[int, TValue]
            target dict
        dict_to_merge : Mapping[TKey, TValue] | Mapping[int, TValue]
            dict to be merged into target dict
        overwrite : bool, optional
            if True, existing keys will be overwritten, by default False
        """
        for key in dict_to_merge:
            if (
                key in target_dict
                and isinstance(target_dict[key], MutableMapping)  # pyright: ignore[reportArgumentType]
                and isinstance(dict_to_merge[key], Mapping)  # pyright: ignore[reportArgumentType]
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

    def _post_merge(self, other: Mapping[K, V]) -> None:
        # merge SDict attributes
        if isinstance(other, SDict):
            self._recursive_merge(target_dict=self.expressions, dict_to_merge=other.expressions)
            self._recursive_merge(target_dict=self.line_comments, dict_to_merge=other.line_comments)
            self._recursive_merge(target_dict=self.block_comments, dict_to_merge=other.block_comments)
            self._recursive_merge(target_dict=self.includes, dict_to_merge=other.includes)
        return

    def include(self, dict_to_include: SDict[_K, _V]) -> None:
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
        if not self._source_file:
            raise AttributeError(
                f"Cannot include {dict_to_include.name}. Attribute '.source_file' of {self._name} is None."
            )

        include_file_path = dict_to_include.source_file
        relative_file_path: Path
        try:
            relative_file_path = relative_path(
                from_path=self._source_file.parent,
                to_path=dict_to_include.source_file,
            )
        except ValueError as e:
            raise ValueError(
                f"Cannot include {dict_to_include.name}. Relative path to {dict_to_include.name} could not be resolved."
            ) from e

        from dictIO import NativeFormatter

        formatter = NativeFormatter()
        include_file_name = str(relative_file_path)
        include_file_name = include_file_name.replace("\\", "\\\\")
        include_file_name = formatter.format_value(include_file_name)

        include_directive = f"#include {include_file_name}"

        ii: int = 0
        placeholder: str = ""
        while True:
            ii = self.counter()
            placeholder = "INCLUDE%06i" % ii
            if placeholder in self:
                continue
            break
        # cast is safe, as `str` is within the type bounds of both K and V
        self[cast(K, placeholder)] = cast(V, placeholder)
        self.includes.update({ii: (include_directive, include_file_name, include_file_path)})
        return

    @overload  # type: ignore[override]
    def __or__(
        self,
        other: dict[K, V],
    ) -> SDict[K, V]:
        pass

    @overload
    def __or__(
        self,
        other: dict[_K, _V],
    ) -> SDict[K | _K, V | _V]:
        pass

    def __or__(
        self,
        other: dict[K, V] | dict[_K, _V],
    ) -> SDict[K, V] | SDict[K | _K, V | _V]:
        """Left `or` operation: `self | other`.

        The `__or__()` method is called by the ` | ` operator when it is used with `self` on the left-hand side.

        Parameters
        ----------
        other : MutableMapping[K, V]
            The other dictionary

        Returns
        -------
        SDict[K, V]
            A new SDict instance containing the content of `self` updated with the content of `other`.
        """
        new_dict: SDict[K | _K, V | _V]
        new_dict = cast(
            SDict[K | _K, V | _V],
            self.__class__(
                cast(
                    Mapping[K, V],
                    super().__or__(other),
                )
            ),
        )
        # update attributes
        new_dict._post_update(
            cast(
                Mapping[K | _K, V | _V],
                other,
            )
        )
        new_dict._clean()
        return new_dict

    @overload  # type: ignore[override]
    def __ror__(
        self,
        other: dict[K, V],
    ) -> dict[K, V]:
        pass

    @overload
    def __ror__(
        self,
        other: dict[_K, _V],
    ) -> dict[K | _K, V | _V]:
        pass

    def __ror__(
        self,
        other: dict[K, V] | dict[_K, _V],
    ) -> dict[K, V] | dict[K | _K, V | _V]:
        """Right `or` operation: `other | self`.

        The `__ror__()` method is called by the ` | ` operator when it is used with `self` on the right-hand side.
        This method is only called if `other` and `self` are of different types
        and `other` does not implement `__or__()`, i.e. other.__or__() returns `NotImplemented`.

        Parameters
        ----------
        other : dict[K, V]
            The other dictionary

        Returns
        -------
        SDict[K, V]
            A new SDict instance containing the content of `other` updated with the content of `self`.
        """
        new_dict: SDict[K | _K, V | _V]
        new_dict = cast(
            SDict[K | _K, V | _V],
            self.__class__(super().__ror__(cast(dict[K, V], other))),
        )
        # update attributes
        new_dict._post_update(cast(SDict[K | _K, V | _V], self))
        new_dict._clean()
        return new_dict

    @overload  # type: ignore[override]
    def __ior__(
        self,
        other: Mapping[K, V],
    ) -> SDict[K, V]:
        pass

    @overload
    def __ior__(
        self,
        other: Iterable[tuple[K, V]],
    ) -> SDict[K, V]:
        pass

    # TODO @CLAROS: Change return type to `Self` (from `typing`module)
    #      once we drop support for Python 3.10
    #      (see https://docs.python.org/3/library/typing.html#typing.Self)
    #      CLAROS, 2024-10-15
    def __ior__(  # noqa: PYI034
        self,
        other: Mapping[K, V] | Iterable[tuple[K, V]],
    ) -> SDict[K, V]:
        # def __ior__(self, other: MutableMapping[K, V]) -> SDict[K, V]:
        """Augmented `or` operation: `self |= other`.

        The `__ior__()` method is called by the ` |= ` operator with `self` on the left-hand side.
        The content of `self` gets updated with the content of `other`.

        Parameters
        ----------
        other : MutableMapping[K, V]
            The other dictionary

        Returns
        -------
        SDict[K, V]
            Reference to `self`.
        """
        should_be_self = super().__ior__(other)
        assert should_be_self is self
        # update attributes
        self._post_update(other)
        self._clean()
        return self

    def __copy__(self) -> SDict[K, V]:
        """Return a shallow copy of the SDict instance.

        Returns
        -------
        SDict[K, V]
            shallow copy of the SDict instance
        """
        copied_dict = self.__class__.__new__(self.__class__)
        copied_dict.__dict__.update(self.__dict__)
        copied_dict.update(super().copy())
        return copied_dict

    def copy(self) -> SDict[K, V]:
        """Return a shallow copy of the SDict instance.

        Returns
        -------
        SDict[K, V]
            shallow copy of the SDict instance
        """
        copied_dict = copy(self)  # calls __copy__()
        return copied_dict

    def __str__(self) -> str:
        """Return a string representation of the SDict instance in dictIO native format.

        Returns
        -------
        str
            the string representation
        """
        from dictIO import (
            NativeFormatter,  # __str__ shall be formatted in dictIO native file format
        )

        formatter = NativeFormatter()
        return formatter.to_string(cast(SDict[TKey, TValue], self))

    def __repr__(self) -> str:
        """Return a string representation of the SDict instance.

        Returns
        -------
        str
            string representation of the SDict instance.
        """
        return f"SDict({self._source_file!r})"

    def __eq__(self, value: object) -> bool:
        """Return self == value.

        Determines equality of two SDict instances by comparing their string representations.

        Parameters
        ----------
        value : object
            the other SDict instance to determine equality with.

        Returns
        -------
        bool
            True if the two SDict instances are equal, otherwise False.
        """
        if isinstance(value, SDict):
            return str(self) == str(value)
        return super().__eq__(value)

    def order_keys(self) -> None:
        """alpha-numeric sorting of keys, recursively."""
        _ = order_keys(self)
        self.expressions = order_keys(self.expressions)
        self.line_comments = order_keys(self.line_comments)
        self.block_comments = order_keys(self.block_comments)
        self.includes = order_keys(self.includes)
        return

    def find_global_key(self, query: str = "") -> list[TGlobalKey] | None:
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
        return find_global_key(cast(SDict[TKey, TValue], self), query)

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
                logger.warning(f"SDict.reduce_scope(): no scope '{e.args[0]}' in dictionary {self._source_file}")
        return

    def reset(self) -> None:
        """Reset the dict.

        Removes all items from the dict.
        """
        super().clear()
        self.counter.reset()
        self._reset_source_file()
        self.line_content.clear()
        self.block_content = ""
        self.tokens.clear()
        self.string_literals.clear()
        self.expressions.clear()
        self.line_comments.clear()
        self.block_comments.clear()
        self.includes.clear()
        return

    def _reset_source_file(self) -> None:
        self._source_file = None
        self._path = Path.cwd()
        self._name = ""

    def _clean(self) -> None:
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within self:
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        """

        def _recursive_clean(data: MutableMapping[TKey, TValue]) -> None:
            self._clean_data(
                data=data,
            )
            # Recursion for nested levels
            for value in list(data.values()):
                if isinstance(value, MutableMapping):
                    _recursive_clean(value)  # Recursion

            return

        _recursive_clean(data=cast(MutableMapping[TKey, TValue], self))

        return

    def _clean_data(self, data: MutableMapping[TKey, TValue]) -> None:
        """Find and remove doublettes of PLACEHOLDER keys.

        Find and remove doublettes of following PLACEHOLDER keys within data:
        - BLOCKCOMMENT
        - INCLUDE
        - LINECOMMENT
        By definition, only keys on the same nest level are checked for doublettes.
        Doublettes are identified through equality with their lookup values.
        """
        # IDENTIFY all placeholders on current level
        keys_on_this_level: list[TKey] = list(data)
        block_comments_on_this_level: list[str] = []
        includes_on_this_level: list[str] = []
        line_comments_on_this_level: list[str] = []
        for key in keys_on_this_level:
            if type(key) is not str:
                continue
            if re.search(pattern=r"BLOCKCOMMENT\d{6}", string=key):
                block_comments_on_this_level.append(key)
            elif re.search(pattern=r"INCLUDE\d{6}", string=key):
                includes_on_this_level.append(key)
            elif re.search(pattern=r"LINECOMMENT\d{6}", string=key):
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
                    del data[_block_comment]
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
                    del data[_include]
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
                    del data[_line_comment]
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
    def data(self) -> dict[K, V]:
        """Mimick the data property of the CppDict class from dictIO <= v0.3.4.

        Mimicks the data property of the deprecated CppDict class to maintain
        backward compatibility. This property is deprecated and will be removed with v0.5.0.

        Returns
        -------
        dict[K, V]
            the content of the SDict instance
        """
        warnings.warn(
            f"`{self.__class__.__name__}.data` is deprecated. Use `SDict` directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    @data.setter
    def data(self, data: dict[K, V]) -> None:
        warnings.warn(
            f"`{self.__class__.__name__}.data` is deprecated. Use `SDict.update()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.clear()
        self.update(data)
        return


def _insert_expression(value: TValue, s_dict: SDict[K, V]) -> TValue:
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
