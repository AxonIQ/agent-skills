#!/usr/bin/env python3
"""Decision-point parser + auto-policy DSL evaluator.

Reads a recipe markdown file, extracts its ## Decision points section, evaluates
each entry's Auto-policy predicates against a pinned state map, and returns the
resolved decisions map (or marks ones that fall back to ask-user / fail).

Used by:
- `run.py resolve <recipe> --pinned k=v ...` — prints per-decision resolution.
- `run.py prep --resolver=automatic` — bakes resolved decisions into the prep'd prompt.

DSL supported (matches references/_template.md "Auto-policy DSL"):
- `pinned.<key> == "<value>"`
- `pinned.<key> in ["<v1>", "<v2>"]`
- `pinned.<key>` (presence check — truthy)
- `decisions.<other-key> == "<value>"`
- `always: <option>`
- `fallback: <ask-user | option-name | fail>`

Sentinel values returned:
- ASK_USER — recipe wants user input; `automatic` mode treats this as failure
- FAIL_DECISION — `fallback: fail` was the only matching line; recipe explicitly refuses
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ASK_USER = "__ASK_USER__"
FAIL_DECISION = "__FAIL__"


# ---------------------------------------------------------------------------
# parsing


@dataclass
class DecisionPoint:
    key: str
    trigger: Optional[str] = None
    auto_policy: list[str] = field(default_factory=list)  # raw predicate lines
    options: list[str] = field(default_factory=list)      # option names (informational)


def parse_decision_points(recipe_path: Path) -> list[DecisionPoint]:
    """Walk a recipe.md, return its DecisionPoints in declaration order."""
    text = recipe_path.read_text()

    # Find the `## Decision points` section
    m = re.search(r"^## Decision points\s*\n(.*?)(?=^## [^\n]|\Z)",
                  text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    section = m.group(1)

    # Split into entries by `### <key>` headings
    entries = re.split(r"^### ([^\n]+)\n", section, flags=re.MULTILINE)
    # entries = [preamble, key1, body1, key2, body2, ...]
    out: list[DecisionPoint] = []
    for i in range(1, len(entries), 2):
        key = entries[i].strip()
        body = entries[i + 1]
        dp = DecisionPoint(key=key)

        # Trigger
        tm = re.search(r"^- \*\*Trigger\*\*:\s*([^\n]+)", body, re.MULTILINE)
        if tm:
            dp.trigger = tm.group(1).strip()

        # Auto-policy: extract the lines under `- **Auto-policy**:`
        ap = re.search(
            r"^- \*\*Auto-policy\*\*:\s*\n((?:    -[^\n]*\n?)+)",
            body, re.MULTILINE,
        )
        if ap:
            for line in ap.group(1).splitlines():
                line = line.strip()
                if not line.startswith("-"):
                    continue
                # Strip leading "- ", drop ALL backticks (some lines wrap the
                # predicate in `code spans` followed by free-form prose).
                payload = line[1:].strip().replace("`", "").strip()
                # Drop trailing "# inline comments" — they are docs, not part of the value
                if "#" in payload:
                    payload = payload.split("#", 1)[0].rstrip()
                if payload:
                    dp.auto_policy.append(payload)

        # Options (informational — extract bullet labels under `- **Options**:`)
        op = re.search(
            r"^- \*\*Options\*\*:\s*\n((?:    -[^\n]*\n?)+)",
            body, re.MULTILINE,
        )
        if op:
            for line in op.group(1).splitlines():
                m2 = re.match(r"\s*-\s+`([^`]+)`", line)
                if m2:
                    dp.options.append(m2.group(1))

        out.append(dp)

    # Filter: skip entries where key looks like noise (e.g., commented-out)
    return [dp for dp in out if dp.key and not dp.key.startswith("(")]


# ---------------------------------------------------------------------------
# DSL evaluator


_PRED_EQ = re.compile(r"""^(pinned|decisions)\.([a-zA-Z0-9_\-]+)\s*==\s*"([^"]*)"\s*:\s*(.+)$""")
_PRED_IN = re.compile(r"""^(pinned|decisions)\.([a-zA-Z0-9_\-]+)\s+in\s+\[(.+?)\]\s*:\s*(.+)$""")
_PRED_PRESENT = re.compile(r"""^pinned\.([a-zA-Z0-9_\-]+)\s*:\s*(.+)$""")
_PRED_ALWAYS = re.compile(r"""^always\s*:\s*(.+)$""")
_PRED_FALLBACK = re.compile(r"""^fallback\s*:\s*(.+?)(?:\s+\(.*\))?$""")


