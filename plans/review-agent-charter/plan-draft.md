# Plan: Review agent charter

## Problem Statement

This repository's "agent charter" - the collection of instruction files,
skill files, agent persona files, and plan templates that agents read
and act on - has grown organically over multiple sessions. It has not yet been
reviewed as a whole, from an outside, unbiased perspective.

This plan asks for a **read-only review** of the current agent charter: an
objective, balanced assessment of its structure and content against
established, canonical patterns for agentic repositories, plus a check for
internal consistency, redundancy, and staleness.

This is **not** an implementation plan. The deliverable is a written review
report with findings and recommendations, not code or documentation changes.
Any follow-up changes suggested by the review should be captured as separate,
new draft plans (or skill promotions/demotions), not applied directly as part
of this plan.

This plan is intended to be run **repeatedly**, as a periodic health check on
the charter, not just once. Each run produces a dated report; when a later
session works through that report's findings, a second, dated "after" report
can be generated to close the loop (see "Reporting convention" below).

**Relationship to `plans/improve-agent-instructions-and-plans/`**: that plan
also targets the instruction files, skills, and draft plans, but audits and
implements changes directly in a single pass. This plan is the periodic,
read-only health check; `improve-agent-instructions-and-plans` (or a
purpose-specific follow-up plan) is the vehicle used to actually apply this
plan's recommendations, once a recommendation is significant enough to
warrant its own implementation pass rather than a direct small fix.

## Baseline

Before reviewing content, establish the scope of "the agent charter" by
enumerating every folder, folder structure, and Markdown (or otherwise
agent-consumed) file that an agent reads, either automatically or because
another charter file explicitly instructs it to. At minimum, this includes:

- Root-level instruction file: [AGENTS.md](../../AGENTS.md)
- GitHub-scoped files: [.github/copilot-instructions.md](../../.github/copilot-instructions.md)
- `.github/instructions/*.instructions.md` (scoped rules with `applyTo`) -
  confirm the folder's actual contents match what `copilot-instructions.md`
  claims (existing vs. referenced-but-absent is itself a finding either
  way), and that each file's `applyTo` glob targets a real, current path -
  or, if it intentionally targets a path that does not exist yet (e.g.
  anticipating a pending rename), that this is explicitly documented in
  the file itself, not left to be mistaken for an error.
- `.github/agents/*.agent.md` (named agent personas)
- `.github/skills/**/SKILL.md` (reusable procedures, including workflow skills)
- `plans/README.md`, `plans/.plan.md` (template), and every
  `plans/<task>/plan-draft.md`
- Any other root-level files an agent is told to consult (e.g.
  [STYLEGUIDE.md](../../STYLEGUIDE.md), [CHANGELOG.md](../../CHANGELOG.md))
- Any repository-, user-, or session-scoped memory files the agent tooling
  itself maintains, if applicable to the tool in use.
- Editor or tool configuration files that affect whether/how charter files
  are discovered or activated (e.g. VS Code `settings.json` entries related
  to custom instructions), even though these are not Markdown themselves.
  The charter's *content* is Markdown, but its *activation* can depend on
  non-Markdown config, which is therefore in scope too.

For skill, agent, and plan folders, enumerate the **whole folder**, not just
the canonical entry file (e.g. `SKILL.md`, `plan-draft.md`) - supporting
files or subfolders (such as a `references/` folder) may exist for some
entries and not others, and that inconsistency is itself worth catching.

Record this enumeration explicitly (e.g. as a file tree with a one-line
purpose per file) as the first artifact of the review. This becomes the
baseline scope against which all review questions below are answered - do not
silently narrow the scope to "the files I already know about".

## Context

- Relevant files: the full charter enumeration produced in Baseline.
- Related tests: none (documentation/configuration review only).
- Constraints:
  - Read-only: do not modify charter files as part of this plan.
  - The review must be balanced - call out what works well, not only
    problems.
  - Every finding must cite the specific file(s) (and, where useful, the
    specific section or line) it is based on. Avoid vague, unsupported
    claims.
  - Do not assume a single "correct" canonical pattern exists; where
    multiple established patterns are valid, say so and explain the
    trade-off instead of picking one dogmatically.

## Assumptions

- "Industry established, canonical patterns" refers to publicly documented
  conventions for steering coding agents (e.g. the emerging `AGENTS.md`
  convention, tool-specific conventions such as GitHub Copilot's
  `copilot-instructions.md` and `*.instructions.md`/`applyTo` scoping,
  Claude's `CLAUDE.md`, and general documentation best practices such as
  single-sourcing and progressive disclosure), not one specific vendor's
  opinion.
