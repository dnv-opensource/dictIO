# Changelog

All notable changes to the [dictIO] project will be documented in this file.<br>
The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Dependencies
* Updated to ruff>=0.8.3  (from ruff>=0.6.3)
* Updated to pyright>=1.1.390  (from pyright>=1.1.378)
* Updated to sourcery>=1.27  (from sourcery>=1.22)
* Updated to lxml>=5.3  (from lxml>=5.2)
* Updated to types-lxml>=2024.11  (from types-lxml>=2024.4)
* Updated to jupyter>=1.1  (from jupyter>=1.0)
* Updated to pytest-cov>=6.0  (from pytest-cov>=5.0)
* Updated to Sphinx>=8.1  (from Sphinx>=8.0)
* Updated to sphinx-argparse-cli>=1.19  (from sphinx-argparse-cli>=1.17)
* Updated to sphinx-autodoc-typehints>=2.5  (from sphinx-autodoc-typehints>=2.2)
* Updated to pre-commit>=4.0  (from pre-commit>=3.8)
* Updated to mypy>=1.13  (from mypy>=1.11.1)

### Solved
* Resolved issues raised by `ruff`


## [0.4.0] - 2024-11-11

### Breaking changes
* Renamed modules: Following modules have been renamed in order to comply with PEP8 naming conventions: <br>
  `dictIO.dictReader` **->** `dictIO.dict_reader` <br>
  `dictIO.dictWriter` **->** `dictIO.dict_writer` <br>
  `dictIO.dictParser` **->** `dictIO.dict_parser` <br>
  `dictIO.cppDict` **->** `dictIO.cpp_dict` <br>
* Module `formatter.py` : <br>
  Renamed `Formatter.format_type()` **->** `Formatter.format_value()` <br>
* Module `parser.py` : <br>
  Renamed `Parser.parse_type()` **->** `Parser.parse_value()` <br>
  Renamed `Parser.parse_types()` **->** `Parser.parse_values()` <br>
* class `CppDict` in module `dictIO.cppDict` has been replaced with the new class `SDict[K, V]` in module `dictIO.dict`. <br>
  In order to maintain backward compatibility, a thin wrapper class named `CppDict` is kept in version ~0.4.0.
  It is marked as deprecated, though, and will be removed with release 0.5.0.
* Where `CppDict` inherited from `UserDict`, `SDict` inherits directly from Python's `dict` class,
  allowing to use it in any context where a `dict` or any other `MutableMapping` is expected.
* `SDict` is generic: Static type checkers will hence require type arguments when `SDict` is used. <br>
  Where in dictIO < 0.4.0 you could write  <br>
  `my_dict: CppDict = CppDict()`,  <br>
  you will now need to specify the type arguments, e.g.  <br>
  `my_dict: SDict[str, Any] = SDict()`.  <br>
  With this change, type hinting is in line with how Python's builtin `dict` class works, and offers more control in static type checking.

### Changed
* Changed from `pip`/`tox` to `uv` as package manager
* README.md : Completely rewrote section "Development Setup", introducing `uv` as package manager.
* Changed publishing workflow to use OpenID Connect (Trusted Publisher Management) when publishing to PyPI
* Updated copyright statement
* VS Code settings: Turned off automatic venv activation
* Replaced black formatter with ruff formatter

### Solved
* Sphinx documentation: Resolved issue that documentation of class members was generated twice.

### Added
* Sphinx documentation: Added extension to support Markdown-based diagrams created with Mermaid.
* Added instance methods `dump()` and `load()` to `SDict`
* Added `mypy` as static type checker (in addition to `pyright`)

### GitHub workflows
* (all workflows): Adapted to use `uv` as package manager
* _test_future.yml : updated Python version to 3.13.0-alpha - 3.13.0
* _test_future.yml : updated name of test job to 'test313'

### Dependencies
* Updated to ruff>=0.6.3  (from ruff==0.4.2)
* Updated to pyright>=1.1.378  (from pyright==1.1.360)
* Updated to sourcery>=1.22  (from sourcery==1.16)
* Updated to pytest>=8.3  (from pytest>=8.2)
* Updated to Sphinx>=8.0  (from Sphinx>=7.3)
* Updated to sphinx-argparse-cli>=1.17  (from sphinx-argparse-cli>=1.16)
* Updated to myst-parser>=4.0  (from myst-parser>=3.0)
* Updated to furo>=2024.8  (from furo>=2024.5)
* updated to setup-python@v5  (from setup-python@v4)
* updated to actions-gh-pages@v4  (from actions-gh-pages@v3)
* updated to upload-artifact@v4  (from upload-artifact@v3)
* Updated to download-artifact@v4  (from download-artifact@v3)
* updated to checkout@v4  (from checkout@v3)


