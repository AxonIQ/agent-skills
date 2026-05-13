# Commit message template

```
<type>(af5-migration): <one-line>

Verified via: <axon4to5-isolatedtest invocation or `./mvnw test-compile …`>
<wiring>; <one or two lines on variant / decisions if non-obvious>
```

`<type>`: `chore` (one-shot, no behavior change) / `refactor` (iterative migration of one item) / `feat` (storage-engine wiring) / `fix` (stabilization) / `docs` (decision-only).

Subject ≤ 70 chars.

## Rules

- One commit per item; never bundle migrations.
- Stage explicit paths; never `git add -A`.
- Include matching `progress.md` rewrite in the same commit.
- Include `learnings.md` if a non-obvious lesson surfaced.
- Never push / amend / `--no-verify` / commit on `main`.
- No co-author lines.
