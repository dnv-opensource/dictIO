import logging
import re
from difflib import ndiff
from typing import List

__all__ = ["remove_quotes", "string_diff"]


logger = logging.getLogger(__name__)


def remove_quotes(string: str):
    """
    Removes quotes (single or double quotes) from the string object passed in.
    Not only leading and trailing quotes are removed; also any quotes inside a string, if so, are removed.
    """
    # search_pattern = re.compile(r'(^[\'\\"]{1}|[\'\\"]{1}$)')  #Removes only leading and trailing quotes. Quotes inside a string are kept.
    search_pattern = re.compile(
        r"[\'\"]"
    )  # Removes ALL quotes in a string. Meaning, not only leading and trailing quotes, but also quotes inside a string are removed.
    return re.sub(search_pattern, "", string)


def string_diff(text_1: str, text_2: str):
    """
    diff line by line
    printing only diff
    """
    lines_1: List[str] = re.split("[\r\n]+", text_1)
    lines_2: List[str] = re.split("[\r\n]+", text_2)
    diffs: List[str] = []
    for index, item in enumerate(line for line in ndiff(lines_1, lines_2) if not re.search(r"^\s*$", line)):
        if re.match(r"^[+\-]", item):
            print("diff in line %4i:" % index, item)
            diffs.append((item))

    line_length = len(diffs)
    print(
        f"There {'is' if line_length == 1 else 'are'} {'no' if line_length == 0 else str(line_length)} difference{'' if line_length == 1 else 's'} between text 1 and text 2."
    )
