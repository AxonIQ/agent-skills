# Drive-evals prompt — paste into a fresh Claude Code session

Fill in `<RECIPE>` (`aggregate` | `event-processor` | `command-gateway` | `all`) and paste:

---

Drive an eval iteration for `axon4to5-migrate` at `skills/axon4to5-migrate`.

Invoke `/skill-creator:skill-creator` to drive the loop.

Pin these defaults so skill-creator uses the existing pipeline — do NOT inline subagent dispatch or write custom HTML:

- **Recipe under test:** `<RECIPE>`
- **Pipeline (run.py picks iteration automatically — highest existing `iteration-N/` or `iteration-1`):**
  1. prep:       `python3 evals/axon4to5-migrate/run.py prep --recipe <RECIPE>`
  2. run:        `python3 evals/axon4to5-migrate/run.py run --recipe <RECIPE>` ← calls `claude -p` per eval in parallel
  3. grade:      `python3 evals/axon4to5-migrate/run.py grade --recipe <RECIPE>`
  4. aggregate:  `python3 evals/axon4to5-migrate/run.py aggregate --recipe <RECIPE>`
- **Dashboard:** after `aggregate`, run `python3 evals/axon4to5-migrate/run.py dashboard --recipe <RECIPE>` — writes `dashboard.html` and opens it in the browser automatically
- **Baseline runs:** add `--baseline` to the `run` command only when you need the `without_skill` delta
- **Subset re-runs:** add `--evals <id,id,…>` to `prep` + `run` to re-run only failing evals

After the dashboard loads, collect user feedback via "Submit All Reviews" → `feedback.json`, then apply improvements to `references/recipes/<RECIPE>/RECIPE.md` and/or `use-cases/` files.
