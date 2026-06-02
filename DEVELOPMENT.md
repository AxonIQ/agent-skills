# Development

How this repository is structured and how to add plugins. For installation/usage, see [README.md](./README.md). For skill-authoring rules, see [CLAUDE.md](./CLAUDE.md).

## Repository layout

This repo is a multi-runtime plugin **marketplace** (`axoniq`) that can host many plugins. Each plugin owns its skills directly — there is no separate root skill pool and no sync step. The same plugin is published to three runtimes (Claude Code, Codex, Cursor) from one set of files; `npx skills` reads the skills directly too.

```
plugins/
  axon4to5/                         # one plugin = manifests + its own skills
    .claude-plugin/plugin.json      # Claude Code manifest
    .codex-plugin/plugin.json       # Codex manifest (skills: "./skills/")
    .cursor-plugin/plugin.json      # Cursor manifest (skills: "./skills/")
    skills/                         # canonical skills for this plugin
      axon4to5-openrewrite/SKILL.md
      axon4to5-migrate/SKILL.md
      axon4to5-isolatedtest/SKILL.md
.claude-plugin/marketplace.json     # Claude marketplace; one entry per plugin
.agents/plugins/marketplace.json    # Codex marketplace; one entry per plugin
.cursor-plugin/marketplace.json     # Cursor marketplace; one entry per plugin
```

Skills are **real files** (not symlinks): Codex and Cursor copy a plugin into a cache on install and do not follow cross-directory symlinks, so each plugin's `skills/` must contain real skill directories. Edit skills in place under `plugins/<plugin>/skills/`.

The three marketplace files all use marketplace name `axoniq` (human label "Axoniq Agent Skills"); each lists the same plugins, differing only in source-path syntax:

| Runtime | Marketplace file | Plugin source field |
| --- | --- | --- |
| Claude Code | `.claude-plugin/marketplace.json` | `"source": "./plugins/<plugin>"` |
| Codex | `.agents/plugins/marketplace.json` | `"source": { "source": "local", "path": "./plugins/<plugin>" }` |
| Cursor | `.cursor-plugin/marketplace.json` | `"source": "plugins/<plugin>"` |

The Claude plugin manifest needs no `skills` field (Claude auto-discovers `skills/` under the plugin root); Codex and Cursor declare `"skills": "./skills/"`.

## Adding a new plugin

1. `mkdir -p plugins/<plugin>/{.claude-plugin,.codex-plugin,.cursor-plugin,skills}`
2. Author the plugin's skills directly under `plugins/<plugin>/skills/<skill>/SKILL.md`.
3. Write the three manifests:
   - `.claude-plugin/plugin.json` — `name`, `description`, identity metadata (no `skills` field needed).
   - `.codex-plugin/plugin.json` — same identity + `"skills": "./skills/"` + an `interface` block (displayName, category, capabilities, defaultPrompt, …).
   - `.cursor-plugin/plugin.json` — same identity + `"skills": "./skills/"`.
4. Add one entry to each marketplace file (`name` + the runtime's source field from the table above).

For a single-runtime plugin, create only that runtime's manifest + marketplace entry.

> **Shared skills:** if two plugins need the same skill, copy it into each plugin's `skills/` (Codex/Cursor require real files and cannot reference another plugin's directory). Only introduce a shared pool + a copy/generate step if that sharing actually arises.

## Installing from a local checkout (development)

Add the checkout as a marketplace and install from it (this copies real skill files into the runtime's cache; `--plugin-dir` is not equivalent).

```bash
git clone https://github.com/AxonIQ/agent-skills.git ~/GitRepos/agent-skills
```

Claude Code:

```
/plugin marketplace add ~/GitRepos/agent-skills
/plugin install axon4to5@axoniq
/plugin marketplace update axoniq            # after editing skills
```

Codex:

```bash
codex plugin marketplace add ~/GitRepos/agent-skills
codex plugin add axon4to5@axoniq
codex plugin marketplace upgrade axoniq      # after editing skills
```

Smoke-test a Codex install in an isolated home before publishing:

```bash
tmp=$(mktemp -d)
CODEX_HOME="$tmp" codex plugin marketplace add .
CODEX_HOME="$tmp" codex plugin add axon4to5@axoniq
find "$tmp"/plugins/cache -name SKILL.md -print
rm -rf "$tmp"
```
