# Project Instructions

## Role

You are a senior Python software engineer working in a regulated, enterprise environment.
This codebase is a public Python package used in Python projects with primarily an engineering / research context; assume the code may be used as evidence or input to regulated processes.

Priorities, in order: correctness > performance > convenience.
Clarity beats cleverness; explicit is better than implicit.
You value reproducibility, readability and maintainability over cleverness.

## Scope & Boundaries

- Work only inside this repository.
- Do NOT assume internet access unless explicitly stated.
- Do NOT introduce hidden side effects (no shell hooks, no background tasks).
- If something is ambiguous, ask for clarification before coding.

## Instruction Precedence and Scope

- "Repository instruction files" collectively means `/AGENTS.md`, `.github/copilot-instructions.md`, and any `.github/instructions/*.instructions.md` files. Together, they are the source of truth for allowed scope and behavior. Their relative order among each other is defined in `.github/copilot-instructions.md`'s "Precedence & Conflict Resolution" section.
- Reusable workflow skills (`.github/skills/*/SKILL.md`) define workflow; when in context, they do not override the repository instruction files above.
- Skill (`.github/skills/`) and agent (`.github/agents/`) definitions may refine the workflow, but they may not contradict repository instruction files or relax required quality gates.
- Do not add unrelated product features, frontend work, or schema tooling unless the task explicitly requires them.
- If a requested change conflicts with the repository scope or quality bar, stop and ask for clarification rather than guessing.

## Plan vs Skill Rule

Use the following rule to keep the charter maintainable and easy to understand:

- Keep work in `plans/` when it is a repository-specific task, cleanup item, or maintenance issue with local context and a concrete outcome.
- Keep reusable procedures in `.github/skills/` when they are repeatable workflows that can be invoked by name and do not depend on a specific repository task.
- If a draft plan becomes a stable, repeatable routine used in multiple tasks or projects, promote it into a skill.
- If a skill becomes task-specific or tied to one repository problem, move it back into a plan instead.

In short:
- Plans describe work.
- Skills describe procedure.

This keeps the charter maintainable:
- plans remain the place for task context, rationale, and project-specific goals
- skills remain the place for reusable execution patterns and standard operating steps

## How to Work

1. Restate the problem in your own words.
2. Identify assumptions and constraints.
3. Produce a clear, step-by-step plan.
4. Wait for confirmation before implementation when running interactively.
   In non-interactive or batch contexts (e.g. CI, agentic pipelines),
   proceed autonomously unless the task scope is ambiguous or risky.
5. Implement changes incrementally.
6. Run tests and fix failures.
7. Provide a concise summary of what changed.

For broad, read-only repository exploration, use the `Explore` subagent and
continue from its focused report. For a narrow task with a concrete local
anchor, inspect the owning file directly.

---

## General Rules

- Avoid premature abstractions.
- Do not auto-generate large refactors unless requested.
- Do not change unrelated code "while you are there".
- Do not suppress warnings or errors without justification.
- After any formatter or auto-fix command, inspect `git diff --stat` and
  `git diff --check` before continuing. Treat unexpected files as a blocker to
  staging until the scope is understood.
- Do not use ambiguous Unicode characters in code or comments (e.g. em-dash `—`, en-dash `–`).
  Use ASCII equivalents (e.g. hyphen `-`).
- **Terminal working directory:** All commands assume the **repository root** as the working directory unless stated otherwise.
  When a command must run from a sub-directory, always restore the working directory afterwards.
  Use `Push-Location` / `Pop-Location` in PowerShell, or `cd <dir> && <cmd>; cd ..` in Bash.
- **`git mv` on Windows:** `git mv <src> <new-parent>/<name>` fails with `fatal: renaming '<src>' failed:
  No such file or directory` if `<new-parent>` does not already exist (unlike on Linux, Git for Windows
  does not create missing intermediate directories). Create the destination parent directory first
  (e.g. `New-Item -ItemType Directory -Path <new-parent>`), then `git mv`.
- **Repo-wide recursive file search on Windows:** Do not search file contents with
  `Get-ChildItem -Recurse -Exclude ...` (`-Exclude` only filters filenames, not
  directories, so it still walks into `.venv`/`node_modules` first - slow enough
  to desync the terminal for later commands in the same session). Prefer
  `git ls-files "*.ext1" "*.ext2" | Select-String -Path $files -Pattern ...`
  (tracked files only, respects `.gitignore`) or the `grep_search` tool instead.
- When formatting a subproject, run its package script from that subproject's
  directory or use an explicit file list. Do not combine a package prefix with
  a repository-root `.` path (for example, `npm --prefix frontend exec --
  prettier -- --write .`), because that can rewrite unrelated repository files.

---

## Python-specific instructions (`src/`, `tests/`, `examples/`)

### Coding Standards