def _strip_value(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s


def evaluate_policy(
    policy_lines: list[str],
    pinned: dict[str, str],
    decisions: dict[str, str],
) -> str:
    """Top-down predicate match. Returns option name, ASK_USER, or FAIL_DECISION."""
    for raw in policy_lines:
        # Strip inline parenthetical comments at the end of a fallback line
        line = raw.strip()

        m = _PRED_EQ.match(line)
        if m:
            scope, key, expected, value = m.group(1), m.group(2), m.group(3), m.group(4)
            src = pinned if scope == "pinned" else decisions
            if src.get(key) == expected:
                return _strip_value(value)
            continue

        m = _PRED_IN.match(line)
        if m:
            scope, key, items_raw, value = m.group(1), m.group(2), m.group(3), m.group(4)
            src = pinned if scope == "pinned" else decisions
            items = [_strip_value(x) for x in re.split(r",\s*", items_raw)]
            if src.get(key) in items:
                return _strip_value(value)
            continue

        m = _PRED_PRESENT.match(line)
        # Careful: PRED_PRESENT also matches "fallback: ..." etc. Reject reserved heads.
        if m and not line.startswith(("fallback", "always", "decisions")):
            key, value = m.group(1), m.group(2)
            if pinned.get(key):
                return _strip_value(value)
            continue

        m = _PRED_ALWAYS.match(line)
        if m:
            return _strip_value(m.group(1))

        m = _PRED_FALLBACK.match(line)
        if m:
            v = m.group(1).strip()
            if v == "ask-user":
                return ASK_USER
            if v == "fail":
                return FAIL_DECISION
            return _strip_value(v)

    # No predicate matched AND no fallback was provided — treat as ask-user
    return ASK_USER


# ---------------------------------------------------------------------------
# recipe-level resolver


@dataclass
class ResolutionReport:
    decisions: dict[str, str]              # key → resolved option
    unresolved: list[str]                  # keys that landed at ASK_USER
    fail_decisions: list[str]              # keys that landed at FAIL_DECISION
    per_decision: list[tuple[str, str]]    # (key, source-label) for diagnostics

    @property
    def all_resolved(self) -> bool:
        return not self.unresolved and not self.fail_decisions


def resolve_recipe(
    recipe_path: Path,
    pinned: dict[str, str],
    pre_pinned_decisions: Optional[dict[str, str]] = None,
) -> ResolutionReport:
    """Parse a recipe + evaluate every decision point's auto-policy."""
    decisions: dict[str, str] = dict(pre_pinned_decisions or {})
    points = parse_decision_points(recipe_path)
    unresolved: list[str] = []
    fail_decisions: list[str] = []
    per_decision: list[tuple[str, str]] = []

    for dp in points:
        if dp.key in decisions:
            per_decision.append((dp.key, f"pre-pinned: {decisions[dp.key]}"))
            continue

        result = evaluate_policy(dp.auto_policy, pinned, decisions)
        if result == ASK_USER:
            unresolved.append(dp.key)
            per_decision.append((dp.key, "<ASK_USER — fallback: ask-user>"))
        elif result == FAIL_DECISION:
            fail_decisions.append(dp.key)
            per_decision.append((dp.key, "<FAIL — fallback: fail>"))
        else:
            decisions[dp.key] = result
            # Find which policy line matched (best-effort for diagnostics)
            source = "auto-policy"
            for raw in dp.auto_policy:
                if result in raw and not raw.startswith("fallback"):
                    source = f"auto-policy: `{raw.strip()}`"
                    break
            per_decision.append((dp.key, source))

    return ResolutionReport(
        decisions=decisions,
        unresolved=unresolved,
        fail_decisions=fail_decisions,
        per_decision=per_decision,
    )


# ---------------------------------------------------------------------------
# CLI


def _print_report(recipe: str, pinned: dict, report: ResolutionReport) -> None:
    print(f"# Recipe: {recipe}")
    print(f"# Pinned state: {pinned}")
    print()
    for key, source in report.per_decision:
        resolved = report.decisions.get(key)
        mark = "✅" if resolved else ("❌" if key in report.fail_decisions else "⚠️ ")
        if resolved:
            print(f"{mark} {key}: {resolved}   ({source})")
        else:
            print(f"{mark} {key}: <unresolved>   ({source})")
    print()
    n = len(report.per_decision)
    resolved_n = len(report.decisions) - len(report.decisions.keys() - {k for k, _ in report.per_decision})
    print(f"==== resolved {len(report.decisions)} / {n} · unresolved {len(report.unresolved)} · failed {len(report.fail_decisions)} ====")


def _parse_kv(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            print(f"WARN: ignoring {item!r} — expected key=value", file=sys.stderr)
            continue
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("recipe", help="Name of recipe (matches references/<name>.md) OR a full path to a recipe file")
    ap.add_argument("--pinned", action="append", default=[],
                    help="Pinned project state — repeatable, key=value form. e.g. --pinned license=axoniq-commercial")
    ap.add_argument("--decision", action="append", default=[],
                    help="Pre-pinned decision answer — repeatable, key=value form.")
    args = ap.parse_args()

    recipe_path = Path(args.recipe)
    if not recipe_path.is_file():
        recipe_path = Path(__file__).resolve().parent.parent / "references" / f"{args.recipe}.md"
    if not recipe_path.is_file():
        print(f"ERROR: recipe not found at {recipe_path}", file=sys.stderr)
        return 2

    pinned = _parse_kv(args.pinned)
    pre = _parse_kv(args.decision)

    report = resolve_recipe(recipe_path, pinned, pre)
    _print_report(recipe_path.stem, pinned, report)

    if report.unresolved or report.fail_decisions:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
