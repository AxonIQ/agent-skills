# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

The canonical skills live in [`skills/`](./skills) at the repo root and follow the [agentskills.io](https://agentskills.io/) format. Plugin bundles contain generated copies of selected root skills so Claude Code and Codex can install curated plugin packages.

## Installation

### Claude Code plugin (recommended)

Curated, named plugins; auto-updates via the marketplace. Run inside Claude Code, or as `claude plugin …` from the shell:

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install axon4to5@axoniq-agent-skills
```

`marketplace update axoniq-agent-skills` later pulls the latest skills.

### Codex plugin

Curated, named plugins; installable from the same checkout or GitHub repository:

```bash
codex plugin marketplace add AxonIQ/agent-skills
codex plugin add axon4to5@axoniq-agent-skills
```

`codex plugin marketplace upgrade axoniq-agent-skills` later pulls the latest skills.

### npx skills (any agent)

For Codex, Gemini CLI, Cursor, opencode, etc. — installs skill folders directly from the canonical `skills/` pool (the plugin layer is ignored):

```bash
npx skills add AxonIQ/agent-skills                                               # interactive picker
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # specific skill + agent
npx skills add AxonIQ/agent-skills --skill '*' -g                                # all skills, user-global
```

## Contributing

Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
