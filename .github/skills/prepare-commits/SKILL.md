---
name: prepare-commits
description: >-
  Split the current uncommitted changes into logical, well-structured local
  commits with conventional commit messages. Use when: asked to prepare, organize, or split uncommitted
  changes into commits, or to stage and commit work in progress, or the working tree has
  uncommitted changes that need to be grouped into clean commits before
  review or a pull request.
  Do not use for: pushing commits, opening a pull request, generating a plan (see the generate-plan skill), or implementing
  new changes (see the implement-plan skill).
disable-model-invocation: true
---

# Prepare Commits

Review the current uncommitted changes in the working tree.

Treat unexpected formatter or auto-fix changes as a scope problem. Before
staging, compare the changed-file list and diff against the requested work;
never include repository-wide formatting churn in a focused commit.

Before committing, verify you are on the correct branch (not `main`).
If on `main`, ask the user for a branch name before proceeding.

If any files were changed since your last validation run in this session
(e.g. reformatted by the user, an editor, or another tool), re-run the
relevant quality gates (formatting/lint/tests) on those files before
committing - do not assume a prior pass still applies.

Prepare reasonably split commits:

- Group related changes into logical units.
- Each commit should be self-contained and pass tests independently where feasible.
- Write clear, conventional commit messages (imperative mood, concise subject line).
- Prefer smaller, focused commits over large monolithic ones.

Do NOT push. Only create local commits.
