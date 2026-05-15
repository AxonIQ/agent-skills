# axon4to5-migrate · evals

Deterministic, grep-based evals for the `axon4to5-migrate` Skill. Lives at the **repo root** (`evals/axon4to5-migrate/`); the skill itself stays at `skills/axon4to5-migrate/`.

## What gets tested

Each eval drives the Skill's single-mode flow against a staged AF4 fixture:

```
framework=<axon|axoniq> configuration=<native|spring> mode=single source=<abs path> skip-openrewrite=true
```

`skip-openrewrite=true` (declared as an optional input in SKILL.md) bypasses Pre-step 2 — necessary because subagents can't recursively invoke another Skill and eval fixtures aren't real Maven/Gradle projects. The recipe sub-flow runs normally (Applicable → Scope → References → Success Criteria → Plan-Apply → Result). The grader inspects two artifacts:

1. **`<run>/outputs/<File>.java`** — the in-place migrated source (and any secondary fixtures: child entities, polymorphic subtypes, test classes, YAML configs).
2. **`<run>/outputs/result.md`** — the orchestrator's final Result block, copied verbatim by the subagent.

## Recipes covered

| Recipe | Eval count | Location |
|---|---|---|
| `aggregate` | 15 | `recipes/aggregate/evals.json` |
| `event-processor` | 8 | `recipes/event-processor/evals.json` |

### `aggregate` — 15 evals

Path A (Spring) baseline; Path B (native Configurer) baseline; constructor-style command handlers; partial post-OpenRewrite-Phase-1 state for both paths; idempotency (already-AF5 source); multi-entity Step M (`List<Entity>`); polymorphic Step P (`concreteTypes`); test-fixture migration (`AggregateTestFixture` → `AxonTestFixture`); Blocker B1 (snapshot trigger); Blocker B2 (Map-typed `@AggregateMember`); Blocker B4 (deadline handler); Rejected — projector routed wrong; Rejected — state-stored aggregate; STOP — invalid `framework` argument.

### `event-processor` — 8 evals

Pure projector (Path A); projector with in-handler command dispatch (`CommandGateway` field → `CommandDispatcher` parameter, `sendAndWait` → async `getResultMessage()`); YAML `axon.serializer.*` → `axon.converter.*` + `sequencing-policy` keys → class-level annotation; `@Bean EventProcessorDefinition` Spring wiring; `MessagingConfigurer.eventProcessing(...)` native wiring; custom `SequencingPolicy` class rewrite (interface + signature + `Optional<Object>` wrapping); dual-role class (`@EventHandler` + `@QueryHandler`); Rejected — aggregate routed wrong.

## Layout

```
evals/axon4to5-migrate/
├── run.py                    # prep / grade / aggregate / status — supports --recipe <name>|all
├── grade.py                  # grep_require / grep_forbid / result_block_* / *_any
├── README.md
├── RUN_EVALS_PROMPT.md       # paste-and-go driver prompt
├── fixtures/                 # shared across recipes
│   ├── axon4/
│   │   ├── heroes/           # real AF4 sources from .knowledge/repositories/axon-examples
│   │   └── gamerental/
│   ├── axon5/                # already-migrated AF5 references (idempotency tests)
│   └── synthetic/            # edge cases not covered by axon-examples
├── recipes/
│   ├── aggregate/evals.json
│   └── event-processor/evals.json
└── workspace/                # generated on prep; gitignored
    └── iteration-N/
        └── <recipe>/
            └── eval-<name>/
                ├── eval_metadata.json
                ├── with_skill/run-1/
                │   ├── outputs/<File>.java   # AF4 fixture copied in; rewritten in place
                │   ├── outputs/result.md
                │   ├── prompt.md
                │   └── grading.json          # written by grade.py
                └── without_skill/run-1/…     # baseline (optional)
```

`run.py` derives `SKILL_DIR` from `<repo>/skills/<same basename as this eval dir>`. The eval dir name is the source of truth.

