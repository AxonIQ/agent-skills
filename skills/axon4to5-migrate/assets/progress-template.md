# Axon Framework 4 → 5 Migration — Progress

> Single source of truth. A fresh session reads this alone and resumes with zero clarifying questions.
> **Protocol:** rewrite the relevant section, THEN commit. Never split work and bookkeeping.

## ▶︎ RESUME HERE

- **next:** _one sentence — e.g. "Migrate aggregate `org.example.Order`."_
- **recipe-loop:** _e.g. `aggregate` (2/8)_
- **recipe:** _e.g. `aggregate`_
- **source:** _e.g. `org.example.Order`_
- **verify:** _exact command_
- **tree:** _clean — last commit `<sha>` / dirty (previous session crashed)_
- **awaiting-caller:** _yes (and the question) / no_

---

## Selection arguments (frozen frame)

```
framework=<axon|axoniq>  configuration=<native|spring>  mode=project  execution=<inline|subagent>
```

---

## OpenRewrite

```
status: not-run
ts: —
note: —
```

---

## Recipe status

| # | Recipe | Status | Items done/total | Last commit |
|---|--------|--------|------------------|-------------|
| 1 | aggregate | pending | 0/? | — |
| 2 | event-processor | pending | 0/? | — |
| 3 | command-gateway | pending | 0/? | — |
| 4 | query-gateway | pending | 0/? | — |
| 5 | query-handler | pending | 0/? | — |
| 6 | interceptors | pending | 0/? | — |
| 7 | saga | pending | 0/? | — |
| 8 | event-store | pending | 0/? | — |

Legend: `pending` · `in-progress` · `done` · `partially-blocked` · `skipped`

---

## Queue

| # | recipe | source | status | last-commit | notes |
|---|--------|--------|--------|-------------|-------|

---

## Caller decisions log

_none yet_