- The reviewer has no prior stake in the current charter's design and should
  actively try to disconfirm its own first impression before finalizing a
  finding (avoid confirmation bias).

## Proposed Approach

1. **Establish scope** - Produce the charter file enumeration described in
   Baseline.
2. **Read everything** - Read every file in scope in full before forming
   conclusions. Note purpose, intended audience (human vs. agent), and
   activation mechanism (auto-loaded vs. explicitly attached vs.
   conditionally applied) for each file.
3. **Answer the review questions** (see below), grounding every answer in
   specific files/sections.
4. **Cross-check plan-draft.md files for repeated content** - Diff the
   structure and recurring passages across all `plans/*/plan-draft.md`
   files to identify candidates for skill extraction. Exclude this review
   plan itself (and any other meta/review-of-the-charter plan) from this
   comparison, since it is not a subject of the analysis it performs.
5. **Synthesize findings** into a structured report, separating:
   - Strengths (what should be preserved).
   - Issues (with severity: low/medium/high, and file references).
   - Open questions where reasonable people could disagree.
   - Concrete, actionable recommendations (each phrased so it could become
     its own draft plan).
6. **Write the report** following the Reporting Convention below (persisted,
   not the disposable `plan.md`).
7. **Do not implement** any recommendation as part of this plan. Instead,
   list which recommendations warrant a new `plans/<task>/plan-draft.md`,
   which warrant a skill promotion/demotion per the Plan vs Skill Rule, and
   which are informational only.

## Reporting Convention

Each time this plan is run, it produces a dated pair of reports (the second
only once remediation work has actually happened):

- **Original report** - `plans/review-agent-charter/review-report-<YYYY-MM-DD>.md`,
  dated with the day the review was performed. This is the initial,
  read-only assessment: strengths, issues (with severity and file
  references), open questions, and recommendations, exactly as described
  above. Never overwrite a prior dated report; each run of this plan gets
  its own file.
- **After report** - `plans/review-agent-charter/review-report-<YYYY-MM-DD>-after.md`,
  reusing the *original* report's date (not the date the after-report is
  written), generated on request once some or all of the original
  report's issues have been worked. It re-answers only what changed since
  the original report: each issue's new status (resolved / still open),
  the evidence for that status (files changed, or an explicit reason it
  is deliberately deferred), and any newly discovered issue that surfaced
  while remediating. It does not repeat findings that are unaffected -
  those still stand as written in the original report. Any items still
  open at the end of the after-report become the natural starting point
  for the next full review cycle.
- Do not generate an after-report until the user explicitly requests one;
  producing it is a separate, later step from the original review, since
  it depends on follow-up work this plan itself does not perform.

## Review Questions

Group findings under these questions. Answer each explicitly in the report,
even if the answer is "no issue found".

### Structure and conventions

- Does the folder structure and do the individual files follow industry
  established, canonical patterns for agent-consumed repository
  documentation (e.g. `AGENTS.md`-style conventions, GitHub Copilot's
  documented instruction/prompt/skill/agent file conventions)?
- Is the split between "portable, tool-agnostic root files" and
  "GitHub-specific `.github/` files" itself a recognized, sensible pattern,
  or does it introduce unnecessary indirection compared to a single
  canonical entry point?
- Are file and folder names, locations, and extensions consistent with what
  the tooling that consumes them actually expects (e.g. does
  `.github/instructions/` contain what `copilot-instructions.md` claims it
  does; do skill/agent files use the frontmatter/format their tooling
  expects)?

### Content quality

- Does the content of the charter follow best practices and canonical
  patterns for writing instructions consumed by an agent (clarity,
  imperative/actionable phrasing, appropriate specificity, avoiding
  contradictions)?
- Is each file appropriately scoped - neither so broad it duplicates other
  files, nor so narrow it fragments closely related guidance across many
  files a reader must hop between?
- Is guidance testable/verifiable (e.g. quality gates, commands) versus
  purely aspirational language that cannot be checked?

### Internal consistency

- Do any parts of the charter contradict each other (e.g. precedence rules
  stated differently in more than one place, conflicting tooling commands,
  conflicting scope statements)?
- Are there ambiguities that could be resolved by rewording, merging, or
  more precise cross-referencing?
- Where the same rule (e.g. precedence order, quality gates) is stated in
  multiple files, is there a single source of truth with the others
  referencing it, or is it duplicated text that can drift out of sync?

### Relevance and currency

- Are there files that are de facto obsolete because no agent or tool
  nominally reads them by default, and they are only consumed because some
  other part of the charter explicitly tells the agent to read them - and if
  so, is that indirection actually desired, or is it a workaround/mistake?
