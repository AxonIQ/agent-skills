# Development

How this repository is structured and how to add plugins. For installation/usage, see [README.md](./README.md). For skill-authoring rules, see [CLAUDE.md](./CLAUDE.md).

## Repository layout

This repo is both a skill pool and a Claude Code / Codex plugin **marketplace** that can host many plugins, each bundling a curated subset of the canonical skills.

```
skills/                          # canonical skill pool (single source of truth)
  axon4to5-openrewrite/SKILL.md
  axon4to5-migrate/SKILL.md
  axon4to5-isolatedtest/SKILL.md
.claude-plugin/
  marketplace.json               # lists all plugins; one entry per plugin
.agents/plugins/
  marketplace.json               # Codex marketplace; one entry per plugin
plugins/
  axon4to5/                      # a plugin = manifest + the skills it bundles
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills.txt                   # canonical list of root skills bundled by this plugin
    skills/                      # materialized from ../../../skills/<name>
      axon4to5-openrewrite/
      axon4to5-migrate/
      axon4to5-isolatedtest/
```

Root `skills/` is the authoring source of truth. Each plugin's `skills/` is a materialized bundle generated from the names in `plugins/<plugin>/skills.txt`:

```bash
scripts/sync-plugin-skills.sh axon4to5
scripts/sync-plugin-skills.sh --all
```

Do not edit files under `plugins/<plugin>/skills/` directly. Edit `skills/<skill>/...`, then re-run the sync script.

Claude Code can install from symlinked plugin skills, but Codex currently installs the plugin into a cache and does not preserve cross-directory skill symlinks there. For that reason, committed plugin bundles contain real copied skill directories while root `skills/` remains canonical. `npx skills` and agentskills.io read the root `skills/` directly and never touch the plugin layer.

## Codex multi-plugin model

Yes, one repository can host many Codex plugins while keeping skill authoring in the root `skills/` pool. The Codex marketplace file has a `plugins[]` array, and each entry points at one `plugins/<plugin>` directory. Each plugin still needs its own `.codex-plugin/plugin.json` and a plugin-local `skills/` directory. Do not point `plugin.json` directly at `../../skills`; Codex expects the manifest skill path to resolve to `skills`, and install caches must contain real skill files.

## Adding a new plugin

1. `mkdir -p plugins/<plugin>/{.claude-plugin,skills}`
2. If the plugin supports Codex too, also create `plugins/<plugin>/.codex-plugin/`.
3. Write `plugins/<plugin>/.claude-plugin/plugin.json` (`name`, `description`, …).
4. Write `plugins/<plugin>/.codex-plugin/plugin.json` with `skills: "./skills/"` plus Codex interface metadata.
5. List bundled root skills in `plugins/<plugin>/skills.txt`, one skill name per line.
6. Materialize the plugin bundle: `scripts/sync-plugin-skills.sh <plugin>`.
7. Add an entry to `.claude-plugin/marketplace.json` (`name` + `source: "./plugins/<plugin>"`).
8. Add an entry to `.agents/plugins/marketplace.json` (`name` + `source.path: "./plugins/<plugin>"`).

For Claude-only plugins, skip the Codex manifest and Codex marketplace entry. For Codex-only plugins, skip the Claude manifest and Claude marketplace entry.

> **Sync note:** run `scripts/sync-plugin-skills.sh <plugin>` after editing any root skill that is bundled by a plugin. The plugin-local copy is intentionally checked in so Codex installs contain real skill files.

## Installing from a local checkout (development)

To test local, uncommitted changes, add the checkout as a marketplace and install from it:

```bash
git clone https://github.com/AxonIQ/agent-skills.git ~/GitRepos/agent-skills
```
```
/plugin marketplace add ~/GitRepos/agent-skills
/plugin install axon4to5@axoniq-agent-skills
/plugin marketplace update axoniq-agent-skills   # after editing skills
```

> Use `marketplace add`, not `--plugin-dir`, so marketplace metadata and plugin bundles are tested together.

For Codex:

```bash
codex plugin marketplace add ~/GitRepos/agent-skills
codex plugin add axon4to5@axoniq-agent-skills
codex plugin marketplace upgrade axoniq-agent-skills   # after editing skills
```

Smoke-test a Codex plugin install before publishing:

```bash
tmp=$(mktemp -d)
CODEX_HOME="$tmp" codex plugin marketplace add .
CODEX_HOME="$tmp" codex plugin add axon4to5@axoniq-agent-skills
find "$tmp/plugins/cache/axoniq-agent-skills/axon4to5/0.1.0/skills" -name SKILL.md -print
rm -rf "$tmp"
```

The local plugin-creator validator is stricter than `codex plugin add`: it rejects `disable-model-invocation: true`. Keep that flag only when the skill is intentionally hidden from automatic model invocation.
