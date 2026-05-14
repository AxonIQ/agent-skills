# Evals — functional, with-skill vs baseline

These evals **actually run the skill**. For each test case, two Agent subagents migrate the same AF4 file: one reads the skill's recipe, one works from built-in AF4→AF5 knowledge only. A grader then greps both outputs for AF5 must-haves / forbidden AF4 leftovers. The benchmark shows the skill's lift over the baseline.

## Layout

```
evals/
├── evals.json          # test cases: prompt + assertions per AF4 fixture
├── manifest.tsv        # source-of-truth list of files bundled into fixtures/
├── fixtures/           # AF4 inputs + AF5 references (copied via build.sh)
├── build.sh            # populates fixtures/ from .knowledge/repositories/
├── grade.py            # one-eval grader: outputs/<file> → grading.json
├── run.py              # orchestrator: prep, grade, aggregate, status
├── README.md           # this file
└── workspace/
    └── iteration-N/
        └── eval-<name>/
            ├── eval_metadata.json
            ├── with_skill/   { inputs/  outputs/  grading.json  timing.json }
            └── without_skill/{ inputs/  outputs/  grading.json  timing.json }
```

## Loop

```bash
# 1) build fixtures (one-time, or after upstream changes)
./build.sh
./build.sh check                                    # exit 1 on drift

# 2) prep — copies AF4 input, prints two ready-to-paste subagent prompts
./run.py prep --iteration 1 --filter aggregate-heroes-dwelling

# 3) execute — driving Claude spawns Agent subagents with the printed prompts.
#    The with_skill subagent reads references/<recipe>.md.
#    The without_skill subagent has no access to the skill files.
#    Each writes its migrated file to outputs/<filename>.

# 4) record timing — for each completed subagent, capture total_tokens + duration_ms
#    into the run's timing.json (the driving session does this from Agent notifications).

# 5) grade — greps each output against the eval's assertions
./run.py grade --iteration 1

# 6) aggregate — produces benchmark.json + benchmark.md for the iteration
./run.py aggregate --iteration 1

# any time:
./run.py status --iteration 1                       # which evals have outputs / grading?
```

## Case schema (`evals.json`)

```json
{
  "skill_name": "axon4to5-migrate",
  "fixtures_root": "evals/fixtures",
  "evals": [
    {
      "id": 1,
      "name": "aggregate-heroes-dwelling",
      "recipe": "aggregate",
      "input": "evals/fixtures/axon4/heroes/Dwelling.java",
      "output_filename": "Dwelling.java",
      "prompt": "...migrate INPUT_PATH to AF5; save to OUTPUT_PATH...",
      "assertions": [
        {"text": "...", "type": "grep_require", "pattern": "@EventSourced"},
        {"text": "...", "type": "grep_forbid",  "pattern": "@AggregateIdentifier"}
      ]
    }
  ]
}
```

`INPUT_PATH` / `OUTPUT_PATH` are placeholders that `run.py prep` substitutes with workspace-relative paths before printing the subagent prompt.

Assertion types:
- `grep_require` — pattern (literal substring) MUST appear in the produced output file.
- `grep_forbid` — pattern MUST NOT appear.

## What the benchmark looks like

`benchmark.md` shows pass-rate, mean tokens, mean wall-clock for each configuration, plus a per-eval table:

```
## with_skill
- passed all-assertions: 1 / 2
- mean assertion pass rate: 94.74%
- mean total_tokens: 33,284
- mean wall-clock: 17.4s

## without_skill
- passed all-assertions: 0 / 2
- mean assertion pass rate: 75.88%
- mean total_tokens: 28,986
- mean wall-clock: 22.9s

| Eval | with_skill | without_skill |
|---|---|---|
| aggregate-heroes-dwelling | ❌ 17/19 | ❌ 13/19 |
| query-handler-heroes-getbyid | ✅ 6/6 | ❌ 5/6 |
```

When `with_skill` fails an assertion, it's a real signal that the recipe's instructions weren't precise enough for the agent to land the exact AF5 shape — an actionable lead for tightening the recipe.

When `without_skill` passes while `with_skill` fails, the skill is hurting more than helping — investigate.

## Coverage

11 test cases covering every recipe (`aggregate` ×2, `event-processor`, `command-gateway` ×2, `query-gateway`, `query-handler`, `event-storage-engine` ×3, `saga`). Drawn from real AF4↔AF5 pairs across heroes / gamerental / bike-rental-extended.

## Add a case

1. Pair an AF4 source with its AF5 reference in `.knowledge/repositories/axon-examples/axon{4,5}/`.
2. Add the AF4 file to `manifest.tsv` and run `./build.sh` to bundle it.
3. Add an entry to `evals.json` with a prompt + `grep_require` / `grep_forbid` assertions derived from the AF5 reference.
4. `./run.py prep --filter <new-eval-name>`, spawn the printed subagents, grade, aggregate.
