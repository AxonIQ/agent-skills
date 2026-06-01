# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

All skills live in [`skills/`](./skills) at the repo root and follow the [agentskills.io](https://agentskills.io/) format — the single canonical source. They can be consumed directly by any agent runtime that loads `SKILL.md` files (e.g. `npx skills`), or installed as a Claude Code plugin (see below).

## Installation

### Claude Code plugin (recommended)

Curated, named plugins; auto-updates via the marketplace. Run inside Claude Code, or as `claude plugin …` from the shell:

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install axon4to5@axoniq-agent-skills
```

`marketplace update axoniq-agent-skills` later pulls the latest skills.

### Codex plugin

🚧 **Coming soon** — a native [OpenAI Codex](https://developers.openai.com/codex/skills/) plugin packaging the same skills. Until then, use the `npx skills` method below with `-a codex`.

### npx skills (any agent)

For Codex, Gemini CLI, Cursor, opencode, etc. — installs skill folders directly from the canonical `skills/` pool (the plugin layer is ignored):

```bash
npx skills add AxonIQ/agent-skills                                               # interactive picker
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # specific skill + agent
npx skills add AxonIQ/agent-skills --skill '*' -g                                # all skills, user-global
```

## Contributing

Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
