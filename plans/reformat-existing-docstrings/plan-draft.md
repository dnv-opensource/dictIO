# Plan: Reformat existing docstrings

## Problem Statement

In the current Python code base, existing docstrings are formatted in various, non-uniform styles.
Goal is to reformat all existing docstrings to be Google-style compliant.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run ruff check --ignore D` to identify existing non-docstring violations in ruff (ruff-check-other-baseline).
- Compare the two baselines (ruff-check-baseline and  ruff-check-other-baseline). The difference between them gives the baseline for docstring violations (ruff-check-docstring-baseline).
- Inventory all files with existing docstrings, noting count per file and current style (Google, NumPy, reST, freeform).

## Proposed Approach

- Read the instructions for docstrings given in
  `/AGENTS.md`, section [Docstrings](../../AGENTS.md#docstrings).
- For each file, apply the following transformations as needed:
  - Convert section headers from NumPy/reST style (e.g. `Parameters\n----------`) to Google style (e.g. `Args:`) and remove separator lines.
  - Remove types from docstring argument/return descriptions (types belong only in type annotations).
  - Document default values for all optional arguments (e.g. "Defaults to `X`.").
  - For arguments defaulting to `None`, document the semantics of `None` in addition to the default.
  - For classes, add `Attributes:` section for public attributes and document constructor args in `__init__`.
- Improve the wording of docstrings where the existing description is incorrect, outdated, or too terse to be useful.
- Work in phases.
- After each phase, follow the common per-phase loop in
  [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md)
  (reformat, then run Validation Strategy). This plan does not use the
  skill's optional stale-`# type: ignore`-comment cleanup sub-step.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: None (docstrings don't affect runtime behavior)
- Constraints:
  - When adding a docstring to a class with an empty body (`pass` only), remove the now-unnecessary `pass` to avoid `PIE790`.

## Validation Strategy

- Ensure all reformatted docstrings are Google-style compliant and follow the instructions for docstrings given in
  `/AGENTS.md`, section [Docstrings](../../AGENTS.md#docstrings).
- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run ruff check --ignore D` (ruff-check-other) and compare the results to the baseline (ruff-check-other-baseline). Ensure there is no regression.
- Compare the two ruff check results (ruff-check and ruff-check-other). The difference between them gives the docstring violations (ruff-check-docstring).
- Compare the docstring violations (ruff-check-docstring) to the baseline (ruff-check-docstring-baseline). Track progress and ensure number of errors decreases compared to the baseline.

## Definition of Done

- [ ] All existing docstrings reformatted to Google style (all phases complete).
- [ ] Reformatted docstrings follow the instructions for docstrings given in
      `/AGENTS.md`, section [Docstrings](../../AGENTS.md#docstrings).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] `uv run ruff check --ignore D` (ruff-check-other) - no regression compared to the baseline (ruff-check-other-baseline).
- [ ] Docstring violations (ruff-check-docstring) - 0 errors.
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] Documentation updated (if needed).
