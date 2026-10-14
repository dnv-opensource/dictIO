# Plan: Add type annotations

## Problem Statement

The Python code base in this project is not fully typed.
The goal is to add type annotations where missing to:
- Public classes
- Arguments and return types of public functions, methods, and properties
- Public attributes and variables
- Private classes
- Arguments and return types of private functions, methods, and properties
- Private attributes and variables

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run ruff check --ignore ANN --ignore RUF100` to identify existing non-annotation violations in ruff (ruff-check-other-baseline).
- Compare the two baselines (ruff-check-baseline and  ruff-check-other-baseline). The difference between them gives the baseline for annotation violations (ruff-check-annotation-baseline).
- Inventory all files with annotation violations, noting count per file and current violations.

## Proposed Approach

- Read the instructions for type annotations given in
  `/AGENTS.md`, section [Type Annotations](/AGENTS.md#type-annotations).
- Work in phases, ordered from easiest-to-resolve types to hardest-to-resolve types.
- After each phase, follow the common per-phase loop in
  [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md),
  including its stale-`# type: ignore`-comment cleanup sub-step and its
  "pyright / mypy divergence on `# type: ignore`" guidance - adding type
  annotations frequently interacts with existing `# type: ignore` /
  `# pyright: ignore` comments.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: All (run `uv run pytest --collect-only -q` to get a list of all tests)

## Validation Strategy

- Ensure all added or changed type annotations follow the instructions for type annotations given in
`/AGENTS.md`, section [Type Annotations](/AGENTS.md#type-annotations).
- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run ruff check --ignore ANN --ignore RUF100` (ruff-check-other) and compare the results to the baseline (ruff-check-other-baseline). Ensure there is no regression.
- Compare the two ruff check results (ruff-check and ruff-check-other). The difference between them gives the annotation violations (ruff-check-annotation).
- Compare the annotation violations (ruff-check-annotation) to the baseline (ruff-check-annotation-baseline). Track progress and ensure number of errors decreases compared to the baseline.

## Definition of Done

- [ ] Missing type annotations added (all phases complete).
- [ ] All type annotations follow the instructions for type annotations given in
      `/AGENTS.md`, section [Type Annotations](/AGENTS.md#type-annotations).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] `uv run ruff check --ignore ANN --ignore RUF100` (ruff-check-other) - no regression compared to the baseline (ruff-check-other-baseline).
- [ ] Annotation violations (ruff-check-annotation) - 0 errors.
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] No rules added to the `ignore` list in `ruff.toml` without documented justification.
