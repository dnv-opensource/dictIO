"""dictIO package provides classes for reading, writing, and parsing dictionaries."""

from dictIO.dict import SDict

from dictIO.cppDict import CppDict  # for backward compatibility

from dictIO.utils.dict import (
    order_keys,
    find_global_key,
    set_global_key,
)

from dictIO.formatter import (
    Formatter,
    NativeFormatter,
    FoamFormatter,
    JsonFormatter,
    XmlFormatter,
)
from dictIO.parser import (
    Parser,
    NativeParser,
    FoamParser,
    JsonParser,
    XmlParser,
)

from dictIO.dictReader import DictReader
from dictIO.dictWriter import DictWriter, create_target_file_name
from dictIO.dictParser import DictParser

__all__ = [
    "CppDict",
    "DictParser",
    "DictReader",
    "DictWriter",
    "FoamFormatter",
    "FoamParser",
    "Formatter",
    "JsonFormatter",
    "JsonParser",
    "NativeFormatter",
    "NativeParser",
    "Parser",
    "SDict",
    "XmlFormatter",
    "XmlParser",
    "create_target_file_name",
    "find_global_key",
    "order_keys",
    "set_global_key",
]
