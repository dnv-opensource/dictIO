# README
dictIO is a Python package to read, parse and write dictionaries in C++ dictionary format, as well as JSON, XML and OpenFOAM.

## What are dictionaries?
Dictionaries are a modified adaptations of C++ dictionaries, as the are used e.g. within OpenFOAM.
Some syntactic addions are made to improve the usability and versatility of dictionaries.
Dictionaries support
* reading and writing data in C++ dictionary format​
* translating files into runtime data structures with minimal expense: dict is one of the core built-in data structures in Python 3.9​
* supporting variables and expressions, resolved during parseing
* supporting cascaded dict files:  base dict including param dict yielding case dict​
* is widely tolerant in reading different flavours (quotes, preserving comments, etc.)​
* can read C++ dictionary, JSON, XML​
* can write C++ dictionary, JSON, XML, OpenFOAM​

## Installation
```
python -m pip install dictIO
```

## Example