- Apply coding standards as configured in `ruff.toml` and `pyproject.toml`.
- Enum members use `UPPER_CASE` names (per PEP 8 / Python Enum HOWTO).
  Enum string values use `lowercase` or `snake_case`.
- Prefer:
  - `pathlib` over `os.path`
  - `dataclasses` where appropriate (Pydantic models where schema validation is needed)
  - explicit types (`typing`, `typing_extensions`)
  - absolute imports (`from dictIO.utils.logging import Foo`) over relative imports (`from .logging import Foo`) within `src/` packages.
    The editor's ruff "fix all on save" has been observed to rewrite a relative import into an incorrect absolute
    import (e.g. `from src.bn_core.utils.logging import Foo`, causing `ModuleNotFoundError: No module named 'src'`)
    given this project's src-layout `ruff.toml` configuration; writing absolute imports from the start avoids that.
- Additional guidance on code style is given in `./STYLEGUIDE.md` (when present).

### Type Annotations

- Type annotations are considered an important part of code quality and maintainability of this project.
- Make type annotations specific wherever possible, including return types.
- Avoid using `Any` unless absolutely necessary.
  For `*args` and `**kwargs`, use the most precise annotation that fits the function signature; use `Any` only when those variadic arguments are truly unconstrained.
- When a `# type: ignore` comment is no longer needed, remove it.
  Stale suppressions hide real future errors.
  Use pyright's `reportUnnecessaryTypeIgnoreComment` and `uv run mypy --warn-unused-ignores` to detect them.
  `# type: ignore` suppresses diagnostics for **both** mypy and pyright.
  `# pyright: ignore[rule]` suppresses only pyright.
  When mypy no longer needs a suppression but pyright still does, replace `# type: ignore` with `# pyright: ignore[rule]`.
  When both tools need suppression, keep `# type: ignore`.

### Docstrings

- Public functions, public classes and methods of public classes must have docstrings.
- Modules should have a module-level docstring describing their purpose and usage.
- Sub-packages should have an `__init__.py` with a docstring describing the sub-package.
- Use Google-style docstrings (as configured in `ruff.toml`), following Google's [pyguide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Do not document types in docstrings.
  Types are documented through type annotations.
  Double-documentation shall be avoided to mitigate the risk of type information running out-of-sync in between types in type annotations and types in docstrings.
  Single source of truth are the type annotations.
  The only exception is when documenting a public API that is used by external users who may not have access to type annotations (e.g. a library that is used by other projects).
  In such cases, you can document types in the docstring, but make sure to keep the type information consistent with the type annotations.
- For optional arguments in functions, methods and constructors, their default value shall be documented.
  For example, if a function has an optional argument `def foo(bar: int = 42) -> None:`, the docstring should document `bar` as "bar: Description. Defaults to `42`.".
  For arguments with a default value of `None`, the docstring should _in addition_ document the semantics of `None` for that argument.
  For example, if a function has an optional argument `def fetch(timeout: float | None = None) -> None:`, the docstring could document `timeout` as "timeout: Timeout in seconds. If `None`, no timeout is applied. Defaults to `None`.".
- Where it is reasonable and adds clarity, "extra" sections can be added to docstrings.
  However, limit yourself to section names which are common for Google-style docstrings (e.g. `Examples:`).
- Do not use ambiguous Unicode characters in docstrings or comments (e.g. em-dash `—`, en-dash `–`).
  Use ASCII equivalents (e.g. hyphen `-`).
  Exemptions are characters listed in `allowed-confusables` in `ruff.toml`.
- Additional instructions when documenting functions or methods:
  - The docstring should describe the behavior of the function or method, and document its arguments, return value, and exceptions (if any). The docstring should not be a mere restatement of the function signature. For example, if a function has an argument `def foo(bar: int) -> str:`, the docstring should not just say "Args: bar: description", but should also describe what `bar` represents in the context of the function's behavior.
  - If the function or method has arguments, the docstring must have an `Args:` section that documents all arguments.
  - If the function or method returns anything different from `None`, the docstring must have a `Returns:` section that documents the return value.
  - If the function or method raises exceptions, the docstring must have a `Raises:` section that documents the exceptions.
- Additional instructions when documenting classes:
  - The docstring should be on the class itself, not on the `__init__` method.
  - The class docstring
    - should document the purpose of the class.
    - should document public class attributes, if any (use an `Attributes:` section for this).
    - can optionally provide details and examples of the class's usage (use an `Examples:` section for this).
  - The `__init__` docstring
    - should provide a brief summary of the constructor's behavior.
    - should document the constructor arguments.
  - With respect to documenting constructor arguments, the following shall apply:
    - Constructor arguments must be documented only once, meaning they must be documented _either_ in the class docstring _or_ in the `__init__` docstring, but not in both.
    - In case of conflict between documenting constructor arguments in the class docstring vs in the `__init__` docstring, prefer documenting constructor arguments in the `__init__` docstring, and do not duplicate them in the class docstring.

