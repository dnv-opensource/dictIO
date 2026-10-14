---
agent: agent
description: "Create detailed plan(s) from one or more draft plans. Attach the plan-draft.md file(s) as context."
---

Read the repository instructions:
- `/.github/copilot-instructions.md`
- `/AGENTS.md`

Then read the plan template at `/plans/.plan.md`.

One or more `plan-draft.md` files are provided as context.
Process each draft plan **in the order provided**, one at a time:

1. Read the `plan-draft.md`.
2. Create a detailed `plan.md` based on the draft and the repository instructions:
   - Follow the structure defined in the plan template (`/plans/.plan.md`).
   - Expand the draft plan's problem statement, approach, and validation strategy into a complete, actionable plan.
   - Treat baseline values in the draft as provisional. Rerun the relevant baseline commands against the current worktree before writing `plan.md`.
   - Include a baseline section that captures measurable starting state and records material differences between the draft baseline and the current worktree.
   - If the plan investigates a Ruff rule family hidden by `ruff.toml`, select that rule family directly in addition to running the normal Ruff check, and record both results.
   - Include a clear definition of done with checkboxes.
3. Save the plan as `plan.md` in the same folder as the `plan-draft.md`.
4. Move on to the next draft plan, if any.
