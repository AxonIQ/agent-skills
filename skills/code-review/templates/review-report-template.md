# Code Review Report

**Date:** [YYYY-MM-DD]
**Reviewer:** Claude Code Review
**Branch/PR:** [branch-name or PR#]
**Target Branch:** [main/develop]

---

## Executive Summary

- **Files Changed:** [X]
- **Issues Found:** [Total] ([Y] blocking, [Z] warnings, [W] suggestions)
- **Automated Fixes Available:** [Number of fixes ready to apply]
- **Documentation Items:** [Number requiring developer input]
- **Overall Status:** [READY / NEEDS FIXES / NEEDS DOCS]

**Quick Assessment:**
[1-2 sentence summary emphasizing what can be fixed automatically vs what needs developer input]

---

## SUGGESTED FIXES

> Numbered fixes with specific before/after code that can be applied immediately.

### FIX #1 (BLOCKING): [Brief Title]
**File:** `[file.java:line]`
**Severity:** BLOCKING ❌
**Category:** [Documentation / API Design / etc.]
**Issue:** [What's wrong - one clear sentence]
**Why:** [Explain reasoning - reference standards/patterns]

**Current code:**
```java
[Exact code from the file]
```

**Suggested fix:**
```java
[Corrected code - ready to apply]
```

**Impact:** [Any imports needed, side effects, or considerations]
**To apply:** Say "Apply fix #1" or "Apply all fixes"

**Reference:** [Checklist section if applicable]

---

### FIX #2 (WARNING): [Next Issue Title]
**File:** `[file.java:line]`
**Severity:** WARNING ⚠️
**Issue:** [Description]
**Why:** [Reasoning]

**Current code:**
```java
[Current implementation]
```

**Suggested fix:**
```java
[Improved implementation]
```

**Impact:** [Considerations]
**To apply:** Say "Apply fix #2"

---

### FIX #3 (SUGGESTION): [Improvement Title]
**File:** `[file.java:line]`
**Severity:** SUGGESTION 💡
**Issue:** [What could be better]
**Why:** [Benefit of the change]

**Current code:**
```java
[Existing code]
```

**Suggested fix:**
```java
[Enhanced code]
```

**Benefit:** [Why this improves the code]
**To apply:** Say "Apply fix #3"

---

## DOCUMENTATION NEEDED

> Items that require developer input - cannot be auto-fixed.

### DOC #1 (BLOCKING): [Documentation Gap]
**Issue:** [What documentation is missing]
**Required:** [Where it should be added - specific path]
**Should cover:**
- [Topic 1]
- [Topic 2]
- [Topic 3]

**Action:** Say "Generate doc template for DOC #1" for a starting point
**Reference:** Antora docs requirement - all features need documentation

---

### TEST #1 (BLOCKING): [Test Coverage Gap]
**Issue:** [What tests are missing]
**Required:** Tests for:
- [Method or scenario 1]
- [Method or scenario 2]

**Action:** Say "Generate test template for TEST #1" for a starting point
**Reference:** 80% coverage requirement

---

## POSITIVE FINDINGS ✅

> Good practices and well-executed elements worth acknowledging.

- ✅ **[Positive finding 1]**
  - Location: `[file.java]`
  - Note: [Why this is good]

- ✅ **[Positive finding 2]**
  - Location: `[file.java]`
  - Note: [Why this is good]

---

## Detailed Analysis by Category

### Documentation Review

#### Antora Documentation (Critical)
- [ ] Feature changes documented in `/docs`
- [ ] New pages added to navigation (`nav.adoc`)
- [ ] Migration guide included (if breaking changes)
- [ ] Code examples provided
- [ ] Vale linter rules pass

**Findings:**
[Details about documentation status]

#### JavaDoc Review
- [ ] All new public/protected members have JavaDoc
- [ ] `@since` tags present with correct version
- [ ] `@author` tags included/updated
- [ ] Parameter descriptions concise (no sentence-style caps)
- [ ] Class-level documentation with examples

**Findings:**
[Details about JavaDoc status]

---

### Test Coverage Review

#### Test Files Identified
- `[TestFile1.java]` - [Coverage assessment]
- `[TestFile2.java]` - [Coverage assessment]

#### Coverage Assessment
- [ ] All new public methods have tests
- [ ] Edge cases covered
- [ ] Null handling tested
- [ ] Concurrency tests (if applicable)
- [ ] Test names descriptive
- [ ] Likely meets 80% threshold

**Findings:**
[Details about test coverage]

**Potential Gaps:**
- [Method or scenario that may lack coverage]

---

### API Design Review

#### Fluent API Patterns
- [ ] No AF4-style builders on infrastructure components
- [ ] Fluent chaining methods present
- [ ] Descriptive static factory methods
- [ ] Follows AF5 patterns

**Findings:**
[Details about API design]

#### Null Safety
- [ ] `@Nullable`/`@Nonnull` annotations present
- [ ] Null checks before dereferencing
- [ ] No apparent NPE vulnerabilities

**Findings:**
[Details about null safety]

#### Method Visibility
- [ ] Methods as restrictive as possible
- [ ] Public API surface minimal and intentional

**Findings:**
[Details about method visibility]

---

### Code Quality Review

#### Error Handling
- [ ] Uses `AxonConfigurationException` for config errors
- [ ] No swallowed exceptions
- [ ] Error messages have context

**Findings:**
[Details about error handling]

#### Performance Considerations
- [ ] Appropriate data structures chosen
- [ ] No unnecessary object creation in hot paths
- [ ] Concurrency handled correctly

**Findings:**
[Details about performance]

#### Type Safety
- [ ] Proper generic type usage
- [ ] No unchecked casts
- [ ] No raw types

**Findings:**
[Details about type safety]

---

### Architecture Review

#### Design Patterns
- [ ] Appropriate use of framework patterns
- [ ] No circular dependencies
- [ ] Minimal coupling

**Findings:**
[Details about architecture]

#### Backward Compatibility
- [ ] No breaking changes OR properly documented
- [ ] Storage compatibility considered
- [ ] Serialization compatibility maintained

**Findings:**
[Details about compatibility]

---

## Files Reviewed

### Modified Files
1. `[path/to/file1.java]` - [Brief description of changes]
2. `[path/to/file2.java]` - [Brief description of changes]

### Test Files
1. `[path/to/Test1.java]` - [Assessment]
2. `[path/to/Test2.java]` - [Assessment]

### Documentation Files
1. `[docs/path/to/file.adoc]` - [Assessment]

### Configuration Files
1. `[path/to/config]` - [Assessment]

---

## Checklist Status

### Critical Requirements
- [ ] Antora documentation updated in `/docs`
- [ ] JavaDoc complete with `@since` tags
- [ ] Test coverage adequate (≥80%)
- [ ] No breaking changes OR properly documented
- [ ] No security vulnerabilities

### API Design
- [ ] Fluent API patterns followed (AF5 style)
- [ ] Null safety annotations present
- [ ] Method visibility minimized
- [ ] Naming conventions followed

### Code Quality
- [ ] Error handling uses correct exception types
- [ ] Performance considerations addressed
- [ ] Type safety maintained
- [ ] Resource cleanup handled properly

### Architecture
- [ ] Design patterns aligned with framework
- [ ] No circular dependencies
- [ ] Backward compatibility maintained

### Documentation
- [ ] Reference guide updated
- [ ] Migration guide (if needed)
- [ ] JavaDoc complete and accurate
- [ ] Vale linter passes

---

## Automated Checks Status

### SonarQube Quality Gates
- [ ] Coverage ≥ 80% on new code
- [ ] Duplication ≤ 3%
- [ ] Reliability Rating: A
- [ ] Security Rating: A
- [ ] Maintainability Rating: A
- [ ] Security Hotspots: 0

**Note:** CI will enforce these automatically.

### Build Status
- [ ] All modules compile successfully
- [ ] No compiler warnings introduced
- [ ] Tests pass

---

## SUMMARY BY SEVERITY

**BLOCKING (must fix before commit):** [N]
- [List blocking items - both FIX# and DOC#/TEST#]

**WARNINGS (should fix):** [N]
- [List warning items]

**SUGGESTIONS (nice to have):** [N]
- [List suggestion items]

---

## QUICK ACTIONS

Ready to fix these issues? Here are your options:

### Apply All Fixes
```
"Apply all fixes"
```
Applies: [FIX #1, #2, #3, ...]
Result: [X] blocking issues, [Y] warnings, [Z] suggestions fixed

### Apply By Severity
```
"Apply blocking fixes only"
"Apply all warnings"
"Apply all suggestions"
```

### Apply Specific Fixes
```
"Apply fix #1"
"Apply fixes #1, #3, #5"
```

### Generate Templates
```
"Generate doc template for DOC #1"
"Generate test template for TEST #1"
```

### Get More Details
```
"Show me fix #[N] in detail"
"Explain why fix #[N] is needed"
```

---

## PROGRESS TRACKER

**Current Status:**
- Total Issues: [N]
- Can Auto-Fix: [X] issues
- Need Developer Input: [Y] items (documentation, tests, architecture)

**After Applying All Fixes:**
- Remaining Issues: [Y]
- Status: [READY / NEEDS DOCS / NEEDS TESTS / NEEDS REVIEW]

---

## REVIEW NOTES

### Assumptions Made
[Any assumptions during review that should be verified]

### Questions for Author
1. [Question about implementation choice]
2. [Next question]

### Additional Context
[Any relevant context about the review or findings]

---

## REFERENCES

- **Comprehensive Checklist:** `.claude/code-review-checklist.md`
- **AF5 Patterns:** `.claude/skills/axon-framework-5-patterns/SKILL.md`
- **Related PRs:** [Link to similar PRs for context]

---

## REVIEW SUMMARY

**Current Recommendation:** [NEEDS FIXES / NEEDS DOCS / READY AFTER FIXES / READY]

**Path to Approval:**
1. [Apply X automated fixes → Say "Apply all fixes"]
2. [Add Y documentation items → Start with "Generate doc template for DOC #1"]
3. [Add Z test cases → Start with "Generate test template for TEST #1"]
4. [Then: Re-review or commit]

**Automated Fix Coverage:** [X]% of issues can be fixed automatically
**Manual Work Needed:** [Y] documentation items, [Z] test cases

---

*Review performed by Claude Code Review Skill*
*Review Criteria Version: 2026-02-06*
