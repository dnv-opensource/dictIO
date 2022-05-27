#!/usr/bin/env python
# coding utf-8

import argparse
import logging
import re
from pathlib import Path
from typing import MutableSequence, Union

from dictIO import DictParser
from dictIO.utils.logging import configure_logging


logger = logging.getLogger(__name__)


def _argparser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog='dictParser',
        usage='%(prog)s dict [options [args]]',
        epilog='_________________dictParser___________________',
        prefix_chars='-',
        add_help=True,
        description=(
            'Reads a dict file, merges sub-dicts referenced through #include directives,\n'
            'evaluates variables and expressions,\n'
            "and finally saves the parsed dict with prefix 'parsed', i.e. parsed.<DICTNAME>."
            'The format of the output file will by default be dictIO dict file format, but can optionally be\n'
            'changed to foam, xml or json format.'
        )
    )

    parser.add_argument(
        'dict',
        metavar='dict',
        type=str,
        help='name of dict file to be parsed.',
    )

    parser.add_argument(
        '-I',
        '--ignore-includes',
        action='store_true',
        help=(
            "ignore include directives (e.g. #include './SUBDICT').\n"
            'This suppresses merging of sub-dicts. '
        ),
        default=False,
        required=False,
    )

    parser.add_argument(
        '--mode',
        help=(
            '\'a\' -- append to output file if a dict with the same name already exists; \n'
            '\'w\' -- overwrite output file (default)'
        ),
        choices=['a', 'w'],
        default='w',
        required=False,
        type=str,
    )

    parser.add_argument(
        '--order',
        action='store_true',
        help='sort the parsed dict.',
        default=False,
        required=False,
    )

    parser.add_argument(
        '-C',
        '--ignore-comments',
        action='store_true',
        help=
        'supress writing comments into the output file. The header is excepted and will always be written.',
        default=False,
        required=False,
    )

    parser.add_argument(
        '--scope',
        action='store',
        help=(
            "optionally specify a scope the dict will be reduced to after parsing.\n"
            "'scope' can be EMPTY, a 'STRING' or a list of strings \"['STRING1', 'STRING2']\""
        ),
        default=None,
        required=False,
    )

    parser.add_argument(
        '-o',
        '--output',
        action='store',
        type=str,
        help='specify format of the output file.',
        choices=['cpp', 'foam', 'xml', 'json'],
        default='cpp',
        required=False,
    )

    console_verbosity = parser.add_mutually_exclusive_group(required=False)

    console_verbosity.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help=('console output will be quiet.'),
        default=False,
    )

    console_verbosity.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help=('console output will be verbose.'),
        default=False,
    )

    parser.add_argument(
        '--log',
        action='store',
        type=str,
        help='name of log file. If specified, this will activate logging to file.',
        default=None,
        required=False,
    )

    parser.add_argument(
        '--log-level',
        action='store',
        type=str,
        help='log level applied to logging to file.',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='WARNING',
        required=False,
    )

    return parser


def main():
    """Entry point for console script as configured in setup.cfg

    Runs the command line interface and parses arguments and options entered on the console.
    """

    parser = _argparser()
    args = parser.parse_args()

    # Configure Logging
    # ..to console
    log_level_console: str = 'WARNING'
    if any([args.quiet, args.verbose]):
        log_level_console = 'ERROR' if args.quiet else log_level_console
        log_level_console = 'DEBUG' if args.verbose else log_level_console
    # ..to file
    log_file: Union[Path, None] = Path(args.log) if args.log else None
    log_level_file: str = args.log_level
    configure_logging(log_level_console, log_file, log_level_file)

    source_file = Path(args.dict)
    includes: bool = not args.ignore_includes
    mode: str = args.mode
    order: bool = args.order
    comments: bool = not args.ignore_comments
    # Validate scope: It needs to be a list of strings
    scope: Union[MutableSequence[str], None] = _validate_scope(args.scope)
    output: Union[str, None] = args.output

    # Check whether source file exists
    if not source_file.exists():
        logger.error(f"dictParser.py: File {source_file} not found.")
        return

    logger.info(
        f"Start dictParser.py with following arguments:\n"
        f"\t source_file: \t\t{source_file}\n"
        f"\t includes: \t\t\t{includes}\n"
        f"\t order: \t\t\t\t{order}\n"
        f"\t comments: \t\t\t{comments}\n"
        f"\t scope: \t\t\t\t{scope}\n"
        f"\t output: \t\t\t{output}"
    )

    # Invoke API
    if DictParser.parse(source_file, includes, mode, order, comments, scope, output):
        logger.info('dictParser.py finished successfully.\n')
    else:
        logger.error('dictParser.py finished with errors.\n')


def _validate_scope(scope: Union[str, MutableSequence[str]]) -> Union[MutableSequence[str], None]:
    # sourcery skip: replace-interpolation-with-fstring
    validated_scope = None
    if isinstance(scope, MutableSequence):                      # Is 'scope' a list ?
        validated_scope = scope                                 # ..great, then no conversion needed
    elif isinstance(scope, str):                                # Is 'scope' a string ?
        if re.match(r'^\s*\[', scope):                          # ..maybe a string that LOOKS like a list?
            try:                                                # Then try to convert that string to a list
                from dictIO import Parser
                parser = Parser()
                scope = scope.strip(' []')
                keys: MutableSequence = [key.strip() for key in scope.split(',')]
                parsed_scope = parser.parse_types(keys)
                validated_scope = parsed_scope if isinstance(
                    parsed_scope, MutableSequence
                ) else None
            except Exception:
                logger.exception('setOptions: misspelled scope: %s' % scope)
        else:                                                   # ..ok, string is just a single value. Nevertheless:
            validated_scope = [scope]                           # Store it not as string but as a (one-element) list
    else:                                                       # Value of 'scope' is neither a list nor a string -> set to None
        validated_scope = None
    return validated_scope


if __name__ == '__main__':
    main()
