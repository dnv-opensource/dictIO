# README
dictIO is a Python package to read and write Python dicts as text files in C++ dictionary (cpp) format.

dictIO was designed to leverage the versatility of text based dictionary files while easing their use in Python through seamless support for Python dicts and provision of a simple, high level API that allows reading and writing Python dicts from/to a dictionary file in essentially one line of code.
~~~
from dictIO import DictReader, DictWriter

my_dict = DictReader.read('myDict')
DictWriter.write(my_dict, 'myDict')
~~~

## Installation
```
python -m pip install dictIO
```

## Core Features
dictIO supports
* reading and writing Python dicts in C++ dictionary format​.
* usage of references and expressions in dict files, dynamically resolved during reading.
* usage of cascaded dict files, allowing separation of a case-agnostic configuration dict and its case-specific parameterization: baseDict + paramDict = caseDict​

Further, dictIO
* is widely tolerant in reading different flavours (quotes, preserving comments, etc.)​
* can read and write also JSON, XML​ and OpenFOAM (with some limitations)

## File Format
The default C++ dictionary format used by dictIO shares, by intention, some commonalities with the [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html) file format, but is kept simpler and more tolerant to different flavours of string formatting.

With some limitations, dictIO supports also reading from and writing to [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html), [Json](https://www.json.org/json-en.html) and [XML](https://www.w3.org/XML/).

For a detailed documentation of the file format, see the [File Format](fileFormat.md) in the documentation.
