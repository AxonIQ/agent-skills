# Recipe sub-flow

The orchestrator-owned spec for executing any recipe in `references/recipes/`. Recipes never re-implement this — they fill in the named sections referenced from the diagram nodes (see `references/recipes/_template/RECIPE.md` for the authoring guide).

Retry budget = **1** additional Apply (≤ 2 Applies total). Each diagram node names the recipe section it consults using markdown header refs (`# Applicable`, `# Scope`, etc. — these map to top-level headings in the recipe file).

```mermaid
flowchart TD
    S(["Recipe invoked with $SOURCE"]) --> S1{"<b>Applicable?</b><br/>read $SOURCE surface per # Source<br/>(annotations / type markers)<br/>evaluate # Applicable rule<br/>(AND / OR / heuristic)"}
    S1 -- no --> RJ[/"RESULT: Rejected<br/>NOTES: which predicate failed"/]
    S1 -- yes --> S2

    subgraph RESEARCH ["Research (loops until scope stabilizes)"]
        direction TB
        S2["<b>Define Scope</b><br/>enumerate per # Scope<br/>on re-entry: add, never shrink"]
        S3["<b>Read References</b><br/>load # References sections<br/>whose apply-condition<br/>matches current scope"]
        SQ{"References reveal<br/>extra files / types<br/>belonging in scope?"}
        S2 --> S3 --> SQ
        SQ -- "yes (extend scope)" --> S2
    end

    SQ -- no --> S4{"<b>Blocker present?</b><br/>per # Blocker:<br/>scope item declared unmigrateable<br/>OR unmet project prerequisite<br/>(caller must resolve, recipe halts)"}
    S4 -- yes --> BL[/"RESULT: Blocker<br/>NOTES: construct + location<br/>or unmet prerequisite"/]
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
        S6["<b>Plan Migration</b><br/>(re)compute the plan each visit<br/>using # References + # Toolbox + # Examples + scope<br/>consult # Gotchas for past learnings<br/>edits sufficient to flip every<br/>mismatched criterion → match"]
        S7["<b>Apply Migration Plan</b><br/>execute edits within scope only<br/>respect # Out of Scope<br/>no drive-by refactors"]
        S6 --> S7
    end
    S7 -- "(edits applied)" --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

## Result

Each recipe completes by returning **exactly one** result block.
The orchestrator reads the `RESULT:` line to control the flow.

```
RESULT: <Success|Blocker|Rejected|Failure>
SOURCE: $SOURCE
RECIPE: axon4to5-<component>
NOTES: <one short paragraph — why this result, what to look at next>
```

**NOTES content:** baseline per-outcome guidance is defined in `references/recipes/DEFAULT.md` (§ Result NOTES baselines) and always applies. Recipes may augment via their own `# Result` subsections when they have recipe-specific facts to record; they cannot override the baseline.

### Example — Success

```
RESULT: Success
SOURCE: com.example.order.OrderAggregate
RECIPE: axon4to5-aggregate
NOTES: 3 files changed (OrderAggregate.java, OrderAggregateTest.java, OrderCommandHandler.java); Success Criteria all match; isolated test passed.
```

### Example — Blocker

```
RESULT: Blocker
SOURCE: com.example.order.OrderAggregate
RECIPE: axon4to5-aggregate
NOTES: @Deadline handler at OrderAggregate.java:142 — Deadlines API not yet stable in Axon 5; caller must resolve before re-running.
```

### Example — Rejected

```
RESULT: Rejected
SOURCE: com.example.order.OrderProjection
RECIPE: axon4to5-aggregate
NOTES: Applicable predicate failed — class is annotated with @ProcessingGroup, not @Aggregate; this is a projection, not an aggregate.
```

### Example — Failure

```
RESULT: Failure
SOURCE: com.example.order.OrderAggregate
RECIPE: axon4to5-aggregate
NOTES: Retry budget exhausted (2 Applies). Failing Success Criterion: isolated test. Last error: "EventSourcingHandler not invoked for OrderCreatedEvent; expected aggregate state=CREATED, was=null".
```

## Invariants

- **Applicable check sits outside Research** — cheap surface check on `$SOURCE` alone; don't pay the Research cost for the wrong recipe.
- **Scope before References** (inside Research) — `scope` drives *which* `references` sections are read.
- **Research is a fixed-point loop** — exits only when SQ says "no new in-scope items"; `scope` can only grow.
- **Single Check Success Criteria** — same evaluation logic pre- and post-Apply; the diamond branches on whether retry budget remains.
- **Blocker fires only from `Blocker in scope?`** — emitted after Research stabilizes. Check / Plan / Apply never short-circuit to Blocker; partial work either passes the Check or counts as Failure.
- **Apply loop is `Check → Plan → Apply → Check`** — only Apply consumes the retry budget. Adjust activities (re-research, source consultation) are *free*.
- **Adjust is open-ended** — on retry the AI picks any subset of: extend scope, consult Axon 5 sources / context7, rethink the approach. Plan Migration is rebuilt each iteration using whatever new info Adjust gathered.
- **Recipe owns content; orchestrator owns control flow.** A recipe never decides "retry" or "skip a step" — it only fills the named sections referenced from the diagram nodes.
