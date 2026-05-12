# CLAUDE.md

Skills follow the [agentskills.io](https://agentskills.io/) format.
Be explicit about tools names. Use Claude Code tools names by default like (`Skill`, `Read`, `Grep` etc)

ALWAYS CREATE NEW SKILLS IN DIRECTORY: [skills](skills) and while developing execute other Skills (expecially
`/skill-creator`) using rules
from: [using-superpowers](.knowledge/repositories/ai-bestpractices/obra-superpowers/skills/using-superpowers)
Follow `/grill-me` SKILL instructions as well to build shared understanding before implementation.

## Skill authoring practices

Concise skill descriptions, max 200 characters.

Simplicity and minimalism is crucial - do not add something I didn't ask you about. But be proactive - propose new
solutions etc. with AskUserQuestion tool.
Do not write how to do things that the LLM model should already know, or do not explain well-known concepts, focus on
Axon Framework specific stuff.

Use [guidelines.md](.knowledge/docs/guidelines.md).

**Recurring patterns:**

- **Anti-hallucination**: "Verify with Grep before asserting a pattern exists"
- **Evidence-first**: Every claim cites `file:line`. Inferences labeled separately from facts.
- **Confidence gating** (review agents): Issues rated 0-100, only >=80 reported.
- **Scope fencing**: Explicit "NOT responsible for" statements. MUST NOT rules prevent scope creep.
- **Tool-specific instructions**: Steps name exact tools ("Use Grep to find...", "Use Glob to discover...")
- **Verify-before-report**: Final step re-reads files to confirm references are accurate.
- **Progressive disclosure**: Core workflow in the agent file; deep domain knowledge in `references/` with routing table
  in SKILL.md.

### Style

Use caveman 60% style for the skill content. Very concise, good for LLM.
But the skill output to the user must be clear and concise, do not be talkative, just good structure with the summary
what was done/ what failed.

### Content

Skill content is just for LLM (optimize for this). No human notes.

Each skill must define expected input, expected output (structured markdown) and can use agent delegation patterns like.

#### Goal

Skills have a clear goal so must have its defined and defined check when the skill job is done.

#### Must and must not

Skills must define what must be done and what must NOT be done.

#### Routing tables

Keep the SKILL.md very short, use routing tables like
in [SKILL.md](.knowledge/repositories/axonframework/claude-plugin/plugins/axoniq-claude-plugin/skills/axonframework/SKILL.md)
(for example how to migrate concept X based on context, like "Event Sourced Aggregate" -> @EventSoucedEntity or "
State-Based Aggregate" to X etc. )

Use additional reference files, but avoid deeply nested references.

- The "one level deep" rule from is about the **reference chain**, not directory nesting:
  every reference file must be reachable in a single hop from `SKILL.md`. Directory nesting is irrelevant.
- All routing/dispatch logic MUST live in `SKILL.md`. Topic files MUST NOT link to other topic files — no
  `event-handling.md → command-handling.md` chains.

#### Visualization

Use graphiz diagrams for flow charts following conventions:
[graphviz-conventions.dot](.knowledge/repositories/ai-bestpractices/obra-superpowers/skills/writing-skills/graphviz-conventions.dot)

### Communication

Messages that will be sent to the user should be standarized in the skill. Friendly tone, with emojis – good visually.
Clear, direct messages are very important for the user experience.

### Claude Code extend with Skills

Follow the official Claude Code skill docs distilled
in [anthropic-extend-claude-with-skills.md](.knowledge/docs/anthropic-extend-claude-with-skills.md).
Key sections to consult while authoring:

- [Frontmatter reference](.knowledge/docs/anthropic-extend-claude-with-skills.md#frontmatter-reference) — required
  `name`/`description`,
  `allowed-tools`, `argument-hint`.
- [String substitutions](.knowledge/docs/anthropic-extend-claude-with-skills.md#available-string-substitutions) —
  `$ARGUMENTS`, `$1`..`$9`,
  `$CLAUDE_PROJECT_DIR`, etc.
- [Pre-approve tools for a skill](.knowledge/docs/anthropic-extend-claude-with-skills.md#pre-approve-tools-for-a-skill) —
  list
  deterministic scripts in `allowed-tools` so they run without prompts.
- [Pass arguments to skills](.knowledge/docs/anthropic-extend-claude-with-skills.md#pass-arguments-to-skills) — for
  parameterised skills (
  e.g. target module path).
- [Inject dynamic context](.knowledge/docs/anthropic-extend-claude-with-skills.md#inject-dynamic-context) — use `!`
  shell blocks inside
  SKILL.md frontmatter/body so output is interpolated at skill-load time. **This is the right place for env probes** (
  e.g. `command -v jdtls`), not interactive `!` from the user prompt.
- [Add supporting files](.knowledge/docs/anthropic-extend-claude-with-skills.md#add-supporting-files) — keep
  scripts/examples beside
  SKILL.md.
- [Run skills in a subagent](.knowledge/docs/anthropic-extend-claude-with-skills.md#run-skills-in-a-subagent) — isolate
  large
  research/migration sweeps from the main context.
- [Troubleshooting: skill not triggering](.knowledge/docs/anthropic-extend-claude-with-skills.md#skill-not-triggering) —
  fix
  description/keywords if a skill is ignored.

When you add an entry-time probe (LSP availability, Maven version, git status) prefer a `!` shell block in the skill
frontmatter over instructing the LLM to run Bash — it executes deterministically before the model reads the body.

### Claude Code Skills Best Practices

Must follow [anthropic-skills-best-practices.md](.knowledge/docs/anthropic-skills-best-practices.md)
Delegate deterministic tasks to scripts (create them while working on skill during a feedback loop).
