---
repo_type: axonframework
repo_name: claude-plugin
submodule_path: .knowledge/repositories/axonframework/claude-plugin
url: https://github.com/AxonIQ/claude-plugin.git
branch: main
keywords:
  - claude plugin
  - axon 5 skills
  - migration skill patterns
  - agent skill authoring
  - axoniq claude plugin
  - skill examples
---

# claude-plugin

## Purpose

AxonIQ's official Claude Code plugin bundling skills that teach Claude how to
write idiomatic Axon Framework 5 code. Practical reference for **how a
migration/authoring skill should be shaped** — directory layout, SKILL.md
frontmatter, scope-per-skill granularity — when building or improving skills
in this repo.

## Feature highlights

- **Per-topic skill bundle** — one skill per Axon 5 concern
  (command handling, event handling, event store primitives, testing, etc.)
  rather than one monolithic guide.
- **Authoring reference for Axon 5 migration skills** — shows the shape and
  granularity AxonIQ ships externally; mirror this when writing in-repo
  skills.
- **Spring + plain configuration coverage** — separate
  `spring-configuration` and `configuration` skills demonstrate how to
  split runtime concerns.
- **Distributed messaging + interceptors** — patterns for cross-cutting
  Axon 5 concerns that migration guides commonly miss.

## Key paths

- `plugins/axoniq-claude-plugin/skills/axonframework/` — the canonical
  set of Axon Framework 5 skills (start here when writing a new skill).
- `plugins/axoniq-claude-plugin/skills/axonframework/SKILL.md` — top-level
  skill index inside the plugin; shows how sub-skills are organized.
- `plugins/axoniq-claude-plugin/skills/axonframework/command-handling/` —
  worked example of a single-topic skill structure.
- `plugins/axoniq-claude-plugin/skills/axonframework/testing/` —
  reference for AxonTestFixture usage in skill-driven code.
- `CHANGELOG.md` — track what the AxonIQ team has shipped and when.

## Highlights

- Use `plugins/axoniq-claude-plugin/skills/axonframework/` as the
  inspiration — directory naming, SKILL.md style, and topic
  granularity in this tree are good conventions.
- Tracks `main` — expect rapid churn; re-pull before deriving patterns
  from a specific skill.
