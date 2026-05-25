# Drive-evals prompt — paste into a fresh Claude Code session

Fill in `<RECIPE>` (`aggregate` | `command-gateway` | `event-processor` | `event-store` | `interceptors` | `query-gateway` | `query-handler` | `saga` | `all`) and paste:

---

Drive an eval iteration for `axon4to5-migrate` at `skills/axon4to5-migrate`.

Invoke `/skill-creator:skill-creator` to drive the loop. It already knows how to
prep, dispatch subagents in parallel, grade, aggregate, and regenerate the viewer.

Pin these defaults so skill-creator doesn't reinvent them:

- **Recipe under test:** `<RECIPE>`
- **Evals source:** `evals/axon4to5-migrate/recipes/<RECIPE>/evals.json` (canonical schema; deterministic `assertions[]` extension used for grading)
- **Pipeline scripts (use, don't replace) — let `run.py` pick the iteration (highest existing `iteration-N/`, else `iteration-1`):**
  - prep: `python3 evals/axon4to5-migrate/run.py prep --recipe <RECIPE>`
  - grade: `python3 evals/axon4to5-migrate/run.py grade --recipe <RECIPE>`
  - aggregate: `python3 evals/axon4to5-migrate/run.py aggregate --recipe <RECIPE>`
- **Workspace per eval (the iteration root is whatever `run.py` chose):** `<workspace>/<recipe>/eval-<name>/with_skill/run-1/outputs/`
- **Subagent contract per eval:** read `prompt.md` in the run dir, then read
  `$SKILL_DIR/SKILL.md` and `$SKILL_DIR/patterns/ALL_IN_ONE.md` (and
  `$SKILL_DIR/examples/ALL_EXAMPLES.md` when a fuller walkthrough is needed —
  individual pattern + example files are linked from the eval prompt). Identify
  the AF4 shapes in the staged source(s), apply the matching patterns IN PLACE,
  then write the `**Result:**` block to `outputs/result.md`. Each eval prompt
  pins `configuration=<spring|native>`, Migration approach **B (AI only)**, and
  `skip-openrewrite=true` so the subagent skips SKILL.md Step 1 (AskUserQuestion
  prompts) and Step 2.5 (progress tracking) cleanly — the harness has no real
  Maven/Gradle project and no project root. Cite AF5 import FQNs verbatim (the
  `.extension.spring.`, `.messaging.`, `.reflection.` infixes are load-bearing).
- **Drive `with_skill/run-1` only** (baseline `without_skill` is optional).

Dashboard at the end: refresh via the skill-creator viewer pointed at the
`<workspace>/<recipe>/` directory `run.py` reported.
