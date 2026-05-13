#!/usr/bin/env python3
"""Grade one eval run by checking assertions against a produced output file.

Reads eval metadata (assertions[]), opens the output file, evaluates each
assertion. Writes grading.json next to the output following the skill-creator
schema: { eval_id, eval_name, passed, total, expectations: [{text, passed, evidence}] }.

Usage:
    grade.py --metadata <eval_metadata.json> --output <produced-file> --out <grading.json>

Assertion types supported:
    grep_require — pattern (literal substring) MUST appear in output file
    grep_forbid  — pattern MUST NOT appear in output file
    file_exists  — output file must exist (implicit; failing this short-circuits)

Exit code: 0 if all assertions passed, 1 if any failed (or file missing).
"""

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: Path) -> dict:
    return json.loads(path.read_text())


def evaluate_assertion(assertion: dict, content: str | None) -> dict:
    text = assertion["text"]
    kind = assertion["type"]
    pattern = assertion.get("pattern", "")

    if content is None:
        return {
            "text": text,
            "passed": False,
            "evidence": f"output file missing — assertion `{kind}: {pattern}` not evaluable",
        }

    if kind == "grep_require":
        present = pattern in content
        return {
            "text": text,
            "passed": present,
            "evidence": (
                f"found `{pattern}`" if present
                else f"missing required substring `{pattern}` in output"
            ),
        }

    if kind == "grep_forbid":
        present = pattern in content
        return {
            "text": text,
            "passed": not present,
            "evidence": (
                f"forbidden substring `{pattern}` absent — good" if not present
                else f"forbidden substring `{pattern}` STILL present in output"
            ),
        }

    if kind == "file_exists":
        # content is non-None ⇒ file exists
        return {"text": text, "passed": True, "evidence": "output file exists"}

    return {
        "text": text,
        "passed": False,
        "evidence": f"unknown assertion type `{kind}`",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True, type=Path,
                    help="Path to eval_metadata.json (or evals.json entry).")
    ap.add_argument("--output", required=True, type=Path,
                    help="Path to the file produced by the subagent.")
    ap.add_argument("--out", required=True, type=Path,
                    help="Where to write grading.json.")
    args = ap.parse_args()

    metadata = load_metadata(args.metadata)
    # metadata may be a full evals.json entry OR a single eval_metadata.json
    if "assertions" not in metadata and "eval" in metadata:
        metadata = metadata["eval"]
    assertions = metadata.get("assertions", [])
    eval_id = metadata.get("id") or metadata.get("eval_id")
    eval_name = metadata.get("name") or metadata.get("eval_name", "")

    content = args.output.read_text() if args.output.is_file() else None
    expectations = [evaluate_assertion(a, content) for a in assertions]

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    all_pass = passed == total and content is not None

    result = {
        "eval_id": eval_id,
        "eval_name": eval_name,
        "output_path": str(args.output),
        "output_exists": content is not None,
        "passed": passed,
        "total": total,
        "all_pass": all_pass,
        "expectations": expectations,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))

    # Console summary
    status = "PASS" if all_pass else "FAIL"
    print(f"{status}  {eval_name}  ({passed}/{total})")
    if not all_pass:
        for e in expectations:
            if not e["passed"]:
                print(f"      ✗ {e['text']}")
                print(f"        {e['evidence']}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
