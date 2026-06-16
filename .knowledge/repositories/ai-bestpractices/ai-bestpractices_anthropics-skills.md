---
repo_type: ai-bestpractices
repo_name: anthropics-skills
repo_path: .knowledge/repositories/ai-bestpractices/anthropics-skills
url: https://github.com/anthropics/skills.git
branch: main
keywords:
  - official skills
  - skill-creator
  - mcp-builder
  - document skills
  - references layout
  - pair-agent evals
  - must-rule quality bars
---

# anthropics-skills

## Purpose

The canonical skills repository from Anthropic. It bundles the showcase library
(`skill-creator`, `mcp-builder`, `webapp-testing`, `doc-coauthoring`,
`frontend-design`, `claude-api`, `brand-guidelines`, …) next to the production
document skills (`pdf`, `docx`, `pptx`, `xlsx`) lifted out of Anthropic's
internal `/mnt/skills/`. The single richest reference for layout, frontmatter,
`references/`, `scripts/`, and quality bars that any agent skill — including
Axon Framework 4→5 migration skills as one example — should mirror.

## Feature highlights

- **Meta-skill for skill authoring** — `skills/skill-creator/SKILL.md` codifies
  the subagent pair-eval methodology and the "be pushy in descriptions" rule
  for fighting under-triggering.
- **Runnable eval viewer + scripts** — `skills/skill-creator/eval-viewer/` and
  `skills/skill-creator/scripts/` include a description-variant optimisation
  loop you can lift as a starter eval harness.
- **In-skill `agents/` + topic-named references** —
  `skills/skill-creator/agents/`, `skills/skill-creator/references/` set the
  template for shipping role-specific subagents and topic-named reference
  files alongside SKILL.md.
- **Conditional reference loading** — `skills/mcp-builder/SKILL.md` and
  `skills/mcp-builder/reference/` demonstrate a 10-question evaluation
  methodology and load-on-demand references.
- **State-machine workflows** — `skills/doc-coauthoring/SKILL.md` runs a
  three-stage state machine (Context Gathering → Refinement → Reader Testing)
  with hard quality gates ("after 3 iterations with no changes, ask what can
  be removed").
- **Production document skills** — `skills/pdf/SKILL.md` (+ `forms.md`,
  `reference.md`, `scripts/`) shows a fillable-vs-non-fillable branching and a
  multi-stage CLI tool family; `skills/xlsx/SKILL.md` encodes quality mandates
  as MUST rules ("ZERO formula errors", blue-text-hardcoded-inputs convention,
  prefer formulas over precomputed values).
- **Negative constraints** — `skills/frontend-design/SKILL.md` steers aesthetics
  with explicit bans (no purple gradients, no uniform rounded corners) instead
  of vague positive direction.
- **Skeleton + spec** — `template/` and `spec/` mirror the open `agentskills.io`
  specification for plugin distribution.

## When to consult

Open this repo before writing a new skill of any kind — frontmatter style,
reference layout, agent scaffolding, quality-bar phrasing. Example
applications: shape the `references/` folder of a migration skill after
`skill-creator/references/`; mirror the pair-agent eval pattern when
pressure-testing a recipe; lift MUST-rule phrasing from `xlsx` for the
verification gates of a migration skill.

## Highlights

- **Pair-agent evals** (`skill-creator`): paired subagents run the same test
  case — one with the skill loaded, one without — in parallel. Lift directly
  for any eval comparing baseline vs. treatment.
- **Pushy descriptions to fight under-triggering** — match the wording style
  of `skill-creator`'s own frontmatter `description` field; vague descriptions
  cause Claude to short-circuit and skip the body.
- **Deterministic CLIs as tools that don't enter the context window** — see
  `skills/pdf/scripts/`. Adapt for any deterministic verification step.
- **MUST-rule quality bars** (`xlsx`) — adopt for verification gates.
- **Exact-shape contracts for structured outputs** — `skill-creator/SKILL.md`
  (Step 4) pins exact field names for `grading.json` and **negative-lists**
  the variants the model is otherwise tempted to invent
  (`text/passed/evidence`, *not* `name/met/details`). The negative-list trick
  is the part most skills miss.
- **Caveat:** the document skills (`skills/{pdf,docx,pptx,xlsx}`) are
  source-available, **not** Apache-2.0 (see each `LICENSE.txt`). Lift
  patterns, do **not** redistribute their text inside derived skills.
