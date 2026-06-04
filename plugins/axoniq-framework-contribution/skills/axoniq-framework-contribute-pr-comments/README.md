# Axon Framework Contributor PR Comments Skill

Process GitHub PR review comments one by one, verifying each concern against the actual code before acting on it. Never blindly applies suggestions — first understands the reviewer's intent, confirms the concern is still valid, then implements only what is correct.

## Purpose

This skill is for **working through reviewer feedback on Axon Framework pull requests** systematically and safely. It covers:

- Fetching all comment sources: inline review threads, review bodies, and issue comments
- Grouping replies into threads and detecting resolved and outdated state via GraphQL
- Filtering noise: bots, pure praise, and genuinely resolved threads
- Classifying what each comment asks for before touching any code
- Verifying whether the reviewer's premise is still correct against the current file state
- Implementing changes with the reviewer's intent in mind, not just the literal wording
- Running related tests after every change and checking for companion changes

## What's Covered

### 1. Comment Fetching and Thread Grouping
- All three GitHub comment sources with full REST pagination
- Resolved and outdated thread state via GraphQL (not available in the REST API)
- Reply threading via `in_reply_to_id`
- Fork detection and safe branch checkout with user confirmation

### 2. Classification
- `[SUGGESTION]` — GitHub suggestion block ready to apply
- `[CHANGE]` — code change, rename, refactor, or restructure
- `[NIT]` — minor style or cosmetic issue
- `[QUESTION]` — needs a response, may or may not require code change
- `[DOCS]` — documentation or JavaDoc update
- `[TEST]` — new or improved test coverage

### 3. Status Flags
- `valid` — actionable, proceed to implement
- `stale` — code changed since the comment; verify before acting
- `questionable` — reviewer's premise may be based on a misread; discuss before implementing
- `needs discussion` — question thread requiring a reply rather than a code change

### 4. Per-Comment Processing Loop
For each comment the user triggers:
1. Show the full thread and diff hunk
2. Read the current file at the commented location
3. Assess: still relevant? premise correct? reviewer intent? confidence level?
4. Check for linked dependencies before implementing
5. Implement at HIGH or MEDIUM confidence only
6. Find related tests using filename + grep, derive the fully qualified class name from the `package` declaration, run scoped Gradle tests
7. Check for companion changes: docs, new tests, other callers
8. Mark done and wait for the next `next` or `process #N`

### 5. Special Cases
- **Stale threads**: show diff hunk vs current code, let user decide
- **Questionable premise**: draft a reply, do not implement, wait for user confirmation
- **Suggestion blocks**: apply as starting point, verify call sites, run tests
- **Linked comments**: process together, run tests once, mark all done

## Prerequisites

- **`gh`** (GitHub CLI) — authenticated with `gh auth login`
- **`git`** — run from within a checkout of the target repository

## Usage

```bash
/axoniq-framework-contribute-pr-comments https://github.com/AxonIQ/AxonFramework/pull/4552
```

Or with a short form if run from inside the repo:

```bash
/axoniq-framework-contribute-pr-comments 4552
```

After the overview is shown, process comments interactively:

```bash
start          # process first item
next           # process next item
process #3     # jump to a specific comment
skip #2        # mark as skipped and move on
show overview  # re-display the full table
```

## File Structure

```
skills/axoniq-framework-contribute-pr-comments/
├── SKILL.md     # Complete skill with all phases and processing rules
└── README.md    # This file
```

## Related Skills

- **axoniq-framework-contribute-review** — Review a branch against AF5 standards before submitting a PR
- **axoniq-framework-contribute-code** — Design patterns for framework infrastructure components
- **axoniq-framework-contribute-docs** — Add or update reference documentation
