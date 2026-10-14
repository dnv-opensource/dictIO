# Plan: Improve agent instructions and plans

## Problem Statement

This repository has agent instructions, skills, and draft plans that are iteratively
refined based on experience. After each working session, learnings should be fed back
into the instruction files and draft plans to improve future sessions.

The goal is to analyse the current setup and identify improvements to:
- `/AGENTS.md` - project-wide engineering rules and default working style
- `/.github/copilot-instructions.md` - GitHub-specific scoping
- `/.github/agents/code-quality.agent.md` - code quality agent persona
- `/.github/skills/**/SKILL.md` - reusable procedures, including workflow skills
- `/plans/*/plan-draft.md` - task-specific draft plans

**Relationship to `plans/review-agent-charter/`**: that plan is the periodic,
read-only health check over this same set of files (structure, internal
consistency, staleness, against canonical patterns), producing a dated report
of findings without applying any fix itself. This plan is the vehicle used to
actually implement changes - either from that report's recommendations, or
from other, independently noticed friction points - once a fix is
significant enough to warrant its own audit-and-implement pass rather than a
direct small fix.

**Relationship to [reflect-and-improve](../../.github/skills/reflect-and-improve/SKILL.md)**: that
skill is the cheap, explicitly invoked, session-scoped reflection step at the end
of every session, proposing minimal fixes tied to that session's own work.
This plan is the broader, systematic audit it escalates to when a session's
reflection surfaces issues wider than its own specific edits (e.g. several
unrelated stale references, or a need to verify every instruction file's
commands/paths across the board) - it is not meant to run after every
session, only when that escalation (or an explicit, standalone request)
warrants the fuller pass.

## Baseline

- Review each instruction file for outdated, incorrect, or incomplete guidance.
- Review each draft plan for commands, paths, or conventions that no longer match
  the current repository state.
- Review skill files for clarity, completeness, and correct file references.
- Note any friction points encountered in recent agent sessions.

## Proposed Approach

1. **Audit instruction files** - Read each file and note inconsistencies, outdated
   references, or missing guidance.
2. **Audit draft plans** - Verify all commands and paths are current. Check that
   validation strategies and definitions of done are complete.
3. **Audit skills** - Verify referenced file paths are correct. Ensure skills
   produce the desired agent behavior.
4. **Propose changes** - Present a summary of proposed improvements for approval.
5. **Implement** - Apply approved changes.

## Context

- Relevant files: all files listed in Problem Statement above
- Related tests: none (documentation/configuration only)
- Constraints:
  - Do not change the fundamental structure or conventions without explicit approval.
  - Changes must be backward-compatible with existing workflows.
  - Keep instructions concise - avoid duplication across files.

## Validation Strategy

- All referenced file paths in instructions and skills resolve correctly.
- All commands in draft plans and instructions are executable and produce expected results.
- The plan-first workflow (draft → generate → implement → commit → reflect) still functions.
- Pre-commit hooks pass on all modified files.

## Definition of Done

- [ ] All instruction files reviewed and updated where needed.
- [ ] All draft plans verified to use current commands and paths.
- [ ] All skills verified to reference correct files.
- [ ] No stale or contradictory guidance remains.
- [ ] Changes are validated and ready for review; committing remains a separate
   explicitly requested workflow.
