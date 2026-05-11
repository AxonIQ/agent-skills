---
repo_type: ai-bestpractices
repo_name: supabase-agent-skills
submodule_path: .knowledge/repositories/ai-bestpractices/supabase-agent-skills
url: https://github.com/supabase/agent-skills.git
branch: main
keywords:
  - tiny SKILL.md
  - find-truth pattern
  - security checklist
  - prefix-namespaced references
  - tested skills
  - priority routing table
---

# supabase-agent-skills

## Purpose

Supabase's official Tier-1 vendor skills, companion to their blog post
*"AI Agents Know About Supabase. They Don't Always Use It Right."* The
reference example for a deliberately *tiny* SKILL.md that **does not
replicate documentation** — instead it teaches the agent how to *find truth*
(changelog → docs → MCP → web search) and bakes inline guardrails for the
platform's known agent-failure modes (RLS, JWT auth, Data API exposure, …).
Any skill that depends on a fast-moving platform — Axon Framework 5 included
— can adopt this shape.

## Feature highlights

- **Tiny main skill** — `skills/supabase/SKILL.md` opens with six numbered
  Core Principles and a multi-section Security Checklist; the body fits the
  "verify, don't memorise" mantra in under ~100 lines.
- **Near-empty references** — `skills/supabase/references/skill-feedback.md`
  is the only auxiliary doc; pattern for keeping a skill's reference set
  small when the platform is the canonical source of truth.
- **Prefix-namespaced references + priority-routing table** —
  `skills/supabase-postgres-best-practices/SKILL.md` opens with a priority
  table mapping each reference-file prefix (`query-`, `conn-`, `security-`,
  `schema-`, `lock-`, `data-`, `monitor-`, `advanced-`) to an impact rating;
  the `references/` directory itself becomes a sortable, greppable index.
- **Per-rule frontmatter** — each reference file carries its own
  `title / impact / impactDescription / tags` frontmatter, so future tooling
  can sort recipes by impact deterministically.
- **Authoring guidance in parity** — top-level `AGENTS.md` and `CLAUDE.md`
  carry the same repo-wide authoring guidance across agents.
- **Tested skills** — `test/`, `vitest.config.ts` run actual unit tests over
  the skill content. Rare and worth studying for CI-checked skills.

## When to consult

Open this repo when authoring a skill for a platform that moves faster than
training data — the structure forces "look up the current truth" instead of
encoding a snapshot. Example application: an Axon 5 area where the framework
moves fast should point to `references/AxonFramework5/docs/...` rather than
inlining excerpts that go stale, exactly as `supabase/SKILL.md` points to its
changelog.

## Highlights

- **"Skill teaches how to find truth, not what truth currently is."** The
  first step in every workflow fetches a small index (here `changelog.md`),
  scans for relevant tags, then follows links.
- **Inline security/correctness checklist** as a numbered section in SKILL.md,
  with the *concrete failure mode* named per item ("Never use `user_metadata`
  claims in JWT-based authorization"). Adapt this shape for any recipe's
  "common pitfalls" — name symptoms, not generic warnings.
- **"Recover from errors, don't loop"** — an explicit Core Principle that caps
  retries at 2–3 and forces reconsideration. Lift verbatim into verification
  skills.
- **Tiny SKILL.md, big trigger description** — the frontmatter `description`
  lists every product surface and trigger phrase a user might say; the body
  stays short. Cleanest example of fighting under-triggering without bloating
  the body.
- **Prefix priority table** (`supabase-postgres-best-practices`) — copy when
  a skill's `references/` set grows past ~5 files. Adapt prefixes to your
  domain (e.g. `cmd-`, `qry-`, `evt-`, `cfg-` for Axon-style recipe catalogues).
- **Per-rule `impact: CRITICAL|HIGH|MEDIUM|LOW`** in frontmatter — makes
  triage deterministic when a skill must pick which recipes apply to a
  partial change.
- **`vitest` against SKILL.md content** is an under-explored idea — worth
  considering for CI on any skill set.
