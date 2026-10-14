---
name: port-external-code
description: >-
  Port and adapt code from a separate, read-only reference repository (a
  prototype, a legacy codebase, an external project) into this repository,
  including decomposing a monolithic source package into cleanly separated
  target packages. Use when: importing/adapting code from a sibling or
  external repo, splitting a source package's domain logic from its
  framework/app layer during import, reconciling dependencies pulled in from
  that source. Do not use for: writing brand-new code with no external
  source, or moving/renaming files that already live in this repository.
---

# Port External Code

Reusable procedure for bringing code from an external, read-only reference
repository into this one - verbatim, adapted, or decomposed into different
target packages - without silently losing content, introducing broken
imports, or carrying over data/licensing that shouldn't be copied.

## When to Use

- Adopting a prototype or legacy codebase (in whole or in part) into this
  repository's `src/` layout.
- Decomposing a source repo's monolithic package into two or more
  cleanly separated target packages (e.g. domain library vs. web app layer).
- Reconciling a source repo's dependencies into this repo's `pyproject.toml`.

## Input

- The **source repository path** (typically a sibling directory, e.g.
  `../some-prototype`), granted read-only access.
- The **target package(s)** in this repo's `src/` the ported code should
  land in.

## Procedure

### Phase 1: Inventory and licensing check (before writing any code)

1. **Confirm the source repository actually contains source, not just build
   output.** A reference repo's working tree can be pruned down to only a
   compiled/built artifact (e.g. a `dist/` bundle) with no source files left
   at all - don't assume a folder that "should" contain source does; list it
   directly and look for recognizable source file extensions before
   inventorying. If only build output exists, treat the task as "recreate
   behavior from a contract/reference" rather than "port code", and say so
   explicitly rather than silently degrading the port.
2. List every source file to be ported, with its target module path and a
   first-pass category (e.g. "domain", "app layer", "ambiguous").
3. **Check the source repository's license** (its `pyproject.toml`/`LICENSE`)
   against this repository's own license. If they differ or the source is
   proprietary, treat this as a blocking question and get explicit,
   documented confirmation before porting anything - this is a legal
   decision, not an engineering one.
4. Flag any files that look like they might contain **sensitive or
   proprietary data**: license keys, credentials, real customer/project data
   examples, anything the source repo itself gitignores. Do not port these
   verbatim; if the underlying mechanism is still needed, port the
   *mechanism* (e.g. an optional-import guard) without the *secret/data*
   itself, and gitignore the equivalent local file in this repo too.
5. For files whose target package is ambiguous (mixes concerns), resolve it
   by inspecting actual coupling - e.g. grep the candidate files for
   framework-specific imports (a web framework, an ORM, etc.) to confirm
   whether they belong with the "pure" side or the "framework" side of the
   split - rather than guessing from file location alone.

### Phase 2: Read source files fully before porting

1. Do not trust a line-count tool's output (`wc -l`, `Measure-Object -Line`,
   or a pre-existing inventory table) as the true file length. Read each
   source file with a generously large line range and confirm you have
   reached the actual end of the file (trailing blank line, closing
   statement) before treating the read as complete.
2. Cross-check completeness by grepping the file's own consumers/tests for
   symbols they import from it - a symbol referenced elsewhere but "missing"
   from your read is a sign the read was truncated, not that the symbol
   doesn't exist.

### Phase 3: Port module-by-module, adapting imports and conventions

1. Port one module (or a small, related batch) at a time, in dependency
   order (leaf modules first).
2. Rewrite imports to match this repository's conventions:
   - Use plain **absolute imports** rooted at the target package (e.g.
     `from bn_core.utils.logging import Foo`), not relative imports
     (`from .logging import Foo`), even if the source repo used relative
     imports. See `AGENTS.md`'s Coding Standards for why relative imports
     are actively unsafe to introduce in this repo (an editor auto-fix can
     silently rewrite them incorrectly).
   - Re-point any import that crossed the old package's internal boundary
     to the new target package path.
3. Bring each ported module up to this repository's own quality bar
   (docstrings, type annotations, style) as part of the port itself, not as
   a follow-up cleanup pass.
