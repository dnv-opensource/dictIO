---
name: reflect-and-improve
description: >-
  Reflect on the current session and propose improvements to repository
  instruction files, reusable skills, and draft plans.
  Use when: ending a session and asked to reflect, capture learnings, or improve
  instructions/skills/plan-drafts based on what happened in the session.
  Do not use for: implementing a plan or preparing commits (see the
  implement-plan and prepare-commits skills), making the proposed edits automatically without
  discussion, or performing a broad, unrelated instruction-file audit (see
  the `improve-agent-instructions-and-plans` plan for that).
disable-model-invocation: true
---

# Reflect and Improve

Before we end this session, reflect on what happened:

1. Review the work done in this session.
2. Consider whether any learnings should be fed back into:
   - The repository instruction files (`/.github/copilot-instructions.md`, `/AGENTS.md`)
   - The reusable skills inside `/.github/skills/`
   - Any `plan-draft.md` files inside `/plans/**/`

The goal is NOT to copy detailed `plan.md` content back into draft plans.
The goal IS to use today's learnings to make future sessions start with slightly _better_ versions of the draft plans and instruction files.

Propose specific, minimal improvements. Explain the reasoning for each.

If the learnings point to something broader than this session's own specific
edits (e.g. multiple unrelated stale references, or a need to systematically
verify every instruction file's commands/paths), do not enumerate a full
ad hoc audit here. Instead, say so explicitly and recommend running the
`plans/improve-agent-instructions-and-plans/` plan (via the standard
`generate-plan` -> `implement-plan` pipeline) to perform that broader audit.
