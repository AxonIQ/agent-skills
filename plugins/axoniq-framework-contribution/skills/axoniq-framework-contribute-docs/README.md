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
- ASCII-only requirement: no smart quotes, no em-dashes in any form (neither `---` nor the Unicode `—` character)
- Product name and acronym casing
- User-centric tone over internal mechanics

### 4. Navigation and xref Management
- How to add entries to `partials/nav.adoc`
- How to verify xref targets exist before committing
- When to update the ROOT nav aggregator

### 5. Migration Tracking
- Always check `docs/changes-to-process.md` after writing or updating any page
- Update the status to COMPLETED with a bullet list of applied changes when the work is done

### 6. Document Current Branch / PR Changes
- Invoke with "document my current branch" or "write docs for this PR"
- Skill runs `git diff main...HEAD` to discover what changed, reads the source, then proceeds through all phases
- Requires Bash access; if unavailable the skill will ask you to describe the changes instead

## Usage

```bash
/axoniq-framework-contribute-docs
```

Or with a target:

```bash
/axoniq-framework-contribute-docs event processors overview
/axoniq-framework-contribute-docs commands/command-dispatching.adoc
/axoniq-framework-contribute-docs GH-1234
/axoniq-framework-contribute-docs current branch
```

## Key Conventions at a Glance

| Rule | Correct | Avoid |
|---|---|---|
| H1 heading | Title Case | sentence case |
| H2+ headings | Sentence case | Title Case |
| Em-dash | use comma/colon/parens | `---` or `—` |
| Quotes | `"straight"` | `"curly"` |
| Non-ASCII | (none) | any Unicode > 127 |
| AF5 term | ProcessingContext | UnitOfWork |
| AF5 term | EventSink | EventBus (publishing) |
| AF5 term | entity | aggregate |
| Code examples | both Spring Boot + plain Java | Spring Boot only |
| changes-to-process.md | always check and update | skip |
| Product name | Axoniq Platform | Axoniq Console, Axoniq Cloud (retired) |

## File Structure

```
skills/axoniq-framework-contribute-docs/
├── SKILL.md     # Complete skill with all phases and conventions
├── README.md    # This file
└── evals/
    └── evals.json   # Test cases for skill evaluation
```

## Related Skills

- **axoniq-framework-contribute-code**: For developing framework infrastructure components
- **axoniq-framework-contribute-review**: For reviewing PRs against AF5 standards
