#!/usr/bin/env python3
"""Orchestrator for axon4to5-migrate single-mode aggregate evals (skill-creator layout).

Workspace layout produced (canonical skill-creator shape):

    evals/workspace/iteration-N/
      eval-<name>/
        eval_metadata.json              ← {eval_id, eval_name, prompt, expectations[], assertions[], …}
        with_skill/
          run-1/
            outputs/<File>.java         ← AF4 fixture copied in; Skill rewrites in place
            outputs/<Secondaries>.java
            outputs/result.md           ← subagent pastes the orchestrator's Result block here
            grading.json                ← canonical {expectations[], summary{}}
            timing.json                 ← {total_tokens, duration_ms, total_duration_seconds}
            prompt.md                   ← ready-to-paste subagent prompt (this script generates it)
        without_skill/
          run-1/…                       ← same shape; baseline (no Skill loaded)

Phases:
    prep      stage fixtures + write eval_metadata.json + render prompt.md per run
    grade     invoke grade.py per run; write grading.json
    aggregate delegate to skill-creator's aggregate_benchmark.py → benchmark.{json,md}
    status    table of which evals are prepped / have outputs / graded

Usage:
    run.py prep      [--iteration N] [--filter <substr>] [--evals <id,id,…>] [--runs M]
    run.py grade     [--iteration N] [--filter <substr>]
    run.py aggregate [--iteration N]
    run.py status    [--iteration N]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
WORKSPACE = EVALS_DIR / "workspace"

CONFIGS = ("with_skill", "without_skill")


def load_evals() -> list[dict]:
    return json.loads((EVALS_DIR / "evals.json").read_text())["evals"]


def filter_evals(evs: list[dict], pattern: str | None, ids: list[int] | None) -> list[dict]:
    if ids:
        return [e for e in evs if e["id"] in ids]
    if pattern:
        return [e for e in evs if pattern in e["name"] or pattern in (e.get("category") or "")]
    return evs


def iteration_dir(n: int | None) -> Path:
    if n is None:
        existing = sorted(WORKSPACE.glob("iteration-*"))
        return existing[-1] if existing else (WORKSPACE / "iteration-1")
    return WORKSPACE / f"iteration-{n}"


def eval_dir(it: Path, name: str) -> Path:
    return it / f"eval-{name}"


def _copy_fixture(fixture: str, dest_dir: Path) -> Path:
    src = EVALS_DIR / "fixtures" / fixture
    if not src.is_file():
        raise FileNotFoundError(f"fixture not found: {src}")
    dest = dest_dir / src.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def _render_skill_args(args_obj: dict, source_path: Path) -> str:
    parts = []
    for key in ("framework", "configuration", "mode", "source"):
        val = args_obj.get(key, "")
        if key == "source" and val == "$SOURCE":
            val = str(source_path)
        if val == "":
            continue  # the "missing source" eval intentionally omits source
        parts.append(f"{key}={val}")
    return " ".join(parts)


def _build_prompt(ev: dict, run_dir: Path, source_path: Path, with_skill: bool) -> str:
    skill_args = _render_skill_args(ev["skill_args"], source_path)
    body = (ev["prompt"]
            .replace("$SKILL_DIR", str(SKILL_DIR))
            .replace("$SOURCE", str(source_path))
            .replace("$WORKSPACE", str(run_dir)))

    pinned = ev.get("pinned_decisions") or {}
    pinned_block = ""
    if pinned:
        pinned_block = "Pinned decisions (the orchestrator MUST NOT prompt the user for these):\n"
        for k, v in pinned.items():
            pinned_block += f"  - {k} = {v}\n"
        pinned_block += "\n"

    intro = (
        "You have the `axon4to5-migrate` Skill loaded at:\n  " + str(SKILL_DIR) + "\n"
        if with_skill else
        "NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, "
        "@EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender "
        "as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.\n"
    )

    output_capture = (
        "When the orchestrator finishes, COPY its final Result block VERBATIM "
        f"(starts with `**Result:**`, ends after the last bullet) to:\n  {run_dir}/outputs/result.md\n"
        "Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), "
        "copy that stop message instead.\n"
    )

    return (
        f"# Eval {ev['id']}: {ev['name']}\n\n"
        f"{intro}\n"
        f"## Skill invocation arguments (use exactly)\n`{skill_args}`\n\n"
        f"{pinned_block}"
        f"## Task\n{body}\n\n"
        f"## Result capture\n{output_capture}\n"
    )


def prep(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    ids = [int(x) for x in args.evals.split(",")] if args.evals else None
    evs = filter_evals(load_evals(), args.filter, ids)
    if not evs:
        print(f"no evals match (filter={args.filter}, ids={ids})")
        return 1

    print(f"# Workspace: {it}\n")
    for ev in evs:
        ed = eval_dir(it, ev["name"])
        ed.mkdir(parents=True, exist_ok=True)

        # eval-level metadata (one per eval, sibling of config dirs)
        metadata = {
            "eval_id":            ev["id"],
            "eval_name":          ev["name"],
            "prompt":             ev["prompt"],
            "expected_output":    ev.get("expected_output"),
            "expectations":       ev.get("expectations", []),
            # extensions for our deterministic grader
            "category":           ev.get("category"),
            "fixture":            ev["fixture"],
            "secondary_fixtures": ev.get("secondary_fixtures") or [],
            "skill_args":         ev.get("skill_args", {}),
            "pinned_decisions":   ev.get("pinned_decisions") or {},
            "expected_result":    ev.get("expected_result"),
            "expected_blocker":   ev.get("expected_blocker"),
            "assertions":         ev["assertions"],
        }
        (ed / "eval_metadata.json").write_text(json.dumps(metadata, indent=2))

        for config in CONFIGS:
            for r in range(1, args.runs + 1):
                run_dir = ed / config / f"run-{r}"
                outputs = run_dir / "outputs"
                outputs.mkdir(parents=True, exist_ok=True)

                src_path = _copy_fixture(ev["fixture"], outputs)
                for sec in ev.get("secondary_fixtures") or []:
                    _copy_fixture(sec, outputs)
                # result.md placeholder — subagent overwrites with the orchestrator's block
                (outputs / "result.md").write_text("")

                prompt = _build_prompt(ev, run_dir, src_path, with_skill=(config == "with_skill"))
                (run_dir / "prompt.md").write_text(prompt)

        print(f"## eval {ev['id']}: {ev['name']}  ({ev.get('category')})  expect={ev.get('expected_result')}")
        for config in CONFIGS:
            for r in range(1, args.runs + 1):
                print(f"  {config}/run-{r}/prompt.md")
        print()
    return 0


def grade(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    evs = filter_evals(load_evals(), args.filter, None)
    grader = EVALS_DIR / "grade.py"
    python = shutil.which("python3") or sys.executable

    rc = 0
    for ev in evs:
        ed = eval_dir(it, ev["name"])
        if not ed.exists():
            continue
        meta = ed / "eval_metadata.json"
        for config in CONFIGS:
            cfg_dir = ed / config
            if not cfg_dir.exists():
                continue
            for run_dir in sorted(cfg_dir.glob("run-*")):
                grading_out = run_dir / "grading.json"
                result = subprocess.run([
                    python, str(grader),
                    "--metadata", str(meta),
                    "--run-dir", str(run_dir),
                    "--out", str(grading_out),
                ])
                if result.returncode != 0:
                    rc = 1
    return rc


def aggregate(args: argparse.Namespace) -> int:
    """Delegate to skill-creator's aggregate_benchmark.py for canonical benchmark.json."""
    it = iteration_dir(args.iteration)
    sc_root = Path(os.path.expanduser(
        "~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator"))
    script = sc_root / "scripts" / "aggregate_benchmark.py"
    if not script.is_file():
        print(f"ERROR: skill-creator aggregate_benchmark.py not found at {script}", file=sys.stderr)
        return 2
    python = os.path.expanduser("~/.claude/venv/bin/python")
    if not Path(python).is_file():
        python = shutil.which("python3") or sys.executable
    cmd = [python, "-m", "scripts.aggregate_benchmark", str(it),
           "--skill-name", "axon4to5-migrate"]
    result = subprocess.run(cmd, cwd=sc_root)
    return result.returncode


