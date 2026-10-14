# Plan: Fix issues raised by ruff check

## Problem Statement

`uv run ruff check` (ruff-check) currently raises various errors across the Python code base in this project.
The goal is to eliminate all ruff check errors and as many warnings as practical by systematically fixing the code for each violated rule - not by suppressing rules.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run ruff check --statistics` to get a per-rule summary.
- Categorize all ruff violations by rule (e.g. `F401`, `E501`, `W291`).
- Inventory all files with ruff violations, noting count per file, current violations, and associated violated rules (categories).

## Proposed Approach

- Work in phases, ordered from easiest mechanical fixes to the most structural refactorings.
- After each phase, follow the common per-phase loop in
  [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md)
  (reformat, then run Validation Strategy). This plan does not use the
  skill's optional stale-`# type: ignore`-comment cleanup sub-step.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: All (run `uv run pytest --collect-only -q` to get a list of all tests)
- Constraints:
  - Do **not** suppress rules globally in `ruff.toml`. The goal is to actually fix the code, not hide errors.
  - Suppress per-line with `# noqa` only as a last resort for cases where the ruff rule is genuinely inapplicable.
  - Some rules (e.g. `UP042`) are classified as "unsafe" by ruff. `--fix` alone will
    silently skip them. Use `--fix --unsafe-fixes` for those categories, but always
    review the diff before committing.

## Validation Strategy

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Track progress and ensure number of errors decreases compared to the baseline.

## Definition of Done

- [ ] Code changes implemented (all phases complete).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - passes (0 errors).
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] No rules added to the `ignore` list in `ruff.toml` without documented justification.
