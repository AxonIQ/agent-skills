# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework — whether you are migrating an application to Axon 5, building applications on Axon Framework 5, or contributing to the framework itself.

Skills follow the [agentskills.io](https://agentskills.io/) format and live with the plugin that owns them, under [`plugins/<plugin>/skills/`](./plugins). This repo is a multi-runtime marketplace (`axoniq`): install a curated plugin into Claude Code, Codex, or Cursor, or pull individual skills into any agent with `npx skills`.

> ⚠️ **These skills drive LLMs, which can make mistakes and hallucinate.** Don't trust the output blindly — **review, test, and verify it before relying on it**, especially anything that changes your code. The skills are provided on a best-effort basis, with no guarantee of correctness or completeness. Spot a problem or a gap? Contributions are very welcome — see [Contributing](#contributing) and help us make these skills better.

## Plugins

| Plugin | Version | For whom |
|--------|---------|----------|
| [`axoniq-migration`](./plugins/axoniq-migration) | 0.2.0 | Anyone **migrating** an application from Axon Framework 4 to Axon Framework 5 / Axoniq Framework 5. |
| [`axoniq-app-development`](./plugins/axoniq-app-development) | 0.4.0 | Developers **building their own applications** with Axon Framework 5 — the framework's users. |
| [`axoniq-framework-contribution`](./plugins/axoniq-framework-contribution) | 1.4.0 | Contributors **developing the Axon Framework itself** — not for building applications with it. |

Each plugin carries its own `CHANGELOG.md` and is versioned independently.

> **`axoniq-migration` is best-effort.** It automates as much of the Axon Framework 4 → 5 migration as it reliably can, but it will not always migrate everything: expect some leftover concerns (unusual patterns, edge cases, manual decisions) flagged for **you** to finish by hand. It migrates code and configuration only — not stored data (event store contents, tracking tokens). Always review and test the result.

## Installation

Replace `<plugin>` below with one of `axoniq-migration`, `axoniq-app-development`, or `axoniq-framework-contribution`.

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
  --skill axon4to5-openrewrite axon4to5-migrate-code axon4to5-isolatedtest \
  -a <agent>                                                                     # all axon4to5 migration skills
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # one skill + agent
```

Common `-a <agent>` values include `gemini-cli`, `cursor`, `codex`, `opencode`, and `claude-code`.

## Contributing

**Contributions are very welcome** — these skills get better the more people use them and report back. Found a hallucinated or wrong result, a migration gap, a missing recipe, or an idea for a new skill? Open an issue or a PR. Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
