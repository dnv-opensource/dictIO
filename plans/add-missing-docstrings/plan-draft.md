# Plan: Add missing docstrings

## Problem Statement

In the current Python code base, many public functions, methods, attributes, classes,
modules and sub-packages are still missing docstrings.
Goal is to ensure all public functions, methods, attributes, classes, modules and
sub-packages have docstrings.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run ruff check --ignore D` to identify existing non-docstring violations in ruff (ruff-check-other-baseline).
- Inventory all files with docstring violations, noting count per file and current violations.

## Proposed Approach

- Read the instructions for docstrings given in
  `/AGENTS.md`, section [Docstrings](/AGENTS.md#docstrings).
- Read `ruff.toml`. Therein, check for ruff rules from the `D10x` family which are listed as "temporarily ignored",
  i.e. listed under the `# Ruff lint rules temporarily ignored` line comment at top of the `ignore` list.
  Such temporarily ignored rules can e.g. be:
    "D100", # Missing docstring in public module
    "D101", # Missing docstring in public class
    "D102", # Missing docstring in public method
    "D103", # Missing docstring in public function
    "D104", # Missing docstring in public package
    "D105", # Missing docstring in magic method
    "D107", # Missing docstring in `__init__`
  In case you _do_ find ruff rules from the `D10x` family listed as "temporarily ignored", then your
  goal is to eventually have these rules reactivated again (i.e. removed from the ignore list).
  As you progress, sequentially re-activate the rules, by step-by-step
  removing them from the ignore list in `ruff.toml`, then add the respective docstrings where flagged missing
  until `uv run ruff check` reports no more missing docstrings, and then repeat for the next rule.
- Work in phases, "inside-out": Start with docstrings for symbols defined in a smaller / more
  local scope to docstrings for symbols defined in a more global scope.
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

- Ensure all added or changed docstrings follow the instructions for docstrings given in
  `/AGENTS.md`, section [Docstrings](/AGENTS.md#docstrings).
- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run ruff check --ignore D` (ruff-check-other) and compare the results to the baseline (ruff-check-other-baseline). Ensure there is no regression.
- Compare the two ruff check results (ruff-check and ruff-check-other). The difference between them gives the docstring violations (ruff-check-docstring).
- Confirm there are no remaining docstring violations (ruff-check-docstring).

## Definition of Done

- [ ] In `ruff.toml`, all `D10x` rules which were listed as temporarily ignored (if so) are reactivated, i.e. removed.
- [ ] Missing docstrings added (all phases complete).
- [ ] Added docstrings follow the instructions for docstrings given in
      `/AGENTS.md`, section [Docstrings](/AGENTS.md#docstrings).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] `uv run ruff check --ignore D` (ruff-check-other) - no regression compared to the baseline (ruff-check-other-baseline).
- [ ] Docstring violations (ruff-check-docstring) - 0 errors.
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] Documentation updated (if needed).
