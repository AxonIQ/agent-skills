# Eval scenarios — recipe coverage on real AF4↔AF5 pairs

Each row pairs an AF4 source file with its AF5 reference from `.knowledge/repositories/axon-examples/`. The recipe must transform AF4 into a file equivalent to the AF5 reference; mismatch ≠ automatic fail (project style may diverge), but every **must-have** line below is required, and any **anti-pattern** line causes fail.

Repo aliases: `H4` = `axon-examples/axon4/heroes`, `H5` = `axon-examples/axon5/heroes`, `G4` / `G5` = same for `gamerental`, `B4` / `B5` = same for `bike-rental-extended`.

## Routing evals — auto-pick the right recipe

| # | Trigger (SINGLE mode, against AF4 clone) | Expected recipe | Must-haves |
|---|---|---|---|
| R1 | `.../write/Dwelling.java` (H4) | `aggregate` | row picked at phase 2; `inputs.wiring = spring-boot` from pinned. |
| R2 | `.../write/Calendar.java` (H4) | `aggregate` | same. |
| R3 | `.../read/DwellingReadModelProjector.java` (H4) — has `@EventHandler` + injects `CommandGateway` | `event-processor` (phase 3) | NOT `command-gateway` — `exclude-when` (`@EventHandler`) fires. |
| R4 | `.../write/recruitcreature/RecruitCreatureRestApi.java` (H4) | `command-gateway` (phase 4) | top-of-chain `CommandGateway` injection, no handler annotations. |
| R5 | `.../read/getdwellingbyid/GetDwellingByIdRestApi.java` (H4) | `query-gateway` (phase 5) | top-of-chain `QueryGateway`; no handler annotations. |
| R6 | `.../read/getdwellingbyid/GetDwellingByIdQueryHandler.java` (H4) | `query-handler` (phase 6) | `@QueryHandler` import-only rewrite case. |
| R7 | `.../write/withdraw/PaidCommandInterceptor.java` (H4) | `interceptors` (phase 7) | `implements MessageHandlerInterceptor`, no handler annotations on the class. |
| R8 | `.../rental/paymentsaga/PaymentSaga.java` (B4) | `saga` (not-supported, per-saga decision) | `result: needs-decision`; no auto-rewrite. |

## Recipe evals — AF4 → AF5 must-haves

### `aggregate` — see [fixtures/aggregate-heroes-dwelling.md](fixtures/aggregate-heroes-dwelling.md)

Reference pair: `H4/.../write/Dwelling.java` ↔ `H5/.../write/Dwelling.java`. Tests Steps 3–14 (annotations, EventAppender, EntityCreator), Path A (Spring `@EventSourced`), blocker B1 (`snapshotTriggerDefinition` — must be flagged BEFORE OpenRewrite or detected via TODO marker).

### `event-processor` — see [fixtures/event-processor-heroes.md](fixtures/event-processor-heroes.md)

Reference pair: `H4/.../creaturerecruitment/automation/WhenCreatureRecruitedThenAddToArmyProcessor.java` ↔ `H5/...`. Tests `@ProcessingGroup` → `@Namespace`, in-handler `CommandGateway` → `CommandDispatcher` parameter, async `send(...)` rewrite.

### `command-gateway` — see [fixtures/command-gateway-heroes.md](fixtures/command-gateway-heroes.md)

Reference pair: `H4/.../recruitcreature/RecruitCreatureRestApi.java` ↔ `H5/...`. Tests import-only `CommandGateway` move + `CompletableFuture<Void>` controller return.

### `query-gateway` — see [fixtures/query-gateway-heroes.md](fixtures/query-gateway-heroes.md)

Reference pair: `H4/.../getalldwellings/GetAllDwellingsMcp.java` ↔ `H5/...`. Tests `ResponseTypes.multipleInstancesOf(...)` → `queryMany(...)`, sync framework callback bridge via `.orTimeout(...).join()`.

### `query-handler` — see [fixtures/query-handler-heroes.md](fixtures/query-handler-heroes.md)

Reference pair: `H4/.../getdwellingbyid/GetDwellingByIdQueryHandler.java` ↔ `H5/...`. Tests import-only AF5 `@QueryHandler` move; everything else preserved.

### `interceptors` — see [fixtures/interceptors-heroes.md](fixtures/interceptors-heroes.md)

Reference pair (AF4 only; AF5 may differ structurally): `H4/.../write/withdraw/PaidCommandInterceptor.java`. Tests `MessageHandlerInterceptor.handle(UnitOfWork, InterceptorChain)` → `interceptOnHandle(M, ProcessingContext, MessageHandlerInterceptorChain<M>)` rewrite, `UnitOfWork` body rewrites, return type `Object` → `MessageStream<?>`.

### `event-storage-engine` — see [fixtures/event-storage-engine-heroes.md](fixtures/event-storage-engine-heroes.md)

Reference pair: `H4/.../resources/application.yaml` + `H4/.../GameConfiguration.java` ↔ `H5/...`. Tests explicit `@Bean EventStorageEngine`, `@EntityScan` on framework packages, `SequencingPolicy` signature migration.

### `saga` — see [fixtures/saga-bike-rental.md](fixtures/saga-bike-rental.md)

Reference pair: `B4/.../paymentsaga/PaymentSaga.java` ↔ `B5/.../paymentsaga/PaymentSaga.java`. Tests blocker detection (`@DeadlineHandler` present), four-way `AskUserQuestion`, NEVER auto-rewrite. AF5 reference shows the `Shape B` outcome (JPA state + scheduler).

## Orchestrator evals — flow / state

| # | Scenario | Pass criteria |
|---|---|---|
| O1 | **License is asked BEFORE any recipe.** Virgin H4 clone has `axon-mongo`? It doesn't — but `axon-server-connector` IS commercial-signal. → first `AskUserQuestion` is license; `recommend_license()` returns `axoniq-commercial`, shown first as `(Recommended)`. **Fail** if openrewrite runs before license is pinned. |
| O2 | **Resume from `progress.md` alone.** After R1 (aggregate Dwelling) finishes, blow away the session and re-invoke. → exactly one confirmation prompt naming `▶︎ RESUME HERE`'s next item; no re-prompts for license/wiring/build-tool. |
| O3 | **Dirty tree on resume.** After R1 commits, manually `echo > /tmp/extra.txt` in the clone. Re-invoke. → `AskUserQuestion` with three options; NEVER `git add -A`. |
| O4 | **`result: blocked` keeps the AF4 surface.** Run `saga` recipe on B4 PaymentSaga, pick `accept-stays-af4`. → no AF4 code deleted; `progress.md` Pinned-decisions records the choice; `learnings.md` has a dated entry. |
| O5 | **DEBUG clusters by root cause.** Take H4 post-OpenRewrite, leave it red. Run `/axon4to5-migrate debug`. → orchestrator runs `mvn test-compile`, clusters by root cause, routes ONE high-leverage cluster, recompiles. **Fail** if it routes N times to the same recipe without re-clustering. |
| O6 | **FINALIZE removes all `isolated-*`.** After last recipe row, every `isolated-<X>` profile created during the run is removed; `./mvnw clean verify` runs with no scope active; single `chore(af5-migration): remove isolated-* scaffolding` commit. |
| O7 | **No data migration.** Heroes uses JPA event store. → `event-storage-engine` recipe records schema-change requirement in `notes` / `learnings.md`; produces **no** `.sql` / Flyway / Liquibase artifact in the working tree. |

## How to run

See [README.md](README.md) "How to run manually". For automation, a future harness can: snapshot AF4 example, run the skill, diff against the AF5 reference, grep for must-haves / anti-patterns.
