# Scenario 04 — fresh session resumes from `progress.md` alone

## Starting state

- `.axon4to5-migration/progress.md` exists.
- Pinned decisions: `license: free-af5`, `wiring: spring-boot`, `build-tool: maven`.
- Phase status: phases 1–2 complete, phase 3 (event-processor) in-progress.
- `▶︎ RESUME HERE` block points at next event-processor item `com.example.heroes.WhenCreatureRecruited` with the exact `axon4to5-isolatedtest` Skill call.
- Working tree clean. HEAD matches the last commit SHA recorded in `progress.md`.

## User input

```
/axon4to5-migrate
```

(Brand new session — no prior context.)

## Expected behavior

1. Mode: PHASED (no args).
2. `progress.md` exists → skip INIT entirely. Read it.
3. `git status --porcelain` clean; HEAD matches → proceed.
4. `AskUserQuestion`: "Resuming at Migration Phase #3. Next: `WhenCreatureRecruited`. Continue?" — exactly one confirmation prompt.
5. **No** license / wiring / build-tool re-prompts.
6. After "yes", `event-processor` recipe runs against the named target.

## Pass / fail signals

- ✅ Pass: one confirmation prompt, then recipe runs with all pinned decisions reused.
- ❌ Fail: orchestrator re-asks license / wiring; runs INIT despite `progress.md` existing; or starts at a different item than `▶︎ RESUME HERE` names.

## Why this matters

`progress.md` is the contract that survives `/clear`. If a fresh session re-prompts for pinned decisions, the user loses confidence and the prompts can drift from the original answer.
