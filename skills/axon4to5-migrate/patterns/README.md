# Migration Patterns — Axon Framework 4 → 5

Flat, per-topic migration patterns. Each file covers one transformation: import mapping table, detection
hint, before/after code, and notes.

## How to use

Load `ALL_IN_ONE.md` at the start of every migration session — it aggregates all patterns into a single
document. The skill loads it automatically in Step 3.

Regenerate `ALL_IN_ONE.md` after editing any pattern file:
```
python3 scripts/generate_all_in_one.py
```

## Pattern Categories

| # | Directory | Topic |
|---|-----------|-------|
| 10 | [10-dependencies](10-dependencies/) | Maven/Gradle dependency and YAML config changes |
| 20 | [20-aggregates](20-aggregates/) | Aggregate class, event emission, entity lifecycle, command routing |
| 30 | [30-event-handlers](30-event-handlers/) | Event processor routing, command dispatch, metadata, sequencing |
| 40 | [40-query-handlers](40-query-handlers/) | Query handler annotations |
| 50 | [50-interceptors](50-interceptors/) | Command/event handler interceptors |
| 60 | [60-sagas](60-sagas/) | Saga → Spring JPA component |
| 70 | [70-event-store](70-event-store/) | Event storage engine configuration |
| 80 | [80-tests](80-tests/) | Test fixture migration |

## Pattern file format

Each file contains:
1. Overview paragraph
2. **Import Mappings** table (AF4 symbol → AF5 symbol)
3. Detection hint (grep command)
4. **Axon Framework 4 Code** — before
5. **Axon Framework 5 Code** — after
6. Notes and caveats (including blockers where applicable)
