"""Module `dictIO.cppDict`.

_Note_: Deprecated since 0.4.0.
Module `dictIO.cppDict` and class `CppDict` will be removed in 0.5.0.
Use module `dictIO.dict` and class `SDict` instead.
"""

from __future__ import annotations

import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    overload,
)

from dictIO.dict import SDict

if TYPE_CHECKING:
    import os
    from _collections_abc import Iterable, Mapping

    from dictIO.types import TValue

__ALL__ = [
    "CppDict",
]


class CppDict(SDict[str, Any]):
    """Data structure for C++ dictionaries.

    This class is deprecated and will be removed in 0.5.0.
    Use SDict[K, V] instead.
    """

    @overload
    def __init__(
        self,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Mapping[str, Any],
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: Iterable[tuple[str, Any]],
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        pass

    @overload
    def __init__(
        self,
        arg: str | os.PathLike[str],
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        pass

    def __init__(
        self,
        arg: Mapping[str, Any] | Iterable[tuple[str, Any]] | str | os.PathLike[str] | None = None,
        **kwargs: TValue,
    ) -> None:
        warnings.warn(
            "`CppDict` is deprecated. Use `SDict[K, V]` instead.",
            DeprecationWarning,
            stacklevel=1,
        )
        super().__init__(arg, **kwargs)  # type: ignore[arg-type, reportArgumentType, reportCallIssue]
        return
