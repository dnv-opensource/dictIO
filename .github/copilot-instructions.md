# GitHub Copilot - Project Instructions

This repository uses a **hybrid instruction model**:

- **Portable, tool-agnostic rules live in the repository root**
- **GitHub-specific scoping and activation live under `.github/`**

GitHub Copilot and GitHub Agents must treat the files below as the
authoritative source of project behavior.

---

## Primary Instruction Sources (Authoritative)

Always load these files first — they define the baseline rules that all
other instructions must stay consistent with:

- `/AGENTS.md`
  Project-wide engineering rules, quality standards, default working style,
  and agent execution discipline (plan-first workflow, quality bar, output
  expectations).

- `/plans/<task>/plan.md` or `/plans/<task>/plan-draft.md` (when present)
  Explicit plan / orchestration artifacts for Plan Mode workflows.
  Each task has its own subfolder under `/plans/`.
  The presence of a `plan-draft.md` indicates a plan-first workflow is expected.
  `/plans/.plan.md` serves as a template and should not be modified directly.

These files form the **knowledge contract** for this repository and
are reviewed and maintained like production code.

---

## GitHub-Scoped Instructions (Additive)

Additional GitHub-specific guidance MAY apply from:

- `.github/instructions/*.instructions.md`
  Narrow, scoped rules using `applyTo` (must not contradict root rules).
  Two narrow examples exist today (`tests.instructions.md`,
  `examples.instructions.md`); add more when a real path-specific need
  arises.

- `.github/agents/*.agent.md`
  Named agent personas, if explicitly activated.

- `.github/skills/**/SKILL.md`
  Reusable, invoke-by-name procedures, including the `generate-plan`,
  `implement-plan`, `prepare-commits`, and `reflect-and-improve` workflows
  (see `.github/skills/README.md`).

Unlike `.github/instructions/` (opted into discovery via
`.vscode/settings.json`'s `chat.instructionsFilesLocations`), the
`agents/` and `skills/` folders above are discovered by
fixed, tool-level convention - no corresponding settings entry is
needed or expected for them.

GitHub-scoped files **refine or specialize** behavior.
They must never redefine or override the intent of `/AGENTS.md`.

---

## Precedence & Conflict Resolution

This mirrors GitHub Copilot's own documented precedence for repository-level
custom instructions (not merely a repository convention):

1. Path-specific `.github/instructions/**/*.instructions.md` (most specific - may only **narrow or refine** root rules for files matching their `applyTo` pattern, never override or contradict them)
2. Repository-wide `.github/copilot-instructions.md` (this file)
3. Agent instructions in `/AGENTS.md`

Skill and agent definitions (`.github/skills/`, `.github/agents/`) rank below all three
tiers above; see `/AGENTS.md`'s "Instruction Precedence and Scope" section
for how they relate to the repository instruction files as a whole.

When in doubt:

- Prefer correctness, testability, and clarity over speed
- Ask for clarification rather than guessing

---

## Safety & Boundaries

- Work only within this repository
- Do not assume network or internet access unless explicitly stated
- Do not introduce hidden side effects, hooks, or background behavior
- Do not change unrelated code opportunistically

All agent output is subject to human review and normal PR processes.

---

## Intentional Non-Goals

- This file does **not** contain detailed coding rules
  (those belong in `/AGENTS.md`)
- This file does **not** encode organization policy or governance logic
- This file avoids duplication by design

Less is intentional. Stability is a feature.
