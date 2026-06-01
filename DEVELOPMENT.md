# Development

How this repository is structured and how to add plugins. For installation/usage, see [README.md](./README.md). For skill-authoring rules, see [CLAUDE.md](./CLAUDE.md).

## Repository layout

This repo is both a skill pool and a Claude Code plugin **marketplace** that can host many plugins, each bundling a curated subset of the canonical skills.

```
skills/                          # canonical skill pool (single source of truth)
  axon4to5-openrewrite/SKILL.md
  axon4to5-migrate/SKILL.md
  axon4to5-isolatedtest/SKILL.md
.claude-plugin/
  marketplace.json               # lists all plugins; one entry per plugin
plugins/
  axon4to5/                      # a plugin = manifest + the skills it bundles
    .claude-plugin/plugin.json
    skills/                      # symlinks into ../../../skills/<name>
      axon4to5-openrewrite -> ../../../skills/axon4to5-openrewrite
      axon4to5-migrate     -> ../../../skills/axon4to5-migrate
      axon4to5-isolatedtest -> ../../../skills/axon4to5-isolatedtest
```

Each plugin's `skills/` contains **symlinks** into the root `skills/` pool, so skill content is never duplicated. When the marketplace is installed, Claude Code dereferences these symlinks and copies the real content into its cache ([docs](https://code.claude.com/docs/en/plugins-reference#share-files-within-a-marketplace-with-symlinks)). `npx skills` and agentskills.io read the root `skills/` directly and never touch the plugin layer.

## Adding a new plugin

1. `mkdir -p plugins/<plugin>/{.claude-plugin,skills}`
2. Write `plugins/<plugin>/.claude-plugin/plugin.json` (`name`, `description`, …).
3. Symlink the skills it bundles: `ln -s ../../../skills/<skill> plugins/<plugin>/skills/<skill>`
4. Add an entry to `.claude-plugin/marketplace.json` (`name` + `source: "./plugins/<plugin>"`).

> **Windows note:** the per-plugin `skills/` entries are git-tracked symlinks. They round-trip cleanly on macOS/Linux. On Windows, clone with symlink support enabled (`git config --global core.symlinks true` + Developer Mode), otherwise Git materializes them as plain text stubs and the bundled skills won't resolve.

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

> Use `marketplace add`, not `--plugin-dir`: the bundled skills are cross-directory symlinks that `--plugin-dir` does not resolve. `marketplace add` copies the real skill content into the plugin cache.
