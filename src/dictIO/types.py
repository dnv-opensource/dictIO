"""Type aliases and generic type variables for the dictIO package."""

from collections.abc import Hashable, MutableMapping, MutableSequence
from typing import Any, TypeVar

# Type aliases for keys
type TKey = Hashable
type TGlobalKey = TKey | int

# Type aliases for values
type TValue = Any
type TSingleValue = str | int | float | bool | None

# Generic Type Variables
K = TypeVar("K", bound=TKey)
V = TypeVar("V", bound=TValue)
M = TypeVar("M", bound=MutableMapping[K, V])  # type: ignore[valid-type]
S = TypeVar("S", bound=MutableSequence[V])  # type: ignore[valid-type]
