# Template — `ai-bestpractices` per-repo detail file

Use this template when `repo_type: ai-bestpractices`. These are general
references — prompt engineering, agent loops, evaluation methodology — that
don't fit the Axon-framework or migrated-example shapes. There is no pairing
and no migration link.

Detail file path:

```
.knowledge/repositories/ai-bestpractices/ai-bestpractices_<repo>.md
```

## Filled-in example

```markdown
---
repo_type: ai-bestpractices
repo_name: anthropic-cookbook
submodule_path: .knowledge/repositories/ai-bestpractices/anthropic-cookbook
url: https://github.com/anthropics/anthropic-cookbook.git
branch: main
keywords:
  - prompt engineering
  - tool use
  - evaluation
  - agent loops
---

# anthropic-cookbook

## Purpose

Reference recipes for building with the Claude API — prompt patterns, tool
use, evaluation harnesses, and worked examples for common agentic loops.

## Feature highlights

- **Prompt patterns** — system-prompt templates for common tasks, with notes
  on tradeoffs.
- **Tool use** — end-to-end examples of multi-turn tool-calling, including
  parallel tool use.
- **Evaluation** — small but real eval harnesses for scoring model outputs.
- **Agentic loops** — minimal implementations of the planner / executor split.

## When to consult

Reach for this whenever a skill needs a sanity-check on a prompt structure
or an agent loop — the cookbook trades depth for breadth and is faster to
scan than the full Anthropic docs.

## Highlights

- Start in `skills/` and `tool_use/` — those folders are where most of the
  reusable patterns live.
- The `misc/` folder is unstructured; useful but expect more churn.
- Official Anthropic docs: <https://docs.anthropic.com/>. The cookbook is the
  practical companion, not a replacement.
```

## Empty scaffold

```markdown
---
repo_type: ai-bestpractices
repo_name: <repo>
submodule_path: .knowledge/repositories/ai-bestpractices/<repo>
url: <git URL>
branch: <branch or omit>
commit: <short-hash or omit>
keywords:
  - <term>
  - <term>
  - <term>
---

# <repo>

## Purpose

<1–2 sentences on what this repo is and why it's tracked here.>

## Feature highlights

- **<Feature 1>** — <one line>
- **<Feature 2>** — <one line>
- **<Feature 3>** — <one line>

## When to consult

<Short closing line: which kinds of tasks should pull this in.>

## Highlights

- <Curated callout — key docs, recommended reading order, anything otherwise
  easy to miss.>
- <Curated callout>
```

## Field rules

- `keywords` must be 3–7 short, discriminative terms — they are the primary
  signal in the type-level `INDEX.md`.
- `## Highlights` is mandatory; use `- _none_` only when the curator
  explicitly has nothing to flag.
