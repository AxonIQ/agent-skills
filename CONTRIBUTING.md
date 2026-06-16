# Contributing

This guide is for **skill contributors** — people developing, updating, or adding skills to this repository. If you just want to install and use the skills, see [README.md](README.md).

## Prerequisites

- Git
- [Claude Code](https://claude.ai/code) CLI (for live skill testing)
- Node.js (for `npx skills` testing)

## Setting up a development checkout

```bash
git clone https://github.com/AxonIQ/agent-skills.git
cd agent-skills
```

The repository contains no submodules, so a plain `git clone` is all you need.

## Knowledge repositories (optional)

Skills that deal with migration or framework contribution read reference source trees (Axon Framework, example applications, AI best-practice repos). These are **not needed to install or run skills** — only to develop skills that rely on browsing that source code.

To fetch them:

```bash
bash .knowledge/scripts/setup-repos.sh
```

This shallow-clones all reference repositories into `.knowledge/repositories/`. The script locates the repo root automatically, so you can run it from anywhere. The directories are gitignored and live only on your machine.

To pull the latest commits on every repository's tracked branch:

```bash
bash .knowledge/scripts/setup-repos.sh --update
```

## Repository layout

See [DEVELOPMENT.md](DEVELOPMENT.md) for a full description of the plugin structure, how to add a new plugin, and versioning and changelog rules.

## Developing skills

Skills live under `plugins/<plugin>/skills/<skill>/SKILL.md`. Edit them in place — there is no build or sync step.

To test a skill locally in Claude Code:

```
/plugin marketplace add <path-to-this-checkout>
/plugin install axoniq-migration@axoniq
```

After editing a skill, reload it:

```
/plugin marketplace update axoniq
```

To test with Codex:

```bash
codex plugin marketplace add <path-to-this-checkout>
codex plugin add axoniq-migration@axoniq
```

## Adding a knowledge repository

Use the `/knowledge-add-repository` skill in Claude Code. It clones the repository, writes descriptor and INDEX files, and appends the clone command to `setup-repos.sh` — all in one step. No `.gitignore` changes are needed; `.knowledge/repositories/` is ignored wholesale, so any new clone is ignored automatically.

## Versioning

Each plugin is versioned independently. When you change a skill, bump the `version` in all three manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`) and add a matching entry to `plugins/<plugin>/CHANGELOG.md`. See [DEVELOPMENT.md](DEVELOPMENT.md#versioning-and-changelogs) for details.
