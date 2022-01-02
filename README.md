# README
dictIO is a Python package to read and write Python dicts as text files in C++ dictionary (cpp) format.

It was designed to leverage the versatility of text based dictionary files while easing their use in Python through seamless support for Python dicts.

dictIO supports
* reading and writing Python dicts in C++ dictionary format​.
* usage of references and expressions in dict files, dynamically resolved during reading.
* usage of cascaded dict files, allowing separation of a case-agnostic configuration dict and its case-specific parameterization: baseDict + paramDict = caseDict​

Further, dictIO
* is widely tolerant in reading different flavours (quotes, preserving comments, etc.)​
* can read and write also JSON, XML​ and OpenFOAM (with some limitations)

## Installation
```sh
pip install dictIO
```

## Usage example

dictIO provides a simple, high level API that allows reading and writing Python dicts from/to a dictionary file in essentially one line of code:
~~~py
from dictIO import DictReader, DictWriter

my_dict = DictReader.read('myDict')
DictWriter.write(my_dict, 'myDict')
~~~
_For more examples and usage, please refer to dictIO's [documentation][docs]._


## File Format
The default C++ dictionary format used by dictIO shares, by intention, some commonalities with the [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html) file format, but is kept simpler and more tolerant to different flavours of string formatting.

With some limitations, dictIO supports also reading from and writing to [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html), [Json](https://www.json.org/json-en.html) and [XML](https://www.w3.org/XML/).

_For a detailed documentation of the file format, see the [File Format](fileFormat.md) in dictIO's [documentation][docs]._

## Development setup

1. Install [Python 3.9](https://www.python.org/downloads/release/python-399/)

2. git clone the dictIO repository locally

3. In the root folder of your local dictIO clone:

Create a Python virtual environment:
~~~sh
python -m venv .venv
~~~
Activate the virtual environment:
~~~sh
.venv\Scripts\activate
~~~
Update pip and setuptools:
~~~sh
python -m pip install --upgrade pip setuptools
~~~
Install dictIO's dependencies:
~~~sh
pip install -r requirements.txt
~~~


## Release History

* 0.1.0
    * First release
* 0.0.9
    * Work in progress

## Meta

Frank Lumpitzsch – [@LinkedIn](https://www.linkedin.com/in/frank-lumpitzsch-23013196/) – frank.lumpitzsch@dnv.com

Claas Rostock – [@LinkedIn](https://www.linkedin.com/in/claasrostock/?locale=en_US) – claas.rostock@dnv.com

Seunghyeon Yoo - [@LinkedIn](https://www.linkedin.com/in/seunghyeon-yoo-3625173b/) - seunghyeon.yoo@dnv.com

Distributed under the MIT license. See [LICENSE](LICENSE.md) for more information.

[https://github.com/dnv-opensource/dictIO](https://github.com/dnv-opensource/dictIO)

## Contributing

1. Fork it (<https://github.com/dnv-opensource/dictIO/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

For your contribution, please make sure you follow the [STYLEGUIDE](STYLEGUIDE.md) before creating the Pull Request.

<!-- Markdown link & img dfn's -->
[docs]: https://turbo-adventure-f218cdea.pages.github.io