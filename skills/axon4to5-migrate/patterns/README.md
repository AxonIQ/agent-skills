# Migration Patterns — Axon Framework 4 → 5

This directory contains flat, per-topic migration patterns following the same structure as
[camunda-7-to-8-migration-tooling](https://github.com/camunda/camunda-7-to-8-migration-tooling/tree/main/code-conversion/patterns).

## How to use

Load `ALL_IN_ONE.md` at the start of every migration session — it aggregates all patterns below
into a single document. The skill loads it automatically in Step 3.

## Pattern Categories

| # | Directory | Topic |
|---|-----------|-------|
| 10 | [10-dependencies](10-dependencies/) | Maven/Gradle dependency and plugin changes |
| 20 | [20-aggregates](20-aggregates/) | Aggregate class, event emission, entity lifecycle |
| 30 | [30-event-handlers](30-event-handlers/) | Event processor routing, command dispatch, metadata |
| 40 | [40-query-handlers](40-query-handlers/) | Query handler annotations, update emitter |
| 50 | [50-interceptors](50-interceptors/) | Command/event handler interceptors |
| 60 | [60-sagas](60-sagas/) | Saga → Spring component |
| 70 | [70-event-store](70-event-store/) | Event storage engine configuration |
| 80 | [80-tests](80-tests/) | Test fixture migration |

## Pattern file format

Each file contains:
1. Overview paragraph
2. **Import Mappings** table (AF4 symbol → AF5 symbol)
3. Detection hint (grep command)
4. **Axon Framework 4 Code** — before
5. **Axon Framework 5 Code** — after
6. Notes and caveats

## ALL_IN_ONE.md

[ALL_IN_ONE.md](ALL_IN_ONE.md) — aggregated reference (all patterns in one file).
Load this file to give the model complete migration context before touching any code.
