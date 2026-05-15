---
repo_type: ai-bestpractices
repo_name: vercel-labs-agent-skills
submodule_path: .knowledge/repositories/ai-bestpractices/vercel-labs-agent-skills
url: https://github.com/vercel-labs/agent-skills.git
branch: main
keywords:
  - rule-based skills
  - AGENTS.md contract
  - tri-agent parity
  - metadata.json
  - skills CLI distribution
  - composition patterns
---

# vercel-labs-agent-skills

## Purpose

Vercel's curated skills plus the skill-quality conventions that underpin the
de-facto cross-agent installer (`npx skills`, `skills.sh`). The cleanest
exemplar of *rule-based* skills — large bullet-list rule sets prioritised by
impact — and of writing one SKILL.md that ships to multiple agents (Claude
Code, Cursor, Copilot, Codex) via `AGENTS.md` parity. Useful any time a
project codifies team coding standards or recipe catalogues as a skill;
Axon 4→5 migration recipes are one such case.

## Feature highlights

- **`AGENTS.md` as a copy-paste lint** — top-level `AGENTS.md` defines the
  skill-authoring contract: kebab-case directory names, required files,
  exact frontmatter shape, distribution `.zip` convention.
- **Tri-agent doc parity** — top-level `CLAUDE.md` mirrors `AGENTS.md` with
  Claude-specific guidance, keeping a single source of truth across agents.
- **Categorised, impact-prioritised rule sets** —
  `skills/react-best-practices/{SKILL.md,rules/,README.md,metadata.json}` is
  the canonical example; mirrors what recipe catalogues look like once
  flattened.
- **Large single-file rule corpus** — `skills/web-design-guidelines/SKILL.md`
  covers accessibility, performance, UX in one linearly-readable document.
- **Composition / router pattern** —
  `skills/composition-patterns/SKILL.md` shows how to compose other skills
  together.
- **Smaller single-purpose skills** —
  `skills/{deploy-to-vercel,vercel-cli-with-tokens,react-view-transitions,react-native-skills}/`
  are useful size targets for per-recipe skills.
- **`metadata.json` per skill** — small machine-readable manifest beside
  SKILL.md; useful for driving CI/eval tooling without re-parsing markdown.
- **npm tooling for distribution** — `packages/` shows how to package and
  version-control skills for distribution.

## When to consult

Open this repo when starting a skill that codifies team coding standards or
a flat catalogue of recipes; the rule-based layout and `metadata.json`
manifest scale better than narrative SKILL.md prose. Example application:
shape a per-recipe migration skill after `react-best-practices/rules/`, with
each recipe as its own rule file ordered by impact.

## Highlights

- **Lift the `AGENTS.md` frontmatter triggering language verbatim** for any
  skill's `description` field — it's the most battle-tested phrasing for
  cross-agent triggering.
- **Adapt the `AGENTS.md` bullet checklist** (scripts use `set -e`,
  status-to-stderr / JSON-to-stdout, ≤500 lines, references one level deep)
  into your own project's authoring guidelines.
- **Rule-based skill structure** (categorised, prioritised by impact) is the
  best fit when the skill is fundamentally *"here are the rules of doing X"*
  rather than a workflow.
- **`metadata.json` per skill** — drop in once a skill set is CI-checked or
  programmatically managed.
- **Tri-agent doc parity** — `AGENTS.md` / `CLAUDE.md` (top-level) plus
  per-skill `AGENTS.md`. Adopt once skills target more than Claude Code.
