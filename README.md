# dictIO
dictIO is a Python package to read, write and manipulate dictionary text files.

It was designed to leverage the versatility of text based dictionary files, or 'dict files' in short, while easing their use in Python through seamless support for Python dicts.

dictIO supports
* reading and writing Python dicts in dict files.
* usage of references and expressions in dict files, dynamically resolved during reading.
* usage of cascaded dict files, allowing separation of a case-agnostic configuration dict and its case-specific parameterization: baseDict + paramDict = caseDict

Further, dictIO
* is widely tolerant in reading different flavours (quotes, preserving comments, etc.)
* can read and write also JSON, XML and OpenFOAM (with some limitations)

## Installation
```sh
pip install dictIO
```

## Usage Example

dictIO provides a simple, high level API that allows reading and writing Python dicts from/to dict files:
~~~py
from dictIO import DictReader, DictWriter

my_dict = DictReader.read('myDict')
DictWriter.write(my_dict, 'parsed.myDict')
~~~

The above example reads a dict file, merges any (sub-)dicts included through #include directives, evaluates expressions contained in the dict,
and finally saves the read and evaluated dict with prefix 'parsed' as 'parsed.myDict'.

This sequence of reading, evaluating and writing a dict is also called 'parsing' in dictIO.
Because this task is so common, dictIO provides a convenience class for it:
Using DictParser.parse() the above task can be accomplished in one line of code:
~~~py
from dictIO import DictParser

DictParser.parse('myDict')
~~~

The above task can also be invoked from the command line, using the 'dictParser' command line script installed with dictIO:
~~~sh
dictParser myDict
~~~

_For more examples and usage, please refer to dictIO's [documentation][dictIO_docs]._


## File Format
The default dictionary file format used by dictIO shares, by intention, some commonalities with the [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html) file format, but is kept simpler and more tolerant to different flavours of string formatting.

With some limitations, dictIO supports also reading from and writing to [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html), [Json](https://www.json.org/json-en.html) and [XML](https://www.w3.org/XML/).

_For a detailed documentation of the dict file format used by dictIO, see [File Format](fileFormat.md) in [dictIO's documentation][dictIO_docs] on GitHub Pages._

## Development Setup

1. Install Python 3.9 or higher, i.e. [Python 3.9](https://www.python.org/downloads/release/python-3912/) or [Python 3.10](https://www.python.org/downloads/release/python-3104/)

2. Update pip and setuptools:

    ~~~sh
    $ python -m pip install --upgrade pip setuptools
    ~~~

3. git clone the dictIO repository into your local development directory:

    ~~~sh
    git clone https://github.com/dnv-opensource/dictIO path/to/your/dev/dictIO
    ~~~

4. In the dictIO root folder:

    Create a Python virtual environment:
    ~~~sh
    $ python -m venv .venv
    ~~~
    Activate the virtual environment: <br>
    ..on Windows:
    ~~~sh
    > .venv\Scripts\activate.bat
    ~~~
    ..on Linux:
    ~~~sh
    $ source .venv/bin/activate
    ~~~
    Update pip and setuptools:
    ~~~sh
    $ python -m pip install --upgrade pip setuptools
    ~~~
    Install dictIO's dependencies:
    ~~~sh
    $ pip install -r requirements-dev.txt
    ~~~

## Meta

Copyright (c) 2023 [DNV](https://www.dnv.com) [open source](https://github.com/dnv-opensource)

Frank Lumpitzsch – [@LinkedIn](https://www.linkedin.com/in/frank-lumpitzsch-23013196/) – frank.lumpitzsch@dnv.com

Claas Rostock – [@LinkedIn](https://www.linkedin.com/in/claasrostock/?locale=en_US) – claas.rostock@dnv.com

Seunghyeon Yoo – [@LinkedIn](https://www.linkedin.com/in/seunghyeon-yoo-3625173b/) – seunghyeon.yoo@dnv.com

Distributed under the MIT license. See [LICENSE](LICENSE.md) for more information.

[https://github.com/dnv-opensource/dictIO](https://github.com/dnv-opensource/dictIO)

## Contributing

1. Fork it (<https://github.com/dnv-opensource/dictIO/fork>)
2. Create your branch (`git checkout -b myBranchName`)
3. Commit your changes (`git commit -am 'place your commit message here'`)
4. Push to the branch (`git push origin myBranchName`)
5. Create a new Pull Request

For your contribution, please make sure you follow the [STYLEGUIDE](STYLEGUIDE.md) before creating the Pull Request.

<!-- Markdown link & img dfn's -->
[dictIO_docs]: https://dnv-opensource.github.io/dictIO/README.html
[ospx_docs]: https://dnv-opensource.github.io/ospx/README.html
[farn_docs]: https://dnv-opensource.github.io/farn/README.html