- Do referenced files, paths, or commands still exist and match the current
  repository state (e.g. tooling commands in `/AGENTS.md` versus
  actual `pyproject.toml`/`ruff.toml` configuration)?
- Are there stale references to folders or conventions that were renamed or
  removed (e.g. references to a former directory name that no longer matches
  the current path)?

### Reuse and the plan-vs-skill boundary

- Is there content repeated across multiple `plan-draft.md` files that
  should be extracted into a shared skill under `.github/skills/`, per the
  Plan vs Skill Rule already documented in [AGENTS.md](../../AGENTS.md)
  and [plans/README.md](../README.md)?
- Conversely, are any existing skills actually tied to one specific,
  non-repeatable task and should be demoted back into a plan?
- Do existing skills and plans follow a consistent internal structure (does
  every skill have a `SKILL.md` with a comparable shape to `plans/.plan.md`)?

### Discoverability and activation

- Will a new agent session reliably discover all relevant charter files
  without a human needing to manually attach them (distinguish
  auto-loaded files like `copilot-instructions.md` from files that require
  explicit attachment, like `plan-draft.md`/`plan.md`)?
- Are `applyTo` scoping patterns correctly targeted, and is it clear which
  files apply always vs. conditionally? For any that are currently inert
  (matching no files yet), is that status explicitly documented as
  intentional rather than left ambiguous?
- Is the activation story documented (e.g. plans/README.md's "Attaching
  Files" section) accurate and complete relative to how the charter is
  actually used?

### Governance and maintainability

- Is it clear who owns/maintains charter files and what the review/update
  process is, given the charter states these files are "reviewed and
  maintained like production code"?
- Is there any mechanism (automated or procedural) to catch charter drift
  over time (e.g. this plan itself, run periodically, plus the existing
  [reflect-and-improve](../../.github/skills/reflect-and-improve/SKILL.md) skill and `improve-agent-instructions-and-plans`
  plan), and is it sufficient?
- Is the charter's own size/complexity proportionate to the size of the
  codebase it governs, or is it over-engineered relative to actual team
  size and repository scope?

## Alternatives Considered

- Option A: Review only the root-level file (`AGENTS.md`) and treat
  `.github/` content as out of scope. Rejected - `.github/copilot-instructions.md`
  explicitly says GitHub-scoped files are part of the same knowledge
  contract, so a partial review would miss consistency issues between the
  two layers.
- Option B: Have the review also propose and apply fixes immediately.
  Rejected for this plan - reviews are more useful when findings and
  remediation are decoupled, so recommendations can be prioritized and
  turned into separate, appropriately-scoped draft plans.

## Validation Strategy

- Every finding in the report references at least one concrete file (and
  section, where applicable).
- The report explicitly answers every question listed above, plus any
  additional questions the reviewer identifies as relevant.
- The report is balanced: it names concrete strengths in addition to
  issues.
- No charter file is modified as part of this plan.

## Risks & Mitigations

- Risk: Reviewer bias toward the reviewer's own prior conventions,
  mistaking "unfamiliar" for "wrong".
  - Mitigation: Explicitly consider at least one alternative, equally
    valid pattern before flagging something as an issue; only flag as an
    issue when there is a concrete inconsistency, contradiction, staleness,
    or documented anti-pattern - not merely a stylistic preference.
- Risk: Scope creep into implementing fixes during the review.
  - Mitigation: This plan's Definition of Done explicitly excludes charter
    edits; recommendations are handed off to new draft plans instead.
- Risk: Incomplete scope (missing a charter file that an agent actually
  consumes).
  - Mitigation: Cross-check the Baseline enumeration against
    `.github/copilot-instructions.md` and `/AGENTS.md` themselves,
    since they describe what should be in scope.

## Definition of Done

- [ ] Charter file enumeration (Baseline) is complete and recorded in the
      report.
- [ ] All review questions above are answered with file-grounded evidence.
- [ ] Additional relevant questions identified by the reviewer are included
      and answered.
- [ ] Report written per the Reporting Convention
      (`review-report-<YYYY-MM-DD>.md`), covering strengths, issues (with
      severity), open questions, and concrete, actionable recommendations.
- [ ] Recommendations are mapped to next steps (new draft plan, skill
      promotion/demotion, or informational only) without being implemented.
- [ ] No charter file has been modified.
- [ ] If an after-report was requested, it is written per the Reporting
      Convention (`review-report-<YYYY-MM-DD>-after.md`, reusing the
      original report's date) and gives every original issue an explicit
      resolved/still-open status with evidence.
