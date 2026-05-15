# CLAUDE.md

All-file content language: English.

Be proactive, challenge me. If you think you have a better idea than what I wanted from you, propose other things.

## Running evals

Evals live at the **repo root**, not inside the skill: `evals/axon4to5-migrate/`. The skill itself stays under `skills/axon4to5-migrate/`. `run.py` derives `SKILL_DIR` from `<repo>/skills/<same basename as the eval dir>`.

Layout (relative to repo root):

```
evals/axon4to5-migrate/
├── run.py                  # prep / grade / aggregate / status — supports --recipe <name>|all
├── grade.py                # grep-based assertion engine
├── fixtures/               # shared AF4 fixtures
├── recipes/
│   ├── aggregate/evals.json
│   └── event-processor/evals.json
└── workspace/iteration-N/<recipe>/eval-<name>/{with_skill,without_skill}/run-1/
```

`run.py` does NOT invoke Claude. The actual migrations are run by **subagents dispatched from this conversation** (the `Agent` tool). Pipeline:

```
prep → [DISPATCH SUBAGENTS via Agent tool] → grade → aggregate
```

Every eval's `skill_args` includes `skip-openrewrite=true` (defined as an optional skill input in SKILL.md). This bypasses Pre-step 2 (the OpenRewrite bulk pass) — necessary because subagents can't recursively invoke another Skill, and because eval fixtures aren't real Maven/Gradle projects. Recipes still run their full `# Applicable` predicate set + Plan-Apply loop normally; they just don't have Phase 1 to lean on.

### Quick start — drive a full iteration in one go

Paste the contents of [`../../evals/axon4to5-migrate/RUN_EVALS_PROMPT.md`](../../evals/axon4to5-migrate/RUN_EVALS_PROMPT.md) into a fresh Claude Code session, fill in `<RECIPE>` (e.g. `aggregate`, `event-processor`, or `all`), and the driver Claude will: prep → dispatch one subagent per eval in parallel → grade → aggregate → regenerate dashboard → report.

That prompt is the canonical entry point. The sections below explain each step in detail if you want to drive it manually.

### Step 1 — Prep one recipe

```bash
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe <recipe-name>
# Examples:
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe aggregate
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe event-processor
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe all                  # both
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe event-processor --evals 1,3,7   # subset
```

Per eval, prep writes:

```
workspace/iteration-1/<recipe>/eval-<name>/
  eval_metadata.json                    # assertions + skill_args + expected_result
  with_skill/run-1/
    outputs/<File>.java                 # AF4 fixture copied in (to be rewritten IN PLACE)
    outputs/<Secondaries>.java          # multi-file evals (multi-entity, polymorphic, test fixture)
    outputs/result.md                   # 0-byte placeholder — subagent overwrites
    prompt.md                           # ready-to-paste subagent prompt
  without_skill/run-1/…                 # baseline — same layout, NO skill loaded
```

### Step 2 — Dispatch subagents (Agent tool, parallel)

For each eval's `prompt.md`, dispatch **one `Agent` tool call** with `subagent_type=general-purpose`. Send all calls in **one message** so they run in parallel. Pattern:

```
You are executing eval <N> of axon4to5-migrate. Skill: <path-to-skill>. You ARE the orchestrator.

1. Read: SKILL.md, references/recipes/FLOW.md, references/recipes/DEFAULT.md,
   references/recipes/<recipe>/RECIPE.md,
   references/recipes/<recipe>/use-cases/<matching-use-case>.md,
   references/docs/paths/<relevant-catalog-entry>.adoc
2. Read the prompt at: <workspace>/<recipe>/eval-<name>/with_skill/run-1/prompt.md
3. Target file(s) to migrate IN PLACE: <workspace>/.../outputs/<File>.java
4. Skip OpenRewrite pre-step (you cannot run that subprocess). Execute the recipe
   sub-flow per FLOW.md directly. Use Edit/Write.
5. Apply the recipe's edits (per the use-case file). Specific guidance per eval —
   include enough detail that the subagent doesn't have to invent AF5 shape from
   scratch (cite imports, annotation names, parameter signatures verbatim).
6. Write the Result block to <workspace>/.../outputs/result.md.
   Required: `**Result:** ✅ Success | 🚧 Blocker | ⏭️ Rejected | ❌ Failure`,
   `**Recipe:** axon4to5-<recipe>`, `**Notes:** …`.
```

Tips:
- **Drive only `with_skill/run-1` by default.** The `without_skill` baseline is for measuring delta — usually skip unless you need it.
- **Cite imports + annotation names verbatim** in the dispatch prompt. AF5 package paths (`.extension.spring.`, `.messaging.`, `.reflection.` infixes) are the most common silent failures when the subagent guesses.
- **Tell the subagent to NOT invoke another skill / agent recursively** — subagents can't dispatch subagents in this harness. They ARE the orchestrator.
- For Blocker / Rejected evals, instruct: "Do NOT edit the source file" — only write `result.md`.

### Step 3 — Grade

```bash
python3 evals/axon4to5-migrate/run.py grade --iteration 1 --recipe <recipe-name>
```

Writes `grading.json` per run dir (canonical skill-creator schema: `{expectations[], summary{passed,failed,total,pass_rate}}`).

### Step 4 — Aggregate + dashboard

```bash
python3 evals/axon4to5-migrate/run.py aggregate --iteration 1 --recipe <recipe-name>
```

Produces `workspace/iteration-1/<recipe>/benchmark.{json,md}` via skill-creator's official `aggregate_benchmark.py`. Then regenerate the HTML dashboard:

```bash
VIEWER=~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/eval-viewer/generate_review.py
WS=evals/axon4to5-migrate/workspace/iteration-1/<recipe-name>
~/.claude/venv/bin/python "$VIEWER" "$WS" \
  --skill-name "axon4to5-migrate/<recipe-name>" \
  --benchmark "$WS/benchmark.json" \
  --static "$WS/dashboard.html"
```

Open `evals/axon4to5-migrate/workspace/iteration-1/<recipe-name>/dashboard.html` in a browser.

### Step 5 — Status snapshot any time

```bash
python3 evals/axon4to5-migrate/run.py status --iteration 1 --recipe <recipe-name>
```

Shows per-eval table: source migrated, result.md written, graded, pass count.

### Re-running specific evals

After tweaking RECIPE.md or use-cases, prep just the failing evals and dispatch them again:

```bash
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe event-processor --evals 2,5
# dispatch 2 subagents for evals 2 and 5
python3 evals/axon4to5-migrate/run.py grade --iteration 1 --recipe event-processor --filter <eval-name-substring>
```

`prep` overwrites the workspace for the prepped evals (re-copies fixtures, resets `result.md`). Already-green evals stay untouched if you scope `--evals`.

### Adding a new recipe

1. Author `references/recipes/<recipe>/RECIPE.md` (sections per `references/recipes/_template/RECIPE.md`).
2. Author `references/recipes/<recipe>/use-cases/*.md` (markdown-linked from RECIPE.md `# Use cases`).
3. Create `evals/axon4to5-migrate/recipes/<recipe>/evals.json` with eval definitions (canonical skill-creator schema + the `assertions[]` extension).
4. Add any new fixtures to `evals/axon4to5-migrate/fixtures/synthetic/` (or reuse `evals/axon4to5-migrate/fixtures/axon4/heroes/*` for real AF4 sources).
5. `run.py` auto-discovers the new recipe — no script changes needed.
