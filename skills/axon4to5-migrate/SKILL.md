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

## Modes

### `single`

Migrate ONE element (one aggregate, one handler, etc.) using exactly one recipe from the list above.

Steps:

1. Parse `mode` from `$ARGUMENTS`. If `mode != single` → STOP and report unsupported mode.
2. Match user's request + `source` to ONE recipe in the auto-listed set (by `name` + `description`). If ambiguous → ask
   user via `AskUserQuestion` to pick. If no match → STOP and report.
3. `Read` the chosen recipe file (`references/recipes/<name>.md`) and follow it exactly for the single source.
4. Verify behavior is preserved (no DCB, keep `AggregateBasedEventStorageEngine`, etc.).
5. Report: recipe used, files changed, follow-ups.

MUST NOT:

- Run multiple recipes in one invocation.
- Migrate more than the single source named by the user.
- Introduce DCB or swap event storage engine.

## Flow

Every mode ends up producing a **queue** of `(recipe, source)` items. A single processing loop drains it. What happens on empty queue depends on the mode.

```mermaid
flowchart TD
    A[Skill invoked] --> B["! list-recipes.sh<br/>(recipes catalog)"]
    B --> C{mode}

    %% mode-specific producers — all feed the same queue
    C -- single --> P1[Match request+source<br/>→ enqueue 1 item]
    C -- other --> X[STOP: unsupported mode]
    P1 --> Q[(Migration queue)]

    %% shared processing loop
    Q --> L{queue empty?}
    L -- no --> W[[Run recipe procedure<br/>see recipe sub-flow]]
    W --> R{recipe result}
    R -- Success --> REC[record: ✅]
    R -- Blocker --> REC2[record: ⚠ blocker]
    R -- Rejected --> REC3[record: ⏭ skipped]
    R -- Failure --> REC4[record: ❌ failure]
    REC --> Q
    REC2 --> Q
    REC3 --> Q
    REC4 --> Q
    L -- yes --> M{mode policy}

    %% empty-queue behavior per mode
    M -- single --> E[Report &amp; END]
```

> The `[[Run recipe procedure]]` node is a **nested sub-flow** defined inside each recipe's `Procedure` section. The orchestrator only reacts to its **result** (one of: `Success`, `Blocker`, `Rejected`, `Failure`) — it does not look inside.

### Result handling

| Result     | Orchestrator action                                            | `single` mode end-state |
|------------|----------------------------------------------------------------|-------------------------|
| `Success`  | Mark item done, continue draining queue                        | Report ✅                |
| `Blocker`  | Record unclear migration path (e.g. Deadlines), continue queue | Report ⚠ with reason    |
| `Rejected` | Recipe not applicable to this source, continue queue           | Report ⏭ with reason    |
| `Failure`  | Recipe applied but criteria still fail, continue queue         | Report ❌ with reason    |

Rule of thumb:

- `single` → enqueue exactly 1, process, END (report whichever result came back).

## Recipe contract

Every file in `references/recipes/` MUST follow `references/recipes/_template.md`. The template defines **what each phase means** (Detect / Early-exit / Plan / Apply / Verify); the orchestrator owns **how phases sequence and when results are emitted** — shown below.

### Recipe sub-flow (orchestrator-owned)

Step numbers below match the recipe's documented contract (and the template's `## Phase implementations` headings). Retry budget = **1**.

Step numbers below match the recipe's documented contract (and the template's `## Phase implementations` headings). Retry budget = **1**.

Step numbers below match the recipe's documented contract (and the template's `## Phase implementations` headings). Retry budget = **1**.

```mermaid
flowchart TD
    S(["Recipe invoked with &lt;Source&gt;"]) --> S1{"<b>1. Applicable?</b><br/>lightweight check on &lt;Source&gt;<br/>(annotations / type markers)<br/>recipe-defined rule"}
    S1 -- no --> RJ[/"RESULT: Rejected<br/>(not the right recipe)"/]
    S1 -- yes --> S2

    subgraph RESEARCH ["Research (loops until scope stabilizes)"]
        direction TB
        S2["<b>2. Define Scope</b><br/>initial inventory:<br/>&lt;Source&gt; + owned types<br/>(commands, events, members)"]
        S3["<b>3. Read References</b><br/>only sections matching<br/>constructs currently in scope<br/>(Migration Paths / Toolbox / Examples)"]
        SQ{"References reveal<br/>extra files / types<br/>that belong in scope?"}
        S2 --> S3 --> SQ
        SQ -- "yes (extend scope)" --> S2
    end

    SQ -- no --> S4{"<b>4. Blocker in scope?</b><br/>constructs with no Migration Path<br/>e.g. Deadlines,<br/>custom interceptors,<br/>ConflictResolver"}
    S4 -- yes --> BL[/"RESULT: Blocker<br/>NOTES: what was found + where"/]
    S4 -- "no (no edits yet)" --> S5

    S5["<b>5. Check Success Criteria</b><br/>compile &lt;Source&gt; + owned<br/>compile matching test if exists<br/>Skill: axon4to5-isolatedtest<br/>behavior invariants"]
    S5 --> S5Q{all green?}
    S5Q -- yes --> SC[/"RESULT: Success<br/>NOTES: edits=none (idempotent)<br/>or files changed + follow-ups"/]
    S5Q -- "no — never applied yet" --> S6
    S5Q -- "no — retry available<br/>(budget = 1)" --> CTX["<b>Consult Axon 5</b><br/>sources on classpath<br/>+ context7 MCP if available<br/>(extends References)"]
    CTX --> S6
    S5Q -- "no — retry exhausted" --> FL[/"RESULT: Failure<br/>NOTES: failing criteria<br/>+ last error verbatim"/]

    S6["<b>6. Build Migration Plan</b><br/>bullet list of concrete edits<br/>derived from References<br/>+ scope inventory"]
    S6 --> S7["<b>7. Apply Migration Plan</b><br/>edits within Scope only<br/>no drive-by refactors"]
    S7 -- "(edits applied)" --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

Notes:

- **Step 1 sits outside Research** — a cheap surface check on `<Source>` alone (annotations/type markers) to confirm the recipe is the right tool *before* paying the cost of cataloging scope and loading References.
- **Scope before References (inside Research)** — scope inventory drives *which* References sections are worth reading (avoids loading the whole playbook for every recipe run).
- **Research is a loop** — if References for a construct reveal that other files / types belong in scope (e.g. a snapshot trigger, a related event class), scope is extended and References re-consulted. Loop exits when scope stabilizes.
- **Step 5 is the single Success Criteria check** — visited at least once (pre-edit), and again after every Apply. The edge labels `(no edits yet)` and `(edits applied)` make the visit context explicit; the check logic is identical. Idempotent re-runs and post-migration verification share the same node.
- **Blocker fires only from step 4** — emitted after Research stabilizes; checks for constructs with no entry in the loaded Migration Paths. Steps 5–7 never short-circuit to Blocker; partial work either passes verification or counts as Failure.
- **Apply loop is `5 → 6 → 7 → 5`** — retry budget = 1 attempt; on the second red verdict after Apply, `CTX` is used to *extend* References before the next plan rebuild, not to re-apply verbatim.
- The recipe file fills in *what to do* inside each numbered step (`Applicable`, `Success Criteria`, `References`, `Migration Plan` builder). Sequencing and retry budget above are fixed by this skill.
