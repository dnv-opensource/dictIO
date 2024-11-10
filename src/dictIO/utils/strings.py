"""Utility functions for string manipulation."""

import logging
import re
from difflib import ndiff
from re import Pattern

__all__ = ["remove_quotes", "string_diff"]


logger = logging.getLogger(__name__)


def remove_quotes(string: str) -> str:
    """Remove quotes (single or double quotes) from the string object passed in.

    Not only leading and trailing quotes are removed; also any quotes inside a string, if so, are removed.
    """
    search_pattern: Pattern[str]
    # Pattern 1 removes only leading and trailing quotes. Quotes inside a string are kept.
    # @NOTE: Left here for documentation purposes only. Pattern 2 is the one used.
    # search_pattern = re.compile(r'(^[\'\\"]{1}|[\'\\"]{1}$)')  # noqa: ERA001

    # Pattern 2 removes ALL quotes in a string.
    # Meaning, not only leading and trailing quotes, but also quotes inside a string are removed.
    search_pattern = re.compile(r"[\'\"]")
    return re.sub(search_pattern, "", string)


def string_diff(text_1: str, text_2: str) -> str:
    """Return diff line by line."""
    lines_1: list[str] = re.split("[\r\n]+", text_1)
    lines_2: list[str] = re.split("[\r\n]+", text_2)
    diffs: list[str] = []
    message: str = ""
    for index, item in enumerate(line for line in ndiff(lines_1, lines_2) if not re.search(r"^\s*$", line)):
        if re.match(r"^[+\-]", item):
            message += str.format("diff in line %4i:" % index) + "\n"
            message += item + "\n"
            diffs.append(item)

    line_length = len(diffs)
    message += (
        f"There {'is' if line_length == 1 else 'are'} "
        f"{'no' if line_length == 0 else str(line_length)} "
        f"difference{'' if line_length == 1 else 's'} "
        "between text 1 and text 2."
    )
    return message
