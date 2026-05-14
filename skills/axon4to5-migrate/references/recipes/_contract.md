# Recipe execution contract

The **orchestrator-owned** specification for executing any recipe in `references/recipes/`. Recipes never re-implement this — they fill in the `§ Section`s that nodes in the diagram bind to (see `_template.md`).

**The sub-flow diagram below is the source of truth.** Every function lives there exactly once, carrying its full signature, recipe-section binding, and one-line behavior — read it as the interface. The TS blocks above and below the diagram only define the *types* it references and the *durable state* it threads.

Retry budget = **1** additional `applyMigrationPlan` call (≤ 2 Applies total).

## Types

```ts
type Source     = string;                           // FQN or file path; from skill invocation
type FilePath   = string;
type FQN        = string;
type Scope      = Set<FilePath | FQN>;              // monotonic — only grows during Research
type References = {                                 // subset of recipe playbook currently loaded
  migrationPaths: Section[];                        // from § readReferences → Migration Paths
  toolbox:        Section[];                        // from § readReferences → Toolbox
  examples:       Section[];                        // from § readReferences → Examples
};
type FailureOutput = {
  failedCheck: 'compile' | 'isolatedtest' | 'invariant';
  stderr:      string;                              // raw tool output, used by classifyFailure
};
type CheckResult = { state: 'green' } | { state: 'red'; output: FailureOutput };
type Plan = Edit[];                                 // ordered; sufficient to flip all red → green
type Edit = { path: FilePath; description: string };
type FailureCause = 'scope_incomplete' | 'knowledge_gap';
type Result = 'Rejected' | 'Blocker' | 'Success' | 'Failure';
```

## Sub-flow

```mermaid
flowchart TD
    S(["recipe(source: Source)"]) --> S1

    S1["<b>isApplicable(source) → boolean</b><br/>§ isApplicable · surface check on <code>source</code> alone (annotations, type markers); outside Research"]
    S1 -- false --> RJ[/"Rejected"/]
    S1 -- true --> S2

    subgraph RESEARCH ["Research · fixed-point loop · scope grows monotonically, never shrinks"]
        direction TB
        S2["<b>defineScope(source, prev?) → Scope</b><br/>§ defineScope · enumerates source + owned types; re-entry only adds revealed items"]
        S3["<b>readReferences(scope) → References</b><br/>§ readReferences · loads only entries whose read-condition matches a construct in scope"]
        SQ["<b>referencesRevealMore(scope, refs) → boolean</b><br/>implicit · inspects loaded refs for in-scope candidates not yet in scope"]
        S2 --> S3 --> SQ
        SQ -- "true · free re-entry" --> S2
    end

    SQ -- false --> S4

    S4["<b>hasBlocker(scope, refs) → boolean</b><br/>§ hasBlocker (known blockers) + missing entry in § readReferences → Migration Paths"]
    S4 -- true --> BL[/"Blocker"/]
    S4 -- false --> S5

    S5["<b>checkSuccessCriteria(scope) → CheckResult</b><br/>§ checkSuccessCriteria · compile + axon4to5-isolatedtest + invariants; same body pre/post-Apply"]
    S5 -- green --> SC[/"Success"/]
    S5 -- "red · applyCount = 0" --> S6
    S5 -- "red · applyCount = 1" --> RC
    S5 -- "red · applyCount = 2" --> FL[/"Failure"/]

    RC["<b>classifyFailure(lastFailure) → FailureCause</b><br/>generic · unknown symbol / untouched related file ⇒ scope_incomplete; Axon 5 API misuse ⇒ knowledge_gap"]
    RC -- scope_incomplete --> S2
    RC -- knowledge_gap --> CTX

    CTX["<b>consultAxon5(lastFailure, refs) → References</b><br/>free · Axon 5 classpath + context7 MCP; extends refs in place"]
    CTX --> S6

    S6["<b>buildMigrationPlan(scope, refs) → Plan</b><br/>reuses § readReferences → Migration Paths + Toolbox · ordered edits, no mutations yet"]
    S6 --> S7

    S7["<b>applyMigrationPlan(plan) → Edit[]</b><br/>§ applyMigrationPlan · negative constraints; edits within scope only, refuses drive-by refactors · applyCount++"]
    S7 --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

## Orchestrator state

Execution is **durable**: state survives across function invocations and process boundaries, so any node can resume from the last persisted value. *How* the orchestrator persists this state (in-memory, file, DB, event log, …) is out of scope for this contract — recipes only see the shape.

```ts
interface State {
  source:      Source;                   // from skill arg; immutable
  scope:       Scope;                    // grows via defineScope (free re-entry)
  references:  References;               // extended by readReferences + consultAxon5 (free)
  applyCount:  0 | 1 | 2;                // bounds retry — only applyMigrationPlan increments
  lastFailure: FailureOutput | null;     // set by checkSuccessCriteria on red
}
```

Retry budget lives entirely in `applyCount`. `defineScope` re-entry and `consultAxon5` are free.

## Return values

The graph terminates at one of four parallelogram nodes. Each emits the same block; only `RESULT:` differs.

```yaml
RESULT:        Success | Blocker | Rejected | Failure
SOURCE:        <fully qualified name or path of source>
RECIPE:        axon4to5-<component>
FILES_CHANGED: [<path>, ...]
NOTES:         <one short paragraph — why this result, what to look at next>
```

The orchestrator parses the `RESULT:` line; the rest is human-readable context.

| Terminal      | Fired by                                              |
|---------------|-------------------------------------------------------|
| `Rejected`    | `isApplicable` → false                                |
| `Blocker`     | `hasBlocker` → true                                   |
| `Success`     | `checkSuccessCriteria` → green                        |
| `Failure`     | `checkSuccessCriteria` → red, `applyCount === 2`      |

## Invariants

- **`isApplicable` sits outside Research** — cheap surface check on `source` alone; don't pay the Research cost for the wrong recipe.
- **Scope before References** (inside Research) — `scope` drives *which* sections `readReferences` loads.
- **Research is a fixed-point loop** — exits only when `referencesRevealMore` returns false; `scope` is monotonically increasing.
- **`checkSuccessCriteria` is the single check** — same body pre- and post-Apply; visit context is encoded in `applyCount`.
- **`Blocker` fires only from `hasBlocker`** — emitted after Research stabilizes. Downstream functions never short-circuit to `Blocker`; partial work either passes `checkSuccessCriteria` or counts as `Failure`.
- **Apply loop is `checkSuccessCriteria → buildMigrationPlan → applyMigrationPlan → checkSuccessCriteria`** with retry budget on `applyCount`. `defineScope` re-entry and `consultAxon5` are free.
- **Two retry routes converge at `applyMigrationPlan`**:
  - `scope_incomplete` → `defineScope` extends scope, Research re-stabilizes, eventually re-Apply.
  - `knowledge_gap` → `consultAxon5` extends references, straight to `buildMigrationPlan`, then re-Apply.
- **Recipe owns content; orchestrator owns control flow.** A recipe never decides "retry" or "skip a function" — it only fills the `§` sections bound in the diagram nodes.
