# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

All skills live in [`skills/`](./skills) at the repo root and follow the [agentskills.io](https://agentskills.io/) format. They can be consumed directly by any agent runtime that loads `SKILL.md` files, or installed as a Claude Code plugin (see below).

## Skills

- [`axon4to5-openrewrite`](./skills/axon4to5-openrewrite/SKILL.md) — Apply the Axon Framework 4 → 5 OpenRewrite bulk-migration recipe (Maven or Gradle, `axon` or `axoniq` variant).

## Claude Code Plugin

This repository is also a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins-marketplaces). Plugins are declared in `.claude-plugin/marketplace.json` and reference the skills they bundle — a single skill can be shipped by multiple plugins without duplication.

### Available plugins

- **`axon4to5-migration`** — Migrate applications from Axon Framework 4 to Axon Framework 5 / AxonIQ Framework 5. Includes the `axon4to5-openrewrite` skill.

  ```
  /axon4to5-migration:axon4to5-openrewrite --framework axon
  ```

### Installation

#### From the public Git URL (recommended)

In Claude Code:

```
/plugin marketplace add AxonIQ/agent-skills
/plugin install axon4to5-migration@axoniq-agent-skills
```

#### From a local clone

```bash
git clone https://github.com/AxonIQ/agent-skills.git ~/path/to/agent-skills
```

Then in Claude Code:

```
/plugin marketplace add ~/path/to/agent-skills
/plugin install axon4to5-migration@axoniq-agent-skills
```

#### Local development

When iterating on a skill in a clone of this repo, add the marketplace from the local path as above; `/plugin marketplace update axoniq-agent-skills` picks up changes.

### Verify

Run `/plugin` to see installed plugins and `/help` to see the slash commands they contribute.

## License

Apache-2.0
