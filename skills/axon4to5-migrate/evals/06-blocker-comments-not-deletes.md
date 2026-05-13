# Scenario 06 — `result: blocked` comments out, never deletes

## Starting state

- Pinned decisions in place. License: `free-af5`.
- Project has a `@Bean DeadlineManager` declaration somewhere in a configuration class.
- User reached this surface via phase 7 (`event-storage-engine` / configuration sweep).

## User input

```
/axon4to5-migrate
```

(continues phased run; reaches the configuration class)

## Expected behavior

1. Recipe Preflight runs `not-supported.md` Detection greps, finds `@Bean DeadlineManager`.
2. `AskUserQuestion` surfaces the blocker — user picks `defer-until-af5-deadlines`.
3. Recipe emits `result: blocked` with `decisions.deadline-manager-bean: defer-until-af5-deadlines` and `caller-expects.commit: true`.
4. Orchestrator commits:
   - The AF4 `@Bean DeadlineManager` is **commented out** in the source file (not deleted).
   - A `// TODO[AF5 migration: <blocker-key>]` marker sits beside the commented block.
   - `progress.md` Pinned-decisions records the resolution.
   - `learnings.md` has a fresh dated entry naming the blocker key.

## Pass / fail signals

- ✅ Pass: AF4 source survives as a comment + TODO; `progress.md` + `learnings.md` updated.
- ❌ Fail: the AF4 bean is silently deleted; or the commented block ships without a TODO marker; or `learnings.md` is not updated.

## Why this matters

Silent deletion erases the wiring shape — the day AF5 ships deadlines, nobody knows what to restore. The TODO marker + blocker key is the audit trail that lets a future migration sweep find every parked surface.
