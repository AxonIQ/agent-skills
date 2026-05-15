# INDEX.md entry templates

Each type directory under `.knowledge/repositories/` has its own
`INDEX.md`. It is a **short catalog** — not a detail dump — that:

1. Tells an AI agent how to use the index.
2. Lists every repo of that type with a one-line purpose, a link to the
   per-repo detail file, and a `Keywords:` line for fast scanning.
3. For `axon-examples` only: groups paired variants under a single app
   heading and includes a Migration Diff callout when both sides exist.

Before editing an existing `INDEX.md`, **read it first** to preserve order and
the established pattern.

## Standard AI-agent header (top of every INDEX.md)

Every `INDEX.md` opens with:

```markdown
# <Type Title>

**For AI Agents:** Use this index to quickly identify relevant repositories for your task. Scan the **Keywords** field to match your task requirements, then read the linked markdown file for comprehensive details about that repository.
```

Type titles:
- `axonframework` → `# Axon Framework References`
- `axon-examples` → `# Migrated Example Applications`
- `ai-bestpractices` → `# AI Best Practices References`

## `axonframework/INDEX.md` — entry template

One `##` heading per submodule. Append entries in the order they are added
unless an existing alphabetical/grouping pattern is already in place.

```markdown
## <RepoName>
[Details](axonframework_<RepoName>.md) — branch `<branch>` (or **Commit:** `<short-hash>`).
**Keywords:** <term>, <term>, <term>, <term>
<One-sentence purpose.>
```

Filled-in:

```markdown
## AxonFramework5
[Details](axonframework_AxonFramework5.md) — branch `feat/migration-skills`.
**Keywords:** axon 5, dynamic consistency boundary, reactive, migration target
Canonical source tree for Axon Framework 5; target of all migration skills.
```

## `axon-examples/INDEX.md` — entry template

One `##` heading per **application** (not per submodule). All variants for
that application — axon4, axon5, alternative axon5 strategies — nest under it
as bullets. The Migration Diff callout appears once per app, only when both
sides exist.

```markdown
## <app-name>
<One-line description of what this app demonstrates.>
**Keywords:** <term>, <term>, <term>

- **axon4:** [details](axon-examples_axon4_<app>.md) — branch `<branch>` · <Language> · <BuildTool>
- **axon5:** [details](axon-examples_axon5_<app>.md) — branch `<branch>` · <Language> · <BuildTool>
- **axon5 (<strategy-label>):** [details](axon-examples_axon5_<app>_<strategy>.md) — <one-line distinction> · <Language> · <BuildTool>

### Migration Diff (<app-name>)

**The difference between `axon4/<app>@<ref>` and `axon5/<app>@<ref>` IS the migration itself.**

\```bash
git -C .knowledge/repositories/axon-examples/axon4/<app> log -1 --oneline
git -C .knowledge/repositories/axon-examples/axon5/<app> log -1 --oneline
git diff <axon4-commit> <axon5-commit>
\```
```

Filled-in:

```markdown
## orderservice
Lightweight order service demonstrating CQRS basics and saga-style process management.
**Keywords:** orders, cqrs, event sourcing, vertical slice

- **axon4:** [details](axon-examples_axon4_orderservice.md) — branch `main` · Kotlin · Gradle
- **axon5:** [details](axon-examples_axon5_orderservice.md) — branch `feat/axon5` · Kotlin · Gradle
- **axon5 (alt):** [details](axon-examples_axon5_orderservice_alt.md) — Java/Maven rewrite for migration comparison · Java · Maven

### Migration Diff (orderservice)

**The difference between `axon4/orderservice@main` and `axon5/orderservice@feat/axon5` IS the migration itself.**

\```bash
git -C .knowledge/repositories/axon-examples/axon4/orderservice log -1 --oneline
git -C .knowledge/repositories/axon-examples/axon5/orderservice log -1 --oneline
git diff <axon4-commit> <axon5-commit>
\```
```

When only one side exists:

```markdown
## <app-name>
<One-line description.>
**Keywords:** <term>, <term>

- **axon4:** [details](axon-examples_axon4_<app>.md) — branch `<branch>` · <Language> · <BuildTool>
- **axon5:** _migration pending_
```

## `ai-bestpractices/INDEX.md` — entry template

```markdown
## <repo>
[Details](ai-bestpractices_<repo>.md) — <one-line purpose>.
**Keywords:** <term>, <term>, <term>
```

Filled-in:

```markdown
## anthropic-cookbook
[Details](ai-bestpractices_anthropic-cookbook.md) — Anthropic's reference cookbook for prompt patterns, tool use, and evaluation.
**Keywords:** prompt engineering, tool use, evaluation, agent loops
```

## Rules summary

- The AI-agent header is mandatory; never omit it when creating a new INDEX.
- The Migration Diff callout MUST be filled with real branches/commits. If
  the user hasn't provided them, the skill asks before writing the callout.
- `Keywords:` is mandatory on every entry. They should match the `keywords:`
  list in the corresponding per-repo file.
- For `axon-examples`, every variant bullet must show
  `branch/commit · <language> · <build_tool>` so a reader can pick the
  right variant without opening the detail file.
- The skill never writes detailed feature bullets, migration notes, or
  highlights into `INDEX.md`. Those live in the per-repo detail file.
