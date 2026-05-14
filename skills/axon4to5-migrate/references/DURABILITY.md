# DURABILITY

**Scope: `mode=project` only.** For `mode=single` — no state dir, no hooks fire, no resume. Recipe runs, result emitted, file edits left for user to review and commit. Skip this entire file for `mode=single`.

Owns state, commits, decisions. Observes hooks across SKILL.md flow. No phases — recipes applied to items.

## State dir

`<repo-root>/.axon4to5-migration/`

- `progress.md` — state + resume + queue + decisions
- `learnings.md` — append-only surprises

Created lazily after Parse accepts args. Never overwritten without caller approval.

## Always first (project mode only)

Before pre-step #1 (Parse):

1. `Read .axon4to5-migration/progress.md` if exists.
2. Present → resume protocol (§Resume) + 📋 message.
3. Absent → 🆕 message, continue to Parse.

## `progress.md` schema

Fixed section order.

```
## ▶︎ RESUME HERE
- next: <one sentence>
- recipe: <id>
- source: <fqn or path>
- verify: <exact command>
- tree: <clean | last-commit <sha>>
- awaiting-caller: <yes | no>

## Selection arguments (frozen frame)
framework=<v> configuration=<v> mode=<v> execution=<v>
# `source` is NOT part of the frozen frame:
#   - mode=project → source ignored.
#   - mode=single  → source is queue-driven (each invocation appends/matches a Queue row).

## OpenRewrite
status: <not-run | success | failed>
ts: <iso>
note: <optional>

## Pinned decisions
- <iso-ts> <topic> → <choice>

## Queue
| # | recipe | source | status | last-commit | notes |
|---|--------|--------|--------|-------------|-------|

## Caller decisions log
- <iso-ts> <recipe>/<source> — blocker(<options>) → <chosen> [<rationale>]
```

Status ∈ `pending`, `in-progress`, `done`, `blocked`, `skipped`, `rejected`, `failed`. Resume skips non-`pending`/`in-progress`.

## `learnings.md` schema

```
## YYYY-MM-DD — <headline>
**Context:** ...
**Surprise:** ...
**Resolution:** ... (commit <sha>?)
```

**MUST `Read learnings.md` when:** surprised, unexpected result, blocker, or ≥2 consecutive failures on the same item. Prior entries often pre-explain the current problem. Skip on routine resume.

## Hooks

Every hook that mutates `progress.md` commits the change in the same op. Code-bearing → `refactor(af5)`. State-only → `chore(af5)`.

| Hook | Trigger in SKILL.md | Action | Commit subject |
|------|---------------------|--------|----------------|
| `on:session-start` | Before pre-steps | Read `progress.md`; resume or fresh. | — |
| `on:args-parsed` | After Parse validates | Init state dir if absent; write Selection frame (framework, configuration, mode, execution — **not** `source`). Resume + frame mismatch → AskUserQuestion (resume / start-over / abort) **before** writing. | `chore(af5): record selection frame` |
| `on:openrewrite-done` | After pre-step #2 | Write outcome to `progress.md`. If status=`success`: stage **all** working-tree changes with `git add -A` (covers OpenRewrite recipe edits + `progress.md`); commit with canonical message (substitute `<framework>` from resolved arg). Resume + already `success` → skip pre-step entirely (no new commit). | `chore(af5): apply Axon 4 → 5 OpenRewrite migration (--framework <framework>)` |
| `on:queue-built` | After producer (Match / Discover+Enqueue) | Snapshot queue. Resume → merge: keep prior statuses; add only new items. | `chore(af5): build queue (<N> items)` |
| `on:item-start` | Drain pick | Status → `in-progress`. | `chore(af5): start <source>` |
| `on:item-result` | After FLOW.md `## Result` emitted | Status per outcome emoji; update notes col. | `chore(af5): record <status> for <source>` |
| `on:item-success` | Result=✅ + Verify ok | Stage code paths + `progress.md` (+ `learnings.md` if dirty). | `refactor(af5): <source> (recipe: <id>)` |
| `on:caller-decision` | After BLOCKER_RESOLUTION choice applied | Append to decisions log. | `chore(af5): caller decision <chosen> for <source>` |
| `on:learning` | Recipe emits `**Learnings:**` block | Append dated entry to `learnings.md`. | folded into next commit; if standalone: `chore(af5): record learning` |
| `on:session-end` | At Render report | Refresh `▶︎ RESUME HERE`. | `chore(af5): update resume pointer` (only if changed) |

`on:item-result` + `on:item-success` MAY coalesce into one `refactor(af5)` commit.

DURABILITY observes; SKILL/FLOW/BLOCKER never call it explicitly.

## Commit rules

- `git commit <explicit-paths>` only. Never `--amend`, `--no-verify`, `push`, co-author lines.
- Exception: `on:openrewrite-done` (status=`success`) uses `git add -A` to stage recipe-wide changes alongside `progress.md` in the one combined commit.
- `git status --porcelain` before each commit. Unexpected paths → AskUserQuestion (reuse existing channel).
- State-write failure → surface, continue. Do not corrupt code state.

## Resume protocol

