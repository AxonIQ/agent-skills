# Axon Framework Contributor Review Skill

Comprehensive code review skill for Axon Framework and Axoniq Framework contributors. Systematically checks changes against AF5 contributor standards and is aware of the feature split between the two frameworks (OSS vs commercial).

Both frameworks share identical coding conventions. The skill identifies which framework is being reviewed and checks that features are placed in the appropriate repo.

## Structure

```
axoniq-framework-contribute-review/
├── SKILL.md                          # Review process, checklist, severity levels, modes
├── README.md                         # This file
├── quick-reference.md                # Top-10 issues, fast checks, grep patterns, decision tree
├── references/
│   └── fix-patterns.md               # How to craft and apply fix suggestions per issue type
└── templates/
    └── review-report-template.md     # Structured review report format
```

## Usage

```bash
/axoniq-framework-contribute-review
```

The skill detects changed files, reads them, applies the AF5 review checklist, and generates a report with numbered fix suggestions (BLOCKING / WARNING / SUGGESTION), review hotspots for human attention, and positive findings. Fixes can then be applied interactively ("Apply fix #1", "Apply all blocking fixes").

## What Gets Checked

- **Critical (BLOCKING)**: Antora documentation for feature changes, JavaDoc completeness (`@since` tags), test coverage (≥80%), documented breaking changes, security
- **API design**: AF5 fluent patterns (not AF4 builders), JSpecify null safety (Jakarta forbidden), minimal visibility
- **Code quality**: exception types (`AxonConfigurationException`), performance, type safety, resource management
- **Architecture**: design patterns, handler wrapper chain preservation, dependencies
- **Tests**: real objects over mocks, resource cleanup

## Related Skills

- `axoniq-framework-contribute-code` — the design patterns this review checks against
- `axoniq-framework-contribute-docs` — writing the documentation a review flags as missing

**Note:** This skill performs systematic reviews but doesn't replace human judgment for architectural decisions, complex trade-offs, or design philosophy questions. Escalate these to human reviewers.
