# .knowledge

Useful resources for developing and updating skills. This directory is **for contributors only** — end users who install the skills from the marketplace do not need any of this.

## Structure

```
.knowledge/
  docs/                       # Tracked markdown guides (skill-authoring best practices, etc.)
  repositories/               # Per-type catalog: INDEX.md + per-repo descriptor files
    axonframework/             # Axon Framework source trees
    axon-examples/             # Example applications (axon4 ↔ axon5 pairs)
    ai-bestpractices/          # External skill/agent best-practice references
  scripts/
    setup-repos.sh             # Fetch all reference repositories (run once after cloning)
```

The `repositories/` subdirectories contain:
- `INDEX.md` — scannable catalog with keywords, for AI agents to pick which repo to open
- `<type>_<name>.md` — per-repo detail files with frontmatter, key paths, and highlights

The actual repository source trees are **gitignored** and fetched separately (see below).

## Fetching reference repositories

Reference repositories (Axon Framework source, example apps, AI best-practice repos) live under `.knowledge/repositories/` but are not committed to this repo. Fetch them with:

```bash
bash .knowledge/scripts/setup-repos.sh
```

This shallow-clones every listed repository. The script locates the repo root automatically, so you can run it from anywhere. Re-run with `--update` to pull the latest commits:

```bash
bash .knowledge/scripts/setup-repos.sh --update
```

Each cloned repository has its push URL disabled (`DISABLED`) so no accidental push reaches upstream.

## Adding a reference repository

Use the `/knowledge-add-repository` skill in Claude Code. It clones the repository, writes the descriptor file and INDEX entry, and appends the clone command to `setup-repos.sh`. No `.gitignore` changes are needed; `.knowledge/repositories/` is ignored wholesale, so any new clone is ignored automatically.

## Reference repositories are read-only

All repositories under `.knowledge/repositories/` are fetched for reference only. The push URL is set to `DISABLED` on every clone to prevent accidental upstream pushes.

To update a repo to the latest on its branch, re-run:

```bash
bash .knowledge/scripts/setup-repos.sh --update
```

To discard local changes in a single repo:

```bash
git -C .knowledge/repositories/<type>/<name> fetch origin
git -C .knowledge/repositories/<type>/<name> reset --hard origin/<branch>
git -C .knowledge/repositories/<type>/<name> clean -fd
```
