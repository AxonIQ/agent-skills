# Axon Framework Contributor Docs Update Skill

Guide for adding or updating Axon Framework 5 reference documentation, covering AsciiDoc conventions, module structure, API verification, and navigation updates.

## Purpose

This skill is for **contributing documentation to the Axon Framework 5 reference guide**, not for reading or using the docs. It covers:

- Adding new `.adoc` pages to any reference guide module
- Updating existing pages with corrected or expanded content
- Renaming or restructuring documentation files
- Keeping navigation and xrefs in sync after changes

## What's Covered

### 1. Doc Structure Orientation
- Reference guide module layout (`docs/reference-guide/modules/`)
- Standalone guides (`getting-started/`, `*-guide/`)
- Nav files and how to update them

### 2. API Verification Before Writing
- How to locate classes in framework source
- AF5 key types to use (ProcessingContext, EventSink, Converter, etc.)
- Things removed or moved to legacy that must not be documented

### 3. AsciiDoc Conventions
- File template with tabs, callouts, and admonitions
- Heading casing rules (Title Case H1, Sentence case H2+)
- ASCII-only requirement (no smart quotes, no em-dashes)
- Product name and acronym casing
- User-centric tone over internal mechanics

### 4. Navigation and xref Management
- How to add entries to `partials/nav.adoc`
- How to verify xref targets exist before committing
- When to update the ROOT nav aggregator

### 5. Migration Tracking
- How to update `docs/changes-to-process.md` when finishing tracked pages

## Usage

```bash
/axonframework-contributor-docs-update
```

Or with a target:

```bash
/axonframework-contributor-docs-update event processors overview
/axonframework-contributor-docs-update commands/command-dispatching.adoc
/axonframework-contributor-docs-update GH-1234
```

## Key Conventions at a Glance

| Rule | Correct | Avoid |
|---|---|---|
| H1 heading | Title Case | sentence case |
| H2+ headings | Sentence case | Title Case |
| Em-dash | use comma/colon/parens | `---` |
| Quotes | `"straight"` | `"curly"` |
| AF5 term | ProcessingContext | UnitOfWork |
| AF5 term | EventSink | EventBus (publishing) |
| AF5 term | entity | aggregate |
| Code examples | both Spring Boot + plain Java | Spring Boot only |

## File Structure

```
skills/axonframework-contributor-docs-update/
├── SKILL.md     # Complete skill with all phases and conventions
└── README.md    # This file
```

## Related Skills

- **axonframework-contributor-coding**: For developing framework infrastructure components
- **axonframework-contributor-review**: For reviewing PRs against AF5 standards
