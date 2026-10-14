# Plan: Add type stubs for 3rd party packages

## Problem Statement

The Python code base in this project uses multiple third party packages.
In order to improve typing in the code base, type stubs for the most relevant third party package(s) shall be created where they don't already ship inline types.
The goal is to have type stubs for those modules and symbols from third party packages which are used in the current code base but lack proper type information.

## Baseline

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common baseline steps (scope determination, `ruff format --check`, `pytest -q` baseline).
- Run `uv run ruff check` to identify all existing violations in ruff (ruff-check-baseline).
- Run `uv run ruff check --ignore ANN --ignore RUF100` to identify existing non-annotation violations in ruff (ruff-check-other-baseline).
- Compare the two baselines (ruff-check-baseline and  ruff-check-other-baseline). The difference between them gives the baseline for annotation violations (ruff-check-annotation-baseline).
- Run `uv run pyright` to identify all existing typing violations in pyright (pyright-baseline).
- Run `uv run mypy` to identify all existing typing violations in mypy (mypy-baseline).
- Identify which third-party imports lack type stubs (look for `reportMissingTypeStubs` in pyright output or `import-untyped` in mypy output).
- Inventory all files with typing violations from missing stubs, noting count per file and current violations.

## Proposed Approach

- Determine which untyped third party packages have relevant negative impact on typing in the code base. Prioritize by how many type errors they cause.
- Work in phases, ordered from easiest-to-infer types to hardest-to-infer types.
- For each 3rd-party class you stub, trace all attribute access chains used in the codebase (e.g. `.venv.envs[0]`).
  Stub every intermediate class and attribute that appears in such a chain, not only the directly imported symbols.
- Place stubs in a `stubs/` directory at the repo root. Register the stub path in `pyproject.toml` under `[tool.mypy] mypy_path` and `[tool.pyright] stubPath`.
- Before creating a stub, verify the actual runtime import owner with `importlib.util.find_spec()` or an equivalent import-path check. Inspect the imported module's symbols and package metadata so the stub package name matches the API used by the codebase.
- For every stubbed package, run a minimal runtime smoke test for the imported symbols and important access chains. Distinguish static-analysis support from runtime package availability, especially for optional dependencies.
- After each phase, follow the common per-phase loop in
  [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md)
  (reformat, stale-`# type: ignore`-comment cleanup, then run Validation
  Strategy).

See the skill's "pyright / mypy divergence on `# type: ignore`" section
for how to resolve conflicts between the two tools' suppressions.

## Context

- Relevant modules: All Python source files in <scope> (confirm scope before starting)
- Related tests: All (run `uv run pytest --collect-only -q` to get a list of all tests)
- Constraints:
  - **`py.typed` check:** Before creating stubs for a package, check whether it ships a `py.typed` marker.
    If it does, mypy will use the package's own inline types and ignore custom stubs in `stubs/`.
    Stubs in that case only benefit pyright (which prefers local stubs). Factor this into prioritization.

## Validation Strategy

- See [.github/skills/quality-gate-plan-pattern/SKILL.md](../../.github/skills/quality-gate-plan-pattern/SKILL.md) for the common `ruff format --check` and `pytest -q` validation steps.
- Run `uv run ruff check` (ruff-check) and compare the results to the baseline (ruff-check-baseline). Ensure there is no regression.
- Run `uv run ruff check --ignore ANN --ignore RUF100` (ruff-check-other) and compare the results to the baseline (ruff-check-other-baseline). Ensure there is no regression.
- Compare the two ruff check results (ruff-check and ruff-check-other). The difference between them gives the annotation violations (ruff-check-annotation).
- Compare the annotation violations (ruff-check-annotation) to the baseline (ruff-check-annotation-baseline). Track progress and ensure number of errors decreases compared to the baseline.
- Run `uv run pyright` (pyright) and compare the results to the baseline (pyright-baseline). Track progress and ensure number of errors decreases compared to the baseline.
- Run `uv run mypy` (mypy) and compare the results to the baseline (mypy-baseline). Track progress and ensure number of errors decreases compared to the baseline.

## Definition of Done

- [ ] Type stubs added for the prioritized third party package (all phases complete)
- [ ] Stub path registered in `pyproject.toml` (mypy and pyright config).
- [ ] `uv run ruff format --check` passes.
- [ ] `uv run ruff check` (ruff-check) - no regression compared to the baseline (ruff-check-baseline).
- [ ] Annotation violations (ruff-check-annotation) - number of errors has reduced by at least 90 % compared to the baseline (ruff-check-annotation-baseline) (target: 100 %).
- [ ] `uv run pyright` (pyright) - number of errors has reduced by at least 90 % compared to the baseline (pyright-baseline) (target: 100 %).
- [ ] `uv run mypy` (mypy) - number of errors has reduced by at least 90 % compared to the baseline (mypy-baseline) (target: 100 %).
- [ ] `uv run pytest -q` (pytest) - no regression compared to the baseline (pytest-baseline).
- [ ] No rules added to the `ignore` lists in `ruff.toml` and `pyproject.toml` without documented justification.
