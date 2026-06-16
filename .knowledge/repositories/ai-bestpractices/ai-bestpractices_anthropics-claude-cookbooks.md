---
repo_type: ai-bestpractices
repo_name: anthropics-claude-cookbooks
repo_path: .knowledge/repositories/ai-bestpractices/anthropics-claude-cookbooks
url: https://github.com/anthropics/claude-cookbooks.git
branch: main
keywords:
  - claude api
  - skills loading model
  - skill evals
  - custom skills
  - jupyter notebooks
  - tool use
---

# anthropics-claude-cookbooks

## Purpose

Anthropic's official cookbook collection — the single best end-to-end walkthrough
of the Claude API together with the Skills runtime. Use it when designing any
agent skill (Axon 4→5 migration recipes are one concrete example) to internalise
the three-tier loading model and to prototype API-driven evaluation harnesses.

## Feature highlights

- **Three-tier loading model walkthrough** — `skills/notebooks/01_skills_introduction.ipynb`
  diagrams metadata → SKILL.md body → bundled files, with the required beta
  headers (`code-execution-2025-08-25`, `files-api-2025-04-14`, `skills-2025-10-02`).
- **End-to-end financial pipeline** — `skills/notebooks/02_skills_financial_applications.ipynb`
  chains extract → analyse → report skills over real PDF/XLSX/PPTX documents.
- **Custom skill authoring** — `skills/notebooks/03_skills_custom_development.ipynb`
  builds and registers a custom skill via the API end-to-end.
- **Worked custom-skill examples** — `skills/custom_skills/{analyzing-financial-statements,applying-brand-guidelines,creating-financial-models}/`
  show the SKILL.md-plus-scripts shape at small scale.
- **Skill management helpers** — `skills/skill_utils.py`, `skills/file_utils.py`
  are reusable templates for an in-house eval/CI harness on top of `/v1/skills`.

## When to consult

Reach for this when you need a sanity-check on a prompt structure, an agent
loop, or how the Skills runtime actually loads content. It trades depth for
breadth and is faster to scan than the full Anthropic docs. Example application:
prototype baseline-vs-treatment evals for a migration recipe by adapting the
notebook harnesses verbatim.

## Highlights

- Start in `skills/notebooks/` and `skills/custom_skills/` — those subtrees
  carry the densest reusable patterns.
- Copy the **token-cost diagrams** of the three-tier loading model into your
  own authoring docs so skill writers internalise "metadata is the only
  triggering signal".
- The custom-skill scaffold (single SKILL.md + scripts) is the cleanest tiny
  example to copy for small per-recipe skills (e.g. a single Axon 5 migration
  recipe).
- Official Claude API docs: <https://docs.anthropic.com/>. The cookbook is the
  practical companion, not a replacement.
