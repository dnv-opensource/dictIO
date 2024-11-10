"""DictReader class for reading dictionaries in dictIO native file format, as well as JSON and XML."""

import contextlib
import logging
import os
import re
import sys
from collections.abc import MutableMapping, MutableSequence
from copy import deepcopy

# Import from math all functions we want to allow inside expressions in a dict.
# This is a bit ugly, but necessary to enable evaluation of parsed expressions with the help of eval().
from math import (  # noqa: F401
    acos,
    asin,
    atan,
    atan2,
    cos,
    e,
    exp,
    log,
    log10,
    pi,
    pow,
    sin,
    sqrt,
    tan,
)
from pathlib import Path
from typing import cast

from numpy import (  # noqa: F401
    array,
    diag,
    eye,
    mean,
    ndarray,
    ones,
    std,
    zeros,
)

from dictIO import Parser, SDict
from dictIO.types import TKey, TValue
from dictIO.utils.counter import DejaVue

__ALL__ = ["DictReader"]

logger = logging.getLogger(__name__)


class DictReader:
    """Reader for dictionaries in dictIO native file format, as well as JSON and XML."""

    def __init__(self) -> None:
        return

    @staticmethod
    def read(
        source_file: str | os.PathLike[str],
        *,
        includes: bool = True,
        order: bool = False,
        comments: bool = True,
        scope: MutableSequence[TKey] | None = None,
        parser: Parser | None = None,
    ) -> SDict[TKey, TValue]:
        """Read a dictionary file in dictIO native file format, as well as JSON and XML.

        Reads a dict file, parses it and transforms its content into a dictIO dict object (SDict).
        Following file formats are supported and interpreted through source_file's file ending:
        no file ending   ->   dictIO native dict file
        '.cpp'           ->   dictIO native dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file
        Return type is in all cases SDict

        Parameters
        ----------
        source_file : Union[str, os.PathLike[str]]
            dict file to be read
        includes : bool, optional
            merge sub-dicts being referenced through #include directives, by default True
        order : bool, optional
            sort the read dict, by default False
        comments : bool, optional
            reads comments from source file, by default True
        scope : MutableSequence[str], optional
            scope the dict will be reduced to after reading, by default None
        parser : Parser, optional
            Parser object to be used, by default None

        Returns
        -------
        SDict
            the read dict

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
        """
        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f"source_file not found: {source_file}")
            raise FileNotFoundError(source_file)

        # Create parser
        # If a parser has been passed to read(), use that.
        # Otherwise choose the parser depending on source_file.
        # source_file = Path.joinpath(Path.cwd(), source_file)  # noqa: ERA001
        parser = parser or Parser.get_parser(source_file)

        # Parse the dict file and transform it into a SDict
        parsed_dict = parser.parse_file(source_file, comments=comments)

        # Merge dict files included through #include directives, if not actively refrained through opts
        if includes:
            DictReader._merge_includes(parent_dict=parsed_dict, comments=comments)

        # Evaluate and insert back expressions
        DictReader._eval_expressions(dict_in=parsed_dict)

        # Reduce scope of the dict if requested through opts
        if scope:
            # We need here safety hook when specified scope is not found: simply stop (not continue with whole content!)
            if parsed_dict.global_key_exists(global_key=scope):
                parsed_dict.reduce_scope(scope)
            else:
                logger.error(f"scope {scope} does not exist in dictionary")
                sys.exit(1)

        # Order the dict, if not actively refrained through opts
        if order:
            parsed_dict.order_keys()

        # Remove includes from the parsed dictionary if requested through opts
        # @TODO: Really necessary?
        # generally a good idea to have a switch suppressing #include ... in output
        # gives the option to disable include (foam required)
        # also to consider: is it really neccessary to have the included dict merged in to current dict.data?
        # if we could avoid that we get a more readable structure, even after some farn operations
        if not includes:
            DictReader._remove_include_keys(parsed_dict)

        return parsed_dict

    @staticmethod
    def _merge_includes(
        parent_dict: SDict[TKey, TValue],
        *,
        comments: bool = True,
    ) -> None:
        """Parse and merge any (child) dicts that are referenced in the dict file through #include directives."""
        # Create dejavue string watchdog
        djv = DejaVue()
        djv.reset()

        # Inner function: Merge all includes, recursively
        def _merge_includes_recursive(parent_dict: SDict[TKey, TValue]) -> SDict[TKey, TValue]:
            # empty dict to merge in temporarily, avoiding dict-has-change-error inside the for loop
            temp_dict: SDict[TKey, TValue] = SDict()

            # loop over all possible includes
            for _, _, path in parent_dict.includes.values():
                prove_recursive_include = djv(path.name)

                if prove_recursive_include is True:
                    call_chain = "->".join(list(djv.strings))
                    logger.warning(
                        f"Recursive include detected. Merging of {call_chain} into {parent_dict.name} aborted."
                    )
                elif not path.exists():
                    logger.warning(f"included dict not found. Merging of {path} aborted.")
                else:
                    parser = Parser.get_parser(source_file=path)
                    included_dict = parser.parse_file(source_file=path, target_dict=None, comments=comments)

                    # recursion in case the i-th include also has includes
                    if len(included_dict.includes) != 0:
                        nested_included_dict = _merge_includes_recursive(included_dict)
                        # merge second level
                        temp_dict.merge(nested_included_dict)

                    # merge first level
                    temp_dict.merge(included_dict)

            # merge all in for loop
            parent_dict.merge(temp_dict)

            return parent_dict

        # Call inner funtion to merge all includes, recursively
        parent_dict.merge(_merge_includes_recursive(parent_dict))

        return

    @staticmethod
    def _resolve_reference(
        reference: str,
        variables: MutableMapping[str, TValue],
    ) -> TValue:
        # resolves a single reference
        value: TValue = None
        try:
            # extract indices, ugly version, nice version is re.sub with a positive lookahead
            indexing = re.findall(pattern=r"\[.+\]$", string=reference)[0]
        except Exception:  # noqa: BLE001
            indexing = ""

        reference = re.sub(pattern=r"(^\$|\[.+$)", repl="", string=reference)  # remove leading $ or trailing [

        if reference in variables:
            value = variables[reference]  # singular value or field

            ref_changed_through_recursion = False
            while re.search(
                pattern=r"\$", string=str(value)
            ):  # resolve nested references, if existing, through recursion
                reference = str(value)
                ref_changed_through_recursion = True
                value = DictReader._resolve_reference(reference=reference, variables=variables)  # recursion
            if ref_changed_through_recursion:
                reference = re.sub(pattern=r"(^\$|\[.+$)", repl="", string=reference)  # remove leading $ or trailing [
            if indexing:
                with contextlib.suppress(Exception):
                    # return the value of the referenced variable (at the specified index, if given)
                    value = eval(f"variables['{reference}']{indexing}")  # noqa: S307
        return value

    @staticmethod
    def _eval_expressions(dict_in: SDict[TKey, TValue]) -> None:
        # Collect all references contained in expressions
        _references: list[str] = []
        _refs: list[str]
        placeholder: str
        expression: str
        for item in dict_in.expressions.values():
            _refs = re.findall(pattern=r"\$\w[\w\[\]]*", string=item["expression"])
            _references.extend(_refs)
        # Resolve references
        variables: dict[str, TValue] = dict_in.variables
        references: dict[str, TValue] = {
            ref: DictReader._resolve_reference(
                reference=ref,
                variables=variables,
            )
            for ref in _references
        }
        references_resolved: dict[str, TValue] = {
            ref: value
            for ref, value in references.items()
            if (value is not None) and (not re.search(pattern=r"EXPRESSION|\$", string=str(value)))
        }
        references_not_resolved: list[str] = [ref for ref in references if ref not in references_resolved]

        # Iteratively try to evaluate expressions contained in the dict and then re-resolve all references
        # With every iteration, this should reduce the number of remaining, non resolved references
        references_not_resolved_old: int = len(references_not_resolved) + 1
        keep_on: bool = True
        while keep_on:
            references_not_resolved_old = len(references_not_resolved)
            expressions_copy: dict[int, dict[str, str]] = deepcopy(dict_in.expressions)
            for key, item in expressions_copy.items():
                placeholder = item["name"]
                expression = item["expression"]
                _refs = re.findall(pattern=r"\$\w[\w\[\]]*", string=expression)
                for ref in _refs:
                    if ref in references_resolved:
                        expression = re.sub(
                            pattern=f"{re.escape(ref)}",
                            repl=str(references_resolved[ref]),
                            string=expression,
                        )

                eval_successful: bool = False
                eval_result: TValue | None = None
                if "$" not in expression:
                    try:
                        eval_result = eval(expression)  # noqa: S307
                        eval_successful = True
                    except NameError:
                        eval_result = expression
                        eval_successful = True
                    except SyntaxError:
                        logger.warning(f'DictReader.(): evaluation of "{expression}" not yet possible')
                if eval_successful:
                    while global_key := dict_in.find_global_key(query=placeholder):
                        # Substitute the placeholder in the dict with the result of the evaluated expression
                        dict_in.set_global_key(global_key, value=eval_result)
                    del dict_in.expressions[key]
                else:
                    # update the item in dict.expressions with the (at least partly) resolved expression
                    dict_in.expressions[key]["expression"] = expression

            # At the end of each iteration, re-resolve all references based on the now updated variables table of dict
            _references = []
            for item in dict_in.expressions.values():
                _refs = re.findall(pattern=r"\$\w[\w\[\]]*", string=item["expression"])
                _references.extend(_refs)
            variables = dict_in.variables
            references = {
                ref: DictReader._resolve_reference(
                    reference=ref,
                    variables=variables,
                )
                for ref in _references
            }
            references_resolved = {
                ref: value
                for ref, value in references.items()
                if (value is not None)
                and (
                    not re.search(
                        pattern=r"EXPRESSION|\$",
                        string=str(value),
                    )
                )
            }
            references_not_resolved = [ref for ref in references if ref not in references_resolved]

            keep_on = len(references_not_resolved) < references_not_resolved_old

        # For expressions that could NOT successfully be evaluated, even after iteration:
        # Back insert the expression string into the dict
        for item in dict_in.expressions.values():
            placeholder = item["name"]
            expression = item["expression"]
            while global_key := dict_in.find_global_key(query=placeholder):
                # Substitute the placeholder with the original (or at least partly resolved) expression
                dict_in.set_global_key(global_key, value=expression)
        dict_in.expressions.clear()

        return

    @staticmethod
    def _remove_comment_keys(data: MutableMapping[TKey, TValue]) -> MutableMapping[TKey, TValue]:
        """Remove comments from data structure for read function call from other programs."""
        remove = "[A-Z]+COMMENT[0-9;]+"

        with contextlib.suppress(Exception):
            for key in list(data.keys()):  # work on a copy of the keys
                if isinstance(data[key], MutableMapping):
                    sub_dict = cast(MutableMapping[TKey, TValue], data[key])
                    data.update({key: DictReader._remove_comment_keys(sub_dict)})  # recursion
                elif re.search(pattern=remove, string=str(key)):
                    _ = data.pop(key)
        return data

    @staticmethod
    def _remove_include_keys(data: MutableMapping[TKey, TValue]) -> None:
        """Remove includes from data structure for read function call from other programs."""
        remove = "INCLUDE[0-9;]+"

        with contextlib.suppress(Exception):
            for key in list(data.keys()):  # work on a copy of the keys
                if type(key) is str and re.search(pattern=remove, string=key):
                    _ = data.pop(key)
        return