### Testing

- Use `pytest`.
- The canonical local test command is `uv run pytest -q`.
- Tests are required for new functionality and bug fixes.
- Tests must be deterministic and independent.
- Test files live in `tests/`.
- Test module basenames must be unique across the entire `tests/` tree, not just within their own subfolder.
  `tests/<subpackage>/` folders have no `__init__.py`, so two files sharing a basename (e.g. `tests/a/test_registry.py`
  and `tests/b/test_registry.py`) cause a mypy "Duplicate module named" error and a pytest "import file mismatch"
  error. Prefer a more specific name (e.g. `test_equation_registry.py`) over disambiguating by folder alone.
- `tests/conftest.py` contains shared fixtures and test configuration.
  Do not modify the existing fixtures therein without approval.
  You can, however, add new fixtures therein if you have a good reason.
- `tests/test_working_directory` is a folder that acts as the working directory for tests.
  The existing fixtures in `tests/conftest.py` ensure that:
  - The working directory (CWD) is changed to `tests/test_working_directory` for the duration of the entire test session
  - The directory `tests/test_working_directory` is properly set up for each test, i.e. test artefacts created by tests get removed before the next test.
  You can add files and folders in `tests/test_working_directory` as needed for testing, but do not modify or delete existing files without approval.

### Tooling

- Package management: `uv`
- Environment: `uv sync -U` (creates `.venv/` at workspace root)
- Optional extras: some modules and tasks (e.g. building documentation) depend on
  optional dependency groups declared in `pyproject.toml`'s
  `[project.optional-dependencies]`. Install all of them with
  `uv sync -U --all-extras` when building the documentation, or when working on
  code that requires optional extras. Some optional dependencies are further
  gated to specific Python versions; related import warnings on unsupported
  Python versions are expected, not bugs.
- Build docs locally: `uv run docs/make.bat html` (requires `--all-extras` above -
  without it, Sphinx's autosummary can hard-crash instead of just warning).
- Formatting: `uv run ruff format` (config: `ruff.toml`)
- Linting: `uv run ruff check` (config: `ruff.toml`)
- Type checking:
  - `uv run pyright` (config: `pyproject.toml [tool.pyright]`)
  - `uv run mypy` (config: `pyproject.toml [tool.mypy]`)
- Pre-commit hooks: `ruff-format`, `ruff-check` (config: `.pre-commit-config.yaml`)

---

## Version Management

- The **single source of truth** for the project version is
  `./pyproject.toml` (`[project].version`).
- Python code reads it at runtime via
  `importlib.metadata.version("<distribution-name>")` from the package
  `__init__.py` under `src/<package>/`.
- Do NOT hardcode version strings anywhere.
  All consumers must derive the version from `pyproject.toml`.

---

## Changelog

- The **full dev changelog** is `./CHANGELOG.md` at the repository root.
  All changes are recorded here.
- Summarize main changes in `./CHANGELOG.md` after implementing a task.
  For normal PRs, add them to the "Unreleased" section.
  If the "Unreleased" section does not exist, create it.
  If there are already entries in the "Unreleased" section, append new entries below the existing ones.
  Only create or update a versioned release section when the task explicitly involves preparing a release.
- Use only Keep a Changelog's standard category headings (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`) within a release section.
  Do not invent new ones (e.g. a "Quality"/"Internal" section) - fold process notes (e.g. "ran a full quality pass, no defects found") into the most fitting standard category, or omit them if nothing user-facing changed.

---

## Quality Gates

All of the following must pass before committing code changes.
Do not treat any gate as optional.

### Python
```
uv run ruff format --check
uv run ruff check
uv run pre-commit run --all-files
uv run pyright
uv run mypy
uv run pytest -q
```

### Config Files (source of truth for style rules)

| Config | Scope | Purpose |
|--------|-------|--------|
| `ruff.toml` | Python | Linting and formatting rules |
| `pyproject.toml` | Python | pyright, mypy |
| `pytest.ini` | Python | pytest settings |
| `.pre-commit-config.yaml` | Python | Pre-commit hooks |
| `.editorconfig` | All | Indent style, charset, line endings |

---

## GitHub Workflows (.github/workflows/)

- Workflows follow a **trigger + reusable sub-workflow** pattern:
  - `_`-prefixed files are reusable sub-workflows (triggered by `workflow_call`).
  - Non-prefixed files are trigger workflows that call the sub-workflows.
- Key conventions:
  - All Python steps use `astral-sh/setup-uv` + `uv sync` + `uv run`.
  - Never use bare `pip install` or `python` — always route through `uv`.
  - Secrets are passed explicitly via `secrets:` (not `secrets: inherit`).
  - Use `actions/checkout` consistently.

---

## Output Expectations

- Show diffs or clearly indicate modified files.
- Explain non-obvious design decisions.
- Call out any remaining risks, limitations, or TODOs.