## [0.3.4] - 2024-05-22

### Dependencies
* updated to ruff==0.4.2  (from ruff==0.2.1)
* updated to pyright==1.1.360  (from pyright==1.1.350)
* updated to sourcery==1.16  (from sourcery==1.15)
* updated to lxml>=5.2  (from lxml>=5.1)
* updated to types-lxml>=2024.4  (from types-lxml>=5.1)
* updated to pytest>=8.2  (from pytest>=7.4)
* updated to pytest-cov>=5.0  (from pytest-cov>=4.1)
* updated to Sphinx>=7.3  (from Sphinx>=7.2)
* updated to sphinx-argparse-cli>=1.15  (from sphinx-argparse-cli>=1.11)
* updated to myst-parser>=3.0  (from myst-parser>=2.0)
* updated to furo>=2024.4  (from furo>=2023.9.10)
* updated to numpy>=1.26,<2.0  (from numpy>=1.26)
* removed black

### Changed
* replaced black formatter with ruff formatter
* Changed publishing workflow to use OpenID Connect (Trusted Publisher Management) when publishing to PyPI
* Updated copyright statement
* VS Code settings: Turned off automatic venv activation


## [0.3.3] - 2024-02-21

### Hotfix
* corrected name of cli script (wrong: dictIO  correct: dictParser)


## [0.3.2] - 2024-02-21

### Added
* README.md : Under `Development Setup`, added a step to install current package in "editable" mode, using the pip install -e option.
This removes the need to manually add /src to the PythonPath environment variable in order for debugging and tests to work.

### Removed
* VS Code settings: Removed the setting which added the /src folder to PythonPath. This is no longer necessary. Installing the project itself as a package in "editable" mode, using the pip install -e option, solves the issue and removes the need to manually add /src to the PythonPath environment variable.

### Changed
* Moved all project configuration from setup.cfg to pyproject.toml
* Moved all tox configuration from setup.cfg to tox.ini.
* Moved pytest configuration from pyproject.toml to pytest.ini
* Deleted setup.cfg

### Dependencies
* updated to black[jupyter]==24.1  (from black[jupyter]==23.12)
* updated to version: '==24.1'  (from version: '==23.12')
* updated to ruff==0.2.1  (from ruff==0.1.8)
* updated to pyright==1.1.350  (from pyright==1.1.338)
* updated to sourcery==1.15  (from sourcery==1.14)
* updated to lxml>=5.1  (from lxml>=4.9)


## [0.3.1] - 2024-01-09

### Solved

