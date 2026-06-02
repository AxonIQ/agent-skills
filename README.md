# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework — whether you are migrating an application to Axon 5, building applications on Axon Framework 5, or contributing to the framework itself.

Skills follow the [agentskills.io](https://agentskills.io/) format and live with the plugin that owns them, under [`plugins/<plugin>/skills/`](./plugins). This repo is a multi-runtime marketplace (`axoniq`): install a curated plugin into Claude Code, Codex, or Cursor, or pull individual skills into any agent with `npx skills`.

## Plugins

| Plugin | Version | For whom |
|--------|---------|----------|
| [`axon4to5`](./plugins/axon4to5) | 0.1.0 | Anyone **migrating** an application from Axon Framework 4 to Axon Framework 5 / Axoniq Framework 5. |
| [`axoniqframework-dev-tools`](./plugins/axoniqframework-dev-tools) | 0.3.9 | Developers **building their own applications** with Axon Framework 5 — the framework's users. |
| [`axoniqframework-contribution-tools`](./plugins/axoniqframework-contribution-tools) | 1.3.1 | Contributors **developing the Axon Framework itself** — not for building applications with it. |

Each plugin carries its own `CHANGELOG.md` and is versioned independently.

## Installation

Replace `<plugin>` below with one of `axon4to5`, `axoniqframework-dev-tools`, or `axoniqframework-contribution-tools`.

### Claude Code plugin (recommended)

Curated, named plugins; auto-updates via the marketplace. Run inside Claude Code, or as `claude plugin …` from the shell:

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install <plugin>@axoniq
```

`marketplace update axoniq` later pulls the latest skills.

### Codex plugin

```bash
codex plugin marketplace add AxonIQ/agent-skills
codex plugin add <plugin>@axoniq
```

`codex plugin marketplace upgrade axoniq` later pulls the latest skills.

### Cursor plugin

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install <plugin>@axoniq
```

Or browse/submit via the [Cursor marketplace](https://cursor.com/marketplace).

### npx skills (any agent)

For Gemini CLI, Cursor, Codex, opencode, and others — installs skill folders directly (skills are discovered under `plugins/*/skills/`). For example, to install the full `axon4to5` migration skill set explicitly:

```bash
npx skills add AxonIQ/agent-skills                                               # interactive picker
npx skills add AxonIQ/agent-skills \
  --skill axon4to5-openrewrite axon4to5-migrate axon4to5-isolatedtest \
  -a <agent>                                                                     # all axon4to5 migration skills
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # one skill + agent
```

Common `-a <agent>` values include `gemini-cli`, `cursor`, `codex`, `opencode`, and `claude-code`.

## Contributing

Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
