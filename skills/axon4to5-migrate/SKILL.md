---
name: axon4to5-migrate
description: >-
  Migrate Axon Framework 4 project to Axon Framework 5 — preserves behavior (do not introduce DCB, keep AggregateBasedEventStorageEngine etc).
argument-hint: "mode=<single> [source=<class|file|fqn>]"
allowed-tools: Bash(./scripts/list-recipes.sh)
disable-model-invocation: true
---

# axon4to5-migrate

## Available recipes (auto-listed)

!`./scripts/list-recipes.sh`

## Inputs

- `mode` (required): currently only `single`.
- `source` (optional, mode=single): user-supplied hint identifying the thing to migrate (class name, file path, FQN).

`$SOURCE` is referenced throughout the recipe sub-flow as the argument passed in from `source`.

## Modes

### `single`

Migrate ONE element (one aggregate, one handler, etc.) using exactly one recipe from the list above.

Steps:

1. Parse `mode` from `$ARGUMENTS`. If `mode != single` → STOP and report unsupported mode.
2. Match user's request + `source` to ONE recipe in the auto-listed set (by `name` + `description`). If ambiguous → ask user via `AskUserQuestion` to pick. If no match → STOP and report.
3. `Read` the chosen recipe file (`references/recipes/<name>.md`) and execute it per the **Recipe sub-flow** below.
4. Verify behavior is preserved (no DCB, keep `AggregateBasedEventStorageEngine`, etc.).
5. Report: recipe used, files changed, follow-ups.

MUST NOT:

- Run multiple recipes in one invocation.
- Migrate more than the single source named by the user.
- Introduce DCB or swap event storage engine.

## Queue flow

Every mode produces a **queue** of `(recipe, source)` items. A single processing loop drains it. What happens on empty queue depends on the mode.

```mermaid
flowchart TD
    A[Skill invoked] --> B["! list-recipes.sh<br/>(recipes catalog)"]
    B --> C{mode}

    %% mode-specific producers — all feed the same queue
    C -- single --> P1["Match request+source<br/>→ enqueue 1 item"]
    C -- other --> X[STOP: unsupported mode]
    P1 --> Q[(Migration queue)]

    %% shared processing loop
    Q --> L{queue empty?}
    L -- no --> W[[Run recipe sub-flow]]
    W --> R{recipe result}
    R -- Success --> REC["record: ✅"]
    R -- Blocker --> REC2["record: ⚠ blocker"]
    R -- Rejected --> REC3["record: ⏭ skipped"]
    R -- Failure --> REC4["record: ❌ failure"]
    REC --> Q
    REC2 --> Q
    REC3 --> Q
    REC4 --> Q
    L -- yes --> M{mode policy}

    %% empty-queue behavior per mode
    M -- single --> E["Report &amp; END"]
```

> The `[[Run recipe sub-flow]]` node is the **nested** sub-flow defined below. The queue only reacts to the recipe's emitted result.

### Queue-level result handling

| Result     | Queue action                | `single` mode end-state |
|------------|-----------------------------|-------------------------|
| `Success`  | mark item done, drain next  | Report ✅                |
| `Blocker`  | record + drain next         | Report ⚠ with reason    |
| `Rejected` | record + drain next         | Report ⏭ with reason    |
| `Failure`  | record + drain next         | Report ❌ with reason    |

Rule of thumb:

- `single` → enqueue exactly 1, process, END (report whichever result came back).

## Recipe sub-flow

The orchestrator-owned spec for executing any recipe in `references/recipes/`. Recipes never re-implement this — they fill in the named sections referenced from the diagram nodes (see `references/recipes/_template.md` for the authoring guide).

Retry budget = **1** additional Apply (≤ 2 Applies total). Each diagram node names the recipe section it consults using markdown header refs (`# Applicable`, `# Scope`, etc. — these map to top-level headings in the recipe file).

