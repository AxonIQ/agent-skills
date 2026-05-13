# Scenario 03 — license is asked BEFORE any recipe runs

## Starting state

- Virgin AF4 project. No `.axon4to5-migration/` directory.
- Project has `axon-mongo` dependency (commercial-only signal).

## User input — variant A (PHASED)

```
/axon4to5-migrate
```

## User input — variant B (SINGLE, virgin project)

```
/axon4to5-migrate src/main/java/com/example/giftcard/GiftCard.java
```

## Expected behavior (both variants)

1. Orchestrator detects no `progress.md`.
2. INIT (variant A) or SINGLE mini-INIT (variant B) calls `ensure_pinned()`.
3. `recommend_license()` returns `axoniq-commercial` because of the `axon-mongo` dependency.
4. **First** `AskUserQuestion`: license. Recommended option listed first as `"axoniq-commercial (Recommended) — your project depends on features not in free AF5 yet"`. The other option is `free-af5`.
5. **No recipe runs and no openrewrite invocation happens before this answer.**
6. After license pinned, wiring is detected/pinned, then build-tool.
7. Only then does the orchestrator proceed: variant A scans not-supported rows; variant B routes the file and runs the recipe.

## Pass / fail signals

- ✅ Pass: license is the very first `AskUserQuestion`; recommendation reflects `axon-mongo`.
- ❌ Fail: openrewrite runs (or any recipe runs) before license is pinned. Recommendation defaults to `free-af5` despite commercial deps.

## Why this matters

License drives `--framework axon|axoniq` for the openrewrite skill and changes recipe paths (commercial recipes own DLQ bean swap, Axon Server engine, etc.). Asking it after a recipe has already started is a wasted run.
