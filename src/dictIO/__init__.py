"""dictIO package provides classes for reading, writing, and parsing dictionaries."""

from dictIO.dict import (
    SDict as SDict,
    order_keys as order_keys,
    find_global_key as find_global_key,
    set_global_key as set_global_key,
)

from dictIO.cpp_dict import (
    CppDict as CppDict,
)

from dictIO.formatter import (
    Formatter as Formatter,
    NativeFormatter as NativeFormatter,
    FoamFormatter as FoamFormatter,
    JsonFormatter as JsonFormatter,
    XmlFormatter as XmlFormatter,
)
from dictIO.parser import (
    Parser as Parser,
    NativeParser as NativeParser,
    FoamParser as FoamParser,
    JsonParser as JsonParser,
    XmlParser as XmlParser,
)

from dictIO.dict_reader import (
    DictReader as DictReader,
)
from dictIO.dict_writer import (
    DictWriter as DictWriter,
    create_target_file_name as create_target_file_name,
)
from dictIO.dict_parser import (
    DictParser as DictParser,
)
