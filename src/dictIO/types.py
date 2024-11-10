"""Type aliases and generic type variables for the dictIO package."""

# ruff: noqa: ERA001

from collections.abc import Hashable, MutableMapping, MutableSequence
from typing import Any, TypeAlias, TypeVar

# Type aliases for keys
TKey: TypeAlias = Hashable
TGlobalKey: TypeAlias = TKey | int

# Type aliases for values
TValue: TypeAlias = Any
TSingleValue: TypeAlias = str | int | float | bool | None

# Generic Type Variables
K = TypeVar("K", bound=TKey)
V = TypeVar("V", bound=TValue)
M = TypeVar("M", bound=MutableMapping[K, V])  # type: ignore[valid-type, reportGeneralTypeIssues]
S = TypeVar("S", bound=MutableSequence[V])  # type: ignore[valid-type, reportGeneralTypeIssues]
