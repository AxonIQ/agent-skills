#!/usr/bin/env python3
"""Grade one axon4to5-migrate eval run.

Reads eval_metadata.json (with `assertions[]`), then for each assertion evaluates
it against either an output file under <run>/outputs/ or the captured Result-block
file <run>/outputs/result.md. Writes grading.json following the skill-creator
canonical schema:

    {
      "expectations": [{"text": str, "passed": bool, "evidence": str}, …],
      "summary":      {"passed": int, "failed": int, "total": int, "pass_rate": float}
    }

Assertion `target` field:
    "source"                — the in-place migrated file at <run>/outputs/<basename of fixture>
    "secondary:<filename>"  — a sibling file under <run>/outputs/<filename>
    "result"                — <run>/outputs/result.md (orchestrator's Result block)

Assertion `type`:
    grep_require               literal substring MUST appear in target
    grep_forbid                literal substring MUST NOT appear in target
    result_block_contains      alias of grep_require with target=result
    result_block_forbid        alias of grep_forbid  with target=result
    result_block_contains_any  ANY of patterns[] MUST appear in target=result (OR-match)

Usage:
    grade.py --metadata <eval_metadata.json> --run-dir <run-N dir> --out <grading.json>
"""

import argparse
import json
import sys
from pathlib import Path


def _read(p: Path) -> str | None:
    try:
        return p.read_text()
    except FileNotFoundError:
        return None


def _resolve(assertion: dict, run_dir: Path, source_basename: str) -> tuple[Path, str | None]:
    target = assertion.get("target", "source")
    outputs = run_dir / "outputs"
    if target == "source":
        p = outputs / source_basename
    elif target == "result":
        p = outputs / "result.md"
    elif target.startswith("secondary:"):
        p = outputs / target.split(":", 1)[1]
    else:
        p = outputs / target
    return p, _read(p)


def _evaluate(assertion: dict, content: str | None, target_path: Path) -> dict:
    text = assertion["text"]
    kind = assertion["type"]

    if content is None:
        return {"text": text, "passed": False,
                "evidence": f"target file missing: {target_path}"}

    if kind in ("grep_require", "result_block_contains"):
        pat = assertion["pattern"]
        ok = pat in content
        return {"text": text, "passed": ok,
                "evidence": (f"found `{pat}` in {target_path.name}" if ok
                             else f"missing required substring `{pat}` in {target_path.name}")}

    if kind in ("grep_forbid", "result_block_forbid"):
        pat = assertion["pattern"]
        ok = pat not in content
        return {"text": text, "passed": ok,
                "evidence": (f"forbidden `{pat}` absent from {target_path.name} — good" if ok
                             else f"forbidden substring `{pat}` STILL present in {target_path.name}")}

    if kind in ("result_block_contains_any", "grep_require_any"):
        pats = assertion["patterns"]
        hit = next((p for p in pats if p in content), None)
        return {"text": text, "passed": hit is not None,
                "evidence": (f"found `{hit}` in {target_path.name}" if hit
                             else f"none of {pats} found in {target_path.name}")}

    if kind == "grep_forbid_all":
        pats = assertion["patterns"]
        offending = [p for p in pats if p in content]
        return {"text": text, "passed": not offending,
                "evidence": (f"none of {pats} present — good" if not offending
                             else f"forbidden substrings still present: {offending}")}

    return {"text": text, "passed": False, "evidence": f"unknown assertion type `{kind}`"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True, type=Path,
                    help="Path to eval_metadata.json (lives at eval-<name>/ level).")
    ap.add_argument("--run-dir", required=True, type=Path,
                    help="The run-N/ directory containing outputs/.")
    ap.add_argument("--out", required=True, type=Path,
                    help="Where to write grading.json.")
    args = ap.parse_args()

    meta = json.loads(args.metadata.read_text())
    assertions = meta.get("assertions", [])
    fixture = meta.get("fixture", "")
    source_basename = Path(fixture).name

    expectations = []
    for a in assertions:
        path, content = _resolve(a, args.run_dir, source_basename)
        expectations.append(_evaluate(a, content, path))

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    failed = total - passed
    pass_rate = (passed / total) if total else 0.0

    out = {
        "expectations": expectations,
        "summary": {
            "passed":   passed,
            "failed":   failed,
            "total":    total,
            "pass_rate": round(pass_rate, 4),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))

    status = "PASS" if passed == total else "FAIL"
    print(f"{status}  {meta.get('eval_name')}  ({passed}/{total})  pass_rate={pass_rate:.2f}")
    if passed < total:
        for e in expectations:
            if not e["passed"]:
                print(f"      ✗ {e['text']}")
                print(f"        {e['evidence']}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
