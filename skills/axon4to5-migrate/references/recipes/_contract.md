# Recipe execution contract

The **orchestrator-owned** spec for executing any recipe in `references/recipes/`. Defines sub-flow, state, retry, and result emission. Recipes never re-implement this — they fill in the named sections referenced in the diagram below (see `_template.md`).

`$SOURCE` = the recipe argument (FQN / file path of the thing to migrate). Retry budget = **1** additional Apply (≤ 2 Applies total).

## Sub-flow

Each node names the recipe section it consults using markdown header refs (# Applicable, # Scope, etc. — these map to top-level headings in the recipe file).

```mermaid
flowchart TD
    S(["Recipe invoked with $SOURCE"]) --> S1{"<b>1. Applicable?</b><br/>read $SOURCE surface only<br/>(annotations / type markers)<br/>evaluate # Applicable rule<br/>(AND / OR / heuristic)"}
    S1 -- no --> RJ[/"RESULT: Rejected<br/>NOTES: which predicate failed"/]
    S1 -- yes --> S2

    subgraph RESEARCH ["Research (loops until scope stabilizes)"]
        direction TB
        S2["<b>2. Define Scope</b><br/>enumerate per # Scope<br/>on re-entry: add, never shrink"]
        S3["<b>3. Read References</b><br/>load # References sections<br/>whose read-condition<br/>matches current scope"]
        SQ{"References reveal<br/>extra files / types<br/>belonging in scope?"}
        S2 --> S3 --> SQ
        SQ -- "yes (extend scope)" --> S2
    end

    SQ -- no --> S4{"<b>4. Blocker in scope?</b><br/>scope item with no Migration Path<br/>or matching # Gotchas<br/>(Deadlines, interceptors,<br/>ConflictResolver, …)"}
    S4 -- yes --> BL[/"RESULT: Blocker<br/>NOTES: construct + location"/]
    S4 -- "no (no edits yet)" --> S5

    S5["<b>5. Check Success Criteria</b><br/>evaluate # Success Criteria<br/>using recipe's aggregation rule<br/>(all / subset / weighted)"]
    S5 --> S5Q{"<b>Success Criteria met?</b><br/>retry budget = 1<br/>(max 2 Apply attempts)"}
    S5Q -- "match" --> SC[/"RESULT: Success<br/>NOTES: edits=none (idempotent)<br/>or files changed + follow-ups"/]
    S5Q -- "mismatch, first attempt" --> S6
    S5Q -- "mismatch, retry available" --> ADJ["<b>Adjust before re-Apply</b><br/>(AI decides; any subset)<br/>• extend scope — re-research # Scope<br/>• consult Axon 5 sources (classpath)<br/>&nbsp;&nbsp;+ context7 MCP if available<br/>• rethink approach with new info"]
    S5Q -- "mismatch, budget exhausted" --> FL[/"RESULT: Failure<br/>NOTES: failing criteria<br/>+ last error verbatim"/]

    ADJ --> S6

    subgraph PLAN_APPLY ["Plan-Apply (re-entered per iteration)"]
        direction TB
        S6["<b>6. Plan Migration</b><br/>(re)compute the plan each visit<br/>using # References + # Toolbox + scope<br/>edits sufficient to flip every<br/>mismatched criterion → match"]
        S7["<b>7. Apply Migration Plan</b><br/>execute edits within scope only<br/>respect # Out of Scope<br/>no drive-by refactors"]
        S6 --> S7
    end
    S7 -- "(edits applied)" --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

## Orchestrator state

The orchestrator tracks the following state across steps. The recipe never tracks state — it only provides decision logic and content.

| Variable | Type | Initialized | Mutated by | Purpose |
|----------|------|-------------|------------|---------|
| `$SOURCE` | string | invocation | — | argument passed to the recipe (FQN / file path) |
| `applicable` | bool | step 1 | — | gate for entering Research |
| `scope` | set&lt;path/type&gt; | step 2 | step 2 (loop) | inventory of files/types in scope |
| `references` | set&lt;ref section&gt; | step 3 | step 3 (loop), CTX | playbook sections currently loaded |
| `criteria_state` | match / mismatch | step 5 | step 5 | last check result |
| `apply_count` | 0..2 | 0 | step 7 | bounds retry; budget = 1 retry ⇒ max 2 Applies |

Apply consumes the retry budget; **scope extension and CTX do not** — only the next Apply does.

## Result emission

Each recipe completes by emitting **exactly one** result block. The orchestrator parses the `RESULT:` line; the rest is human-readable context.

```
RESULT: <Success|Blocker|Rejected|Failure>
SOURCE: $SOURCE
RECIPE: axon4to5-<component>
FILES_CHANGED: [<path>, ...]
NOTES: <one short paragraph — why this result, what to look at next>
```

## Invariants

- **Step 1 sits outside Research** — cheap surface check on `$SOURCE` alone; don't pay the Research cost for the wrong recipe.
- **Scope before References** (inside Research) — `scope` drives *which* `references` sections are read.
- **Research is a fixed-point loop** — exits only when SQ says "no new in-scope items"; `scope` can only grow.
- **Step 5 is the single check** — same evaluation logic pre- and post-Apply; visit context is encoded in `apply_count`.
- **Blocker fires only from step 4** — emitted after Research stabilizes. Steps 5–7 never short-circuit to Blocker; partial work either passes step 5 or counts as Failure.
- **Apply loop is `5 → 6 → 7 → 5`** with retry budget on `apply_count`. Re-Research (step 2 re-entry) and CTX are *free* (no budget); only Apply consumes.
- **Two retry routes converge at step 7**:
  - `scope_incomplete` → re-enter step 2; Research extends scope; eventually re-Apply.
  - `knowledge_gap` → CTX → step 6 → re-Apply.
- **Recipe owns content; orchestrator owns control flow.** A recipe never decides "retry" or "skip a step" — it only fills the named sections referenced from the diagram nodes.
