# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework — whether you are upgrading an application to Axon 5, building applications on Axon Framework 5, or contributing to the framework itself.

Skills follow the [agentskills.io](https://agentskills.io/) format and live with the plugin that owns them, under [`plugins/<plugin>/skills/`](./plugins). This repo is a multi-runtime marketplace (`axoniq`): install a curated plugin into Claude Code, Codex, or Cursor, or pull individual skills into any agent with `npx skills`.

> ⚠️ **These skills drive LLMs, which can make mistakes and hallucinate.** Don't trust the output blindly — **review, test, and verify it before relying on it**. The skills are provided on a best-effort basis, with no guarantee of correctness or completeness. Spot a problem or a gap? Contributions are very welcome — see [Contributing](#contributing) and help us make these skills better.

## Plugins

| Plugin | Version | For whom |
|--------|---------|----------|
| [`axoniq-migration`](./plugins/axoniq-migration) | 0.3.0 | Anyone **upgrading** an application to Axon Framework 5 / Axoniq Framework 5 or legacy sagas to workflows. |
| [`axoniq-app-development`](./plugins/axoniq-app-development) | 0.4.0 | Developers **building their own applications** with Axon Framework 5 — the framework's users. |
| [`axoniq-framework-contribution`](./plugins/axoniq-framework-contribution) | 1.4.0 | Contributors **developing the Axon Framework itself** — not for building applications with it. |
| [`axoniq-platform`](./plugins/axoniq-platform) | 0.1.0 | Developers **implementing an AxonIQ Platform project** locally — read the spec via MCP and generate AF5 code. |

Each plugin carries its own `CHANGELOG.md` and is versioned independently.

> **`axoniq-migration` is best-effort.** It automates as much of the Axon Framework 4 → 5 upgrade as it reliably can, but it will not always upgrade everything: expect some leftover concerns (unusual patterns, edge cases, manual decisions) flagged for **you** to finish by hand. It upgrades code and configuration and prepares saga/workflow coexistence — it does not convert stored events, tokens, or serialized saga rows into workflow histories. Always review and test the result.

### Saga to workflow

[`saga-to-workflow`](./plugins/axoniq-migration/skills/saga-to-workflow/SKILL.md) derives workflows from existing saga behavior, ports behavioral tests, prepares coexistence for new workflows and draining sagas, and checks retirement. It includes adaptable Java helpers and fixture examples. Start after the AF5 legacy-saga and DCB prerequisites are ready; follow the [staged upgrade guide](https://docs.axoniq.io/axon-framework-reference/development/migration/) for the complete journey.

```bash
npx skills add AxonIQ/agent-skills --skill saga-to-workflow
```

[Skill README and process details](./plugins/axoniq-migration/skills/saga-to-workflow/README.md).

## Installation

Replace `<plugin>` below with one of `axoniq-migration`, `axoniq-app-development`, `axoniq-framework-contribution`, or `axoniq-platform`.

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

Installs skill folders directly for supported agents (skills are discovered under `plugins/*/skills/`). For example, to install all upgrade skills explicitly:

```bash
npx skills add AxonIQ/agent-skills                                               # interactive picker
npx skills add AxonIQ/agent-skills \
  --skill axon4to5-openrewrite axon4to5-migrate-code axon4to5-isolatedtest saga-to-workflow \
  -a <agent>                                                                     # all upgrade skills
npx skills add AxonIQ/agent-skills --skill axon4to5-openrewrite -a claude-code   # one skill + agent
```

Common `-a <agent>` values include `gemini-cli`, `cursor`, `codex`, `opencode`, and `claude-code`.

## Contributing

**Contributions are very welcome** — these skills get better the more people use them and report back. Found a hallucinated or wrong result, an upgrade gap, a missing recipe, or an idea for a new skill? Open an issue or a PR. Repository layout and how to add a plugin: see [DEVELOPMENT.md](./DEVELOPMENT.md).