* Solved a bug that led to single character references not being identified
  (solves [#14](https://github.com/dnv-opensource/dictIO/issues/14)).


## [0.3.0] - 2024-01-08

### Changed

* Enabled recognition of strings with nested quotes in it (solves [#2](https://github.com/dnv-opensource/dictIO/issues/2))
* GitHub workflows: Included Python 3.12 release version as standard, and Python 3.13.0a2 as "future" test.

### Dependencies

* updated to black[jupyter]==23.12  (from black[jupyter]==23.11)
* updated to ruff==0.1.8  (from ruff==0.1.6)
* updated to pyright==1.1.338  (from pyright==1.1.336)


## [0.2.9] - 2023-09-20

### Dependencies

* Updated dependencies to latest versions


## [0.2.8] - 2023-06-22

### Changed

* Modularized GitHub workflows
* Changed default Python version in GitHub workflows from 3.10 to 3.11

### Dependencies

* requirements-dev.txt: Updated dependencies to latest versions


## [0.2.7] - 2023-05-04

### Changed

* dependencies: updated dependencies to latest versions
* ruff: added rule-set "B" (flake8-bugbear)


## [0.2.6] - 2023-01-11

### Changed

* Added missing DocStrings for public classes, methods and functions
* Changed links to package documentation to open README.html, not the default index page


## [0.2.5] - 2023-01-04

### Changed

* Linter: Migrated from flake8 to ruff. <br>
  (Added ruff; removed flake8 and isort)
* Adjusted GitHub CI workflow accordingly. <br>
  (Added ruff job; removed flake8 and isort jobs)
* VS Code settings: Adjusted Pylance configuration
* Sphinx documentation: Rebuilt API documentation

### Added

* Added a batch file 'qa.bat' in root folder to ease local execution of code quality checks


## [0.2.4] - 2022-12-12

### Changed

* Moved dev-only dependencies from requirements.txt to requirements-dev.txt
* dictIO/`__utils__`.py : ensured that imported symbols get also exported <br>
  (added "as" clause -> "from x import y as y" instead of only "from x import y")
* Configured code quality tools flake8, black, isort, pyright
* Improved code quality, resolving all warnings and errors flagged by the configured code quality tools
  (flake8, black, isort, pyright, sourcery)

### Added

* Added support for selected numpy functions (diag, eye, ones, zeros)
  which can now be used in expressions. <br>
  This is an experimental feature which might be removed or changed in future.
* Added GitHub workflow 'main.yml' for continuous integration (runs all CI tasks except Sphinx)
    * format checks: black, isort
    * lint check: flake8, flake8-bugbear
    * type check: pyright
    * test: uses tox to run pytest on {Windows, Linux, MacOS} with {py39, py310}
    * publish: publishing to PyPI (runs only on push of new tag vx.x.x, and after all other jobs succeeded)
    * merge_to_release_branch: merge tagged commit to release branch (runs after publish)


## [0.2.3] - 2022-12-01

### Changed

* Code formatting: Changed from yapf to black
* STYLEGUIDE.md : Adjusted to match black formatting
* VS Code settings: Updated to use black as formatter
* requirements.txt: Updated dependencies to their most recent versions
* GitHub actions (yml files): Updated following actions to their most recent versions:
    * checkout@v1 -> checkout@v3
    * setup-python@v2 -> setup-python@v4
    * cache@v2 -> cache@v3

### Added

* Added sourcery configuration (.sourcery.yaml)
* Added py.typed file into the package root folder and included it setup.cfg as package_data
* Documentation: Included sub-package dictIO.utils in documentation


## [0.2.2] - 2022-11-08

### Added

* JsonParser: JsonParser now supports the usage of references and expressions, similar to the CppParser.

## [0.2.1] - 2022-10-13

### Solved

* XmlParser: Solved a bug where default namespaces in an XML file would not be parsed correctly.

## [0.2.0] - 2022-09-29

### Added

* dictIO.utils.path.py: Added two new functions
    * highest_common_root_folder(paths)
    * relative_path(from_path, to_path)

### Changed

* Replaced usages of pathlib.Path.resolve_to() with dictIO.utils.path.relative_path()

### Removed

* dictIO.utils.path.py: Removed obsolete function silent_remove()


## [0.1.2] - 2022-09-27

### Solved

* XmlParser: Changed how empty XML nodes get parsed. <br>
    The value for an empty node is now saved as an empty dict, i.e. {}, instead of None.
    This change solves [issue #4](https://github.com/dnv-opensource/dictIO/issues/4).<br>
    Problem was that None is not iterable, and code such as the following had caused an exception:
    ~~~py
    if '_attributes' in my_parsed_xml_dict[node_key]:
        ...
    ~~~
    because my_parsed_xml_dict[node_key] had been None.

    Now, with the code change in place, my_parsed_xml_dict[node_key] would resolve to an empty dict ( {} ) instead of to None. As a dict is formally iterable (even when empty), querying code as above does no longer crash.


## [0.1.1] - 2022-08-19

### Added

* cppDict:
    * Added method include(dict_to_include).
        This method adds an include directive for the passed in dict inside the dict the method is called on.


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
[unreleased]: https://github.com/dnv-opensource/dictIO/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/dnv-opensource/dictIO/compare/v0.3.4...v0.4.0
[0.3.4]: https://github.com/dnv-opensource/dictIO/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/dnv-opensource/dictIO/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/dnv-opensource/dictIO/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/dnv-opensource/dictIO/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dnv-opensource/dictIO/compare/v0.2.9...v0.3.0
[0.2.9]: https://github.com/dnv-opensource/dictIO/compare/v0.2.8...v0.2.9
[0.2.8]: https://github.com/dnv-opensource/dictIO/compare/v0.2.7...v0.2.8
[0.2.7]: https://github.com/dnv-opensource/dictIO/compare/v0.2.6...v0.2.7
[0.2.6]: https://github.com/dnv-opensource/dictIO/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/dnv-opensource/dictIO/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/dnv-opensource/dictIO/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/dnv-opensource/dictIO/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/dnv-opensource/dictIO/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/dnv-opensource/dictIO/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/dnv-opensource/dictIO/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/dnv-opensource/dictIO/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/dnv-opensource/dictIO/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dnv-opensource/dictIO/compare/v0.0.22...v0.1.0
[0.0.22]: https://github.com/dnv-opensource/dictIO/compare/v0.0.17...v0.0.22
[0.0.17]: https://github.com/dnv-opensource/dictIO/releases/tag/v0.0.17
[dictIO]: https://github.com/dnv-opensource/dictIO
