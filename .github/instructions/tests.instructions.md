---
applyTo: "tests/**/*"
---

Test files in `tests/` are subject to the project-wide docstring
requirements in `/AGENTS.md`; public test modules, classes, functions,
and methods need behavior-focused Google-style docstrings. Ruff's `D`
rules are enabled for tests. Other test-specific exceptions remain in
`ruff.toml`'s `"tests/**/*"` ignore block:

- Return type annotations are **not required** on test functions or
  methods (`ANN201`/`ANN202` ignored).
- `assert` statements and magic values in comparisons are allowed
  (`S101`, `PLR2004` ignored) - this is normal `pytest` usage, not a
  code smell.
- Unused function/method arguments are allowed where required by a
  fixture or parametrization signature (`ARG001`, `ARG002` ignored).
- Accessing private members (`SLF001`) is allowed for white-box
  testing.
- `tests/` is not required to be an importable package with
  `__init__.py` (`INP001` ignored).
- Commented-out code (`ERA001`) is allowed - test files sometimes keep
  an alternate assertion or fixture call commented out for local
  debugging.
- `@pytest.mark.parametrize`'s first argument may be a comma-separated
  string of parameter names (`PT006` ignored), e.g.
  `"arg_1,arg_2,arg_3"`.
- Raising `TypeError` is not required for invalid-type branches
  (`TRY004` ignored).

All other rules in `/AGENTS.md` (fixtures, `tests/test_working_directory`
handling, determinism/independence) still apply in full - see
`/AGENTS.md`'s "Testing" section.
