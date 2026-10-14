---
applyTo: "examples/**/*"
---

Files in `examples/` (tutorial and example scripts/notebooks)
are exempt from some rules that apply elsewhere in the codebase,
matching `ruff.toml`'s `"examples/**/*"` ignore block:

- Docstrings are **not required** (ruff's `D` family is ignored
  here).
- `assert` statements and magic values in comparisons are allowed
  (`S101`, `PLR2004` ignored) - illustrative/tutorial code, not
  production logic.
- `print()` calls are allowed (`T201` ignored) - examples are meant
  to show output interactively.
- Module-level imports do not need to be at the top of the
  file/cell (`E402` ignored) - common in notebook-style examples
  with setup cells.
- `examples/` is not required to be an importable package with
  `__init__.py` (`INP001` ignored).