4. After each batch: run `uv run ruff format` and `uv run ruff check` on
   just the changed paths, and fix findings immediately, before moving to
   the next batch. Small, frequent validation makes it much easier to
   attribute a new failure to the change that caused it.

### Phase 4: Port tests alongside their source module

1. Port each module's corresponding test file(s) in the same batch as the
   module itself - don't defer all test porting to the end.
2. Rewrite test imports the same way as production imports (Phase 3).
3. **Check for test module basename collisions** before/after moving files:
   if this repo's `tests/<subpackage>/` folders have no `__init__.py`, two
   test files sharing a basename in different subfolders will break both
   mypy ("Duplicate module named") and pytest ("import file mismatch").
   Rename to a more specific basename if needed (matching the source repo's
   own naming when it already disambiguates, e.g. `test_equation_grammar.py`
   rather than a generic `test_grammar.py`).
4. If the source repo's fixture data depends on files/paths that don't (and
   shouldn't) exist in this repo, adapt the test to either use synthetic
   fixture data or an explicit `skipif`-guarded path, rather than porting
   real external data files.

### Phase 5: Reconcile dependencies

1. Add the source repo's runtime dependencies needed by the ported code to
   this repo's `pyproject.toml`, reconciling version constraints against
   what's already declared (don't just copy the source repo's pins verbatim
   - check whether a current release of each dependency is compatible with
   this repo's existing constraints).
2. If a dependency isn't resolvable through the package indexes this repo's
   lockfile can reach (e.g. it's only published on a private/vendor index),
   do **not** declare it as a normal `[project.optional-dependencies]` entry
   - `uv lock`'s universal resolution will fail for the whole project. Only
   document the manual install command (e.g. as a comment in
   `pyproject.toml`), and gate the code that uses it behind a runtime
   optional-import check.
3. Drop dependencies that turn out to be unused template/placeholder
   leftovers only if confirmed unused by grepping the *entire* repo
   (`src/` **and** `tests/`), not just the code being ported.

### Phase 6: Final integration validation

1. Run the full quality-gate suite (`ruff format --check`, `ruff check`,
   `pre-commit run --all-files`, `pyright`, `mypy`, `pytest -q`) across the
   whole repository, not just the newly-ported paths.
2. If the port was meant to enforce a one-directional dependency between
   two target packages (e.g. an app layer depending on a domain layer but
   not vice versa), verify it statically: grep the "lower" package for any
   reference to the "higher" one, and for any import of the "higher"
   package's own framework dependencies.
3. Update `CHANGELOG.md` under "Unreleased" describing what was ported and
   from where.

## Known Pitfalls

- **Silent import mangling**: in this repo, an editor auto-fix-on-save can
  rewrite a relative import into an incorrect absolute one. Writing absolute
  imports from the start (Phase 3) avoids this entirely; if you see a
  `ModuleNotFoundError` naming a path that includes a top-level `src`
  segment, this is almost certainly the cause.
- **Undercounted file lengths**: see Phase 2. A truncated read produces a
  plausible-looking but incomplete port that only surfaces as a failure much
  later (e.g. a missing class field breaking an unrelated consumer).
- **Proprietary/sensitive data carried over by accident**: see Phase 1. A
  bundled third-party SDK folder, a hardcoded license key, or a real
  customer data file in the source repo's own examples are not code and
  should not be ported as if they were.
- **A "reference repo" that turns out to hold no source at all**: see Phase
  1. A sibling repo's working tree can be pruned down to just a build
  artifact (e.g. `dist/`) with the actual source deleted or never checked
  out on this machine - confirmed once already in this repo (a frontend
  "reference" repo had only a compiled JS/CSS bundle, no `.svelte`/`.tsx`
  source anywhere). Treat that as "no source to port" and say so, rather
  than reverse-engineering a minified bundle or silently treating a partial
  match as complete.
- **Terminal/tool flakiness during long validation sessions**: if a shell
  command fails with a generic "not recognized" error for a tool that is
  normally available, retry once or twice before treating it as a real
  environment blocker.

## Related

- `AGENTS.md`'s Coding Standards (absolute imports) and Testing (unique test basenames) sections codify two of the pitfalls above as standing rules.
