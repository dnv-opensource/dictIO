# mypy: ignore-errors

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version
from pathlib import Path

sys.path.insert(0, str(Path("../../src").absolute()))

# Read version from installed package metadata
try:
    __version__ = _get_version("dictIO")
except PackageNotFoundError:
    # Docs may be built from a source checkout without the package installed
    __version__ = "0.0.0.dev0"

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "dictIO"
copyright = "2026, DNV SE. All rights reserved."
author = "Frank Lumpitzsch, Claas Rostock, Seunghyeon Yoo"

# The full version, including alpha/beta/rc tags
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_argparse_cli",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinxcontrib.mermaid",
]

# Extenstion for myst_parser
myst_enable_extensions = [
    "dollarmath",
    "attrs_inline",
]

# The file extensions of source files.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = f"dictIO {release}"
html_theme = "furo"
html_static_path = ["_static"]
html_logo = "_static/dictIO.svg"
autodoc_default_options = {
    "member-order": "groupwise",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_preserve_defaults = True
autodoc_typehints = "both"
autodoc_typehints_description_target = "all"

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True

myst_heading_anchors = 3

todo_include_todos = False

# add markdown mermaid support
myst_fence_as_directive = ["mermaid"]
