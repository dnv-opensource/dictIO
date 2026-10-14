"""Utility functions for string manipulation."""

import logging
import re
from difflib import ndiff
from re import Pattern

__all__: list[str] = ["remove_quotes", "string_diff"]


logger: logging.Logger = logging.getLogger(__name__)


def remove_quotes(string: str) -> str:
    """Remove quotes (single or double quotes) from the string object passed in.

    Removes quote characters throughout the string, including quotes between
    other characters.

    Args:
        string: Text from which to remove single and double quote characters.

    Returns:
        The input text with all single and double quote characters removed.
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
    """Describe the line-by-line differences between two text values.

    Blank lines in the diff output are omitted.

    Args:
        text_1: First text value to compare.
        text_2: Second text value to compare.

    Returns:
        A summary containing changed lines and the total number of differences.
    """
    lines_1: list[str] = re.split("[\r\n]+", text_1)
    lines_2: list[str] = re.split("[\r\n]+", text_2)
    diffs: list[str] = []
    message: str = ""
    for index, item in enumerate(line for line in ndiff(lines_1, lines_2) if not re.search(r"^\s*$", line)):
        if re.match(r"^[+\-]", item):
            message += f"diff in line {index:4d}:" + "\n"
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
