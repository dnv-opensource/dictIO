# Changelog

All notable changes to the [dictIO] project will be documented in this file.<br>
The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

* -

## [0.1.0] - 2022-05-28

### Changed

* Simplified imports from namespace dictIO. Example:
    * Old (<= v0.0.22):
        ~~~py
        from dictIO.dictParser import DictParser
        ~~~
    * New:
        ~~~py
        from dictIO import DictParser
        ~~~

* parser.py
    * Parser.remove_quotes_from_string()
        * Changed default of 'all' argument from True to False<br>
        This change was introduced in order to, by default, protect inner quotes in i.e. a farn filter expression "var in ['item1', 'item2']" from being removed.

    * CppParser._parse_tokenized_dict()
        * Changed implementation of the conditional code where a key value pair gets parsed.<br>
        This change was introduced in order to better identify invalid key value pairs.<br>
        Two invalid keys were added in test_parser_dict (section 'invalid') and a respective test was added.

* formatter.py
    * JsonFormatter.insert_includes()
        * Changed correction of backslashes, so that backslashes in include paths are not substituted by forwardslashes but actually escaped in Json compliant way.

* dictWriter.py
    * DictWriter.write()
        * Changed default of 'mode' argument from 'w' (overwrite) to 'a' (append)

* utils\strings.py
    * plural() function moved to farn package (-> moved into utils\logging.py module in farn)<br>
    It was moved since the plural() function is currently used in farn logging only (neither in dictIO nor in ospx).


## [0.0.22] - 2022-05-09

* First public release

## [0.0.17] - 2022-02-14

### Added

* Added support for Python 3.10

<!-- Markdown link & img dfn's -->
[unreleased]: https://github.com/dnv-opensource/dictIO/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dnv-opensource/dictIO/compare/v0.0.22...v0.1.0
[0.0.22]: https://github.com/dnv-opensource/dictIO/compare/v0.0.17...v0.0.22
[0.0.17]: https://github.com/dnv-opensource/dictIO/releases/tag/v0.0.17
[dictIO]: https://github.com/dnv-opensource/dictIO
