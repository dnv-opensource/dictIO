# Plan Draft: Rename Demo Terminology to Example Terminology

## Problem Statement

The repository uses `demos` and related terms in directory names, file names,
and file contents. Rename the top-level `demos/` directory to `examples/`,
rename any other matching folders and files using the requested singular or
plural replacements, and update matching words inside workspace files.

This is a sequential rename and exact text-replacement task. Preserve the
meaning and identity of each item, preserve every file and folder, and do not
make unrelated content or behavior changes.

## Baseline

Initial read-only inspection of the current worktree found:

- The current branch is `maintenance-updates`; the worktree was clean.
- A top-level `demos/` directory exists. The tracked path inventory found
  `demos/folder_for_demos.py` as a file whose own name contains a target term.
- A case-sensitive content search found candidate matches in repository
  configuration, documentation, the changelog, a plan draft, and files below
  `demos/`. The raw search also finds words such as `demonstrates` that contain
  a similar letter sequence but are not one of the requested words.
- The full authoritative folder, file, and content inventories must be
  regenerated immediately before implementation. Do not use the copied
  `plan.md`'s project-specific file lists, exclusions, counts, or exceptions
  as the baseline for this repository.

## Context

- **Relevant scope:** The repository working tree, including tracked,
  untracked, hidden, and ignored workspace files, subject to the explicit
  planning-metadata exception below. Do not search or modify `.git` internals.
- **Related tests:** No new tests are expected for a path and text rename.
  Run the existing project test suite and relevant lint/format checks after
  updates to configuration or source paths.
- **Constraints:**
  - First create and switch to a new branch named
    `rename-demos-to-examples`.
  - Rename folders and files; do not delete any folder or file.
  - Apply only the requested exact, case-sensitive content substitutions.
  - Preserve file bytes, encoding, notebook structure, and unrelated content.
  - Review each name and text context so the new wording remains accurate
    and unambiguous. Do not change unrelated words such as `demonstrates`,
    which are not among the requested words.
  - Preserve the active plan directory
    `plans/rename-demos-to-examples/` and its planning files, including
    `plan.md` and this `plan-draft.md`. This exception was confirmed by the
    user because renaming or rewriting the task's own planning metadata would
    make its identity and instructions self-referential or ambiguous.

## Assumptions

