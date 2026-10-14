# Plan: Fix issues raised by pyright

## Problem Statement

`uv run pyright` (pyright) currently raises various errors across the Python code base in this project.
The goal is to eliminate all pyright errors and as many pyright warnings as practical by systematically fixing the code for each violated rule — not by suppressing rules.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run pyright` to identify all existing violations in pyright (pyright-baseline).
- Run `uv run mypy` to identify all existing violations in mypy (mypy-baseline).
- Categorize all pyright violations by rule (e.g. `reportGeneralClassIssues`, `reportAttributeAccessIssue`, `reportArgumentType`).
- Inventory all files with pyright violations, noting count per file, current violations, and associated violated rules (categories).

## Proposed Approach

Work in phases, ordered from easiest mechanical fixes to the most
structural refactorings. After each phase, follow the common per-phase
loop in
[.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md)
(reformat, stale-`# type: ignore`-comment cleanup, then run Validation
Strategy).

### pyright `reportUnknownMemberType` warnings

When you see many `reportUnknownMemberType` warnings cascading from a single variable, the root cause is usually that the variable itself is typed as `Unknown` (often due to an incomplete stub or an untyped return value). Fix it by adding an explicit type annotation at the assignment point rather than chasing each usage individually.

See the skill's "pyright / mypy divergence on `# type: ignore`" section
for how to resolve conflicts between the two tools' suppressions.

### pyright `reportUnusedCallResult` warning

Fix by prepending `_ = ` to the call. Two edge cases:

1. **Parameter name conflict** — If `_` is already a parameter name in the same
   function (e.g. `def f(_: argparse.Namespace)`), reassigning `_` triggers a type
   error. Fix: rename the parameter (e.g. `_args`).
2. **Void-returning functions** — Do NOT assign `_ = json.dump(...)` or other
   `-> None` functions. mypy raises `func-returns-value`. Pyright does not flag
   void-returning calls as unused, so no fix is needed for these.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: All (run `uv run pytest --collect-only -q` to get a list of all tests)
- Constraints:
  - Do **not** suppress rules globally in `pyproject.toml`. The goal is to actually fix the code, not hide errors.
  - Suppress per-line with `# pyright: ignore` only as a last resort for cases where the pyright rule is genuinely inapplicable.

## Validation Strategy

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run pyright` (pyright) and compare the results to the baseline (pyright-baseline). Track progress and ensure number of errors decreases compared to the baseline.
- Run `uv run mypy` (mypy) and compare the results to the baseline (mypy-baseline). Ensure there is no regression.

## Definition of Done

- [ ] Code changes implemented (all phases complete).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] `uv run pyright` (pyright) - passes (0 errors) and reports no `reportUnnecessaryTypeIgnoreComment` information.
- [ ] `uv run mypy` (mypy) - no regression compared to the baseline (mypy-baseline).
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] No rules added to the `ignore` list in `pyproject.toml` without documented justification.
