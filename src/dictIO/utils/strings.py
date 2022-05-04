import re
from difflib import ndiff
import logging

__all__ = ['remove_quotes', 'string_diff']


logger = logging.getLogger(__name__)


def remove_quotes(string):
    '''
    Removes quotes (single or double quotes) from the string object passed in.
    Not only leading and trailing quotes are removed; also any quotes inside a string, if so, are removed.
    '''
    # search_pattern = re.compile(r'(^[\'\\"]{1}|[\'\\"]{1}$)')  #Removes only leading and trailing quotes. Quotes inside a string are kept.
    search_pattern = re.compile(r'[\'\"]')  # Removes ALL quotes in a string. Meaning, not only leading and trailing quotes, but also quotes inside a string are removed.
    # Remove quotes and return
    string = re.sub(search_pattern, '', string)
    return string


def string_diff(line_1, line_2):
    '''
    diff line by line
    printing only diff
    '''
    line_1 = re.split('[\r\n]+', line_1)
    line_2 = re.split('[\r\n]+', line_2)
    diffs = []
    for index, item in enumerate(line for line in ndiff(line_1, line_2) if not re.search(r'^\s*$', line)):
        if re.match(r'^[+\-]', item):
            print('diff in line %4i:' % index, item)
            diffs.append((item))

    line_length = len(diffs)
    print(
        f"There {'is' if line_length == 1 else 'are'} {'no' if line_length == 0 else str(line_length)} difference{'' if line_length == 1 else 's'} between text 1 and text 2."
    )
