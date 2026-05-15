# Axoniq Agent Skills

Agent Skills to help developers using AI agents with Axon Framework.

All skills live in [`skills/`](./skills) at the repo root and follow the [agentskills.io](https://agentskills.io/) format. They can be consumed directly by any agent runtime that loads `SKILL.md` files, or installed as a Claude Code plugin (see below).

## Claude Code Plugin

This repository is also a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins-marketplaces). 

### Local usage

To load the plugin for a single Claude Code session without installing it, launch Claude with `--plugin-dir` pointing at the checkout root:

```bash
git clone --branch skills/monolith https://github.com/AxonIQ/agent-skills.git ~/GitRepos/path-to-agent-skills-repo
claude --plugin-dir ~/GitRepos/path-to-agent-skills-repo #run in your project that needs to be migrated
```