```mermaid
flowchart TD
    S(["Recipe invoked with $SOURCE"]) --> S1{"<b>Applicable?</b><br/>read $SOURCE surface only<br/>(annotations / type markers)<br/>evaluate # Applicable rule<br/>(AND / OR / heuristic)"}
    S1 -- no --> RJ[/"RESULT: Rejected<br/>NOTES: which predicate failed"/]
    S1 -- yes --> S2

    subgraph RESEARCH ["Research (loops until scope stabilizes)"]
        direction TB
        S2["<b>Define Scope</b><br/>enumerate per # Scope<br/>on re-entry: add, never shrink"]
        S3["<b>Read References</b><br/>load # References sections<br/>whose read-condition<br/>matches current scope"]
        SQ{"References reveal<br/>extra files / types<br/>belonging in scope?"}
        S2 --> S3 --> SQ
        SQ -- "yes (extend scope)" --> S2
    end

    SQ -- no --> S4{"<b>Blocker in scope?</b><br/>scope item the recipe<br/>declares as unmigrateable<br/>per # Blocker<br/>(no migration path, too complex,<br/>recipe-specific exclusions)"}
    S4 -- yes --> BL[/"RESULT: Blocker<br/>NOTES: construct + location"/]
    S4 -- "no (no edits yet)" --> S5

    S5["<b>Check Success Criteria</b><br/>evaluate # Success Criteria<br/>using recipe's aggregation rule<br/>(all / subset / weighted)"]
    S5 --> S5Q{"<b>Success Criteria met?</b><br/>retry budget = 1<br/>(max 2 Apply attempts)"}
    S5Q -- "match" --> SC[/"RESULT: Success<br/>NOTES: edits=none (idempotent)<br/>or files changed + follow-ups"/]
    S5Q -- "mismatch, first attempt" --> S6
    S5Q -- "mismatch, retry available" --> ADJ["<b>Adjust before re-Apply</b><br/>(AI decides; any subset)<br/>• extend scope — re-research # Scope<br/>• consult Axon 5 sources (classpath)<br/>&nbsp;&nbsp;+ context7 MCP if available<br/>• rethink approach with new info"]
    S5Q -- "mismatch, budget exhausted" --> FL[/"RESULT: Failure<br/>NOTES: failing criteria<br/>+ last error verbatim"/]

    ADJ --> S6

    subgraph PLAN_APPLY ["Plan-Apply (re-entered per iteration)"]
        direction TB
        S6["<b>Plan Migration</b><br/>(re)compute the plan each visit<br/>using # References + # Toolbox + scope<br/>consult # Gotchas for past learnings<br/>edits sufficient to flip every<br/>mismatched criterion → match"]
        S7["<b>Apply Migration Plan</b><br/>execute edits within scope only<br/>respect # Out of Scope<br/>no drive-by refactors"]
        S6 --> S7
    end
    S7 -- "(edits applied)" --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

### Result emission

Each recipe completes by emitting **exactly one** result block. The orchestrator parses the `RESULT:` line; the rest is human-readable context.

```
RESULT: <Success|Blocker|Rejected|Failure>
SOURCE: $SOURCE
RECIPE: axon4to5-<component>
FILES_CHANGED: [<path>, ...]
NOTES: <one short paragraph — why this result, what to look at next>
```

### Invariants

- **Applicable check sits outside Research** — cheap surface check on `$SOURCE` alone; don't pay the Research cost for the wrong recipe.
- **Scope before References** (inside Research) — `scope` drives *which* `references` sections are read.
- **Research is a fixed-point loop** — exits only when SQ says "no new in-scope items"; `scope` can only grow.
- **Single Check Success Criteria** — same evaluation logic pre- and post-Apply; the diamond branches on whether retry budget remains.
- **Blocker fires only from `Blocker in scope?`** — emitted after Research stabilizes. Check / Plan / Apply never short-circuit to Blocker; partial work either passes the Check or counts as Failure.
- **Apply loop is `Check → Plan → Apply → Check`** — only Apply consumes the retry budget. Adjust activities (re-research, source consultation) are *free*.
- **Adjust is open-ended** — on retry the AI picks any subset of: extend scope, consult Axon 5 sources / context7, rethink the approach. Plan Migration is rebuilt each iteration using whatever new info Adjust gathered.
- **Recipe owns content; orchestrator owns control flow.** A recipe never decides "retry" or "skip a step" — it only fills the named sections referenced from the diagram nodes.