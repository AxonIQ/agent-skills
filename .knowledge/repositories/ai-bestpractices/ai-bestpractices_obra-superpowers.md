---
repo_type: ai-bestpractices
repo_name: obra-superpowers
submodule_path: .knowledge/repositories/ai-bestpractices/obra-superpowers
url: https://github.com/obra/superpowers.git
branch: main
keywords:
  - tdd for skills
  - triggering rules
  - subagent workflows
  - plugin marketplace
  - multi-agent parity
  - brainstorming
  - systematic debugging
---

# obra-superpowers

## Purpose

The most sophisticated community framework for disciplined agent-skill
authoring, distributed via the official `claude-plugins-official` marketplace.
Encodes a TDD methodology for *skill authoring itself*, a formalised
triggering/precedence model, and a subagent-driven implementation loop with
code-review checkpoints. The closest reference for "how to write disciplined
skills that don't drift" — useful for any rigorous skill, including the Axon
4→5 migration skills as a concrete example.

## Feature highlights

- **TDD applied to skill authoring** — `skills/writing-skills/SKILL.md` walks
  through writing pressure-test cases with subagents, watching them fail
  (RED), writing the skill (GREEN), then refactoring.
- **Reference set for writing-skills** — `anthropic-best-practices.md`,
  `persuasion-principles.md`, `testing-skills-with-subagents.md`, and an
  `examples/` directory supporting that workflow.
- **Triggering flowchart and tool-name mapping** —
  `skills/using-superpowers/SKILL.md` codifies the "even a 1% chance a skill
  applies → invoke it" rule and provides a cross-agent tool-name mapping
  (Claude Code / Codex / Copilot CLI / Gemini).
- **Subagent-driven implementation loop** —
  `skills/subagent-driven-development/SKILL.md` (+ `implementer-prompt.md`,
  `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md`) runs
  independent subagents per task with two-stage code review.
- **Composable technique skills** — `skills/{brainstorming,test-driven-development,systematic-debugging,verification-before-completion,executing-plans,writing-plans}/`
  cover small reusable techniques you can compose into project workflow skills.
- **Orchestration primitives** — `skills/dispatching-parallel-agents/`,
  `skills/using-git-worktrees/`, `skills/finishing-a-development-branch/`.
- **Tri-platform parity** — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` carry the
  same content authored for three agents; a clean example of cross-platform
  doc parity.

## When to consult

Open this repo when designing a skill that must stay disciplined under
pressure (multi-step migrations, debugging skills, verification gates). The
"even 1% chance" trigger rule is also a useful precedent for any project that
wants a skill-first stance. Example application: structure a migration
orchestrator skill using the `implementer` / `spec-reviewer` /
`code-quality-reviewer` agent prompts as a skeleton.

## Highlights

- **TDD-for-skills** is the single highest-leverage pattern here: pressure-test
  cases first, observe the failure mode, then fix the skill — not just the
  wording. Pair with the eval harness from
  `anthropics-skills/skills/skill-creator/`.
- **Generic-actionable descriptions** — `writing-skills` warns that
  descriptions which *summarise* the workflow cause Claude to short-circuit
  and skip the body. Match this style for any skill whose body must actually
  be read.
- **Subagent-driven dev loop** with explicit role prompts is reusable as the
  skeleton for any multi-agent orchestration skill.
- **Doc parity discipline** (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`) is worth
  copying once a skill targets more than Claude Code.
