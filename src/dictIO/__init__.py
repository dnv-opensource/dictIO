"""dictIO package provides classes for reading, writing, and parsing dictionaries."""

from dictIO.dict import SDict

from dictIO.cpp_dict import CppDict  # for backward compatibility

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

from dictIO.dict_reader import DictReader
from dictIO.dict_writer import DictWriter, create_target_file_name
from dictIO.dict_parser import DictParser

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
