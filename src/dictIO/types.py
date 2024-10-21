# ruff: noqa: ERA001

from typing import Any, TypeAlias

TSingleValue: TypeAlias = str | int | float | bool | None

# Type aliases for keys and values
# TKey: TypeAlias = int | str
# TValue: TypeAlias = int | float | str | bool | MutableMapping[TKey, Any] | MutableSequence[Any] | Any | None
TKey: TypeAlias = Any
TValue: TypeAlias = Any