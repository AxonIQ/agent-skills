# CLAUDE.md

All-file content language: English.

## Multi-language support

This skill must work for **Java, Kotlin, Scala, and any other JVM language** a project may use. Never hardcode
a single-language file filter.

- All grep commands that search source files must include at minimum `--include='*.java' --include='*.kt' --include='*.scala'`. Do not use `--include='*.java'` alone.
- Code examples in atoms/recipes may use Java syntax for conciseness, but the transformation rules apply to all JVM languages — the reader adapts idioms (e.g. `data class` for records in Kotlin, `case class` in Scala).
- `detect:` grep in atom frontmatter is a **first-signal hint**, not a final judgment. A missing grep hit does not prove a pattern is absent — read the source file to confirm before deciding.
- `$SOURCE` may be a `.kt`, `.scala`, or other JVM file. Do not assume `.java` extension anywhere in paths, glob patterns, or file-open instructions.

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
│   ├── command-gateway/evals.json
│   ├── event-processor/evals.json
│   ├── event-store/evals.json
│   ├── interceptors/evals.json
│   ├── query-gateway/evals.json
│   ├── query-handler/evals.json
│   └── saga/evals.json
└── workspace/iteration-N/<recipe>/eval-<name>/{with_skill,without_skill}/run-1/
```

`run.py` does NOT invoke Claude. The actual migrations are run by **subagents dispatched from this conversation** (the `Agent` tool). Pipeline:

```
prep → [DISPATCH SUBAGENTS via Agent tool] → grade → aggregate
```

Every eval's `skill_args` is `{configuration: spring|native, skip-openrewrite: "true"}` and the eval prompt explicitly tells the subagent to **skip SKILL.md Step 1** (the AskUserQuestion Q1/Q2/Q3) and **skip Step 2.5** (progress tracking). This is required because (a) subagents can't recursively invoke another Skill so they can't run the OpenRewrite bulk pass from Step 3 Approach A, (b) eval fixtures aren't real Maven/Gradle projects, and (c) there is no project root to host `.axon4to5-migration/progress.md`. Subagents still load `patterns/ALL_IN_ONE.md` + the specific pattern files named in the eval prompt and apply them to the staged fixture in place.

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
You are executing eval <N> of axon4to5-migrate. The skill lives at <path-to-skill>.

1. Read: <skill>/SKILL.md, <skill>/patterns/ALL_IN_ONE.md
   (and <skill>/examples/ALL_EXAMPLES.md if the prompt names a specific
   example file you need a full walkthrough for).
2. Read the prompt at: <workspace>/<recipe>/eval-<name>/with_skill/run-1/prompt.md
3. Target file(s) to migrate IN PLACE: <workspace>/.../outputs/<File>.java
4. Skip SKILL.md Step 1 (AskUserQuestion Q1/Q2/Q3) and Step 2.5 (progress
   tracking) — the eval prompt pins configuration + Approach B + skip-openrewrite.
5. Identify the AF4 shapes in the source against the pattern catalog, apply the
   matching patterns IN PLACE (Edit/Write). Specific guidance per eval — the
   prompt already cites the relevant imports/annotation names verbatim.
6. Write the Result block to <workspace>/.../outputs/result.md.
   Required: `**Result:** ✅ Success | 🚧 Blocker | ⏭️ Rejected | ❌ Failure`,
   `**Recipe:** axon4to5-<recipe>`, `**Notes:** …`.
```

Tips:
- **Drive only `with_skill/run-1` by default.** The `without_skill` baseline is for measuring delta — usually skip unless you need it.
- **Cite imports + annotation names verbatim** in the dispatch prompt. AF5 package paths (`.extension.spring.`, `.messaging.`, `.reflection.` infixes) are the most common silent failures when the subagent guesses.
- **Tell the subagent to NOT invoke another skill / agent recursively** — subagents can't dispatch subagents in this harness.
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

After tweaking patterns or examples, prep just the failing evals and dispatch them again:

```bash
python3 evals/axon4to5-migrate/run.py prep --iteration 1 --recipe event-processor --evals 2,5
# dispatch 2 subagents for evals 2 and 5
python3 evals/axon4to5-migrate/run.py grade --iteration 1 --recipe event-processor --filter <eval-name-substring>
```

`prep` overwrites the workspace for the prepped evals (re-copies fixtures, resets `result.md`). Already-green evals stay untouched if you scope `--evals`.

### Adding a new eval recipe (grouping)

Recipes are workspace groupings for the eval pipeline, not a runtime concept in SKILL.md any more — SKILL.md is a flat pattern catalog. Each `recipes/<name>/evals.json` just selects which fixtures + assertions belong together.

1. Confirm the patterns the new recipe exercises already exist under `patterns/<phase>/*` (and corresponding examples under `examples/<area>/*`). If not, add them via `axon4to5-knowledge-update` first.
2. Create `evals/axon4to5-migrate/recipes/<recipe>/evals.json` with eval definitions (canonical skill-creator schema + the `assertions[]` extension). Each eval's `prompt` should name the specific pattern + example files it covers.
3. Add any new fixtures to `evals/axon4to5-migrate/fixtures/synthetic/` (or reuse `evals/axon4to5-migrate/fixtures/axon4/heroes/*` for real AF4 sources).
4. `run.py` auto-discovers the new recipe — no script changes needed.
