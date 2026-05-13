# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

All skills live in [`skills/`](./skills) at the repo root and follow the [agentskills.io](https://agentskills.io/) format. They can be consumed directly by any agent runtime that loads `SKILL.md` files, or installed as a Claude Code plugin (see below).

## Skills

| Skill | Purpose | Invocation |
| --- | --- | --- |
| [`axon4to5-openrewrite`](./skills/axon4to5-openrewrite/SKILL.md) | Apply the Axon Framework 4 → 5 OpenRewrite bulk-migration recipe (Maven or Gradle, `axon` or `axoniq` variant). Idempotent. | User-invocable |
| [`axon4to5-isolatedtest`](./skills/axon4to5-isolatedtest/SKILL.md) | Internal helper. Scopes Maven/Gradle compile+test to ONE class via per-target profile or source-set. Invoked by other skills. | Internal only |

## Claude Code Plugin

This repository is also a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins-marketplaces). Plugins are declared in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) and reference the skills they bundle — a single skill can be shipped by multiple plugins without duplication.

### Available plugins

- **`axon4to5-migration`** — Bundles all the Axon 4→5 migration skills

  Once installed:

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

This installs from the default branch (`main`).

#### Ephemeral / one-shot session (no marketplace install)

To load the plugin for a single Claude Code session without installing it, launch Claude with `--plugin-dir` pointing at the checkout root:

```bash
git clone --branch skills/monolith https://github.com/AxonIQ/agent-skills.git ~/GitRepos/path-to-agent-skills-repo
claude --plugin-dir ~/GitRepos/path-to-agent-skills-repo #run in your repository
```

The plugin and all bundled skills are loaded for that session only — nothing is persisted to your Claude Code config. Repeat the flag (`--plugin-dir A --plugin-dir B`) to load multiple plugins.

#### Local development

When iterating on a skill in a clone of this repo, add the marketplace from the local path as above; `/plugin marketplace update axoniq-agent-skills` picks up changes. For a quick sanity check without touching your installed marketplaces, use `claude --plugin-dir ./` from the repo root.

### Verify

Run `/plugin` to see installed plugins and `/help` to see the slash commands they contribute. The bundled skills appear under the `axon4to5-migration:` namespace.

## License

Apache-2.0
