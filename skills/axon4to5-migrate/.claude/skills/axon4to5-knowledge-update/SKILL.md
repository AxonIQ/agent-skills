---
name: axon4to5-knowledge-update
description: Updates atoms and recipes in the axon4to5-migrate skill from new API knowledge. Use when you have: an Axon Framework 5 changelog or release notes, a real migrated repo to learn from, new migration path documentation (.adoc), or a correction to a wrong atom/recipe. Triggers on "update atoms from", "ingest API changes", "this atom is wrong", "new AF5 API", "migration path changed", "update the skill from", "add this example to the skill", "I found a correction", "AF5 released X".
---

# axon4to5 Knowledge Update

Given new AF4→AF5 knowledge (changelog, migrated repo, migration doc, or correction), update atoms and/or recipes so future migrations use accurate patterns.

## Input sources

| Source type | What to extract |
|-------------|-----------------|
| API changelog / release notes | AF4 symbol → AF5 symbol mappings; import changes; removed APIs |
| Migrated repo or diff | Before/after patterns discovered in practice; gotchas |
| Migration path doc (`.adoc`) | New catalog entry → add to recipe `## References` section |
| Correction | Wrong info + correct info + which atom/recipe file(s) |

---

## Phase 1 — Extract changes

Read the source. For each distinct API change, record:
- **AF4 symbol(s)**: annotation, class, or method being replaced
- **AF5 symbol(s)**: what replaces it (exact FQN)
- **Import paths**: fully-qualified for both sides
- **Transform**: minimal before/after code snippet
- **Gotchas**: wrong-guess traps, silent failures, ordering constraints

For a migrated repo: compare before/after files. Focus on changed imports, annotation renames, method signature changes, new required annotations, and removed classes.

---

## Phase 2 — Map to existing atoms

For each extracted change, check `references/atoms/INDEX.md` and grep for the AF4 symbol:

```bash
grep -rn '<af4-symbol>' references/atoms/ --include='*.md'
```

**Decision tree:**

```
Does an existing atom's af4-symbols cover this change?
├── YES → update that atom (add gotcha, fix import, add variant)
├── NO but related to an existing atom's concept group → add to that atom
├── NO, purely recipe-level (new blocker, scope change) → update recipe only
└── NO, genuinely new API change → create new atom (Phase 4)
```

---

## Phase 3 — Update existing atoms

Edit the atom file. What may change:

- Fix a wrong import FQN
- Add a new gotcha or edge case
- Add a Kotlin/Scala transform variant alongside the Java example
- Add a new AF4 symbol to `af4-symbols:` frontmatter
- Fix the `detect:` grep pattern

Constraint: every grep in `detect:` and in the body **must** include `--include='*.java' --include='*.kt' --include='*.scala'`. Never single-language.

---

## Phase 4 — Create new atoms

Read `references/atom-template.md` for the exact format.

**Naming convention** — pick the anchor based on this table:

| Situation | Name after | Example |
|-----------|-----------|---------|
| AF4 concept changed and has a distinct, greppable name | AF4 symbol | `unit-of-work`, `aggregate-annotation` |
| Concept name is stable across versions (same name, just package move) | Concept | `command-handler`, `event-handler` |
| Multiple AF4 things collapse to one AF5 thing, no single anchor | Directional | `saga-spi-to-spring-component` |
| No AF4 anchor (new annotation added, nothing existed before) | AF5 name | `entity-creator` |

After writing the atom file:

1. Add a row to `INDEX.md` under the correct category
2. Set `used-by:` in the atom's YAML frontmatter to the recipes that need it
3. Add the atom to those recipes' `### Atoms` table with an `apply-condition`
4. Update the `## Cross-reference: component → atoms` table at the bottom of `INDEX.md`

---

## Phase 5 — Update recipes

For every recipe in the atom's `used-by:`:

- Verify the apply-condition in the `### Atoms` table is still accurate
- If a new atom was added: add a row to the atoms table **and** a corresponding step in `## Toolbox`
- If a recipe step was encoding HOW inline (not delegating to an atom): extract to an atom and replace with `[[atom-id]]`
- If a correction changes a blocker or out-of-scope rule: update `## Blocker` or `## Out of Scope`

---

## Phase 6 — Verify consistency

Run these checks before declaring done:

```bash
# 1. No broken [[wikilinks]] — every linked atom-id must exist as a file
grep -roh '\[\[[^]]*\]\]' references/atoms/ references/recipes/ --include='*.md' \
  | grep -oP '\[\[\K[^\]]+' | grep -v '/' | sort -u > /tmp/links.txt
ls references/atoms/*.md | xargs -I{} basename {} .md | sort > /tmp/atoms.txt
comm -23 /tmp/links.txt /tmp/atoms.txt   # shows broken links (recipes like [[aggregate]] are expected)

# 2. No file-path references pointing to renamed/moved atoms
grep -rn 'atoms/[a-z-]*\.md' references/recipes/ --include='*.md'

# 3. All grep detect patterns are JVM-agnostic
grep -rn "include='\*\.java'" references/atoms/ --include='*.md' | grep -v "\.kt"
# ↑ any hit = a mono-language grep that needs fixing
```

Fix any inconsistencies found before reporting done.

---

## Output

Report concisely:
- Atoms updated: `<atom-id>` — what changed (import fix / gotcha added / etc.)
- Atoms created: `<atom-id>` — what it covers, added to which recipe(s)
- Recipes updated: `<recipe>` — which section changed
- Inconsistencies fixed (if any)
