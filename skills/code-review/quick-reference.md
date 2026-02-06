# Code Review Quick Reference

Fast lookup guide for common review scenarios. For comprehensive details, see `../code-review-checklist.md`.

## Top 10 Most Common Issues

Based on analyzing 20+ PRs, fix these first:

1. ❌ **Missing `@since` tags** - Add to ALL new public/protected members
2. ❌ **Missing Antora docs** - Feature changes MUST update `/docs`
3. ❌ **Missing `@author` tags** - Credit original authors when refactoring
4. ⚠️ **Missing null annotations** - Add `@Nullable` / `@Nonnull` (jakarta, not jspecify!)
5. ⚠️ **Generic exceptions** - Use `AxonConfigurationException`, not `IllegalStateException`
6. ⚠️ **Low test coverage** - Must reach 80% minimum
7. 💡 **Public methods** - Could they be `protected` or `private`?
8. 💡 **LinkedList for lookups** - Use `LinkedHashMap` instead
9. 💡 **AF4 builder pattern** - Convert to AF5 fluent style
10. 💡 **Missing JavaDoc examples** - Add usage examples for complex APIs

## Fast Checks (Under 2 Minutes)

### 1. Documentation Check (30 seconds)
```bash
# Check if reference guide was updated
git diff --name-only | grep "^docs/reference-guide/"

# If empty and feature changes exist → BLOCKING
```

### 2. Test Coverage Check (30 seconds)
```bash
# List changed Java files
git diff --name-only | grep "\.java$" | grep -v "Test\.java$"

# List test files
git diff --name-only | grep "Test\.java$"

# If new features without tests → WARNING
```

### 3. JavaDoc @since Check (30 seconds)
```bash
# Search for new public methods
git diff | grep "^\+.*public.*("

# Check if @since tags exist in the same file
git diff | grep "@since"

# Missing @since on new public methods → BLOCKING
```

### 4. Breaking Changes Check (30 seconds)
```bash
# Check for API changes
git diff | grep -E "(@Deprecated|public.*\(|protected.*\()"

# Look for migration docs
git diff --name-only | grep -i "migration"

# Breaking changes without docs → BLOCKING
```

## Critical Requirements Matrix

| Requirement | Check | Blocking? | Fix Time |
|------------|-------|-----------|----------|
| Reference guide updated | `/docs/reference-guide/modules` changes | ✅ YES | 15-60 min |
| `@since` tags | New public/protected | ✅ YES | 2 min |
| Test coverage ≥80% | Tests exist | ✅ YES | Varies |
| Breaking changes doc | Migration guide | ✅ YES | 30-60 min |
| `@author` tags | Refactored code | ⚠️ Should | 1 min |
| Null annotations | Parameters | ⚠️ Should | 5 min |
| Correct exceptions | Config errors | ⚠️ Should | 5 min |
| Method visibility | Public methods | 💡 Nice | 2 min |

## Code Pattern Quick Checks

### Fluent API (AF5 Pattern)
```java
// ❌ AVOID - AF4 style
MyComponent.builder()
    .withX(x)
    .build()

// ✅ PREFER - AF5 style
MyComponent.combining(name1, item1)
    .and(name2, item2)
    .withDefaults()
```

**Check:** Search for `.builder()` on infrastructure components → WARNING

### Exception Handling
```java
// ❌ AVOID
throw new IllegalStateException("Bad config")

// ✅ PREFER
throw new AxonConfigurationException("Component X requires Y to be configured")
```

**Check:** Search for `new IllegalStateException` in config code → WARNING

### Null Annotations
```java
// ❌ AVOID - Wrong library
import org.jspecify.annotations.NonNull;

// ✅ PREFER - Jakarta
import jakarta.annotation.Nonnull;
import jakarta.annotation.Nullable;

public void method(@Nonnull String required, @Nullable String optional)
```

**Check:** Search for `jspecify` imports → BLOCKING

### Data Structures
```java
// ❌ AVOID - Slow lookups
LinkedList<Item> items = new LinkedList<>();
// Walking this is O(n)

// ✅ PREFER - Fast lookups
LinkedHashMap<String, Item> items = new LinkedHashMap<>();
// Lookup is O(1)
```

**Check:** Search for `new LinkedList<>()` in non-queue usage → WARNING

### Modern Java
```java
// ❌ AVOID - Old style
if (token instanceof MultiSourceToken) {
    MultiSourceToken mst = (MultiSourceToken) token;
    // use mst
}

// ✅ PREFER - Pattern matching
if (token instanceof MultiSourceToken mst) {
    // use mst directly
}
```

**Check:** Look for cast on next line after instanceof → SUGGESTION

## JavaDoc Quick Patterns

### Class-Level
```java
/**
 * [Purpose and what it does]
 *
 * <p>[Additional details about usage]
 *
 * <p>Example usage:
 * <pre>{@code
 * MyComponent component = MyComponent.combining("name", item)
 *                                    .and("name2", item2)
 *                                    .withDefaults();
 * }</pre>
 *
 * @author [Author Name]
 * @since 5.1.0
 */
```

### Method-Level
```java
/**
 * [What it does - no capitalization for params]
 *
 * @param name the name of the item (no cap, concise)
 * @param item the item to add (no cap, concise)
 * @return this instance for fluent chaining
 * @throws AxonConfigurationException if name is duplicate
 * @since 5.1.0
 */
```

