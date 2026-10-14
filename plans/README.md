# Plans

This folder contains task-specific plans used with the agent workflow.

## Structure

```
plans/
  .plan.md                          # Template (do not modify)
  README.md                         # This file
  <task-name>/
    plan-draft.md                   # Problem statement & rough approach (human-authored)
    plan.md                         # Detailed plan (agent-generated from draft)
```

## Workflow

1. **Create a draft** - Create a new subfolder under `plans/` and write a `plan-draft.md` describing the problem and rough approach. By default, treat the new plan as one-off: add the local `.gitignore` described under Conventions to the subfolder right away, before or as you write `plan-draft.md`. Only remove it later if the plan turns out to be worth reusing.
2. **Generate a plan** - Attach one or more `plan-draft.md` files to the chat. Invoke the [generate-plan](../.github/skills/generate-plan/SKILL.md) skill to task the agent with expanding the drafts (`plan-draft.md` files) into respective detailed plans (`plan.md` files). The agent will process the draft plans in the order attached.
3. **Implement** - Attach one or more `plan.md` files to the chat. Invoke the [implement-plan](../.github/skills/implement-plan/SKILL.md) skill to execute the plans. The agent will execute the plans in the order attached.
4. **Reflect** - Invoke the [reflect-and-improve](../.github/skills/reflect-and-improve/SKILL.md) skill to feed learnings back into drafts and instructions.
5. **Commit** - Invoke the [prepare-commits](../.github/skills/prepare-commits/SKILL.md) skill to split changes into logical commits.

All workflow skills are located in `.github/skills/<skill-name>/SKILL.md`.
Invoke them explicitly as slash commands (for example, `/generate-plan`);
these four skills disable automatic model invocation.

## Attaching Files

Workflow skills reference files you "attach" as context. Files are **not** attached automatically from open editor tabs - you must add them explicitly. Ways to attach:

- **Paperclip / "+" button** in the chat input - select files from the picker.
- **Type `#file:`** in your prompt - autocomplete lets you pick a file.
- **Drag and drop** a file from the Explorer sidebar into the chat input.

When working on multiple tasks in a preferred sequence, attach the files in the order you want them processed.

## Conventions

- Each task gets its own subfolder.
- Draft plans are named `plan-draft.md`
  (human-maintained, iterated over time; included in version control only
  once a plan is deliberately kept reusable - see the default below).
- Generated plans are named `plan.md`
  (disposable, foreseen to be regenerated from the draft each time the `generate-plan` skill is used. Hence also git-ignored).
- The template `.plan.md` defines the expected structure for plans.
  (both for the _draft_ plans the user creates (-> `plan-draft.md` files) as well as for the plans the agent then generates from the drafts (-> `plan.md` files)).
- **Default: every new plan folder is one-off.** Most plans are drafted,
  expanded (`generate-plan`), and implemented (`implement-plan`) exactly
  once and never revisited - a plan foreseen or hindcast as reusable is the
  exception, not the rule. So, as soon as a new plan subfolder exists, add a
  local `.gitignore` to it containing:

  ```gitignore
  # One-time plan folder - kept local only, never committed.
  # This .gitignore file ensures all files in this plan folder are ignored by Git (default behavior).
  # If you decide to make the plan reusable, remove the .gitignore file.
  # The draft plan (`plan-draft.md`) will then get committed and sustained in the repository.
  *
  ```

  This keeps the entire folder (draft, generated plan, and the `.gitignore`
  itself) out of version control by default, without having to delete
  anything.
- If a plan turns out to be worth reusing across multiple tasks, remove its
  local `.gitignore` so `plan-draft.md` gets committed and sustained in the
  repository like any other tracked file.
- A plan folder may also intentionally contain only a `plan.md` with no
  `plan-draft.md` at all, for a one-time task where even a local-only draft
  isn't worth keeping around (e.g. a branch restructuring effort). Its
  `plan-draft.md` may have been deliberately deleted after generating
  `plan.md` - a stronger, final form of "one-off" than the local
  `.gitignore` above (which still keeps the draft around locally) - distinct
  from an orphaned or incomplete plan.

## Plan vs Skill Rule

Use this rule to keep the split stable over time:

- Keep a task in `plans/` when it is a repository-specific problem, maintenance item, or work item with local context and a clear outcome.
- Keep a workflow in `.github/skills/` when it is a reusable, repeatable procedure that can be invoked by name and does not depend on a specific local task context.
- If a draft plan becomes a stable, repeatable routine used across multiple tasks or projects, move it into a skill.
- If a skill becomes task-specific or tied to a single repository problem, consider moving it back into a draft plan instead.

This keeps the distinction simple: plans describe work; skills describe procedure.

## Code Quality Agent

The `code-quality` agent (defined in `.github/agents/code-quality.agent.md`) is
aware of the plans in this folder and can execute the full workflow autonomously.

### Invocation

In VS Code chat, switch to the `code-quality` agent and use natural language:

```
@code-quality run fix-ruff-check
@code-quality run add-missing-docstrings
@code-quality perform code quality maintenance
```

The last form lets the agent assess which plans are relevant by running the
quality tools first, then executing applicable plans automatically.

### What the Agent Does

When triggered, the agent follows the same 4-phase sequence you would do
manually with the workflow skills:

1. **Generate plan** — reads the `plan-draft.md`, expands it into a `plan.md`
2. **Implement plan** — executes the plan, validates with quality gates
3. **Reflect and improve** — feeds learnings back into drafts/instructions
4. **Prepare commits** — splits changes into logical conventional commits

No file attachments are needed — the agent knows where the plans live.
