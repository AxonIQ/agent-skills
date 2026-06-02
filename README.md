# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

Skills follow the [agentskills.io](https://agentskills.io/) format and live with the plugin that owns them, under [`plugins/<plugin>/skills/`](./plugins). This repo is a multi-runtime marketplace (`axoniq`): install a curated plugin into Claude Code, Codex, or Cursor, or pull individual skills into any agent with `npx skills`.

## Installation

### Claude Code plugin (recommended)

Curated, named plugins; auto-updates via the marketplace. Run inside Claude Code, or as `claude plugin …` from the shell:

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install axon4to5@axoniq
```

`marketplace update axoniq` later pulls the latest skills.

### Codex plugin

```bash
codex plugin marketplace add AxonIQ/agent-skills
codex plugin add axon4to5@axoniq
```

`codex plugin marketplace upgrade axoniq` later pulls the latest skills.

### Cursor plugin

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install axon4to5@axoniq
```

Or browse/submit via the [Cursor marketplace](https://cursor.com/marketplace).

### npx skills (any agent)

For Gemini CLI, opencode, and others — installs skill folders directly (the plugin layer is ignored; skills are discovered under `plugins/*/skills/`):

```bash
npx skills add AxonIQ/agent-skills                                               # interactive picker
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # specific skill + agent
npx skills add AxonIQ/agent-skills --skill '*' -g                                # all skills, user-global
```

## Contributing

Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
