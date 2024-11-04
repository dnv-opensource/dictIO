[![pypi](https://img.shields.io/pypi/v/dictIO.svg?color=blue)](https://pypi.python.org/pypi/dictIO)
[![versions](https://img.shields.io/pypi/pyversions/dictIO.svg?color=blue)](https://pypi.python.org/pypi/dictIO)
[![license](https://img.shields.io/pypi/l/dictIO.svg)](https://github.com/dnv-opensource/dictIO/blob/main/LICENSE)
![ci](https://img.shields.io/github/actions/workflow/status/dnv-opensource/dictIO/.github%2Fworkflows%2Fnightly_build.yml?label=ci)
[![docs](https://img.shields.io/github/actions/workflow/status/dnv-opensource/dictIO/.github%2Fworkflows%2Fpush_to_release.yml?label=docs)][dictIO_docs]

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

dictIO's core class is `SDict`, a generic data structure for serializable dictionaries. <br>
`SDict` inherits from Python's builtin `dict`. It can hence be used transparently in any context where a `dict` or any other `MutableMapping` type is expected.

You can use `SDict` the same way you use `dict`. E.g. you can pass a dict literal to its constructor:
```py
from dictIO import SDict

my_dict: SDict[str, int] = SDict(
    {
        "foo": 1,
        "bar": 2,
    }
)
```

The simplest way to to dump and load a dict to / from a file, is to use SDict's `dump()` and `load()` instance methods:

To dump `my_dict` to a file, use `.dump()`:
```py
my_dict.dump("myDict")
```

To load the formerly dumped file into a new dict, use `.load()`:
```py
my_dict_loaded: SDict[str, int] = SDict().load("myDict")
```

In cases where you need more control over how dict files are read and written, <br>
dictIO's `DictReader` and `DictWriter` classes offer this flexibility, while still maintaining a simple and high level API:
```py
from dictIO import DictReader, DictWriter

my_dict = DictReader.read('myDict')
DictWriter.write(my_dict, 'parsed.myDict')
```

The above example reads a dict file, merges any (sub-)dicts included through #include directives, evaluates expressions contained in the dict,
and finally saves the read and evaluated dict with prefix 'parsed' as 'parsed.myDict'.

This sequence of reading, evaluating and writing a dict is also called 'parsing' in dictIO.
Because this task is so common, dictIO provides a convenience class for it:
Using `DictParser.parse()` the above task can be accomplished in one line of code:
```py
from dictIO import DictParser

DictParser.parse('myDict')
```

The `parse` operation can also be executed from the command line, using the 'dictParser' command line script installed with dictIO:
```sh
dictParser myDict
```

_For more examples and usage, please refer to dictIO's [documentation][dictIO_docs]._


## File Format
The native file format used by dictIO shares, by intention, some commonalities with the [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html) file format, but is kept simpler and more tolerant to different flavours of string formatting.

With some limitations, dictIO supports also reading from and writing to [OpenFOAM](https://www.openfoam.com/documentation/guides/latest/doc/openfoam-guide-input-types.html), [Json](https://www.json.org/json-en.html) and [XML](https://www.w3.org/XML/).

_For a detailed documentation of the native file format used by dictIO, see [File Format](fileFormat.rst) in [dictIO's documentation][dictIO_docs] on GitHub Pages._

## Development Setup

### 1. Install uv
This project uses `uv` as package manager.
If you haven't already, install [uv](https://docs.astral.sh/uv), preferably using it's ["Standalone installer"](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2) method: <br>
..on Windows:
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
..on MacOS and Linux:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```
(see [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) for all / alternative installation methods.)

Once installed, you can update `uv` to its latest version, anytime, by running:
```sh
uv self update
```

### 2. Install Python
This project requires Python 3.10 or later. <br>
If you don't already have a compatible version installed on your machine, the probably most comfortable way to install Python is through `uv`:
```sh
uv python install
```
This will install the latest stable version of Python into the uv Python directory, i.e. as a uv-managed version of Python.

Alternatively, and if you want a standalone version of Python on your machine, you can install Python either via `winget`:
```sh
winget install --id Python.Python
```
or you can download and install Python from the [python.org](https://www.python.org/downloads/) website.

### 3. Clone the repository
Clone the dictIO repository into your local development directory:
```sh
git clone https://github.com/dnv-opensource/dictIO path/to/your/dev/dictIO
```

### 4. Install dependencies
Run `uv sync` to create a virtual environment and install all project dependencies into it:
```sh
uv sync
```

### 5. (Optional) Install CUDA support
Run `uv sync` with option `--extra cuda` to in addition install torch with CUDA support:
```sh
uv sync --extra cuda
```

Alternatively, you can manually install torch with CUDA support.
_Note 1_: Do this preferably _after_ running `uv sync`. That way you ensure a virtual environment exists, which is a prerequisite before you install torch with CUDA support using below `uv pip install` command.

To manually install torch with CUDA support, generate a `uv pip install` command matching your local machine's operating system using the wizard on the official [PyTorch website](https://pytorch.org/get-started/locally/).
_Note_: As we use `uv` as package manager, remember to replace `pip` in the command generated by the wizard with `uv pip`.

If you are on Windows, the resulting `uv pip install` command will most likely look something like this:
```sh
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

_Hint:_ If you are unsure which cuda version to indicate in above `uv pip install .. /cuXXX` command, you can use the shell command `nvidia-smi` on your local system to find out the cuda version supported by the current graphics driver installed on your system. When then generating the `uv pip install` command with the wizard from the [PyTorch website](https://pytorch.org/get-started/locally/), select the cuda version that matches the major version of what your graphics driver supports (major version must match, minor version may deviate).


### 6. (Optional) Activate the virtual environment
When using `uv`, there is in almost all cases no longer a need to manually activate the virtual environment. <br>
`uv` will find the `.venv` virtual environment in the working directory or any parent directory, and activate it on the fly whenever you run a command via `uv` inside your project folder structure:
```sh
uv run <command>
```

However, you still _can_ manually activate the virtual environment if needed.
When developing in an IDE, for instance, this can in some cases be necessary depending on your IDE settings.
To manually activate the virtual environment, run one of the "known" legacy commands: <br>
..on Windows:
```sh
.venv\Scripts\activate.bat
```
..on Linux:
```sh
source .venv/bin/activate
```

### 7. Install pre-commit hooks
The `.pre-commit-config.yaml` file in the project root directory contains a configuration for pre-commit hooks.
To install the pre-commit hooks defined therein in your local git repository, run:
```sh
uv run pre-commit install
```

All pre-commit hooks configured in `.pre-commit-config.yaml` will now run each time you commit changes.


### 8. Test that the installation works
To test that the installation works, run pytest in the project root folder:
```sh
uv run pytest
```

## Meta

Copyright (c) 2024 [DNV](https://www.dnv.com) SE. All rights reserved.

Frank Lumpitzsch – [@LinkedIn](https://www.linkedin.com/in/frank-lumpitzsch-23013196/) – frank.lumpitzsch@dnv.com

Claas Rostock – [@LinkedIn](https://www.linkedin.com/in/claasrostock/?locale=en_US) – claas.rostock@dnv.com

Seunghyeon Yoo – [@LinkedIn](https://www.linkedin.com/in/seunghyeon-yoo-3625173b/) – seunghyeon.yoo@dnv.com

Distributed under the MIT license. See [LICENSE](LICENSE.md) for more information.

[https://github.com/dnv-opensource/dictIO](https://github.com/dnv-opensource/dictIO)

## Contributing

1. Fork it (<https://github.com/dnv-opensource/dictIO/fork>)
2. Create an issue in your GitHub repo
3. Create your branch based on the issue number and type (`git checkout -b issue-name`)
4. Evaluate and stage the changes you want to commit (`git add -i`)
5. Commit your changes (`git commit -am 'place a descriptive commit message here'`)
6. Push to the branch (`git push origin issue-name`)
7. Create a new Pull Request in GitHub

For your contribution, please make sure you follow the [STYLEGUIDE](STYLEGUIDE.md) before creating the Pull Request.

<!-- Markdown link & img dfn's -->
[dictIO_docs]: https://dnv-opensource.github.io/dictIO/README.html
[ospx_docs]: https://dnv-opensource.github.io/ospx/README.html
[farn_docs]: https://dnv-opensource.github.io/farn/README.html
