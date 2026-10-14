# Skills

This folder contains reusable, repeatable procedures invoked by name,
following the open [Agent Skills specification](https://agentskills.io/)
and [VS Code's Agent Skills conventions](https://code.visualstudio.com/docs/copilot/customization/agent-skills).

## Structure

```
skills/
  <skill-name>/
    SKILL.md          # Required: YAML frontmatter + instructions
    scripts/          # Optional: executable code
    references/       # Optional: detailed reference material, linked from SKILL.md
    assets/           # Optional: templates, resources
```

- `SKILL.md` is the only required file. `name` must exactly match the
  parent directory name - VS Code silently fails to load the skill
  otherwise.
- `scripts/`, `references/`, and `assets/` subfolders are optional and
  added only when a skill has supporting material substantial enough to
  offload from `SKILL.md`. It is normal and expected for skills to differ
  here:
  - `bump-version/` has `references/version-files.md` because that skill
    needs a maintained list of version-bearing files.
  - `prepare-release/` has no subfolder because its procedure fits
    entirely in `SKILL.md`.

  Both shapes are correct; the presence or absence of a subfolder is not
  itself an inconsistency to fix.
- Any additional file referenced from a skill's instructions must be
  linked via a relative Markdown link (e.g. `[...](./references/foo.md)`)
  for the agent to pick it up.

## Frontmatter

| Field | Required | Notes |
|---|---|---|
| `name` | Yes | Must match the parent directory name exactly. |
| `description` | Yes | Loaded at discovery time; be specific about both capability and "Use when:" / "Do not use for:" triggers. |
| `argument-hint` | No | Short, bracket-style placeholder text shown in the chat input field when the skill is invoked as a slash command (e.g. `[version]`). |

## Plan vs Skill Rule

See the Plan vs Skill Rule in [/AGENTS.md](../../AGENTS.md) and
[plans/README.md](../../plans/README.md) for guidance on when a new
procedure belongs here versus in `plans/`.
