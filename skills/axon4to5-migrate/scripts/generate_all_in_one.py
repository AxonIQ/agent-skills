#!/usr/bin/env python3
"""Generate ALL_IN_ONE.md (patterns) and ALL_EXAMPLES.md (examples)."""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(SCRIPT_DIR, "..")
PATTERNS_DIR = os.path.join(SKILL_DIR, "patterns")
EXAMPLES_DIR = os.path.join(SKILL_DIR, "examples")
OUTPUT_FILE = os.path.join(PATTERNS_DIR, "ALL_IN_ONE.md")
EXAMPLES_OUTPUT = os.path.join(EXAMPLES_DIR, "ALL_EXAMPLES.md")
IGNORED = {"ALL_IN_ONE.md", "ALL_EXAMPLES.md", "README.md"}


def strip_prefix(name):
    return re.sub(r"^\d+[-_]", "", name).replace("-", " ").replace("_", " ").replace(".md", "")


def normalize_headings(content, level_offset):
    def replace(m):
        level = len(m.group(1))
        new_level = min(level + level_offset, 6)
        return "#" * new_level + " "
    return re.sub(r"^(#{1,6}) ", replace, content, flags=re.MULTILINE)


def collect(directory, depth=1, top_dir=None):
    if top_dir is None:
        top_dir = directory
    parts = []
    entries = sorted(os.listdir(directory))

    readme_path = next(
        (os.path.join(directory, e) for e in entries if e.lower() == "readme.md"), None
    )
    files = [
        e for e in entries
        if e.endswith(".md") and e not in IGNORED and e.lower() != "readme.md"
    ]
    subdirs = [
        e for e in entries
        if os.path.isdir(os.path.join(directory, e))
    ]

    is_top = os.path.realpath(directory) == os.path.realpath(top_dir)

    readme_title = None
    readme_body = None
    if readme_path and os.path.exists(readme_path):
        raw = open(readme_path, encoding="utf-8").read()
        m = re.search(r"^# (.+)", raw, re.MULTILINE)
        readme_title = m.group(1).strip() if m else None
        readme_body = re.sub(r"^# .+\n?", "", raw, count=1).strip()

    section_title = readme_title or strip_prefix(os.path.basename(directory))

    if not is_top:
        parts.append(f"\n{'#' * depth} {section_title}\n")
        if readme_body:
            parts.append(normalize_headings(readme_body, depth) + "\n")

    for filename in files:
        filepath = os.path.join(directory, filename)
        raw = open(filepath, encoding="utf-8").read()
        m = re.search(r"^# (.+)", raw, re.MULTILINE)
        title = m.group(1).strip() if m else strip_prefix(filename)
        body = re.sub(r"^# .+\n?", "", raw, count=1).strip()
        parts.append(f"\n{'#' * (depth + 1)} {title}\n\n")
        parts.append(normalize_headings(body, depth + 1).strip() + "\n\n---\n")

    for subdir in subdirs:
        parts.append(collect(os.path.join(directory, subdir), depth + 1, top_dir))

    return "".join(parts)


def make_toc(content):
    lines = []
    for line in content.splitlines():
        m = re.match(r"^(#{2,4}) (.+)", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
            lines.append("  " * (level - 2) + f"- [{title}](#{anchor})")
    return "\n".join(lines)


def main():
    # Generate patterns/ALL_IN_ONE.md
    body = collect(PATTERNS_DIR, top_dir=PATTERNS_DIR).strip()
    toc = make_toc(body)
    output = f"""# Axon Framework 4 → 5 Migration Patterns

Automatically generated — do not edit manually. Regenerate with:
```
python3 scripts/generate_all_in_one.py
```

{toc}

{body}
"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"✅ {OUTPUT_FILE} generated.")

    # Generate examples/ALL_EXAMPLES.md if examples/ directory exists
    if os.path.isdir(EXAMPLES_DIR):
        ex_body = collect(EXAMPLES_DIR, top_dir=EXAMPLES_DIR).strip()
        ex_toc = make_toc(ex_body)
        ex_output = f"""# Axon Framework 4 → 5 Migration Examples

Automatically generated — do not edit manually. Regenerate with:
```
python3 scripts/generate_all_in_one.py
```

Concrete before/after examples showing full file migrations. Consult when a pattern alone is insufficient.

{ex_toc}

{ex_body}
"""
        with open(EXAMPLES_OUTPUT, "w", encoding="utf-8") as f:
            f.write(ex_output)
        print(f"✅ {EXAMPLES_OUTPUT} generated.")


if __name__ == "__main__":
    main()
