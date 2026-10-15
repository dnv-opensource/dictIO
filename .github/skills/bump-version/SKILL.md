---
name: bump-version
description: >-
  Bump the project version number across all files that embed it.
  Use when: changing the version, bumping version, updating version strings,
  preparing a version change, post-release version bump, pre-release version.
  Do not use for: promoting changelog entries or running release quality
  gates (see the prepare-release skill).
argument-hint: "[version]"
---

# Bump Version

Propagate a new version number to every file that embeds it.

## When to Use

- Bumping to a new release version (e.g. `0.0.8` to `0.0.9`)
- Setting a pre-release version (e.g. `0.0.9a1`)
- Correcting a version mid-cycle

## Input

The **target version** -- a valid PEP 440 version string (e.g. `0.0.9`,
`0.1.0a1`).

## Procedure

Follow these 4 phases in order.

### Phase 1: Determine Old Version

1. Read `./pyproject.toml` and extract the current `version` value.
2. Store the old version string for use in the validation phase.

### Phase 2: Update Canonical Sources

1. Edit `./pyproject.toml`: change the `version` field to the target version.
2. Run `uv sync` so that `uv.lock` picks up the new version.

### Phase 3: Propagate to All Version-Bearing Files

Consult [./references/version-files.md](./references/version-files.md) for
the complete list of files and their update mechanisms.

#### 3a. Auto-updated files (run these commands in order)

```powershell
# None currently. Commands will be added as new auto-updated files are introduced.
```

#### 3b. Manual-propagation files

Search-and-replace the old version string with the new version in each of
these files. See `./references/version-files.md` (Manual Propagation section)
for the exact fields.

Files to edit:
- `CITATION.cff` -- update the `version` field to the target version.

### Phase 4: Verify

1. Run a grep for the **old** version across all relevant file types. Prefer
   `git ls-files` over `Get-ChildItem -Recurse` here: the latter still walks
   into `.venv`/`node_modules` even with `-Exclude` (which only filters
   filenames, not directories), which can stall/desync the terminal for
   later commands in the same session.
   ```powershell
   $files = git ls-files "*.py" "*.toml" "*.md" "*.json" "*.svelte" "*.cff" | Where-Object { $_ -notmatch '\.lock$' }
   Select-String -Path $files -Pattern "<old_version>"
   ```
2. Review matches. The only acceptable matches are:
   - `./CHANGELOG.md` -- historical release entries
   - `plans/` -- plan documents referencing past versions
   - `uv.lock` -- hash lines (not the `version =` line)
3. If unexpected matches remain, fix them and re-run the grep.
4. Report the full list of files changed.

## Important

- This skill does **NOT** commit. The caller (human or `prepare-release`
  skill) decides when and how to commit.
- This skill does **NOT** update `./CHANGELOG.md`.
  Changelog changes are handled by the `prepare-release` skill or manually.
