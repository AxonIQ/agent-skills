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
        S6["<b>Plan Migration</b><br/>(re)compute the plan each visit<br/>using # References + # Toolbox + # Use cases + scope<br/>(# Use cases = full before/after transformations,<br/>loaded when their apply-condition matches)<br/>consult # Gotchas for past learnings<br/>edits sufficient to flip every<br/>mismatched criterion → match"]
        S7["<b>Apply Migration Plan</b><br/>execute edits within scope only<br/>respect # Out of Scope<br/>no drive-by refactors"]
        S6 --> S7
    end
    S7 -- "(edits applied)" --> S5

    classDef result fill:#eef,stroke:#557,stroke-width:1px;
    class RJ,BL,SC,FL result;
```

## Result

Each recipe **MUST** emit **exactly one** result block, formatted as markdown, before returning control to the orchestrator. The orchestrator reads the bolded **Result** line to control the flow. **Omitting the Result block is an error** — without it, the orchestrator cannot route the outcome.

### Schema

```markdown
**Result:** ✅ Success | 🚧 Blocker | ⏭️ Rejected | ❌ Failure
**Source:** `<fqn or file path>`
**Recipe:** axon4to5-<component>

**Notes:** <short summary — why this result, what to look at next. Do NOT enumerate changed files; git diff covers that.>

**Learnings:** (optional — omit on trivial runs)
- <bullet>
- <bullet>

**Options:** (required when Result = Blocker; otherwise omit)
- [ ] **<id>** — <short description>
- [ ] **<id>** — <short description>
```

**Learnings is optional** and exists for the non-trivial cases: a step that needed a retry, an assumption that turned out wrong, a project-specific shape the recipe had to discover. Trivial green runs do not need Learnings — leave the field out. When present, keep bullets short and scannable; reference `file:line` whenever possible.

**Options is required on Blocker outcomes.** The recipe must enumerate every continuation path it considers viable from the current partial state. Three options are **always** available (defined in `references/recipes/DEFAULT.md`):

- [ ] **skip** — keep `$SOURCE` in its current partial state; queue moves on.
- [ ] **revert** — undo any edits this recipe applied to `$SOURCE`; return to pre-recipe state; queue moves on.
- [ ] **solve-manually** — pause this item; caller fixes the blocker by hand outside the skill, then re-invokes to continue.

Recipes MAY add more options when there is a genuine recipe-specific path; they MUST NOT override or remove the baseline three. The orchestrator's `BLOCKER_RESOLUTION.md` node surfaces this list to the caller.

**Notes baseline** per-outcome guidance lives in `references/recipes/DEFAULT.md` (§ Result Notes / Learnings baselines) and always applies. Recipes may augment via their own `# Result` subsections when they have recipe-specific facts to record; they cannot override the baseline.

### Example — ✅ Success (trivial — no Learnings)

> **Result:** ✅ Success
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.calendar.Calendar`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match on first Apply. OpenRewrite Phase 1 had already produced the correct AF5 shape; this recipe only verified.

### Example — ✅ Success (with Learnings — surprises encountered)

> **Result:** ✅ Success
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.army.Army`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** All Success Criteria match. Isolated test green; one test expectation updated for the AF5 entity-creator semantics.
>
> **Learnings:**
> - Test expectation flip surprised the recipe: AF4 threw `AggregateNotFoundException` for a missing aggregate, but AF5 with no-arg `@EntityCreator` materialises an empty entity and runs the instance handler — so the domain rule (`Can remove only present creatures`) fires instead. Documented gotcha in `creation-policy-decision.md`; expected test outcome had to be rewritten before the criterion passed.
> - Stranded comment in source (`// performance downside in comparison to constructor`) originally referred to `CREATE_IF_MISSING`'s cost on every command. Still loosely accurate (instance handler re-loads the aggregate), so left in place — but the original referent is gone.

### Example — 🚧 Blocker

> **Result:** 🚧 Blocker
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.write.dwelling.Dwelling`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Caller must decide before re-running. OpenRewrite Phase 1 already dropped the snapshotting attribute and left a `// TODO #LLM: reconfigure snapshot trigger`. AF5's `@EventSourced` does not yet expose a snapshotting API.
>
> **Learnings:**
> - AF4 `@Aggregate(snapshotTriggerDefinition = "...")` has no AF5 equivalent yet — per `not-supported.md` B1 this needs an explicit decision from the caller. The recipe cannot pick one.
> - Existing snapshot rows in storage are NOT touched — data migration is out of scope of this skill, the caller owns that decision.
> - The `public` field declarations on `Dwelling.java` (`public DwellingId dwellingId; // needs to be public for snapshotting`) become unnecessary once snapshotting is dropped — can be tightened to `private` during stabilization, not by this recipe.
>
> **Options:**
> - [ ] **skip** — leave `Dwelling` in its current partial state (annotation already dropped, TODO comment present); queue moves on.
> - [ ] **revert** — restore `@Aggregate(snapshotTriggerDefinition = "dwellingSnapshotTrigger")`, undo OpenRewrite's snapshotting changes, return to pre-recipe state.
> - [ ] **solve-manually** — pause this item; caller hand-resolves snapshotting (e.g. by removing the snapshot trigger bean themselves) and re-invokes.

