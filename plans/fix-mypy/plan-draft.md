# Plan: Fix issues raised by mypy

## Problem Statement

`uv run mypy` (mypy) currently raises various errors across the Python code base in this project.
The goal is to eliminate all mypy errors and as many mypy warnings as practical by systematically fixing the code for each violated rule — not by suppressing rules.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run pyright` to identify all existing violations in pyright (pyright-baseline).
- Run `uv run mypy` to identify all existing violations in mypy (mypy-baseline).
- Run `uv run mypy --warn-unused-ignores` and record stale `# type: ignore` comments. These often represent the bulk of the work.
- Categorize all mypy violations by rule (e.g. `arg-type`, `assignment`, `override`, `attr-defined`).
- Inventory all files with mypy violations, noting count per file, current violations, and associated violated rules (categories).

## Proposed Approach

Work in phases, ordered from easiest mechanical fixes to the most
structural refactorings. After each phase, follow the common per-phase
loop in
[.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md)
(reformat, stale-`# type: ignore`-comment cleanup, then run Validation
Strategy).

See the skill's "pyright / mypy divergence on `# type: ignore`" section
for how to resolve conflicts between the two tools' suppressions.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: All (run `uv run pytest --collect-only -q` to get a list of all tests)
- Constraints:
  - Do **not** suppress rules globally in `pyproject.toml`. The goal is to actually fix the code, not hide errors.
  - Suppress per-line with `# type: ignore` only as a last resort for cases where the mypy rule is genuinely inapplicable.

## Validation Strategy

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run pyright` (pyright) and compare the results to the baseline (pyright-baseline).
Ensure there is no regression.
- Run `uv run mypy` (mypy) and compare the results to the baseline (mypy-baseline).
Track progress and ensure number of errors decreases compared to the baseline.

## Definition of Done

- [ ] Code implemented (all phases complete).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] `uv run pyright` (pyright) - no regression compared to the baseline (pyright-baseline).
- [ ] `uv run mypy` (mypy) - passes (0 errors).
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] No rules added to the `ignore` list in `pyproject.toml` without documented justification.