### Parameter Documentation Style
```java
// ❌ AVOID - Sentence style
@param name The name of the item.

// ✅ PREFER - Concise, lowercase
@param name the name of the item
```

## File-Specific Checks

### For New Java Classes
- [ ] Class-level JavaDoc with example
- [ ] `@author` tag
- [ ] `@since` tag
- [ ] All public methods documented
- [ ] Null annotations on all parameters
- [ ] Corresponding test file exists

### For Modified Java Classes
- [ ] New methods have `@since` tags
- [ ] `@author` preserved if refactoring
- [ ] JavaDoc updated for behavior changes
- [ ] Tests updated for changes

### For Test Files
- [ ] Test new public methods
- [ ] Test edge cases (null, empty, invalid)
- [ ] Descriptive test method names
- [ ] Clear assertion messages
- [ ] `@Nested` classes for organization

### For Documentation Files (.adoc)
- [ ] Sentence-case headings
- [ ] Use "for example" not "e.g."
- [ ] Code blocks properly formatted
- [ ] Cross-references use `xref:`
- [ ] Added to `nav.adoc` if new page

## Grep Patterns for Common Issues

```bash
# Missing @since on public methods
git diff | grep -A5 "^\+.*public.*(" | grep -v "@since"

# Wrong annotation library
git grep "org.jspecify"

# Generic exceptions in new code
git diff | grep "new IllegalStateException"
git diff | grep "new IllegalArgumentException"

# Missing null annotations
git diff | grep -B2 "^\+.*public.*(" | grep -v "@Nullable\|@Nonnull"

# Old-style instanceof
git diff | grep "instanceof.*{" -A1 | grep "^\+.*=.*("

# LinkedList usage
git diff | grep "new LinkedList"

# Builder pattern on infrastructure
git diff | grep "\.builder()"
```

## Severity Decision Tree

```
Is this issue blocking approval?
│
├─ YES if:
│  ├─ Missing required documentation
│  ├─ Security vulnerability
│  ├─ Breaking changes undocumented
│  ├─ Likely fails 80% test coverage
│  ├─ Missing @since on public API
│  └─ Resource leaks
│
├─ WARNING if:
│  ├─ Missing @author tags
│  ├─ Wrong exception types
│  ├─ Missing null annotations
│  ├─ Method visibility too broad
│  ├─ Performance concerns
│  └─ Code duplication
│
└─ SUGGESTION if:
   ├─ Naming improvements
   ├─ Additional test cases
   ├─ Code organization
   └─ Minor refactoring opportunities
```

## Review Timing Estimates

| Review Type | Duration | When to Use |
|-------------|----------|-------------|
| **Quick Check** | 2-5 min | Pre-commit sanity check |
| **Standard Review** | 15-30 min | Most PRs |
| **Comprehensive Review** | 45-90 min | Large features, breaking changes |
| **Architectural Review** | 90+ min | Major refactoring, new modules |

## Commands Cheat Sheet

```bash
# See what changed
git status --short
git diff --stat
git diff main...HEAD --name-only

# Check specific patterns
git diff | grep "@since"
git diff | grep "@author"
git diff --name-only | grep "^docs/"
git diff --name-only | grep "Test\.java$"

# Read changed files
git diff main...HEAD --name-only | xargs -I {} echo "Read: {}"

# Check for breaking changes
git diff main...HEAD | grep -E "(@Deprecated|public|protected)"

# Count changed lines
git diff --stat | tail -1
```

## When to Escalate

### Escalate to Human Reviewer
- Architectural decisions (new patterns, major refactoring)
- Complex performance implications
- Security-critical changes
- Cross-module impact unclear
- Design philosophy questions

### Can Review Confidently
- Missing documentation
- Missing JavaDoc tags
- Test coverage issues
- Code quality patterns
- Null safety
- Exception handling
- Naming conventions
- Visibility modifiers

## Review Report Template Shortcuts

### BLOCKING Issue Template
```markdown
### Missing Antora Documentation
**Severity:** BLOCKING ❌
**Location:** `EventStore.java:123`
**Issue:** New feature added without documentation
**Action:** Add docs in docs/reference-guide/modules/events/pages/
```

### WARNING Issue Template
```markdown
### Missing @since Tag
**Severity:** WARNING ⚠️
**Location:** `EventStore.java:456`
**Issue:** New public method without @since tag
**Action:** Add @since 5.1.0 to method JavaDoc
```

### SUGGESTION Template
```markdown
### Consider Reducing Visibility
**Severity:** SUGGESTION 💡
**Location:** `EventStore.java:789`
**Suggestion:** Method could be protected (only used by subclasses)
```

## One-Liner Review Assessment

After reading files, ask:
1. **Docs?** Changes in `/docs` for feature changes?
2. **Tests?** New tests for new code?
3. **Tags?** `@since` on new public methods?
4. **Break?** Breaking changes documented?
5. **Nulls?** Annotations on parameters?

If all YES → Detailed review
If any NO → Likely has blocking issues

---

**Remember:** The goal is helpful, actionable feedback that improves code quality while respecting the developer's effort.

**Related Files:**
- Full checklist: `../../code-review-checklist.md`
- Review template: `templates/review-report-template.md`
- AF5 patterns: `../axon-framework-5-patterns/SKILL.md`
