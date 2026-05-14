# axon4to5-migrate · single-mode aggregate evals

TDD-style evals for the `axon4to5-migrate` Skill invoked in **single mode** with the **aggregate** recipe.

## What gets tested

Each eval drives the Skill's full single-mode flow:

```
framework=<axon|axoniq> configuration=<native|spring> mode=single source=<file or FQN>
```

The Skill must: run its OpenRewrite pre-step → match the aggregate recipe → execute the recipe sub-flow → rewrite the source in place → emit a `**Result:** …` block. The grader checks **two artifacts**:

1. **`<run>/project/<File>.java`** — the in-place migrated AF4 → AF5 source (and any secondary fixtures like child entities, test classes, polymorphic subtypes).
2. **`<run>/result.md`** — the orchestrator's final Result block, copied verbatim from the agent transcript.

## TDD status

`references/recipes/aggregate/RECIPE.md` is currently **empty** (frontmatter only) by design. Every eval is expected to **FAIL** on the first run — that is the red bar that drives recipe authoring. The RECIPE.md will be populated next to make them green.

## Eval coverage (31 evals)

| Category | Evals | Notes |
|---|---|---|
| spring-path-straight | 1, 2, 3, 4 | Calendar / Astrologers / ResourcesPool / Army — Path A `@EventSourced` |
| spring-path-constructor-handler | 5 | gamerental Game — constructor-style cmd handler + `@Profile` + `@ExceptionHandler` |
| blocker-snapshot-B1 | 6 | Dwelling — no decision pinned → emit Blocker B1 with three default Options |
| blocker-snapshot-B1-resolved | 7 | Dwelling — `snapshotting=accept-drop` → migrate, drop attribute |
| blocker-snapshot-B1-pause | 31 | Dwelling — `snapshotting=pause-migration` → still Blocker, no edits |
| blocker-deadline-B4 | 8 | Shipment (synthetic) — `@DeadlineHandler` + `DeadlineManager` |
| blocker-map-aggregatemember-B2 | 9 | Inventory (synthetic) — `@AggregateMember Map<…>` |
| native-path-straight | 10, 11, 12, 13 | Same four heroes aggregates — Path B `@EventSourcedEntity` |
| native-path-constructor-handler | 14 | gamerental Game — Path B |
| native-path-blocker-resolved | 15 | Dwelling — Path B + accept-drop |
| license-axon-community | 16, 17 | `framework=axon` — Calendar Path A + Path B (no `io.axoniq.framework` coords) |
| rejected-not-aggregate | 18, 19 | Projector + Saga — `# Applicable` predicate fails |
| rejected-state-stored | 20 | Customer (synthetic) — JPA `@Entity` + zero `@EventSourcingHandler` |
| idempotency | 21, 22 | Already-migrated AF5 Calendar + Game — `edits=none (idempotent)` |
| multi-entity | 23 | GiftCard + Transaction — `@AggregateMember List<>` → `@EntityMember` |
| polymorphic | 24 | Card + 2 subtypes — `concreteTypes` on abstract base |
| source-resolution | 25, 26 | source by FQN; source by simple class name |
| test-fixture-migration | 27 | Calendar + CalendarTest — `AggregateTestFixture` → `AxonTestFixture` (fluent API) |
| argument-validation | 28, 29, 30 | Bad `framework`, bad `configuration`, missing `source` → STOP |

## Layout

```
evals/
├── evals.json
├── fixtures/
│   ├── axon4/
│   │   ├── heroes/         {Calendar, Astrologers, Army, ResourcesPool, Dwelling, DwellingReadModelProjector}.java
│   │   └── gamerental/     Game.java
│   ├── axon5/              already-migrated reference files for idempotency tests
│   └── synthetic/          edge cases not in axon-examples (deadline, map-aggregatemember, multi-entity,
│                           polymorphic, state-stored, saga, test fixture)
├── run.py                  prep / grade / aggregate / status
├── grade.py                grep_require / grep_forbid / result_block_*
└── workspace/              created on first prep (iteration-N/eval-<name>/{with_skill,without_skill}/…)
```

## Running

### Prep one iteration

```bash
python3 evals/run.py prep --iteration 1
# Or just a subset:
python3 evals/run.py prep --iteration 1 --filter blocker
python3 evals/run.py prep --iteration 1 --evals 1,7,23
```

Per eval, this creates:

```
workspace/iteration-1/eval-<name>/
  with_skill/
    project/<File>.java         ← AF4 fixture copied in
    project/<Secondaries>.java
    result.md                   ← placeholder (subagent overwrites)
    prompt.md                   ← the ready-to-paste subagent prompt
    eval_metadata.json
  without_skill/                ← baseline; same layout, NO Skill loaded
```

### Drive each eval

For each `prompt.md`, dispatch an `Agent` (general-purpose) subagent and paste the contents. The subagent must:

- For `with_skill`: have access to the Skill at `skills/axon4to5-migrate/`.
- For `without_skill`: NOT load the Skill — work from general AF5 knowledge.

Both write the migrated source back to `<run>/project/<File>.java` (in place) and the orchestrator's Result block to `<run>/result.md`.

### Grade + aggregate

```bash
python3 evals/run.py grade --iteration 1
python3 evals/run.py aggregate --iteration 1
```

Aggregate writes `benchmark.{json,md}` next to the iteration directory.

## Assertion vocabulary (grade.py)

- `grep_require` — pattern must appear in the target file
- `grep_forbid` — pattern must NOT appear
- `result_block_contains` / `result_block_forbid` — same, target = `result.md`
- `result_block_contains_any` — OR-match across `patterns[]`

Targets:

- `source` — `<run>/project/<basename of fixture>`
- `secondary:<filename>` — e.g. `secondary:Transaction.java` for multi-entity child
- `result` — `<run>/result.md`
