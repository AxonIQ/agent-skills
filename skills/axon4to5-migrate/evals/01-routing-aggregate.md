# Scenario 01 — SINGLE: aggregate class routes to `aggregate` recipe

## Starting state

- Target project: AF4 Spring Boot project, OpenRewrite already run.
- `progress.md` exists with license, wiring, build-tool pinned.
- File `src/main/java/com/example/giftcard/GiftCard.java` declares
  `@Aggregate` and at least one `@EventSourcingHandler` method.

## User input

```
/axon4to5-migrate src/main/java/com/example/giftcard/GiftCard.java
```

## Expected behavior

1. Mode resolves to **SINGLE** (path argument).
2. `ensure_pinned()` returns early — license + wiring + build-tool already pinned, no `AskUserQuestion`.
3. Routing table walked in `Phase` order:
   - `openrewrite` (one-shot, phase 1) — does not match a file argument; skip.
   - `aggregate` (phase 2) — discovery grep `@Aggregate\b\|@AggregateRoot\b` matches → row wins.
4. `aggregate` recipe runs with `inputs.target = com.example.giftcard.GiftCard`, `inputs.wiring = spring-boot`.
5. After `result: success`, ONE commit with subject `refactor(af5-migration): migrate aggregate GiftCard to AF5 (Migration Phase #2)`. Commit includes code + `progress.md` rewrite.
6. Orchestrator suggests `/clear` and stops.

## Pass / fail signals

- ✅ Pass: exactly one new commit; `progress.md` Per-phase plan row for `GiftCard` updated to `done` with the commit SHA.
- ❌ Fail: orchestrator asks "which recipe?" (auto-routing broken), runs `event-processor` instead of `aggregate`, or commits without `progress.md` update.

## Why this matters

Single-file routing is the entry point most users will hit. The routing table is the single source of truth — auto-pick MUST work without user prompts. Phase ordering matters because some discovery greps overlap (an aggregate class can mention `@EventHandler` in javadoc).
