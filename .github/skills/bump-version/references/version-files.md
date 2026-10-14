# Version-Bearing Files

Authoritative registry of every file in the repository that embeds the
project version number. Organized by update mechanism.

Maintain this file whenever a new file starts embedding the version.

## Canonical Source (Single Source of Truth)

| File | Field / pattern | Notes |
|------|----------------|-------|
| `./pyproject.toml` | `version = "<version>"` | Edit this first; everything else derives from it |

## Auto-Updated by Tooling

These files are updated automatically by running the listed command.
Do NOT edit them by hand.

| File | Command | Notes |
|------|---------|-------|
| `uv.lock` | `uv sync` | Lock file; update when `pyproject.toml` version changes |

## Manual Propagation

These files contain hardcoded version strings that must be updated by an
agent or human. Search-and-replace the old version with the new version.

| File | Field / pattern | Notes |
|------|----------------|-------|
| `CITATION.cff` | `version: <version>` | Citation metadata must stay in sync with the package version |

## Not Version-Bearing (Auto-Derived at Runtime)

| File | Notes |
|------|-------|
| `src/<package>/__init__.py` | `__version__` reads from package metadata at runtime; no hardcoded string |
