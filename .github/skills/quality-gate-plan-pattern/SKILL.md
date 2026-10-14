---
name: quality-gate-plan-pattern
description: >-
  Shared baseline, validation, and per-phase pattern for Python
  quality-gate remediation plans (ruff check, ruff format, pyright,
  mypy, docstrings, type annotations, type stubs). Use when: generating
  or implementing a plans/<task>/plan-draft.md that fixes or improves
  compliance with one of these quality gates, to avoid re-deriving the
  common baseline/validation boilerplate already defined here.
---

# Quality Gate Plan Pattern

Reusable procedure referenced by the `add-missing-docstrings`,
`add-type-hints`, `add-type-stubs`, `fix-mypy`, `fix-pyright`,
`fix-ruff-check`, and `reformat-existing-docstrings` draft plans in
`plans/`. Each of those plans states only its own rule-specific delta
(which command/rule family, which extra constraints) and points here
for the shared steps below.

## Common Baseline steps

1. Determine scope: check which directories in the current code base
   actually contain Python source files (e.g. `src/`, `examples/`,
   `scripts/`, `tests/`, `packages/`, `tools/`, etc.).
2. Inspect the Ruff configuration's global and per-file ignores for
   suppressions of the plan's target rule family. Run the normal configured
   check and a direct check selecting that rule family with relevant
   per-file ignores disabled, then record both results. Do not treat a clean
   configured check as proof that the target family has no findings.
3. Run `uv run ruff format --check` and confirm formatting is clean.
4. Run `uv run pytest -q` and record how many tests pass
   (pytest-baseline).
5. Run the plan's own rule-specific baseline command(s) (e.g.
   `uv run ruff check --ignore <FAMILY>`, `uv run pyright`,
   `uv run mypy`) - see the calling plan for which ones apply.

## Common Context pattern

- Relevant modules: All Python source files in `<scope>` (confirm
  scope before starting).
- Related tests: state explicitly per plan - `All` (run
  `uv run pytest --collect-only -q` to list them) for plans that
  change runtime-affecting code (type annotations, type stubs,
  ruff-check fixes, mypy/pyright fixes); `None` for plans that only
  affect docstrings.

## Common per-phase loop

Work in phases (the ordering criterion is rule-specific - see the
calling plan). After each phase:

1. Run `uv run ruff format` to reformat any changed files.
2. **Typing-related plans only** (`add-type-hints`, `add-type-stubs`,
   `fix-mypy`, `fix-pyright`): clean up stale `# type: ignore` /
   `# pyright: ignore` comments. Use pyright's
   `reportUnnecessaryTypeIgnoreComment` (surfaces as "information"
   level) and `uv run mypy --warn-unused-ignores` to detect them, then
   remove the stale ones.
3. Run the plan's Validation Strategy.

## pyright / mypy divergence on `# type: ignore`

`# type: ignore` suppresses diagnostics for **both** mypy and pyright.
`# pyright: ignore`, instead, suppresses only pyright.

When you remove or modify a `# type: ignore` comment while fixing an
error in one tool, always check the *other* tool still passes. In case
of a conflict:
- If pyright no longer needs a suppression but mypy still does, remove
  the conflicting `# type: ignore` comment on line level but add a
  mypy ignore comment on module level instead for the specific rule,
  i.e. `# mypy: disable-error-code="rule"`.
- If mypy no longer needs a suppression but pyright still does, replace
  the conflicting `# type: ignore` comment with `# pyright: ignore[rule]`
  instead.

## Common Validation Strategy steps

- Run `uv run ruff format --check` to confirm all files are correctly
  formatted.
- Run the plan's own rule-specific validation command(s) and compare
  to that command's baseline - see the calling plan for which ones
  apply and whether "no regression" or "track progress toward zero"
  is expected.
- Run `uv run pytest -q` (pytest) and compare the results to the
  baseline (pytest-baseline). Ensure there is no regression.

## Common Definition of Done items

Every calling plan's own Definition of Done should include these,
spelled out in full (not referenced), alongside its rule-specific
items:

- [ ] `uv run ruff format --check` passes.
- [ ] `uv run pytest -q` (pytest) - no regression compared to the
      baseline (pytest-baseline).
