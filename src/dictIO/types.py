# ruff: noqa: ERA001

from collections.abc import Hashable
from typing import Any, TypeAlias

TSingleValue: TypeAlias = str | int | float | bool | None

# Type aliases for keys and values
# TKey: TypeAlias = int | str
# TValue: TypeAlias = int | float | str | bool | MutableMapping[TKey, Any] | MutableSequence[Any] | Any | None
# TKey: TypeAlias = str | int
TKey: TypeAlias = Hashable
TValue: TypeAlias = Any

TGlobalKey: TypeAlias = TKey | int
