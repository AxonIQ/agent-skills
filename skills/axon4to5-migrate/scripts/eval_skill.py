#!/usr/bin/env python3
"""Lightweight evals for the axon4to5-migrate skill.

These checks are intentionally structural. They guard the simplification goal:
small entrypoint, explicit routing, no graph/state-machine artifacts, preserved
recipe surface, and routing behavior for representative source snippets.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_RECIPES = [
    "openrewrite",
    "aggregate",
    "event-processor",
    "command-gateway",
    "query-gateway",
    "query-handler",
    "interceptors",
    "event-storage-engine",
]

RECIPE_FILES = {
    "openrewrite": ROOT / "references/openrewrite.md",
    "aggregate": ROOT / "references/aggregate/aggregate.md",
    "event-processor": ROOT / "references/event-processor/event-processor.md",
    "command-gateway": ROOT / "references/command-gateway/command-gateway.md",
    "query-gateway": ROOT / "references/query-gateway/query-gateway.md",
    "query-handler": ROOT / "references/query-handler/query-handler.md",
    "interceptors": ROOT / "references/interceptors/interceptors.md",
    "event-storage-engine": ROOT / "references/event-storage-engine/event-storage-engine.md",
    "debug": ROOT / "references/debug/debug.md",
    "saga": ROOT / "references/saga/saga.md",
}

ROUTING_RULES = [
    ("aggregate", re.compile(r"@Aggregate\b|@AggregateRoot\b")),
    ("event-processor", re.compile(r"@ProcessingGroup|org\.axonframework\.eventhandling\.EventHandler")),
    (
        "command-gateway",
        re.compile(r"org\.axonframework\.commandhandling\.gateway\.CommandGateway"),
        re.compile(r"@EventHandler|@CommandHandler|@QueryHandler|@MessageHandlerInterceptor"),
    ),
    (
        "query-gateway",
        re.compile(r"org\.axonframework\.queryhandling\.QueryGateway"),
        re.compile(r"@EventHandler|@CommandHandler|@QueryHandler"),
    ),
    ("query-handler", re.compile(r"org\.axonframework\.queryhandling\.QueryHandler")),
    (
        "interceptors",
        re.compile(r"implements\s+MessageDispatchInterceptor\b|implements\s+MessageHandlerInterceptor\b"),
        re.compile(r"@CommandHandler|@EventHandler|@QueryHandler"),
    ),
]

SAMPLE_ROUTES = {
    "aggregate": "import org.axonframework.spring.stereotype.Aggregate;\n@Aggregate class GiftCard {}",
    "event-processor": "import org.axonframework.eventhandling.EventHandler;\nclass Projection { @EventHandler void on(E e){} }",
    "command-gateway": "import org.axonframework.commandhandling.gateway.CommandGateway;\nclass Controller { CommandGateway gateway; }",
    "query-gateway": "import org.axonframework.queryhandling.QueryGateway;\nclass Controller { QueryGateway gateway; }",
    "query-handler": "import org.axonframework.queryhandling.QueryHandler;\nclass Queries { @QueryHandler Object handle(Q q){ return null; } }",
    "interceptors": "class Audit implements MessageDispatchInterceptor<CommandMessage<?>> {}",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_true(path.exists(), f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def route(content: str) -> str | None:
    for rule in ROUTING_RULES:
        name, include = rule[0], rule[1]
        exclude = rule[2] if len(rule) == 3 else None
        if include.search(content) and not (exclude and exclude.search(content)):
            return name
    return None


def check_entrypoint() -> None:
    skill = read(ROOT / "SKILL.md")
    lines = skill.splitlines()
    assert_true(len(lines) <= 180, f"SKILL.md too long: {len(lines)} lines")
    for required in ["references/routing.md", "references/flow.md", "references/state.md", "references/recipe-contract.md"]:
        assert_true(required in skill, f"SKILL.md does not point to {required}")
    forbidden = ["PROCESS_ITEMS", "EXECUTE_RECIPE", "digraph", "orchestration.svg"]
    for token in forbidden:
        assert_true(token not in skill, f"entrypoint still contains orchestration token {token!r}")


def check_size_and_nesting() -> None:
    too_long: list[str] = []
    too_deep: list[str] = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] == "docs":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        limit = 180 if rel.name == "SKILL.md" else 30 if "examples" in rel.parts else 130
        if len(lines) > limit:
            too_long.append(f"{rel}: {len(lines)} > {limit}")
        for i, line in enumerate(lines, start=1):
            if line.startswith("####"):
                too_deep.append(f"{rel}:{i}")
    assert_true(not too_long, "markdown file(s) too long: " + "; ".join(too_long[:20]))
    assert_true(not too_deep, "heading nesting deeper than ###: " + "; ".join(too_deep[:20]))
    oversized_docs = []
    for path in (ROOT / "docs").rglob("*.adoc"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 220:
            oversized_docs.append(f"{path.relative_to(ROOT)}: {len(lines)} > 220")
    assert_true(not oversized_docs, "docs too long: " + "; ".join(oversized_docs[:20]))


def check_artifacts_removed() -> None:
    for name in ["orchestration.md", "orchestration.dot", "orchestration.svg"]:
        assert_true(not (ROOT / name).exists(), f"obsolete artifact still exists: {name}")


def check_routing() -> None:
    routing = read(ROOT / "references/routing.md")
    positions = []
    for recipe in EXPECTED_RECIPES:
        pos = routing.find(f"`{recipe}`")
        assert_true(pos >= 0, f"routing missing recipe {recipe}")
        positions.append(pos)
    assert_true(positions == sorted(positions), "routing recipe order changed unexpectedly")
    for expected, sample in SAMPLE_ROUTES.items():
        actual = route(sample)
        assert_true(actual == expected, f"sample route expected {expected}, got {actual}")
    mixed_handler = (
        "import org.axonframework.commandhandling.gateway.CommandGateway;\n"
        "import org.axonframework.eventhandling.EventHandler;\n"
        "class Handler { @EventHandler void on(E e){} CommandGateway gateway; }"
    )
    assert_true(route(mixed_handler) == "event-processor", "handler class must not route to command-gateway")


def check_recipe_surface() -> None:
    contract = read(ROOT / "references/recipe-contract.md")
    assert_true("success | skipped | rejected | needs-decision | blocked | failed" in contract, "contract lost result union")
    for recipe, path in RECIPE_FILES.items():
        text = read(path)
        for heading in ["## Inputs", "## Preflight", "## Procedure", "## End condition", "## Output"]:
            assert_true(heading in text, f"{recipe} missing {heading}")
        assert_true("result:" in text, f"{recipe} output does not mention result:")


def check_local_links() -> None:
    missing: list[str] = []
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            href = match.group(1).split("#", 1)[0]
            if not href or "://" in href or href.startswith("mailto:") or href.startswith("<"):
                continue
            if not (path.parent / href).exists():
                missing.append(f"{path.relative_to(ROOT)} -> {href}")
    assert_true(not missing, "missing local markdown link(s): " + "; ".join(missing[:10]))


def check_vocabulary() -> None:
    stale: list[str] = []
    for path in [ROOT / "SKILL.md", *ROOT.glob("assets/*.md"), *ROOT.rglob("references/**/*.md")]:
        if path.is_file() and "orchestrator" in path.read_text(encoding="utf-8").lower():
            stale.append(str(path.relative_to(ROOT)))
    assert_true(not stale, "stale orchestration vocabulary: " + ", ".join(stale))


def main() -> None:
    check_entrypoint()
    check_size_and_nesting()
    check_artifacts_removed()
    check_routing()
    check_recipe_surface()
    check_local_links()
    check_vocabulary()
    print("axon4to5-migrate evals passed")


if __name__ == "__main__":
    main()
