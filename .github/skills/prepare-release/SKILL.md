---
name: prepare-release
description: "Prepare a release of the package. Use when: releasing a new version, promoting changelog entries, and running pre-release quality gates. Delegates version bumping to the bump-version skill. Do not use for: bumping the version number in isolation without preparing a full release (see the bump-version skill)."
argument-hint: "[version]"
---

# Prepare Release

Release preparation workflow for the package.

## When to Use

- Preparing a new release for review
- Promoting unreleased changelog entries to a versioned section
- Running pre-release quality gates

## Input

The **target version** -- a valid PEP 440 version string (e.g. `0.0.9`).

## Procedure

Follow these 6 phases in order. Each phase depends on artifacts produced by
earlier phases.

### Phase 1: Environment Sync

1. Update and lock all Python dependencies:
   ```powershell
   uv sync -U
   ```
2. Verify the environment is healthy:
   ```powershell
   uv run python -c "import importlib.metadata as metadata, pathlib, tomllib; project = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['name']; print(metadata.version(project))"
   ```

### Phase 2: Version Bump

Delegate to the **`bump-version`** skill.

1. Load `.github/skills/bump-version/SKILL.md` and follow its full procedure
   with the target version as input.
2. When the `bump-version` procedure completes, all version-bearing files
   should reflect the new version. Confirm by checking the output of its
   Phase 4 validation step.

### Phase 3: Changelog Promotion

1. Open `./CHANGELOG.md` (the full dev changelog at the repository root).
2. Before promoting, sanity-check that `[Unreleased]` actually reflects what
   was merged: skim `git log <last-release-tag-or-commit>..HEAD --oneline`
   (or the equivalent commit range since the previous version) for
   user-facing commits with no matching changelog bullet. Add missing entries
   to `[Unreleased]` first -- a commit not touching `CHANGELOG.md` is not
   proof it had no user-facing effect. Skip this check only if `[Unreleased]`
   is expected to be empty (see step 6 below).
3. Locate the `## [Unreleased]` section.
4. Copy the full content under `## [Unreleased]` (all sub-headers and bullets)
   into a **new versioned section** inserted immediately after `[Unreleased]`:
   ```
   ## [<version>] - <today's date in YYYY-MM-DD format>
   ```
5. If the unreleased content contains **duplicate sub-headers** (e.g. two
   `### Added` sections), merge their bullets into a single sub-header
   during promotion.
6. Clear the content under `## [Unreleased]`, but **keep the
   `## [Unreleased]` header line itself**. The section should be empty and
   ready for post-release changes. Sub-headers (`### Added`, `### Changed`,
   etc.) may be removed -- they will be re-added as needed.
7. **Pre-release promotion** (e.g. `0.1.0a2` → `0.1.0`): If `[Unreleased]`
   is empty, the new versioned section will also be empty. This is expected
   -- the pre-release sections already document the changes. Still insert
   the version header so the changelog records the stable release date.

### Phase 4: Code Quality Pass

Delegate to the **`code-quality`** agent for one maintenance pass.

Ask the agent to:

- Format and lint Python code (`ruff format`, `ruff check`)
- Run type checkers (`pyright`, `mypy`)
- Run the full test suite (`pytest`)

All 6 validation gates must pass for the code quality phase:

1. `uv run ruff format --check`
2. `uv run ruff check`
3. `uv run pre-commit run --all-files`
4. `uv run pyright`
5. `uv run mypy`
6. `uv run pytest -q`

### Phase 5: Final Validation and Commit

1. Verify you are on the intended release branch. This skill does not
   assume `main` -- if the current branch is not obviously a release
   branch (e.g. it is an unmerged feature branch), say so explicitly in
   the Phase 6 handoff summary rather than silently committing, so the
   human can confirm the release-prep commit belongs there before it gets
   merged/pushed.
2. Run the full 6-gate validation checklist one final time (same as Phase 4).
   If Phase 4 made **no code changes**, this re-run may be skipped because the
   gates are already confirmed green.
3. Grep for any stale references to the **old** version. Prefer `git ls-files`
   over `Get-ChildItem -Recurse` here: the latter still walks into
   `.venv`/`node_modules` even with `-Exclude` (filename-only filtering), which
   can stall/desync the terminal for later commands in the same session.
   ```powershell
   $files = git ls-files "*.py" "*.toml" "*.md" "*.json" "*.svelte" | Where-Object { $_ -notmatch '\.lock$' }
   Select-String -Path $files -Pattern "<old_version>"
   ```
   Only `./CHANGELOG.md` historical entries and `plans/` documents are acceptable.
4. Produce a summary of all files changed and the release version.
5. Stage and commit all changes:
   ```powershell
   git add -A
   git commit -m "release: prepare v<version>"
   ```
6. Do **NOT** push. Do **NOT** create tags. Those are handled by CI/CD or human review.

### Phase 6: Review and Handoff

1. Confirm that only the intended repository-local changes remain.
2. Confirm the changelog and version bump match the release scope.
3. If Phase 5 step 1 flagged a non-release branch, restate that explicitly
   here rather than letting it pass silently.
4. Hand the release candidate back to the reviewer or release pipeline with a concise summary.

## Important

- This skill does NOT push or publish. It only prepares local state.
- If any validation gate fails, fix the issue before proceeding to the next
  phase. Do not skip gates.
- The `[Unreleased]` section in the changelog must never be deleted. It is
  the landing zone for post-release changes.
