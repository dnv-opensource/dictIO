import contextlib
import logging
import os
import re
from copy import deepcopy
# Import from math all functions we want to allow inside expressions in a dict.
# This is a bit ugly, but necessary to enable evaluation of parsed expressions with the help of eval().
from math import (  # noqa: F401
    acos, asin, atan, atan2, cos, e, exp, log, log10, pi, pow, sin, sqrt, tan
)
from pathlib import Path
from typing import MutableMapping, MutableSequence, Union

from dictIO import CppDict, Parser
from dictIO.utils.counter import DejaVue


__ALL__ = ['DictReader']

logger = logging.getLogger(__name__)


class DictReader():
    """Reader for dictionaries in dictIO dict file format, as well as JSON and XML
    """

    def __init__(self):
        return

    @staticmethod
    def read(
        source_file: Union[str, os.PathLike[str]],
        includes: bool = True,
        order: bool = False,
        comments: bool = True,
        scope: Union[MutableSequence[str], None] = None,
        parser: Union[Parser, None] = None,
    ) -> CppDict:
        """Reads a dictionary file in dictIO dict file format, as well as JSON and XML.

        Reads a dict file, parses it and transforms its content into a dictIO dict object (CppDict).
        Following file formats are supported and interpreted through source_file's file ending:
        no file ending   ->   dictIO dict file
        '.cpp'           ->   dictIO dict file
        '.foam'          ->   Foam dictionary file
        '.json'          ->   Json dictionary file
        '.xml'           ->   XML file
        Return type is in all cases CppDict

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
        CppDict
            the read dict

        Raises
        ------
        FileNotFoundError
            if source_file does not exist
        """

        # Make sure source_file argument is of type Path. If not, cast it to Path type.
        source_file = source_file if isinstance(source_file, Path) else Path(source_file)
        if not source_file.exists():
            logger.error(f'source_file not found: {source_file}')
            raise FileNotFoundError(source_file)

        # Create parser
        # If a parser has been passed to read(), use that.
        # Otherwise choose the parser depending on source_file.
        # source_file = Path.joinpath(Path.cwd(), source_file)
        parser = parser or Parser.get_parser(source_file)

        # Parse the dict file and transform it into a CppDict
        parsed_dict = parser.parse_file(source_file, comments=comments)

        # Merge dict files included through #include directives, if not actively refrained through opts
        if includes:
            __class__._merge_includes(parsed_dict, comments=comments)

        # Evaluate and insert back expressions
        __class__._eval_expressions(parsed_dict)

        # Reduce scope of the dict if requested through opts
        if scope:
            # We need here safety hook when specified scope is not found: simply stop (not continue with whole content!)
            if parsed_dict.global_key_exists(scope):
                parsed_dict.reduce_scope(scope)
            else:
                logger.error(f'scope {scope} does not exist in dictionary')
                exit(1)

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
            __class__._remove_include_keys(parsed_dict.data)

        return parsed_dict

    @staticmethod
    def _merge_includes(dict: CppDict, comments: bool = True):
        '''
        Parses and merges any (child) dicts that are referenced in the dict file through #include directives
        '''
        # Create dejavue string watchdog
        djv = DejaVue()
        djv.reset()

        # Inner function: Merge all includes, recursively
        def _merge_includes_recursive(dict: CppDict):

            # empty dict to merge in temporarily, avoiding dict-has-change-error inside the for loop
            temp_dict = CppDict()

            # loop over all possible includes
            for _, _, path in dict.includes.values():
                prove_recursive_include = djv(path)

                if prove_recursive_include is True:
                    call_chain = '->'.join([p.name for p in djv.strings])
                    logger.warning(
                        f'Recursive include detected. Merging of {call_chain} into {dict.name} aborted.'
                    )
                elif not path.exists():
                    logger.warning(f'included dict not found. Merging of {path} aborted.')
                else:
                    parser = Parser.get_parser(path)
                    included_dict = parser.parse_file(path, None, comments=comments)

                    # recursion in case the i-th include also has includes
                    if len(included_dict.includes) != 0:
                        nested_included_dict = _merge_includes_recursive(included_dict)
                        # merge second level
                        temp_dict.merge(nested_included_dict)

                    # merge first level
                    temp_dict.merge(included_dict)

            # merge all in for loop
            dict.merge(temp_dict)

            return dict

        # Call inner funtion to merge all includes, recursively
        dict.merge(_merge_includes_recursive(dict))

        return

    @staticmethod
    def _resolve_reference(ref, vars):
        # resolves a single reference
        ret = None
        try:
            # extract indices, ugly version, nice version is re.sub with a positive lookahead
            indexing = re.findall(r'\[.+\]$', ref)[0]
        except Exception:
            indexing = ''

        ref = re.sub(r'(^\$|\[.+$)', '', ref)   # remove leading $ or trailing [

        if ref in vars:
            ret = vars[ref]     # singular value or field

            ref_changed_through_recursion = False
            while re.search(
                r'\$', str(ret)
            ):                                                  # resolve nested references, if existing, through recursion
                ref = ret
                ref_changed_through_recursion = True
                ret = __class__._resolve_reference(ref, vars)   # recursion
            if ref_changed_through_recursion:
                ref = re.sub(r'(^\$|\[.+$)', '', ref)           # remove leading $ or trailing [
            if indexing:
                with contextlib.suppress(Exception):
                    ret = eval(
                        f"vars['{ref}']{indexing}"
                    )                                           # return the value of the referenced variable (at the specified index, if given)
        return ret

    @staticmethod
    def _eval_expressions(dict: CppDict):
        # Collect all references contained in expressions
        references = []
        for item in dict.expressions.values():
            refs = re.findall(r'\$\w[\w\[\]]+', item['expression'])
            references.extend(refs)
        # Resolve references
        variables = dict.variables
        references = {ref: __class__._resolve_reference(ref, variables) for ref in references}
        references_resolved = {
            ref: value
            for ref,
            value in references.items()
            if (value is not None) and (not re.search(r'EXPRESSION|\$', str(value)))
        }
        references_not_resolved = [ref for ref in references if ref not in references_resolved]

        # Iteratively try to evaluate expressions contained in the dict and then re-resolve all references
        # With every iteration, this should reduce the number of remaining, non resolved references
        references_not_resolved_old = len(references_not_resolved) + 1
        keep_on = True
        while keep_on:
            references_not_resolved_old = len(references_not_resolved)
            expressions_copy = deepcopy(dict.expressions)
            for key, item in expressions_copy.items():
                placeholder = str(item['name'])
                expression = str(item['expression'])
                refs = re.findall(r'\$\w[\w\[\]]+', expression)
                for ref in refs:
                    if ref in references_resolved:
                        expression = re.sub(
                            f'{re.escape(ref)}', str(references_resolved[ref]), expression
                        )

                eval_successful = False
                eval_result = None
                if '$' not in expression:
                    try:
                        eval_result = eval(expression)
                        eval_successful = True
                    except NameError:
                        eval_result = expression
                        eval_successful = True
                    except SyntaxError:
                        logger.warning(
                            'DictReader.(): evaluation of \"%s\" not yet possible' % expression
                        )
                if eval_successful:
                    while global_key := dict.find_global_key(query=placeholder):
                        # Substitute the placeholder in the dict with the result of the evaluated expression
                        dict.set_global_key(global_key, value=eval_result)
                    del dict.expressions[key]
                else:
                    # update the item in dict.expressions with the (at least partly) resolved expression
                    dict.expressions[key]['expression'] = expression

            # At the end of each iteration, re-resolve all references based on the now updated variables table of dict
            references = []
            for item in dict.expressions.values():
                refs = re.findall(r'\$\w[\w\[\]]+', item['expression'])
                references.extend(refs)
            variables = dict.variables
            references = {ref: __class__._resolve_reference(ref, variables) for ref in references}
            references_resolved = {
                ref: value
                for ref,
                value in references.items()
                if (value is not None) and (not re.search(r'EXPRESSION|\$', str(value)))
            }
            references_not_resolved = [ref for ref in references if ref not in references_resolved]

            keep_on = (len(references_not_resolved) < references_not_resolved_old)

        # For expressions that could NOT successfully be evaluated, even after iteration:
        # Back insert the expression string into the dict
        for key, item in dict.expressions.items():
            placeholder = str(item['name'])
            expression = str(item['expression'])
            while global_key := dict.find_global_key(query=placeholder):
                # Substitute the placeholder with the original (or at least partly resolved) expression
                dict.set_global_key(global_key, value=expression)
        dict.expressions.clear()

        return

    @staticmethod
    def _remove_comment_keys(data: MutableMapping):
        '''
        remove comments from data structure for read function call from other programs
        '''
        remove = '[A-Z]+COMMENT[0-9;]+'

        temp_dict = deepcopy(data)

        with contextlib.suppress(Exception):
            for key in temp_dict.keys():
                if isinstance(data[key], MutableMapping):
                    data.update({key: __class__._remove_comment_keys(data[key])})   # recursion
                elif not re.search(remove, key):
                    data.update({key: temp_dict[key]})
        return

    @staticmethod
    def _remove_include_keys(data: MutableMapping):
        '''
        remove includes from data structure for read function call from other programs
        '''
        remove = 'INCLUDE[0-9;]+'

        temp_dict = deepcopy(data)

        with contextlib.suppress(Exception):
            for key in temp_dict.keys():
                if re.search(remove, key):
                    data.pop(key)
        return