def status(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    if not it.exists():
        print(f"no workspace at {it}")
        return 0
    evs = load_evals()
    print(f"# {it.name}\n")
    print("| ID | Eval | category | expected | with_skill run-1 outputs | result.md | graded | pass |")
    print("|---|---|---|---|---|---|---|---|")
    for ev in evs:
        ed = eval_dir(it, ev["name"])
        if not ed.exists():
            continue
        run_dir = ed / "with_skill" / "run-1"
        src = run_dir / "outputs" / Path(ev["fixture"]).name
        result_md = run_dir / "outputs" / "result.md"
        grading = run_dir / "grading.json"
        pass_str = "—"
        if grading.exists():
            g = json.loads(grading.read_text())
            s = g.get("summary", {})
            pass_str = f"{s.get('passed', 0)}/{s.get('total', 0)}"
        print(f"| {ev['id']} | {ev['name']} | {ev.get('category')} | {ev.get('expected_result')} | "
              f"{'✓' if src.exists() else '—'} | "
              f"{'✓' if result_md.exists() and result_md.stat().st_size > 0 else '—'} | "
              f"{'✓' if grading.exists() else '—'} | {pass_str} |")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prep")
    p_prep.add_argument("--iteration", type=int, default=None)
    p_prep.add_argument("--filter", type=str, default=None)
    p_prep.add_argument("--evals", type=str, default=None)
    p_prep.add_argument("--runs", type=int, default=1,
                        help="Runs per (eval, config). Default 1; bump to 3 for variance analysis.")

    p_grade = sub.add_parser("grade")
    p_grade.add_argument("--iteration", type=int, default=None)
    p_grade.add_argument("--filter", type=str, default=None)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--iteration", type=int, default=None)

    p_stat = sub.add_parser("status")
    p_stat.add_argument("--iteration", type=int, default=None)

    args = ap.parse_args()
    return {"prep": prep, "grade": grade, "aggregate": aggregate, "status": status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
