---
name: implement-plan
description: >-
  Implement one or more plan.md files under plans/<task>/ step by step,
  running the plan's validation commands and reporting a definitive outcome
  for each. Use when: asked to implement or execute an already existing plan.md, carrying out the
  implementation phase of the plan-first workflow.
  Do not use for: drafting a new a plan-draft.md, generating a plan.md from a plan-draft.md / expanding a plan-draft.md into a plan.md (see
  the generate-plan skill), or preparing commits/reflecting on a session.
argument-hint: "[plan.md path(s)]"
disable-model-invocation: true
---

# Implement Plan

Implement one or more plans. Attach the `plan.md` file(s) as context before
invoking this skill.

Read the repository instructions:

- `/AGENTS.md`

One or more `plan.md` files are provided as context.
Implement each plan **in the order provided**, one at a time:

1. Read the `plan.md`.
2. Implement following the plan:
   - Work through the plan phases/steps incrementally.
   - Before running a formatter or auto-fix tool, confirm its working directory
     and scope.
   - After formatter/auto-fix commands, inspect `git diff --stat` and
     `git diff --check`; stop and investigate unexpected files before proceeding.
   - Run validation commands (tests, linting, formatting) as specified in the plan's validation strategy. If the target Ruff rule family is ignored or hidden by configuration, run a direct `--select` check for that family and compare its findings before and after each relevant phase.
   - Run each long-running validation command in an isolated terminal execution. Do not start another validation command in the same terminal until the previous command returns a definitive exit code and final summary.
   - Fix any issues that arise during implementation.
3. After completing each plan, briefly summarize what changed.
4. Move on to the next plan, if any.

After all plans are implemented, provide a final summary of all changes and any remaining risks or TODOs.

For every validation command, report exactly one outcome: `passed`, `failed`, `blocked`, or `incomplete`.

- `passed`: the command exits successfully or produces a definitive successful test/tool summary.
- `failed`: the command exits non-zero or produces a definitive failing test/tool summary.
- `blocked`: the command cannot start or run because an environment or tool prerequisite is unavailable.
- `incomplete`: the command started but no definitive result was obtained, such as a timeout, interruption, or missing final summary.

Do not mark `blocked` or `incomplete` checks as passed in the final summary or in plan checklists. List them separately with the evidence available and any remaining action.

If a terminal command fails immediately with a generic "command/executable not recognized" error for a tool that is normally available (e.g. `uv`), treat it as a transient shell hiccup, not a real `blocked` outcome: retry the exact same command once or twice before investigating further or reporting it as blocked.

If a validation command's terminal output comes back empty, truncated, or otherwise garbled even though the command should produce output (observed with Node/npm-based tools in some environments), do not treat that as `passed`, `failed`, or `blocked` on its own: redirect the command's output to a temporary file and read the file back (e.g. `<command> 2>&1 | Out-File -FilePath out.log; Get-Content out.log`) to get a reliable result, then delete the temporary file. A freshly-written log file can still read back as empty or partial on the first attempt even after the command has finished (a filesystem write-visibility lag, also observed with `uv run pytest`, not just Node tooling) - re-read it once or twice more before concluding the command produced no output.

If changes affect the package (code, tests, public docs, or API), update `./CHANGELOG.md` (at the repository root) - add entries to the "Unreleased" section.
