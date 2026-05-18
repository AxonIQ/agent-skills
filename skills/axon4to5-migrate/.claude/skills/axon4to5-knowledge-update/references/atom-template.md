# Atom File Template

Copy this structure when creating a new atom. Replace every `<…>` placeholder.

## Frontmatter

```yaml
---
atom-id: <af4-centric-or-concept-name>
title: "<AF4 symbol> → <AF5 symbol> — <one-phrase summary>"
af4-symbols: ["<AnnotationOrClass>", "org.axonframework.<af4.package.ClassName>"]
af5-symbols: ["<AnnotationOrClass>", "org.axonframework.<af5.package.ClassName>"]
detect: grep -rn '<regex>' --include='*.java' --include='*.kt' --include='*.scala' .
used-by: [<recipe-id>, ...]
---
```

Rules:
- `atom-id` matches the filename (no `.md`)
- `af4-symbols` lists both short name and fully-qualified import(s) — all AF4 import paths that must be removed
- `af5-symbols` lists both short name and fully-qualified import(s) — all AF5 import paths that must be added
- `detect` is a first-signal hint; the recipe confirms by reading the file
- `used-by` contains recipe directory names (e.g. `aggregate`, `event-processor`, `saga`)

## Body sections

```markdown
# <Short Title>

<One-sentence description of the transformation and why AF5 changed it.>

## Detect

\```bash
grep -rn '<pattern>' --include='*.java' --include='*.kt' --include='*.scala' .
\```

## Transform (or ## Path A / ## Path B when two variants exist)

**Remove:**
\```java
import org.axonframework.<af4.package>;

@AF4Annotation
public class Foo { … }
\```

**Replace with:**
\```java
import org.axonframework.<af5.package>;

@AF5Annotation
public class Foo { … }
\```

⚠️ Note any mandatory infix or package trap here (e.g. "`.messaging.` is mandatory").

## Import changes

Remove: `org.axonframework.<af4.fully.qualified>`
Add: `org.axonframework.<af5.fully.qualified>`

## Gotchas

- **<trap name>** — <what goes wrong and why it's hard to spot>
- **<common mistake>** — <what to check to confirm it was applied correctly>

## Used By

- **[[<recipe-id>]]** — Step N (<always | apply-condition>)
```

## Section conventions

- Use `## Path A` / `## Path B` when Spring Boot and native configurer paths diverge
- Use `## Annotation mapping` table when multiple AF4 annotations → one AF5 annotation (saga pattern)
- Gotchas go in a bullet list; each bullet leads with a **bold label**
- `## Used By` always present; matches `used-by:` frontmatter

## What NOT to include

- Scope rules, blockers, apply-conditions — those belong in the recipe, not the atom
- Prose about why the migration is necessary beyond one sentence — keep it scannable
- Speculative "may also apply to" notes — only what's known