## Running

`run.py` does NOT invoke Claude. Subagents dispatched from a driver session do the migrations. Pipeline:

```
prep → [dispatch subagents via Agent tool] → grade → aggregate
```

`--iteration` is optional — `run.py` picks the highest existing `iteration-N/` (or `iteration-1` on first run).

### Prep

```bash
python3 evals/axon4to5-migrate/run.py prep --recipe aggregate
python3 evals/axon4to5-migrate/run.py prep --recipe event-processor
python3 evals/axon4to5-migrate/run.py prep --recipe all
python3 evals/axon4to5-migrate/run.py prep --recipe event-processor --evals 1,4,7   # subset
```

Per eval, prep writes the workspace tree shown above. Every rendered prompt includes `skip-openrewrite=true` in the skill_args line.

### Dispatch subagents

Open [`RUN_EVALS_PROMPT.md`](RUN_EVALS_PROMPT.md), fill in `<RECIPE>`, paste into a fresh Claude Code session. The driver Claude invokes `/skill-creator:skill-creator` to handle prep → parallel subagent dispatch → grade → aggregate → dashboard refresh. Or drive manually: dispatch one `Agent` (general-purpose) call per `prompt.md`, all in a single message so they run in parallel.

### Grade

```bash
python3 evals/axon4to5-migrate/run.py grade --recipe <name>
```

Writes `grading.json` per run dir using the canonical skill-creator schema: `{expectations[]{text,passed,evidence}, summary{passed,failed,total,pass_rate}}`.

### Aggregate + dashboard

```bash
python3 evals/axon4to5-migrate/run.py aggregate --recipe <name>
```

Produces `workspace/iteration-N/<recipe>/benchmark.{json,md}` via skill-creator's official `aggregate_benchmark.py`. Refresh the HTML viewer:

```bash
VIEWER=~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/eval-viewer/generate_review.py
WS=evals/axon4to5-migrate/workspace/iteration-1/<recipe>
~/.claude/venv/bin/python "$VIEWER" "$WS" \
  --skill-name "axon4to5-migrate/<recipe>" \
  --benchmark "$WS/benchmark.json" \
  --static "$WS/dashboard.html"
```

### Status

```bash
python3 evals/axon4to5-migrate/run.py status --recipe <name>
```

## Assertion vocabulary (`grade.py`)

| Type | Behaviour |
|---|---|
| `grep_require` | `pattern` MUST appear in the target file |
| `grep_forbid` | `pattern` MUST NOT appear in the target file |
| `grep_require_any` | ANY of `patterns[]` MUST appear (OR-match) |
| `grep_forbid_all` | NONE of `patterns[]` may appear (AND-forbid) |
| `result_block_contains` | alias of `grep_require` with target `result` |
| `result_block_forbid` | alias of `grep_forbid` with target `result` |
| `result_block_contains_any` | alias of `grep_require_any` with target `result` |

Targets:

- `source` — `<run>/outputs/<basename of fixture>`
- `secondary:<filename>` — e.g. `secondary:Transaction.java` for multi-entity child
- `result` — `<run>/outputs/result.md`

## Adding a new recipe

1. Author `skills/axon4to5-migrate/references/recipes/<recipe>/RECIPE.md` (sections per `references/recipes/_template/RECIPE.md`).
2. Author `references/recipes/<recipe>/use-cases/*.md` (markdown-linked from RECIPE.md `# Use cases`).
3. Create `evals/axon4to5-migrate/recipes/<recipe>/evals.json` (canonical skill-creator schema + `assertions[]` extension; every eval's `skill_args` should include `"skip-openrewrite": "true"`).
4. Drop any new fixtures into `evals/axon4to5-migrate/fixtures/synthetic/` (or reuse the real heroes / gamerental ones).
5. `run.py` auto-discovers the new recipe — no script changes needed.