### Example — ⏭️ Rejected

> **Result:** ⏭️ Rejected
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.read.DwellingReadModelProjector`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Not an aggregate — this is a read-side projector. Recipe did not apply any edits. Route to the event-processor recipe instead.
>
> **Learnings:**
> - Class is annotated `@ProcessingGroup` (not `@Aggregate`) — Applicable predicate failed on the very first surface check.
> - For projectors in this codebase, the migration is mostly OpenRewrite output (`@ProcessingGroup` → `@Namespace`, `@EventHandler` / `@ResetHandler` / `@MetadataValue` imports). The only manual step is moving the AF4 `axon.eventhandling.processors.<group>.sequencing-policy` YAML key onto the class as `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)`.
> - The shared bean `gameIdSequencingPolicy` is referenced by 4 other processor groups in YAML — do not delete it; the write-configuration recipe handles bean cleanup once all groups have been annotated.

### Example — ❌ Failure

> **Result:** ❌ Failure
> **Source:** `com.dddheroes.heroesofddd.creaturerecruitment.process.WhenCreatureRecruitedThenAddToArmyProcessor`
> **Recipe:** axon4to5-aggregate
>
> **Notes:** Retry budget exhausted (2 Applies). Compilation OK on both attempts. Failing Success Criterion: isolated test — last error verbatim: `Wanted but not invoked: commandGateway.send(IncreaseAvailableCreatures.command(...), ...); Actually, there were zero interactions with this mock.`
>
> **Learnings:**
> - AF5 `CommandGateway.send(...)` returns a `CommandResult` whose `getResultMessage()` is a `CompletableFuture<? extends Message>` — the AF4 try/catch around `send(...).getResultMessage()` never catches anything because the failure surfaces on the future, not in the try-block. This is a real behavioural regression, not just a test issue: AF4 automations that compensated via try/catch silently stop compensating under AF5.
> - Suspected fix shape (not applied — outside this recipe's scope): rewrite to `.exceptionallyCompose(error -> commandDispatcher.send(IncreaseAvailableCreatures.command(...), metadata).getResultMessage())`. Will likely need a `.thenApply(m -> m)` bridge to widen `CompletableFuture<? extends Message>` to `CompletableFuture<Message>` (wildcard capture refuses `exceptionallyCompose`'s type bound otherwise).
> - AF5 `org.axonframework.messaging.core.Message` is **NOT generic** — declared as `public interface Message` (verified via `javap` against `axon-messaging-5.1.1-SNAPSHOT.jar`). Any recipe pseudocode using `CompletableFuture<? extends Message<?>>` is wrong; the correct shape is `CompletableFuture<? extends Message>`.
> - This `$SOURCE` is a processor, not an aggregate — Applicable should arguably have rejected it earlier. The aggregate recipe is the wrong tool for try/catch → reactive-compensation refactoring; caller should re-route to the event-processor recipe and re-invoke.

## MUST / MUST NOT

MUST:
- Emit exactly one Result block (schema per § Result) before returning. No exceptions.
- Emit ✅ Success (not ⏭️ Rejected) when `$SOURCE` is already migrated and Success Criteria pass without edits — that is an idempotent Success, not a Rejected outcome. ⏭️ Rejected is reserved for when the `# Applicable` predicate fails (wrong recipe for this source type).
- Emit `**Options:**` when Result = 🚧 Blocker.

MUST NOT:
- Return to the orchestrator without emitting a Result block.
- Emit more than one Result block per recipe execution.

## Invariants

- **Applicable check sits outside Research** — cheap surface check on `$SOURCE` alone; don't pay the Research cost for the wrong recipe.
- **Scope before References** (inside Research) — `scope` drives *which* `references` sections are read.
- **Research is a fixed-point loop** — exits only when SQ says "no new in-scope items"; `scope` can only grow.
- **Single Check Success Criteria** — same evaluation logic pre- and post-Apply; the diamond branches on whether retry budget remains.
- **Blocker fires only from `Blocker in scope?`** — emitted after Research stabilizes. Check / Plan / Apply never short-circuit to Blocker; partial work either passes the Check or counts as Failure.
- **Apply loop is `Check → Plan → Apply → Check`** — only Apply consumes the retry budget. Adjust activities (re-research, source consultation) are *free*.
- **Adjust is open-ended** — on retry the AI picks any subset of: extend scope, consult Axon 5 sources / context7, rethink the approach. Plan Migration is rebuilt each iteration using whatever new info Adjust gathered.
- **Recipe owns content; orchestrator owns control flow.** A recipe never decides "retry" or "skip a step" — it only fills the named sections referenced from the diagram nodes.
- **Result block is non-negotiable** — every flowchart path (SC, RJ, BL, FL) exits through a Result block. The recipe has no valid return path without one.
