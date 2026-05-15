# CLAUDE.md

Skills follow the [agentskills.io](https://agentskills.io/) format.

ALWAYS CREATE NEW SKILLS IN DIRECTORY: [skills](skills) and while developing execute other Skills (expecially
`/skill-creator`) using rules from: [using-superpowers](.knowledge/repositories/ai-bestpractices/obra-superpowers/skills/using-superpowers)

## Skill authoring practices

- Follow official Anthropic guides: [anthropic-skills-best-practices.md](.knowledge/docs/anthropic-skills-best-practices.md) and [anthropic-extend-claude-with-skills.md](.knowledge/docs/anthropic-extend-claude-with-skills.md) and 
- Concise skill descriptions, max 200 characters.
- Simplicity and minimalism are crucial – do not add something I didn't ask you about. But be proactive – propose new
solutions and challenge the design.
- Do not write how to do things that the LLM model should already know, or do not explain well-known concepts, focus on
  Axon Framework specific stuff.
- **Never put forward-looking / roadmap content (e.g. "future modes", "planned bulk mode", "TODO when we add X") into
  `SKILL.md` or any reference file the skill loads.** SKILL.md must describe only what is implemented today, so the LLM
  doesn't act on imagined capabilities. Park such ideas in a `docs/PLANS.md` placed next to the skill's local `CLAUDE.md` (
  i.e. inside the skill directory). `PLANS.md` is for humans — it MUST NOT be referenced from `SKILL.md`.

**Recurring patterns:**
- **Anti-hallucination**: "Verify with Grep before asserting a pattern exists"
- **Scope fencing**: Explicit "NOT responsible for" statements. MUST NOT rules prevent scope creep.
- **Tool-specific instructions**: Steps name exact tools ("Use Grep to find...", "Use Glob to discover...")
- **Verify-before-report**: Final step re-reads files to confirm references are accurate.
- **Progressive disclosure**: Core workflow in the agent file; deep domain knowledge in `references/` with routing table
  with conditions in SKILL.md.