# C++ dictionary (cpp)

## Description

C++ dictionary (cpp) is the default file format used by dictIO.
The C++ dictionary format used by dictIO has (by intention) many similarities with the OpenFOAM file format,
but is slightly simpler and more flexible in its lexical structure.

## Structure

The basic structure of a cpp dict file consists of
* header (block comment) [optional]
* include directive(s) [optional]
* elements (each written as key value pair)

As header and include directives are optional, the simplest form of a cpp dict file could look as follows, i.e. containing just a single element:
~~~
key     value;
~~~

## Header

The default C++ block comment used as header in cpp dict files looks as follows:
~~~
/*---------------------------------*- C++ -*----------------------------------*\
filetype dictionary; coding utf-8; version 0.1; local --; purpose --;
\*----------------------------------------------------------------------------*/
~~~

## Include Directive(s)

One of the most powerful features of OpenFOAM files is their ability to be cascaded through the use of include directives.
An include directive declares an external dict file to be included.
'Included' means all elements of the external dict will be read and merged into the 'parent' dict when reading.

Example of an include directive looks like follows:


## Example

Below example shows a typical dict file.
In the example, ..:
