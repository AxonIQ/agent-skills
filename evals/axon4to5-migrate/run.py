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
    run       execute prepped evals via `claude -p` (parallel); writes timing.json per run dir
    grade     invoke grade.py per run; write grading.json
    aggregate delegate to skill-creator's aggregate_benchmark.py → benchmark.{json,md}
    status    table of which evals are prepped / have outputs / graded

Usage:
    run.py prep      [--iteration N] [--filter <substr>] [--evals <id,id,…>] [--runs M]
    run.py run       [--iteration N] [--recipe <name>] [--filter <substr>] [--evals <id,id,…>]
                     [--baseline] [--workers N] [--timeout N] [--model <id>]
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
import time as _time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Layout (repo-rooted, decoupled from any specific developer's filesystem):
#   <repo>/
#     evals/<skill-name>/      ← EVALS_DIR (this file lives in run.py here)
#     skills/<skill-name>/     ← SKILL_DIR (same basename as EVALS_DIR)
EVALS_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVALS_DIR.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / EVALS_DIR.name
WORKSPACE = EVALS_DIR / "workspace"
RECIPES_ROOT = EVALS_DIR / "recipes"

if not SKILL_DIR.is_dir():
    raise SystemExit(
        f"run.py expected the skill at {SKILL_DIR} (mirroring this evals dir's name `{EVALS_DIR.name}`) "
        f"but no such directory exists. Check the repo layout."
    )

CONFIGS = ("with_skill", "without_skill")


def discover_recipes() -> list[str]:
    """Every subdirectory of evals/recipes/ that has an evals.json is a recipe."""
    if not RECIPES_ROOT.is_dir():
        return []
    return sorted(d.name for d in RECIPES_ROOT.iterdir()
                  if d.is_dir() and (d / "evals.json").is_file())


def resolve_recipes(recipe_arg: str | None) -> list[str]:
    """`--recipe` accepts a single name, a comma-separated list, or `all` / None → every discovered recipe."""
    all_recipes = discover_recipes()
    if not all_recipes:
        return []
    if not recipe_arg or recipe_arg == "all":
        return all_recipes
    requested = [r.strip() for r in recipe_arg.split(",")]
    unknown = [r for r in requested if r not in all_recipes]
    if unknown:
        raise SystemExit(f"unknown recipe(s): {unknown}; available: {all_recipes}")
    return requested


def load_evals(recipe: str) -> list[dict]:
    path = RECIPES_ROOT / recipe / "evals.json"
    if not path.is_file():
        raise SystemExit(f"evals.json not found for recipe `{recipe}` at {path}")
    return json.loads(path.read_text())["evals"]


def filter_evals(evs: list[dict], pattern: str | None, ids: list[int] | None) -> list[dict]:
    if ids:
        return [e for e in evs if e["id"] in ids]
    if pattern:
        return [e for e in evs if pattern in e["name"] or pattern in (e.get("category") or "")]
    return evs


def iteration_dir(n: int | None) -> Path:
    if n is None:
        # `iteration-1`, `iteration-2`, … lives directly under WORKSPACE; per-recipe sub-dirs go inside.
        existing = sorted(WORKSPACE.glob("iteration-*"))
        return existing[-1] if existing else (WORKSPACE / "iteration-1")
    return WORKSPACE / f"iteration-{n}"


def recipe_dir(it: Path, recipe: str) -> Path:
    return it / recipe


def eval_dir(it: Path, recipe: str, name: str) -> Path:
    return recipe_dir(it, recipe) / f"eval-{name}"


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
    # Render keys in a stable, copy-pastable order. `skip-openrewrite` last so it reads as an opt-in switch.
    for key in ("framework", "configuration", "mode", "source", "execution", "skip-openrewrite"):
        val = args_obj.get(key, "")
        if key == "source" and val == "$SOURCE":
            val = str(source_path)
        if val == "":
            continue  # e.g. the "missing source" eval intentionally omits source
        parts.append(f"{key}={val}")
    return " ".join(parts)


def _build_prompt(ev: dict, run_dir: Path, source_path: Path, with_skill: bool) -> str:
    skill_args = _render_skill_args(ev["skill_args"], source_path)
    body = (ev["prompt"]
            .replace("$SKILL_DIR", str(SKILL_DIR))
            .replace("$SOURCE", str(source_path))
            .replace("$WORKSPACE", str(run_dir)))

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
        f"## Task\n{body}\n\n"
        f"## Result capture\n{output_capture}\n"
    )


