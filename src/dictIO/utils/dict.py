"""Utility functions for working with dictionaries."""

import re
from _collections_abc import MutableMapping, MutableSequence
from collections.abc import Sequence
from copy import copy
from typing import Any, cast

from dictIO.types import K, M, V


def order_keys(arg: M) -> M:
    """alpha-numeric sorting of keys, recursively.

    Parameters
    ----------
    arg : _MT
        MutableMapping, the keys of which shall be sorted.

    Returns
    -------
    _MT
        the passed in MutableMapping, with keys sorted. The same instance is returned.
    """
    sorted_dict: dict[Any, Any] = dict(sorted(arg.items(), key=lambda x: (isinstance(x[0], str), x[0])))
    for key, value in copy(sorted_dict).items():
        if isinstance(value, MutableMapping):
            sorted_dict[key] = order_keys(value)  # Recursion
    arg.clear()
    arg.update(sorted_dict)
    return arg


def find_global_key(
    arg: MutableMapping[K, V] | MutableSequence[V],
    query: str = "",
) -> list[K | int] | None:
    """Return the global key thread to the first key the value of which matches the passed in query.

    Parameters
    ----------
    arg : Union[MutableMapping[K, V], MutableSequence[V]]
        dict to search in for the queried value
    query : str, optional
        query string for the value to search for, by default ''

    Returns
    -------
    list[K | int] | None
        global key thread to the first key the value of which matches the passed in query, if found. Otherwise None.
    """
    global_key: list[K | int] = []
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
            elif re.search(pattern=query, string=str(value)):
                global_key.append(index)
                break

    return global_key or None


def set_global_key(
    arg: MutableMapping[K, V],
    global_key: Sequence[K | int],
    value: V,
) -> None:
    """Set the value for the passed in global key.

    Parameters
    ----------
    arg : MutableMapping[K, V]
        dict the target key in which shall be set
    global_key : MutableSequence[K | int]
        list of keys defining the global key thread to the target key (such as returned by method find_global_key())
    value : V
        value the target key shall be set to
    """
    if not global_key:
        return

    last_node: MutableMapping[K, V] | MutableSequence[V]
    next_node: MutableMapping[K, V] | MutableSequence[V] | V
    target_node: MutableMapping[K, V] | MutableSequence[V]
    remaining_keys: list[K | int]
    next_key: K | int
    target_key: K | int

    last_node = arg
    remaining_keys = list(global_key)
    ii: int = 0
    while len(remaining_keys) > 1:
        # as long as we didn't arrive at the last node (the one that contains the target key)..
        next_key = remaining_keys[0]
        # ..walk one level further down
        if isinstance(last_node, MutableSequence):
            if not isinstance(next_key, int):
                raise KeyError(f"KeyError: {global_key} not found in {arg}")
            next_node = last_node[cast(int, next_key)]
        else:
            next_node = last_node[cast(K, next_key)]
        if not isinstance(next_node, MutableMapping | MutableSequence):
            raise KeyError(f"KeyError: {global_key} not found in {arg}")
        last_node = next_node
        remaining_keys = remaining_keys[1:]
        ii += 1
        if ii == 10:  # noqa: PLR2004
            raise RecursionError(
                "RecursionError: Maximum recursion depth exceeded in set_global_key()."
                "set_global_key() is not designed to handle more than 10 levels of nested keys."
            )

    # Only one key left in remaining_keys, which is the key of the target node
    target_node = last_node
    target_key = remaining_keys[0]
    # Set the target key in target node to the passed in value
    if isinstance(target_node, MutableSequence):
        if not isinstance(target_key, int):
            raise KeyError(f"KeyError: {global_key} not found in {arg}")
        target_node[int(target_key)] = value
    else:
        target_node[cast(K, target_key)] = value

    return


def global_key_exists(
    dict_in: MutableMapping[K, V],
    global_key: MutableSequence[K | int],
) -> bool:
    """Check whether the specified global key exists in the passed in dict.

    Parameters
    ----------
    dict_in : MutableMapping[K, V]
        dict to check for existence of the specified global key
    global_key : MutableSequence[K | int]
        global key the existence of which is checked in the passed in dict

    Returns
    -------
    bool
        True if the specified global key exists, otherwise False
    """
    _last_branch: MutableMapping[K, V] = dict_in
    _next_branch: MutableMapping[K, V] | V
    try:
        for key in global_key:
            _next_branch = _last_branch[key]  # type: ignore[index, reportArgumentType]
            if not isinstance(_next_branch, MutableMapping):
                return False
            _last_branch = _next_branch
    except KeyError:
        return False
    return True
