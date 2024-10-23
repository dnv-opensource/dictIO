"""Module `dictIO.cppDict`.

_Note_: Deprecated since 0.4.0.
Module `dictIO.cppDict` and class `CppDict` will be removed in 0.5.0.
Use module `dictIO.dict` and class `SDict` instead.
"""

from __future__ import annotations

import warnings
from typing import (
    TYPE_CHECKING,
    overload,
)

from dictIO.dict import SDict
from dictIO.types import TKey, TValue

if TYPE_CHECKING:
    import os
    from _collections_abc import Iterable, Mapping

__ALL__ = [
    "CppDict",
]


class CppDict(SDict[TKey, TValue]):
    """Data structure for C++ dictionaries.

    This class is deprecated and will be removed in 0.5.0.
    Use SDict[TKey, TValue] instead.
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
