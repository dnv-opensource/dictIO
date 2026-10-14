# Path-Specific Instructions

Files in this folder provide narrow, scoped guidance that only
applies to files matching a given path glob, per GitHub Copilot's
[path-specific custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
convention.

## When to add a file here

Add a `NAME.instructions.md` file when a subset of the codebase has
conventions that genuinely differ from the repository-wide rules in
`/AGENTS.md`, and stating them unconditionally in `/AGENTS.md` would
either be wrong for the rest of the codebase or add detail irrelevant
to most requests. Prefer extending `/AGENTS.md` directly when the
guidance applies everywhere.

## Format

```markdown
---
applyTo: "glob/pattern/**"
---

Guidance that only applies to files matching the glob above.
```

`applyTo` supports comma-separated multiple globs. See
[`.github/copilot-instructions.md`](../copilot-instructions.md)'s
"Precedence & Conflict Resolution" section for how these files rank
relative to `/AGENTS.md` and `.github/copilot-instructions.md`.

## Existing files

- [`tests.instructions.md`](./tests.instructions.md) - exemptions
  from `/AGENTS.md`'s universal docstring/type-annotation rules that
  apply to `tests/**/*`, mirroring `ruff.toml`'s `"tests/**/*"`
  ignore block.
- [`examples.instructions.md`](./examples.instructions.md) -
  exemptions for tutorial/example code, mirroring `ruff.toml`'s
  `"examples/**/*"` ignore block.
