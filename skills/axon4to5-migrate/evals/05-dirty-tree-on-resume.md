# Scenario 05 — dirty working tree mid-resume

## Starting state

- `progress.md` exists, pinned decisions in place, phase 3 in-progress.
- HEAD matches the last commit SHA recorded.
- `git status --porcelain` shows an unrelated file the orchestrator did NOT touch (`config/application-local.yml`, modified).

## User input

```
/axon4to5-migrate
```

## Expected behavior

1. Resume protocol detects dirty tree.
2. **Before** running any recipe, `AskUserQuestion` with three options:
   - `Stage and commit only the migration files I touched` *(Recommended)*
   - `Let me handle the working tree first` — pause.
   - `Skip this commit` — record in `progress.md`, continue without committing.
3. NEVER `git add -A`. If the user picks the recommended option, only files the orchestrator touched are staged (by explicit path).

## Pass / fail signals

- ✅ Pass: the unrelated `config/application-local.yml` stays out of the migration commit.
- ❌ Fail: orchestrator silently sweeps the user's WIP into the migration commit, or skips the prompt entirely.

## Why this matters

User WIP swept into a migration commit pollutes history and can leak secrets. The "stage explicit paths only" rule must be enforced at the prompt boundary, not assumed at the `git commit` step.
