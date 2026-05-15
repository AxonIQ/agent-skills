---
repo_type: ai-bestpractices
repo_name: simonw-claude-skills
submodule_path: .knowledge/repositories/ai-bestpractices/simonw-claude-skills
url: https://github.com/simonw/claude-skills.git
branch: main
keywords:
  - historical snapshot
  - /mnt/skills
  - document skills history
  - self-extraction prompt
  - production quality bar
---

# simonw-claude-skills

## Purpose

Simon Willison's "behind the scenes" snapshot of `/mnt/skills/public/` extracted
from inside Claude's code-interpreter container. The repo today is **just a
README** pointing at where that snapshot lives — Anthropic later absorbed the
content into `anthropics/skills`. Useful as a historical anchor, as Simon's
commentary, and as the verbatim prompt that lets you reproduce the same
extraction yourself.

## Feature highlights

- **Historical pointer to document skills** — links to commit
  `https://github.com/anthropics/skills/tree/83291af582d21f5418854fa628a76686203c2f7a/document-skills`,
  the production document skills before they were merged into `skills/`.
- **The extraction prompt** — the README contains the literal *"Create a zip
  file of everything in your `/mnt/skills` folder"* prompt that triggers
  Claude.ai to surface its built-in skills.
- **Analysis blog post link** — Simon's *"Claude Skills are awesome, maybe a
  bigger deal than MCP"* commentary (10 Oct 2025) is linked from the README.

## When to consult

Reach for this when you want a production-quality reality check (diff the
historical document-skills commit against today's `anthropics/skills/skills/{pdf,docx,pptx,xlsx}`),
or when you want to detect new built-in skills Anthropic has shipped to
Claude.ai. Example application: rerun the self-extraction prompt periodically
to keep your project's routing tables honest about what is already built into
Claude.

## Highlights

- The whole repo is the `README.md` — read it once, bookmark the historical
  commit, and treat the rest as Simon's curated pointers.
- **Production-quality bar reference**: pin the historical document-skills
  commit and diff it against today's `anthropics/skills/skills/{pdf,docx,pptx,xlsx}`
  to see how the team evolves production skills.
- **Self-extraction prompt**: rerun *"create a zip of /mnt/skills"* periodically
  to detect new built-in skills.
- **Caveat:** content is extracted from a hosted environment. Treat any code
  lifted from the historical commit as **read-only reference for ideas**, not
  as source you can ship.