def prep(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    ids = [int(x) for x in args.evals.split(",")] if args.evals else None
    recipes = resolve_recipes(args.recipe)
    if not recipes:
        print(f"no recipes found under {RECIPES_ROOT}")
        return 1

    print(f"# Workspace: {it}\n")
    total_prepped = 0
    for recipe in recipes:
        evs = filter_evals(load_evals(recipe), args.filter, ids)
        if not evs:
            print(f"## recipe `{recipe}` — no evals match (filter={args.filter}, ids={ids})\n")
            continue
        print(f"# Recipe `{recipe}` — {len(evs)} evals\n")
        for ev in evs:
            ed = eval_dir(it, recipe, ev["name"])
            ed.mkdir(parents=True, exist_ok=True)

            metadata = {
                "eval_id":            ev["id"],
                "eval_name":          ev["name"],
                "recipe":             recipe,
                "prompt":             ev["prompt"],
                "expected_output":    ev.get("expected_output"),
                "expectations":       ev.get("expectations", []),
                # extensions for our deterministic grader
                "category":           ev.get("category"),
                "fixture":            ev["fixture"],
                "secondary_fixtures": ev.get("secondary_fixtures") or [],
                "skill_args":         ev.get("skill_args", {}),
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
                    (outputs / "result.md").write_text("")

                    prompt = _build_prompt(ev, run_dir, src_path, with_skill=(config == "with_skill"))
                    (run_dir / "prompt.md").write_text(prompt)

            print(f"## {recipe}/eval {ev['id']}: {ev['name']}  ({ev.get('category')})  expect={ev.get('expected_result')}")
            for config in CONFIGS:
                for r in range(1, args.runs + 1):
                    print(f"  {config}/run-{r}/prompt.md")
            print()
            total_prepped += 1
    return 0 if total_prepped > 0 else 1


def grade(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    recipes = resolve_recipes(args.recipe)
    grader = EVALS_DIR / "grade.py"
    python = shutil.which("python3") or sys.executable

    rc = 0
    for recipe in recipes:
        evs = filter_evals(load_evals(recipe), args.filter, None)
        for ev in evs:
            ed = eval_dir(it, recipe, ev["name"])
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
    """Delegate to skill-creator's aggregate_benchmark.py for canonical benchmark.json. Per recipe by default."""
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

    recipes = resolve_recipes(args.recipe)
    rc = 0
    for recipe in recipes:
        target = recipe_dir(it, recipe)
        if not target.exists():
            print(f"SKIP `{recipe}` — no workspace at {target}")
            continue
        print(f"\n# Aggregating recipe `{recipe}` at {target}")
        cmd = [python, "-m", "scripts.aggregate_benchmark", str(target),
               "--skill-name", f"axon4to5-migrate/{recipe}"]
        result = subprocess.run(cmd, cwd=sc_root)
        if result.returncode != 0:
            rc = 1
    return rc


def run_single_prompt(
    prompt_path: str,
    run_dir: str,
    repo_root: str,
    timeout: int,
    model: str | None,
) -> dict:
    """Invoke `claude -p` for one eval run; write timing.json; return timing dict.

    Top-level (not nested) so ProcessPoolExecutor can pickle it.
    """
    start = _time.time()
    prompt_text = Path(prompt_path).read_text()

    cmd = [
        "claude", "-p", prompt_text,
        "--add-dir", repo_root,
        "--output-format", "stream-json",
        "--verbose",
    ]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=repo_root, env=env,
        )
        rc = result.returncode
        stdout = result.stdout or ""
    except subprocess.TimeoutExpired:
        duration_ms = int((_time.time() - start) * 1000)
        timing = {
            "total_tokens": 0,
            "duration_ms": duration_ms,
            "total_duration_seconds": round(duration_ms / 1000, 1),
            "error": "timeout",
        }
        Path(run_dir, "timing.json").write_text(json.dumps(timing, indent=2))
        return timing

    duration_ms = int((_time.time() - start) * 1000)

    total_tokens = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            if event.get("type") == "result":
                usage = event.get("usage", {})
                total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        except json.JSONDecodeError:
            continue

    timing: dict = {
        "total_tokens": total_tokens,
        "duration_ms": duration_ms,
        "total_duration_seconds": round(duration_ms / 1000, 1),
    }
    if rc != 0:
        timing["error"] = f"exit_code={rc}"

    Path(run_dir, "timing.json").write_text(json.dumps(timing, indent=2))
    return timing


def run_cmd(args: argparse.Namespace) -> int:
    """Execute prepped evals via `claude -p` (parallel); writes timing.json per run dir."""
    it = iteration_dir(args.iteration)
    ids = [int(x) for x in args.evals.split(",")] if args.evals else None
    recipes = resolve_recipes(args.recipe)
    configs = list(CONFIGS) if args.baseline else ["with_skill"]

    tasks: list[tuple[str, str, str, int, Path, Path]] = []
    for recipe in recipes:
        evs = filter_evals(load_evals(recipe), args.filter, ids)
        for ev in evs:
            ed = eval_dir(it, recipe, ev["name"])
            if not ed.exists():
                print(f"SKIP {recipe}/{ev['name']} — not prepped (run `prep` first)")
                continue
            for config in configs:
                for r in range(1, args.runs + 1):
                    run_dir = ed / config / f"run-{r}"
                    prompt_path = run_dir / "prompt.md"
                    if prompt_path.is_file():
                        tasks.append((recipe, ev["name"], config, r, run_dir, prompt_path))
                    else:
                        print(f"SKIP {recipe}/{ev['name']}/{config}/run-{r} — no prompt.md")

    if not tasks:
        print("no prepped evals found")
        return 1

    print(f"dispatching {len(tasks)} eval run(s)  workers={args.workers}  timeout={args.timeout}s\n")

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(
                run_single_prompt,
                str(prompt_path), str(run_dir), str(REPO_ROOT), args.timeout, args.model,
            ): (recipe, name, config, r)
            for recipe, name, config, r, run_dir, prompt_path in tasks
        }

        done = 0
        total = len(future_map)
        for future in as_completed(future_map):
            recipe, name, config, r = future_map[future]
            done += 1
            try:
                timing = future.result()
                err = timing.get("error")
                label = (f"TIMEOUT" if err == "timeout"
                         else f"exit_code≠0" if err
                         else f"{timing['total_duration_seconds']}s / {timing['total_tokens']} tok")
            except Exception as exc:
                label = f"EXCEPTION: {exc}"
            print(f"  [{done}/{total}] {recipe}/{name}/{config}/run-{r}  {label}")

    return 0


def all_cmd(args: argparse.Namespace) -> int:
    """Run the full pipeline: prep → run → grade → aggregate → dashboard."""
    for phase, fn in [("prep", prep), ("run", run_cmd), ("grade", grade),
                      ("aggregate", aggregate), ("dashboard", dashboard)]:
        print(f"\n{'='*60}\n# {phase}\n{'='*60}")
        rc = fn(args)
        if rc != 0:
            print(f"\nERROR: `{phase}` failed (exit {rc}) — stopping.", file=sys.stderr)
            return rc
    return 0


def dashboard(args: argparse.Namespace) -> int:
    """Generate skill-creator HTML viewer; auto-detects previous iteration for comparison."""
    it = iteration_dir(args.iteration)
    recipes = resolve_recipes(args.recipe)

    sc_root = Path(os.path.expanduser(
        "~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator"))
    viewer = sc_root / "eval-viewer" / "generate_review.py"
    if not viewer.is_file():
        print(f"ERROR: generate_review.py not found at {viewer}", file=sys.stderr)
        return 2

    python = os.path.expanduser("~/.claude/venv/bin/python")
    if not Path(python).is_file():
        python = shutil.which("python3") or sys.executable

    it_num = int(it.name.rsplit("-", 1)[-1]) if it.name.startswith("iteration-") else None

    rc = 0
    for recipe in recipes:
        target = recipe_dir(it, recipe)
        if not target.exists():
            print(f"SKIP `{recipe}` — no workspace at {target}")
            continue
        benchmark = target / "benchmark.json"
        if not benchmark.is_file():
            print(f"SKIP `{recipe}` — no benchmark.json (run `aggregate` first)")
            continue

        cmd = [
            python, str(viewer),
            str(target),
            "--skill-name", f"axon4to5-migrate/{recipe}",
            "--benchmark", str(benchmark),
        ]

        if it_num and it_num >= 2:
            prev = recipe_dir(WORKSPACE / f"iteration-{it_num - 1}", recipe)
            if prev.exists():
                cmd.extend(["--previous-workspace", str(prev)])

        out_html = target / "dashboard.html"
        if not args.serve:
            cmd.extend(["--static", str(out_html)])

        result = subprocess.run(cmd)
        if result.returncode != 0:
            rc = 1
            continue

        if not args.serve and out_html.exists():
            print(f"\ndashboard → {out_html}")
            opener = shutil.which("open") or shutil.which("xdg-open")
            if opener:
                subprocess.run([opener, str(out_html)], check=False)

    return rc


def status(args: argparse.Namespace) -> int:
    it = iteration_dir(args.iteration)
    if not it.exists():
        print(f"no workspace at {it}")
        return 0
    recipes = resolve_recipes(args.recipe)
    print(f"# {it.name}\n")
    for recipe in recipes:
        evs = load_evals(recipe)
        print(f"## recipe `{recipe}`\n")
        print("| ID | Eval | category | expected | with_skill run-1 outputs | result.md | graded | pass |")
        print("|---|---|---|---|---|---|---|---|")
        for ev in evs:
            ed = eval_dir(it, recipe, ev["name"])
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
        print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    recipe_help = "Recipe name, comma-separated list, or `all` (default). Discovered from evals/recipes/*/evals.json."

    p_prep = sub.add_parser("prep")
    p_prep.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_prep.add_argument("--iteration", type=int, default=None)
    p_prep.add_argument("--filter", type=str, default=None)
    p_prep.add_argument("--evals", type=str, default=None)
    p_prep.add_argument("--runs", type=int, default=1,
                        help="Runs per (eval, config). Default 1; bump to 3 for variance analysis.")

    p_run = sub.add_parser("run", help="Execute prepped evals via claude -p (parallel).")
    p_run.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_run.add_argument("--iteration", type=int, default=None)
    p_run.add_argument("--filter", type=str, default=None)
    p_run.add_argument("--evals", type=str, default=None, help="Comma-separated eval IDs.")
    p_run.add_argument("--runs", type=int, default=1, help="Runs per (eval, config). Default 1.")
    p_run.add_argument("--baseline", action="store_true",
                       help="Also run without_skill baseline configs.")
    p_run.add_argument("--workers", type=int, default=5,
                       help="Parallel claude -p workers. Default 5.")
    p_run.add_argument("--timeout", type=int, default=300,
                       help="Per-eval timeout in seconds. Default 300.")
    p_run.add_argument("--model", type=str, default=None,
                       help="Model ID for claude -p (default: user's configured model).")

    p_grade = sub.add_parser("grade")
    p_grade.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_grade.add_argument("--iteration", type=int, default=None)
    p_grade.add_argument("--filter", type=str, default=None)

    p_agg = sub.add_parser("aggregate")
    p_agg.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_agg.add_argument("--iteration", type=int, default=None)

    p_all = sub.add_parser("all", help="Full pipeline: prep → run → grade → aggregate → dashboard.")
    p_all.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_all.add_argument("--iteration", type=int, default=None)
    p_all.add_argument("--filter", type=str, default=None)
    p_all.add_argument("--evals", type=str, default=None, help="Comma-separated eval IDs.")
    p_all.add_argument("--runs", type=int, default=1)
    p_all.add_argument("--baseline", action="store_true")
    p_all.add_argument("--workers", type=int, default=5)
    p_all.add_argument("--timeout", type=int, default=300)
    p_all.add_argument("--model", type=str, default=None)
    p_all.add_argument("--serve", action="store_true")

    p_dash = sub.add_parser("dashboard", help="Generate skill-creator HTML viewer after aggregate.")
    p_dash.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_dash.add_argument("--iteration", type=int, default=None)
    p_dash.add_argument("--serve", action="store_true",
                        help="Start live server instead of writing static HTML.")

    p_stat = sub.add_parser("status")
    p_stat.add_argument("--recipe", type=str, default=None, help=recipe_help)
    p_stat.add_argument("--iteration", type=int, default=None)

    args = ap.parse_args()
    return {
        "all": all_cmd, "prep": prep, "run": run_cmd, "grade": grade,
        "aggregate": aggregate, "dashboard": dashboard, "status": status,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
