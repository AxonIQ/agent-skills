#!/usr/bin/env python3
"""Orchestrator for axon4to5-migrate functional evals.

Runs in three phases:

  prep     — for each eval (or just the ones matching --filter):
                 mk workspace/iteration-N/eval-<name>/{with_skill,without_skill}/{inputs,outputs}/
                 copy AF4 fixture into inputs/
                 write eval_metadata.json
             then print, for each eval, two READY-TO-PASTE prompts:
               - with_skill — for Agent(general-purpose) invocation with skill loaded
               - without_skill — same task, no skill access
             (the human / driving Claude session pastes these into Agent tool calls)

  grade    — for each eval, look at outputs/<filename> in each run dir, invoke grade.py,
             write grading.json + timing.json (timing fed by --timing JSON file).

  aggregate — collate every grading.json into benchmark.{json,md}: pass-rate, mean tokens,
             mean wall-clock, per-eval breakdown, with-skill-vs-baseline delta.

Usage:
    run.py prep      [--iteration N] [--filter <substr>]
    run.py grade     [--iteration N] [--filter <substr>]
    run.py aggregate [--iteration N]
    run.py status    [--iteration N]

The default iteration is the highest existing iteration-<N>/ dir, or 1 if none.

Workspace layout:
    workspace/
      iteration-1/
        eval-aggregate-heroes-dwelling/
          eval_metadata.json
          with_skill/
            inputs/Dwelling.java         # AF4 baseline
            outputs/Dwelling.java        # filled by Agent subagent
            grading.json
            timing.json
          without_skill/
            inputs/Dwelling.java
            outputs/Dwelling.java
            grading.json
            timing.json
        ...
        benchmark.json
        benchmark.md
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Iterable

EVALS_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
WORKSPACE = EVALS_DIR / "workspace"


# ---------------------------------------------------------------------------
# helpers


def load_evals() -> list[dict]:
    return json.loads((EVALS_DIR / "evals.json").read_text())["evals"]


def filter_evals(evals: list[dict], pattern: str | None) -> list[dict]:
    if not pattern:
        return evals
    return [e for e in evals if pattern in e["name"]]


def iteration_dir(n: int | None) -> Path:
    if n is None:
        existing = sorted(WORKSPACE.glob("iteration-*"))
        if existing:
            return existing[-1]
        return WORKSPACE / "iteration-1"
    return WORKSPACE / f"iteration-{n}"


def eval_dir(it: Path, name: str) -> Path:
    return it / f"eval-{name}"


def relpath_from_repo(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT))


# ---------------------------------------------------------------------------
# prep


def prep(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    evals = filter_evals(load_evals(), args.filter)
    if not evals:
        print(f"no evals match filter `{args.filter}`")
        return 1

    print(f"# Workspace: {relpath_from_repo(it)}\n")
    for ev in evals:
        ed = eval_dir(it, ev["name"])
        for run in ("with_skill", "without_skill"):
            (ed / run / "inputs").mkdir(parents=True, exist_ok=True)
            (ed / run / "outputs").mkdir(parents=True, exist_ok=True)

        src = REPO_ROOT / SKILL_DIR.relative_to(REPO_ROOT) / ev["input"]
        if not src.is_file():
            # ev["input"] starts with `evals/fixtures/…` (relative to skill)
            src = SKILL_DIR / ev["input"]
        if not src.is_file():
            print(f"ERROR: source fixture missing for {ev['name']}: {ev['input']}",
                  file=sys.stderr)
            return 1

        input_filename = src.name
        for run in ("with_skill", "without_skill"):
            shutil.copy2(src, ed / run / "inputs" / input_filename)

        metadata = {
            "eval_id": ev["id"],
            "eval_name": ev["name"],
            "recipe": ev["recipe"],
            "prompt": ev["prompt"],
            "input": ev["input"],
            "output_filename": ev["output_filename"],
            "assertions": ev["assertions"],
        }
        (ed / "eval_metadata.json").write_text(json.dumps(metadata, indent=2))

        # Print the ready-to-paste subagent prompts
        skill_abs = relpath_from_repo(SKILL_DIR)
        input_with = relpath_from_repo(ed / "with_skill" / "inputs" / input_filename)
        output_with = relpath_from_repo(ed / "with_skill" / "outputs" / ev["output_filename"])
        input_baseline = relpath_from_repo(ed / "without_skill" / "inputs" / input_filename)
        output_baseline = relpath_from_repo(ed / "without_skill" / "outputs" / ev["output_filename"])

        # Substitute the placeholders in the prompt
        prompt_with = (ev["prompt"]
                       .replace("INPUT_PATH", input_with)
                       .replace("OUTPUT_PATH", output_with))
        # Baseline strips any skill-aware framing
        baseline_intro = (
            "You are migrating an Axon Framework 4 source file to Axon Framework 5. "
            "Apply the standard AF4→AF5 mechanical edits you know: handler/annotation moves, "
            "@EventSourced/@EventSourcedEntity for aggregates, @Namespace for event processors, "
            "import package moves to org.axonframework.messaging.*, async dispatch via "
            "CompletableFuture chains, etc. Don't invent new behavior — just port the AF4 patterns "
            "to AF5 equivalents."
        )
        # Drop the leading "You have the axon4to5-migrate skill loaded." sentence for baseline
        baseline_body = ev["prompt"].split(". ", 1)[1] if ". " in ev["prompt"] else ev["prompt"]
        prompt_baseline = (baseline_intro + " " + baseline_body
                           .replace("INPUT_PATH", input_baseline)
                           .replace("OUTPUT_PATH", output_baseline)
                           .replace("per references/" + ev["recipe"] + ".md", "")
                           .replace("the axon4to5-migrate skill", "your AF4→AF5 migration knowledge"))

        print(f"## eval {ev['id']}: {ev['name']}\n")
        print("### with_skill prompt — give this to a subagent that has the skill loaded:")
        print("```")
        print(f"Skill directory available at: {skill_abs}")
        print(f"Read references/{ev['recipe']}.md in that directory.")
        print(f"Read INPUT_PATH = {input_with}")
        print(f"Migrated output → OUTPUT_PATH = {output_with}")
        print()
        print(prompt_with)
        print("```\n")
        print("### without_skill prompt — give this to a baseline subagent (NO skill):")
        print("```")
        print(f"Read INPUT_PATH = {input_baseline}")
        print(f"Migrated output → OUTPUT_PATH = {output_baseline}")
        print()
        print(prompt_baseline)
        print("```\n")
    return 0


# ---------------------------------------------------------------------------
# grade


def grade(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    evals = filter_evals(load_evals(), args.filter)
    grader = EVALS_DIR / "grade.py"
    python = shutil.which("python3") or sys.executable

    rc = 0
    for ev in evals:
        ed = eval_dir(it, ev["name"])
        if not ed.exists():
            print(f"SKIP  {ev['name']} (no workspace — run prep first)")
            continue
        metadata_path = ed / "eval_metadata.json"
        for run in ("with_skill", "without_skill"):
            out_path = ed / run / "outputs" / ev["output_filename"]
            grading_out = ed / run / "grading.json"
            result = subprocess.run(
                [python, str(grader),
                 "--metadata", str(metadata_path),
                 "--output", str(out_path),
                 "--out", str(grading_out)],
                cwd=REPO_ROOT,
            )
            tag = f"{ev['name']} :: {run}"
            if result.returncode != 0:
                rc = 1
    return rc


# ---------------------------------------------------------------------------
# aggregate


def _safe_load(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def aggregate(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    evals = load_evals()

    rows = []
    for ev in evals:
        ed = eval_dir(it, ev["name"])
        row = {"eval_id": ev["id"], "eval_name": ev["name"], "recipe": ev["recipe"]}
        for run in ("with_skill", "without_skill"):
            grading = _safe_load(ed / run / "grading.json")
            timing = _safe_load(ed / run / "timing.json")
            row[run] = {
                "passed": grading.get("passed") if grading else None,
                "total": grading.get("total") if grading else None,
                "all_pass": grading.get("all_pass", False) if grading else False,
                "total_tokens": timing.get("total_tokens") if timing else None,
                "duration_ms": timing.get("duration_ms") if timing else None,
            }
        rows.append(row)

    def aggregate_runs(key: str) -> dict:
        rates = [r[key]["passed"] / r[key]["total"] for r in rows
                 if r[key]["total"]]
        passed_all = sum(1 for r in rows if r[key]["all_pass"])
        tokens = [r[key]["total_tokens"] for r in rows if r[key]["total_tokens"]]
        durs = [r[key]["duration_ms"] for r in rows if r[key]["duration_ms"]]
        return {
            "all_pass_count": passed_all,
            "total_evals": len([r for r in rows if r[key]["total"]]),
            "mean_assertion_pass_rate": (statistics.mean(rates) if rates else None),
            "mean_total_tokens": (statistics.mean(tokens) if tokens else None),
            "mean_duration_ms": (statistics.mean(durs) if durs else None),
        }

    summary = {
        "iteration": it.name,
        "with_skill": aggregate_runs("with_skill"),
        "without_skill": aggregate_runs("without_skill"),
        "evals": rows,
    }

    (it / "benchmark.json").write_text(json.dumps(summary, indent=2))

    # Markdown rendering
    lines = [f"# Benchmark — {it.name}", ""]
    for k in ("with_skill", "without_skill"):
        s = summary[k]
        lines.append(f"## {k}")
        lines.append(f"- passed all-assertions: **{s['all_pass_count']} / {s['total_evals']}**")
        if s["mean_assertion_pass_rate"] is not None:
            lines.append(f"- mean assertion pass rate: {s['mean_assertion_pass_rate']:.2%}")
        if s["mean_total_tokens"]:
            lines.append(f"- mean total_tokens: {s['mean_total_tokens']:,.0f}")
        if s["mean_duration_ms"]:
            lines.append(f"- mean wall-clock: {s['mean_duration_ms']/1000:.1f}s")
        lines.append("")
    lines.append("## Per-eval")
    lines.append("")
    lines.append("| Eval | Recipe | with_skill | without_skill |")
    lines.append("|---|---|---|---|")
    for r in rows:
        ws = r["with_skill"]; wos = r["without_skill"]
        def fmt(run):
            if run["total"] is None:
                return "—"
            mark = "✅" if run["all_pass"] else "❌"
            return f"{mark} {run['passed']}/{run['total']}"
        lines.append(f"| {r['eval_name']} | {r['recipe']} | {fmt(ws)} | {fmt(wos)} |")
    (it / "benchmark.md").write_text("\n".join(lines) + "\n")

    print((it / "benchmark.md").read_text())
    print(f"\nWrote: {relpath_from_repo(it / 'benchmark.json')}")
    print(f"Wrote: {relpath_from_repo(it / 'benchmark.md')}")
    return 0


# ---------------------------------------------------------------------------
# status


def status(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    if not it.exists():
        print(f"no workspace at {it}")
        return 0
    evals = load_evals()
    print(f"# {it.name}")
    print()
    print("| Eval | with_skill output | without_skill output | graded |")
    print("|---|---|---|---|")
    for ev in evals:
        ed = eval_dir(it, ev["name"])
        if not ed.exists():
            continue
        ws_out = ed / "with_skill" / "outputs" / ev["output_filename"]
        wos_out = ed / "without_skill" / "outputs" / ev["output_filename"]
        graded_ws = (ed / "with_skill" / "grading.json").exists()
        graded_wos = (ed / "without_skill" / "grading.json").exists()
        print(f"| {ev['name']} | "
              f"{'✓' if ws_out.exists() else '—'} | "
              f"{'✓' if wos_out.exists() else '—'} | "
              f"{'✓' if graded_ws and graded_wos else '—'} |")
    return 0


# ---------------------------------------------------------------------------
# entrypoint


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prep")
    p_prep.add_argument("--iteration", type=int, default=None)
    p_prep.add_argument("--filter", type=str, default=None)

    p_grade = sub.add_parser("grade")
    p_grade.add_argument("--iteration", type=int, default=None)
    p_grade.add_argument("--filter", type=str, default=None)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--iteration", type=int, default=None)

    p_status = sub.add_parser("status")
    p_status.add_argument("--iteration", type=int, default=None)

    args = ap.parse_args()
    return {"prep": prep, "grade": grade, "aggregate": aggregate, "status": status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