- The repository working tree (not Git's internal metadata) is the intended
  workspace search boundary.
- Name matching is case-sensitive and follows the exact lowercase forms
  provided for names. Content matching is case-sensitive and uses the eight
  listed lower- and title-case forms.
- Treat a target as a word in text only when it is a whole-word match. For
  paths and filenames, identify the target term within each name, apply the
  specified replacement, and review the resulting name for collisions or
  changed meaning before moving it.
- The requested substitutions apply to all in-scope content, including
  historical text and configuration references. Do not carry over exemptions
  or special-case decisions from the copied plan.
- If a matching item cannot be renamed or edited without ambiguity, collision,
  data loss, or damage to a binary format, stop that item and resolve the
  handling before proceeding; do not silently skip it or delete it.

## Proposed Approach

Perform each phase in order. Re-run the affected inventory after each rename
phase because paths change as the work proceeds.

### 1. Establish the branch and confirm the starting state

1. Verify the current repository and branch, and inspect `git status`.
2. Confirm the target branch does not already exist. If it does, inspect it
   and stop for a decision rather than overwriting or resetting it.
3. Require a clean worktree before branching, or preserve and account for any
   existing user changes without including them in this task.
4. Create and switch to `rename-demos-to-examples` from the current branch
   using the repository's normal Git workflow.

### 2. Inventory matching folders

1. Enumerate all in-scope workspace folders, including hidden and ignored
   workspace content, without traversing `.git`.
2. Find names containing the exact target forms and record each original path,
   proposed destination, and reason the replacement preserves meaning.
3. Exclude only the active plan directory and its contents as specified in
   Context. Do not infer additional exceptions from the copied plan.
4. Check every proposed destination for collisions. Rename the top-level
   `demos/` directory to `examples/`, then process any other matching folders
   in a safe order (deepest paths first where necessary).
5. Use rename operations that preserve the folder contents. On Windows, ensure
   each destination parent exists before invoking `git mv` for tracked paths.
6. After each rename, verify that all contained files and nested folders are
   still present and that no content was lost.

### 3. Inventory and rename matching files

1. Re-enumerate in-scope files after the folder moves, including untracked,
   hidden, and ignored workspace files; keep the active plan artifacts out of
   scope.
2. For each matching filename, record its old and new path and check that the
   new name is unique and describes the same item.
3. Apply these literal, case-sensitive name substitutions, checking longer
   forms before shorter forms:
   - `demonstrations` -> `examples`
   - `demonstration` -> `example`
   - `demos` -> `examples`
   - `demo` -> `example`
4. Rename tracked paths with `git mv`. Rename any in-scope untracked paths
   without deleting or replacing their contents.
5. Verify each move by checking the destination exists and the original
   content is preserved.

### 4. Replace matching words inside files

1. Search all in-scope file contents, including hidden and ignored workspace
   files, excluding `.git` internals and the active plan artifacts. Include
   text in notebooks and configuration files; preserve their file structure.
2. Before editing, save the exact path-and-line inventory and occurrence
   counts. Distinguish whole-word matches from prefixes or substrings in
   unrelated words.
3. Apply the following literal, case-sensitive whole-word replacements,
   processing longer forms before shorter ones:
   - `demonstrations` -> `examples`
   - `Demonstrations` -> `Examples`
   - `demonstration` -> `example`
   - `Demonstration` -> `Example`
   - `demos` -> `examples`
   - `Demos` -> `Examples`
   - `demo` -> `example`
   - `Demo` -> `Example`
4. Review every changed line in context. Confirm the replacement still refers
   to the same concept, reads unambiguously, and does not modify a larger,
   unrelated word. If the prescribed replacement alone makes the meaning
   unclear, stop and resolve that case before proceeding; do not make
   unrequested wording changes.
5. For binary or structured files, use a format-aware update when a target
   occurs. Preserve encoding and structure; stop for a decision if a safe,
   meaning-preserving edit cannot be made.
6. Reconcile the before-and-after occurrence counts, accounting for the exact
   mappings and renamed paths.

### 5. Verify scope and behavior

1. Repeat the folder-name, filename, and content searches across the same
   in-scope workspace boundary. Confirm no requested term remains outside the
   active plan artifacts and `.git`.
2. Confirm the plan directory and both planning files remain at their original
   paths and retain their contents.
3. Inspect `git diff --name-status` and the worktree inventory. Changes must
   consist only of intended renames and in-place text modifications. Confirm
   there are no deleted files or folders and no unrelated changes.
4. Check moved files against their pre-rename content, and inspect notebook,
   configuration, and other structured-file diffs for valid structure.
5. Search path-dependent configuration, documentation, and test references
   for stale paths after the replacements.
6. Run the project's relevant formatting, linting, and test commands. Record
   their results and distinguish any pre-existing baseline findings from
   regressions.

## Alternatives Considered

- **Rename paths and replace text in a single pass:** Rejected because
  separating discovery, folder moves, file moves, and content replacements
  makes omissions and accidental deletions easier to detect.
- **Use unrestricted substring replacement:** Rejected because it can alter
  larger words that are not among the requested terms and can change meaning.
- **Reuse the copied `plan.md` inventories or exceptions:** Rejected because
  that plan describes another project and is only a structural example.
- **Rewrite the active plan directory and planning files:** Rejected following
  the user's confirmation to preserve task metadata and avoid self-referential
  plan paths and instructions.

## Validation Strategy

- Compare the pre-change and post-change path inventories. Every renamed
  destination must exist, and no source file or folder may be lost.
- Search folder names, file names, and in-file text separately for all
  requested forms. Only the confirmed planning-metadata exception and `.git`
  internals are excluded.
- Review the complete diff to verify exact substitutions, semantic
  consistency, valid structured files, and absence of unrelated edits.
- Run repository formatting and lint checks appropriate to changed files and
  `uv run pytest -q`; compare results to baselines measured on the branch
  before implementation.
- No validation step may treat a deleted item as an acceptable side effect of
  a rename.

## Risks & Mitigations

- **Destination collision:** A target folder or file name may already exist.
  - Check all destinations before moving anything; stop and resolve
    collisions without merging or overwriting content.
- **Substring replacement changes unrelated words:**
  - Use exact, case-sensitive whole-word matches for file contents and review
    each changed line.
- **Meaning or grammar changes after replacement:**
  - Inspect each replacement in context. If the specified replacement alone
    cannot preserve clear meaning, stop and resolve the case without making
    unrequested copy edits.
- **Ignored or untracked workspace content is missed:**
  - Inventory beyond tracked Git paths, including hidden and ignored workspace
    files; document any item that cannot be safely processed rather than
    silently omitting it.
- **Rename tools appear as delete/add operations:**
  - Use rename operations that preserve content and verify destination
    contents and the final Git name-status report; do not delete and recreate.
- **Self-referential changes to planning metadata:**
  - Keep the active plan directory and its planning files outside the rename
    and replacement scope, as confirmed by the user.

## Definition of Done

- [ ] A new branch named `rename-demos-to-examples` is created and checked out.
- [ ] The top-level `demos/` directory and every other in-scope matching
      folder are renamed using the specified mapping.
- [ ] Every in-scope matching file is renamed using the specified mapping.
- [ ] All in-scope whole-word content occurrences are replaced with the
      specified case-sensitive mappings.
- [ ] Each resulting name and changed text has been reviewed for preserved,
      unambiguous meaning.
- [ ] No file or folder has been deleted, lost, overwritten, or changed
      outside the requested renames and replacements.
- [ ] The active plan directory, `plan.md`, and `plan-draft.md` remain
      unchanged and at their original paths.
- [ ] Final searches find no target occurrences outside the stated exclusions.
- [ ] Relevant formatting, lint, and test checks pass, or any baseline
      findings are explicitly recorded without being misreported as passes.