1. Read `progress.md`. Extract `▶︎ RESUME HERE`.
2. Validate working-tree expectation. Mismatch → AskUserQuestion.
3. Validate incoming frame (`framework`, `configuration`, `mode`, `execution`) vs stored `## Selection arguments`. Mismatch → AskUserQuestion (resume / start-over / abort). Do not overwrite stored frame unless caller picks start-over.
4. Mode-specific source handling:
   - `mode=project` — ignore incoming `source`.
   - `mode=single` — look up the queue row for the matched recipe + incoming `source`:
     - **not in queue** → append a new `pending` row (extending a prior run with a new target).
     - **exists, status=`pending`/`in-progress`** → resume on it.
     - **exists, status=`done`** → 🏁 already-done message, exit.
     - **exists, status=`blocked`/`failed`/`rejected`/`skipped`** → AskUserQuestion: `retry` (status → `pending`) / `leave-as-is` (exit) / `start-over` (wipe state dir).
5. Skip pre-steps marked complete (OpenRewrite `success` → skip pre-step #2). Skip queue rebuild — load from `## Queue`.
6. Jump to drain loop at next `pending` item.

## Messages

| Marker | Text |
|--------|------|
| 🆕 | `New migration. State → .axon4to5-migration/` |
| 📋 | `Resuming. Next: <recipe>/<source>. <N> done · <M> blocked · <K> pending.` |
| ⚠️ | `Selection args changed (was: X, now: Y). Resume / start-over / abort?` |
| ⏭ | `OpenRewrite already succeeded on <ts>, skipping.` |
| ✅ | `Committed <source> (recipe: <id>) → <sha>` |
| 🚧 | `Recorded: <recipe>/<source> → <chosen>` |
| 💡 | `Surprise detected — checking learnings.md for prior occurrences.` |
| 🏁 | `Migration complete. <N done> · <M blocked> · <K skipped>. See .axon4to5-migration/progress.md.` |

## MUST / MUST NOT

MUST:
- read `progress.md` before any other action.
- persist + commit on every `progress.md` mutation.
- persist Selection arguments **only after** Parse validates them.
- `Read learnings.md` on surprise, blocker, or repeated failure.
- reuse the orchestrator's existing AskUserQuestion path for caller prompts.

MUST NOT:
- identify the caller (user / subagent / auto) — `BLOCKER_RESOLUTION.md`'s concern.
- re-run OpenRewrite when state shows `success`.
- halt the orchestrator on a state-write failure.
- write SQL or recipe-emitted artifacts (recipes own their side files).
- overwrite Selection arguments on mismatch without caller approval.
- use the word "phase".

## Session sequence

```mermaid
sequenceDiagram
    autonumber
    participant C as Caller
    participant S as Skill (SKILL.md)
    participant R as Recipe (FLOW.md)
    participant D as Durability
    participant F as Filesystem
    participant G as Git

    Note over C,G: Fresh session
    C->>S: invoke
    S->>D: on:session-start
    D->>F: Read progress.md (absent)
    D-->>S: 🆕 fresh start
    S->>S: Parse args (validate)
    S->>D: on:args-parsed
    D->>F: write Selection args
    D->>G: commit (chore: selection args)
    S->>S: OpenRewrite (--commit false)
    S->>D: on:openrewrite-done
    D->>F: write status to progress.md
    D->>G: commit git add -A → chore(af5): apply Axon 4→5 OpenRewrite migration (--framework <fw>)
    S->>S: producer (Match / Discover)
    S->>D: on:queue-built
    D->>F: write queue
    D->>G: commit (chore: queue built)
    loop drain
        S->>D: on:item-start
        D->>F: status in-progress
        D->>G: commit (chore: start <source>)
        S->>R: execute recipe
        R-->>S: RESULT (+ Learnings?)
        alt has Learnings
            S->>D: on:learning
            D->>F: append learnings.md
        end
        alt Result = ✅
            S->>S: Verify
            S->>D: on:item-result + on:item-success (coalesced)
            D->>F: stage code + progress.md
            D->>G: commit (refactor: <source>)
            S-->>C: ✅
        else Blocker
            S->>R: BLOCKER_RESOLUTION
            R->>C: AskUserQuestion (options)
            C-->>R: choice
            R->>D: on:caller-decision
            D->>F: append decisions log
            D->>G: commit (chore: decision)
            S-->>C: 🚧
        else Rejected / Failure
            S->>D: on:item-result
            D->>F: status
            D->>G: commit (chore: record <status>)
        end
    end
    S->>D: on:session-end
    D->>F: refresh ▶︎ RESUME HERE
    D->>G: commit (chore: resume pointer)
    S-->>C: 🏁

    Note over C,G: Resume session
    C->>S: invoke
    S->>D: on:session-start
    D->>F: Read progress.md (found)
    D-->>S: 📋 next=<recipe>/<source>
    S->>S: Parse args
    S->>D: on:args-parsed
    D->>F: compare with stored
    alt args mismatch
        D->>C: ⚠️ resume / start-over / abort?
    end
    Note right of S: OpenRewrite skipped (status=success)
    S->>F: load queue from progress.md
    Note right of G: commit on every progress.md mutation
```
