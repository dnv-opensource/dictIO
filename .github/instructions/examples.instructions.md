---
applyTo: "examples/**/*"
---

Files in `examples/` (tutorial and example scripts/notebooks) are
subject to the project-wide docstring requirements in `/AGENTS.md`;
public modules, classes, functions, and methods need behavior-focused
Google-style docstrings. Ruff's `D` rules are enabled for examples.
Other example-specific exceptions remain in `ruff.toml`'s
`"examples/**/*"` ignore block:

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
