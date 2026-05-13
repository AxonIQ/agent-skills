#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

MAX_FILES = 8
MAX_MD_LINES = 260
MAX_TOTAL_LINES = 520


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def text(path: Path) -> str:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def route(src: str) -> str | None:
    rules = [
        ("aggregate", r"@Aggregate\b|@AggregateRoot\b", None),
        ("event-processor", r"@ProcessingGroup|org\.axonframework\.eventhandling\.EventHandler", None),
        ("command-gateway", r"org\.axonframework\.commandhandling\.gateway\.CommandGateway", r"@EventHandler|@CommandHandler|@QueryHandler"),
        ("query-gateway", r"org\.axonframework\.queryhandling\.QueryGateway", r"@EventHandler|@CommandHandler|@QueryHandler"),
        ("query-handler", r"org\.axonframework\.queryhandling\.QueryHandler", None),
        ("interceptors", r"implements\s+MessageDispatchInterceptor\b|implements\s+MessageHandlerInterceptor\b", r"@CommandHandler|@EventHandler|@QueryHandler"),
    ]
    for name, include, exclude in rules:
        if re.search(include, src) and not (exclude and re.search(exclude, src)):
            return name
    return None


def main() -> None:
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    if len(files) > MAX_FILES:
        fail(f"too many files: {len(files)} > {MAX_FILES}")

    forbidden_dirs = ["docs"]
    for dirname in forbidden_dirs:
        if (ROOT / dirname).exists():
            fail(f"obsolete directory still exists: {dirname}")

    markdown = [p for p in files if p.suffix in {".md", ".adoc"}]
    total = 0
    for path in markdown:
        lines = text(path).splitlines()
        total += len(lines)
        if len(lines) > MAX_MD_LINES:
            fail(f"{path.relative_to(ROOT)} too long: {len(lines)}")
        if any(line.startswith("####") for line in lines):
            fail(f"{path.relative_to(ROOT)} nests headings too deeply")

    if total > MAX_TOTAL_LINES:
        fail(f"too many markdown lines: {total} > {MAX_TOTAL_LINES}")

    skill = text(ROOT / "SKILL.md")
    playbook = text(ROOT / "references/playbook.md")
    if "references/playbook.md" not in skill:
        fail("SKILL.md must point to the playbook")
    if "```mermaid" not in playbook:
        fail("playbook must include the flow diagram")
    for token in ["PROCESS_ITEMS", "EXECUTE_RECIPE", "orchestration.svg", "orchestrator"]:
        if token in skill + playbook:
            fail(f"stale complexity token: {token}")

    for token in ["openrewrite", "aggregate", "event-processor", "command-gateway", "query-gateway", "query-handler", "interceptors", "event-storage-engine"]:
        if token not in playbook:
            fail(f"missing route: {token}")

    samples = {
        "aggregate": "import org.axonframework.spring.stereotype.Aggregate; @Aggregate class A {}",
        "event-processor": "import org.axonframework.eventhandling.EventHandler; class P { @EventHandler void on(E e){} }",
        "command-gateway": "import org.axonframework.commandhandling.gateway.CommandGateway; class C { CommandGateway g; }",
        "query-gateway": "import org.axonframework.queryhandling.QueryGateway; class C { QueryGateway q; }",
        "query-handler": "import org.axonframework.queryhandling.QueryHandler; class H { @QueryHandler Object h(Q q){return null;} }",
        "interceptors": "class I implements MessageDispatchInterceptor<CommandMessage<?>> {}",
    }
    for expected, src in samples.items():
        actual = route(src)
        if actual != expected:
            fail(f"route {expected} -> {actual}")

    mixed = "import org.axonframework.commandhandling.gateway.CommandGateway; import org.axonframework.eventhandling.EventHandler; class H { @EventHandler void on(E e){} CommandGateway g; }"
    if route(mixed) != "event-processor":
        fail("handler with gateway must route to event-processor first")

    print("axon4to5-migrate evals passed")


if __name__ == "__main__":
    main()
