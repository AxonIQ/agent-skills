# Code Review Skill

Comprehensive code review skill for Axon Framework that systematically checks pull requests and code changes against AF5 standards.

## Files in This Skill

```
.claude/skills/code-review/
├── SKILL.md                    # Main skill definition and instructions
├── README.md                   # This file
├── quick-reference.md          # Fast lookup guide for common patterns
└── templates/
    └── review-report-template.md  # Structured review report format
```

## Related Files

- `../../code-review-checklist.md` - Comprehensive 27-category checklist compiled from PR analysis

## Usage

### Basic Usage
```bash
/code-review
```

This will:
1. Detect changed files via `git status` and `git diff`
2. Read all modified Java, test, and documentation files
3. Apply the comprehensive review checklist systematically
4. Generate a structured review report with:
   - BLOCKING issues (must fix)
   - WARNINGS (should fix)
   - SUGGESTIONS (nice to have)
   - POSITIVE findings (what's done well)

### Review Options

**Quick pre-commit check** (focuses on critical items only):
```bash
/code-review --quick
```

**Review specific branch** (compares against main):
```bash
/code-review feature/my-feature
```

**Comprehensive review** (deep analysis):
```bash
/code-review --comprehensive
```

## What Gets Checked

### Critical Requirements (BLOCKING)
- ✅ Antora documentation in `/docs` for feature changes
- ✅ JavaDoc completeness with `@since` tags
- ✅ Test coverage (≥80% target)
- ✅ Breaking changes properly documented
- ✅ No security vulnerabilities

### API Design
- ✅ Fluent API patterns (AF5 style, not AF4 builders)
- ✅ Null safety annotations (`@Nullable`, `@Nonnull`)
- ✅ Method visibility minimized
- ✅ Naming conventions followed

### Code Quality
- ✅ Proper exception types (`AxonConfigurationException`)
- ✅ Performance considerations (data structures, concurrency)
- ✅ Type safety and generics
- ✅ Resource management

### Architecture
- ✅ Design patterns alignment
- ✅ Backward compatibility
- ✅ No circular dependencies

## Review Severity Levels

### BLOCKING ❌
Must be fixed before approval:
- Missing documentation for features
- Missing `@since` tags on public APIs
- Insufficient test coverage
- Breaking changes without migration docs
- Security issues

### WARNING ⚠️
Should be addressed:
- Missing `@author` tags
- Wrong exception types
- Missing null annotations
- Method visibility too broad

### SUGGESTION 💡
Nice to have improvements:
- Better naming
- Additional tests
- Code organization enhancements

## Common Issues Detected

Based on analysis of 20+ PRs, the skill specifically looks for:

1. Missing `@since` tags (very common)
2. Missing Antora documentation updates
3. Missing `@author` credits when refactoring
4. Insufficient test coverage
5. Missing `@Nullable`/`@Nonnull` annotations
6. Use of generic exceptions instead of `AxonConfigurationException`
7. Methods that could have more restrictive visibility
8. `LinkedList` usage where `LinkedHashMap` would be better
9. AF4-style builder patterns on infrastructure components
10. Missing JavaDoc examples for complex APIs

## Integration with Other Skills

### With axon-framework-5-patterns
For reviewing builder patterns and infrastructure components:
```bash
/axon-framework-5-patterns  # First validate patterns
/code-review                # Then comprehensive review
```

### Pre-commit workflow
```bash
# Make changes
git add .

# Review before committing
/code-review

# Address issues, then commit
git commit
```

## Quick Reference

See `quick-reference.md` for:
- Top 10 most common issues
- Fast checks (under 2 minutes)
- Grep patterns for common problems
- Code pattern examples
- Severity decision tree
- Commands cheat sheet

## Review Report Format

The skill generates structured reports with:

1. **Executive Summary** - Quick status overview
2. **Blocking Issues** - Must fix with file:line references
3. **Warnings** - Should address
4. **Suggestions** - Improvements
5. **Positive Findings** - Acknowledgment of good work
6. **Detailed Analysis** - Category-by-category breakdown
7. **Checklist Status** - What's complete, what's missing
8. **Next Steps** - Specific action items

See `templates/review-report-template.md` for the full structure.

## How It Works

### Step 1: Detection
```bash
git status --short
git diff --stat
git diff main...HEAD --name-only
```

### Step 2: File Analysis
Reads all changed files:
- Java source files
- Test files
- Documentation (`.adoc`)
- Configuration files

### Step 3: Systematic Review
Applies checklist categories in order:
1. Critical requirements
2. API design
3. Code quality
4. Architecture
5. Documentation
6. Tests

### Step 4: Report Generation
Creates actionable report with:
- Specific file:line references
- Code examples (before/after)
- Clear action items
- Severity classifications

## Configuration

The skill is configured in `SKILL.md` with:

```yaml
name: code-review
description: Performs comprehensive code reviews using Axon Framework standards
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Task
```

## Tips for Best Results

1. **Commit before reviewing** - Skill works best with committed changes
2. **Review early** - Catch issues before they compound
3. **Read the quick-reference** - Familiarize with common patterns
4. **Address blocking issues first** - Don't let perfect be the enemy of good
5. **Use with other skills** - Combine with `axon-framework-5-patterns` for infrastructure components

## Example Output

```markdown
# Code Review Report

## Summary
- Files Changed: 5
- Blocking Issues: 2 ❌
- Warnings: 3 ⚠️
- Suggestions: 2 💡

## BLOCKING ISSUES ❌

### Missing Antora Documentation
**Location:** `EventStore.java:123`
**Issue:** New feature added without documentation
**Action:** Add documentation in docs/reference-guide/modules/events/pages/

### Missing @since Tag
**Location:** `EventStore.java:456`
**Issue:** New public method readEvents() without @since tag
**Action:** Add @since 5.1.0 to method JavaDoc

## WARNINGS ⚠️

### Missing @author Tag
**Location:** `EventStoreImpl.java:78`
**Issue:** Refactored code from original author not credited
**Action:** Add @author Greg Woods

[... more sections ...]

## Next Steps
1. Add Antora documentation for new feature
2. Add @since tags to new methods
3. Add @author credit for refactored code
```

## Maintenance

### Updating the Checklist
Edit `../../code-review-checklist.md` to add new review criteria.

### Adding New Patterns
Update `quick-reference.md` with new common issues or code patterns.

### Modifying Report Format
Edit `templates/review-report-template.md` for different report structure.

## Related Documentation

- **Comprehensive Checklist**: `../../code-review-checklist.md` (27 categories, compiled from 20+ PRs)
- **AF5 Patterns**: `../axon-framework-5-patterns/SKILL.md` (Builder patterns and coding standards)
- **Antora Docs**: `/docs` (Reference guide and migration docs)

## Version History

- **2026-02-06**: Initial creation based on analysis of PRs #4116, #4136, #4120, #4090, #4141, #4147, #4150, #4101, #4077, #4099, #4131, #4075, #4121, #4149, #4152, #4164, #4165, and others

---

**Note:** This skill performs systematic reviews but doesn't replace human judgment for architectural decisions, complex trade-offs, or design philosophy questions. Escalate these to human reviewers.
