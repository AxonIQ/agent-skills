---
name: axoniq-framework-contribute-pr-comments
description: >
  Process GitHub PR review comments one by one for an Axon Framework pull request.
  Use when the user says "process PR comments", "work through review comments",
  "handle review feedback", "go through PR feedback", or provides a GitHub PR URL or PR number
  and wants to address reviewer comments systematically.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Task, TodoWrite
---

# PR Comment Processing Skill

Process reviewer comments on a GitHub PR one by one, verifying each comment against the actual code before acting on it. Never blindly apply suggestions — first understand the reviewer's intent, confirm the concern is still valid in the current code, then implement only what is correct.

## Prerequisites

This skill requires two CLI tools to be installed and authenticated:

- **`gh`** (GitHub CLI) — used to fetch PR comments, reviews, and metadata via the GitHub API. Install: `brew install gh` / `gh auth login`.
- **`git`** — used to read the current file state, find the module root, and compare the diff against the working tree. Must be run from within a checkout of the target repository.

Check both before doing anything else:

```bash
gh auth status
git rev-parse --is-inside-work-tree
```

If either check fails, stop and tell the user what is missing before proceeding.

## Arguments
- $ARGUMENTS: A GitHub PR reference — full URL (`https://github.com/owner/repo/pull/123`), short form (`owner/repo#123`), or bare number (`123`) when run from within the target repo.

---

## Phase 1: Resolve the PR Reference

Determine the owner, repo, and PR number from $ARGUMENTS:

```bash
# If a full URL is given, parse it:
# https://github.com/AxonIQ/AxonFramework/pull/4552 → owner=AxonIQ repo=AxonFramework pr=4552

# If only a number is given, infer repo from git remote:
gh repo view --json nameWithOwner -q .nameWithOwner

# Fetch PR metadata (use the resolved $PR_OWNER, $PR_REPO, $PR_NUMBER):
gh pr view "$PR_NUMBER" --repo "$PR_OWNER/$PR_REPO" \
  --json title,author,baseRefName,headRefName,headRepository,state,body
```

Extract and store:
- `PR_OWNER` — repository owner
- `PR_REPO` — repository name
- `PR_NUMBER` — PR number
- `PR_AUTHOR` — `.author.login`
- `PR_BASE_BRANCH` — `.baseRefName`
- `PR_HEAD_BRANCH` — `.headRefName`
- `PR_HEAD_REPO` — `.headRepository.owner.login` (the fork owner; equals `PR_OWNER` when not a fork)
- `PR_STATE` — `.state` (one of `OPEN`, `MERGED`, `CLOSED`)

### Check PR state

If `PR_STATE` is `MERGED` or `CLOSED`, inform the user before continuing:
> "This PR is already `<PR_STATE>`. You can still process its comments (e.g., to address feedback in a follow-up), but no further commits can be pushed to it directly."

Then wait for the user to confirm they want to proceed.

### Verify the local repo matches the PR

```bash
# Extract owner/repo from the remote URL — handles both HTTPS and SSH formats:
# https://github.com/AxonIQ/AxonFramework.git  →  AxonIQ/AxonFramework
# git@github.com:AxonIQ/AxonFramework.git      →  AxonIQ/AxonFramework
git remote get-url origin \
  | sed 's|.*github.com[:/]\(.*\)\.git|\1|; s|.*github.com[:/]\(.*\)|\1|'
```

Compare the extracted `owner/repo` string to `$PR_OWNER/$PR_REPO`. If they do not match, stop and tell the user:
> "Your working directory is `<local-repo>` but the PR is on `<PR_OWNER>/<PR_REPO>`. Please navigate to the correct repository."

### Handle forked PRs

If `PR_HEAD_REPO` differs from `PR_OWNER` (i.e., the PR comes from a fork), the PR branch is not automatically present locally. Before fetching it, warn the user:

```bash
# Show the current branch so the user knows what will change
git branch --show-current
```

Tell the user:
> "This PR comes from a fork (`<PR_HEAD_REPO>`). To read the correct file versions I need to check out the PR branch locally. Your current branch is `<CURRENT_BRANCH>`. This will switch your working tree — do you want to proceed?"

Wait for confirmation before running:

```bash
gh pr checkout "$PR_NUMBER" --repo "$PR_OWNER/$PR_REPO"
```

After the skill session is complete, remind the user to switch back to their original branch if needed.

---

## Phase 2: Fetch All Comments

Fetch all three comment sources with pagination. Never assume a single page is complete.

### 2a. Inline review comments (line-specific) — with resolved state

Resolved thread state is only available via GraphQL — the REST API does not expose it.

```bash
# Fetch thread resolution state via GraphQL — paginated with cursor
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 100) {
            pageInfo {
              hasNextPage
            }
            nodes {
              databaseId
            }
          }
        }
      }
    }
  }
}' -f owner="$PR_OWNER" -f repo="$PR_REPO" -F pr="$PR_NUMBER"
```

Note: `-f` passes a string value; `-F` passes a typed value (integer for the PR number). On the **first call**, omit `-f cursor=...` entirely — `$cursor` is nullable and defaults to null, which fetches from the start. On **subsequent calls**, add `-f cursor="<endCursor value from previous response>"`.

If `pageInfo.hasNextPage` is true on `reviewThreads`, repeat the query passing `pageInfo.endCursor` as `$cursor` until `hasNextPage` is false. Collect all `nodes` across pages before proceeding.

If any thread's `comments.pageInfo.hasNextPage` is true, that thread has more than 100 replies. This is extremely rare in practice, but if encountered, fetch the remaining `databaseId`s using a cursor-paginated query scoped to that thread:

```bash
gh api graphql -f query='
query($threadId: ID!, $cursor: String) {
  node(id: $threadId) {
    ... on PullRequestReviewThread {
      comments(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          databaseId
        }
      }
    }
  }
}' -f threadId="<THREAD_NODE_ID>" -f cursor="<END_CURSOR>"
```

Repeat until `hasNextPage` is false, then merge the additional `databaseId`s into the thread's mapping.

Use the `databaseId` values to map each inline comment to its thread's `isResolved` and `isOutdated` flags.

Then fetch the inline comments themselves:

```bash
gh api --paginate \
  "repos/$PR_OWNER/$PR_REPO/pulls/$PR_NUMBER/comments" \
  --jq '[.[] | {
    id: .id,
    in_reply_to_id: .in_reply_to_id,
    author: .user.login,
    body: .body,
    path: .path,
    line: (.line // .original_line),
    diff_hunk: .diff_hunk,
    created_at: .created_at
  }]'
```

Merge the two results: attach `isResolved` and `isOutdated` from GraphQL to each comment using the `databaseId` → `id` mapping.

### 2b. Review bodies (top-level reviewer summaries)

```bash
gh api --paginate \
  "repos/$PR_OWNER/$PR_REPO/pulls/$PR_NUMBER/reviews" \
  --jq '[.[] | select(.body != "" and .body != null) | {
    id: .id,
    author: .user.login,
    body: .body,
    state: .state,
    submitted_at: .submitted_at,
    source: "review_body"
  }]'
```

Review bodies have no file or line attached. However, a reviewer may mention specific files, classes, or line numbers in their prose (e.g., "line 87 in `Foo.java` looks wrong"). When processing a review body comment in Phase 9, scan the text for:
- Explicit file names or paths (e.g., `Foo.java`, `org/axonframework/...`)
- Line number references (e.g., "line 87", "L87")
- Class or method names that appear in the PR's changed files

If such references are found, look up the relevant code and treat the review body as if it were an inline comment on that location. If the references are ambiguous or no specific location can be inferred, present the review body as a general concern and ask the user where it applies.

### 2c. Issue comments (general conversation on the PR)

```bash
gh api --paginate \
  "repos/$PR_OWNER/$PR_REPO/issues/$PR_NUMBER/comments" \
  --jq '[.[] | {
    id: .id,
    author: .user.login,
    body: .body,
    created_at: .created_at,
    source: "issue_comment"
  }]'
```

---

## Phase 3: Build Comment Threads

Group inline comments into threads using `in_reply_to_id`:

- A comment with no `in_reply_to_id` is a **thread root**.
- Comments with `in_reply_to_id` are **replies** — attach them to their root in chronological order.
- Each thread carries the `isResolved` and `isOutdated` flags from Phase 2a.

Each thread becomes one unit — not individual comments.

Review bodies (2b) and issue comments (2c) are standalone units with no threading.

---

## Phase 4: Filter Noise

Remove units that do not require action:

| Filter | Rule |
|---|---|
| **Bot comments** | Author login ends in `[bot]` (e.g., `github-actions[bot]`, `sonarcloud[bot]`) |
| **Resolved threads** | `isResolved` is true, unless a reply in the thread after the resolution expresses disagreement (e.g., "this wasn't actually addressed", "I still think…") — in that case keep the thread and mark it `needs discussion` |
| **Pure praise** | Thread contains only positive sentiment with no actionable request ("LGTM", "Nice!", "+1") |

**Do NOT filter:**
- Resolved threads where the resolution is contested
- Threads with `isOutdated: true` — flag them but keep them; the underlying concern may still apply to current code
- The PR author's own replies — these are essential context for understanding the thread

If after filtering there are zero actionable units, stop and report:
> "No actionable comments found — all threads are resolved, bot-generated, or purely positive."

---

## Phase 5: Classify Each Thread

Assign one label and one status per thread.

**Classification label** (based on content of the root comment):

| Label | Meaning |
|---|---|
| `[SUGGESTION]` | Contains a GitHub suggestion block (` ```suggestion `) — a ready-made code replacement |
| `[CHANGE]` | Requests a code change, rename, refactor, or restructure |
| `[NIT]` | Minor style or cosmetic issue, low priority |
| `[QUESTION]` | Asks why/how something works; may or may not require a code change |
| `[DOCS]` | Requests documentation or JavaDoc update |
| `[TEST]` | Requests new or improved test coverage |

**Status flag** (set during classification or updated in Phase 9 Step 3 after reading the code):

| Status | Set when | Meaning |
|---|---|---|
| `valid` | Phase 5 | Concern appears actionable based on the thread content |
| `stale` | Phase 5 | `isOutdated: true` from GitHub — code has changed since comment was written; verify before acting |
| `questionable` | Phase 5 **or** Phase 9 Step 3 | Reviewer's premise appears to be based on a misread — either obvious from the comment text alone, or discovered after reading the actual code. Do not implement; discuss first. |
| `needs discussion` | Phase 5 | `[QUESTION]` thread requiring a response rather than a code change |

`questionable` can be detected in two places: in Phase 5 when the comment text contains a clearly incorrect assertion (e.g., "this method is never called" when it clearly is), or in Phase 9 Step 3 after reading the code and finding the concern does not hold. Either way, the handling is the same: do not implement, draft a reply, wait for user confirmation.

A `[QUESTION]` that the reviewer answers themselves ("I see now that…") within the same thread can be downgraded to resolved and filtered in Phase 4.

---

## Phase 6: Build the Overview

Do a **lightweight** pass to build the overview table — do not read every file here. That would be prohibitively slow for large PRs and will be done per-comment during Phase 9 when it is actually needed.

For this pass, only extract from the data already fetched:
- File path and line number from the comment
- Whether the file path resolves in the local working tree: `git ls-files --error-unmatch <path> 2>/dev/null`

For paths that do not resolve, set their Status column to `⚠️ path not found` in the table and add a note below the table listing the affected comment numbers and their paths:

```
⚠️ The following paths could not be found in the local working tree.
The file may have been deleted, renamed, or the wrong branch is checked out:
  - Comment #7: messaging/src/main/java/org/axonframework/OldClass.java
```

Output a numbered overview table, sorted by file then line number, grouped by file:

```
# PR #4552 — Review Comments Overview
## AxonIQ/AxonFramework — "Fix handler wrapper chain preservation"

Total: 12 threads | 9 actionable | 2 stale | 1 resolved

---

### messaging/src/main/java/org/axonframework/.../AnnotatedEventHandlingComponent.java

| # | Lines | Author | Label | Summary | Status |
|---|-------|--------|-------|---------|--------|
| 1 | 87–92 | reviewer-a | [CHANGE] | Replace instanceof with canHandleMessageType() | valid |
| 2 | 102 | reviewer-a | [NIT] | Rename local variable for clarity | valid |
| 3 | 115 | reviewer-b | [QUESTION] | Why not unwrap here? | needs discussion |

### messaging/src/test/java/org/axonframework/.../AnnotatedEventHandlingComponentTest.java

| # | Lines | Author | Label | Summary | Status |
|---|-------|--------|-------|---------|--------|
| 4 | 44 | reviewer-a | [TEST] | Add test for wrapped handler scenario | valid |

### (General PR comments — no file)

| # | Author | Label | Summary | Status |
|---|--------|-------|---------|--------|
| 5 | reviewer-b | [QUESTION] | Confirm this doesn't affect replay behavior | needs discussion |

---

**Dependencies detected:**
- Comments #1 and #4 are linked: fixing #1 (code change) requires adding test #4 to verify it.
- Comment #2 is independent.
```

---

## Phase 7: Create Todo List

Create a TodoWrite task for each actionable thread. Format:

```
PR#<number> #<N>: [LABEL] — <brief description> (<file>:<line>)
```

Example:
```
PR#4552 #1: [CHANGE] — Replace instanceof with canHandleMessageType() (AnnotatedEventHandlingComponent.java:87)
PR#4552 #2: [NIT] — Rename local variable (AnnotatedEventHandlingComponent.java:102)
PR#4552 #3: [QUESTION] — Discuss: why not unwrap at line 115?
PR#4552 #4: [TEST] — Add wrapped handler test (AnnotatedEventHandlingComponentTest.java:44)
PR#4552 #5: [QUESTION] — Confirm no replay behavior regression
```

---

## Phase 8: Wait

After the overview and todo list are set up, **wait**. Do not auto-process any comments.

Tell the user:
> "Overview ready. Say `start` or `next` to process the first item, or `process #N` to jump to a specific one."

---

## Phase 9: Process Comments One by One

For each comment the user asks to process, follow these steps in order.

### Step 1: Show the full thread

Display the complete thread — root comment and all replies in chronological order. Include the `diff_hunk` so the user can see what the reviewer was looking at.

### Step 2: Read the current code

If this comment has status `⚠️ path not found`, stop here and tell the user:
> "Comment #N was flagged — `<path>` could not be found in the working tree. This may mean the file was deleted, renamed, or a different branch is checked out. Should I skip this comment or search for the file under a different path?"

Wait for the user to decide before proceeding.

Otherwise, use the `Read` tool on `comment.path`, from line `max(1, comment.line - 30)` to `comment.line + 30`. This gives ±30 lines of context around the exact location the reviewer was looking at.

Compare the current code to the `diff_hunk` from the comment. If the code has visibly changed, note it explicitly — this is the primary signal that the thread may be stale.

### Step 3: Assess the concern

State clearly:

- **Still relevant?** Is the code the reviewer flagged still present?
- **Premise correct?** Does the reviewer's concern hold given what the code actually does?
- **Reviewer intent (the WHY):** Articulate what problem the reviewer is trying to solve, not just what they asked for. A rename suggestion may be about reducing ambiguity; a restructure suggestion may be about enforcing a separation of concerns.
- **Confidence:** HIGH (clear issue) / MEDIUM (likely issue, minor uncertainty) / LOW (possible misunderstanding — do not implement without confirming with the user)

If confidence is LOW: do not implement. Draft a clear explanation of what the code does and why it may be correct, and ask the user whether to reply or investigate further.

If the thread is `stale`: show what the reviewer saw vs. what the code looks like now, and ask the user whether the current code already addresses the concern.

If the thread is `questionable`: explain the misread and draft a reply for the user to review. Do not post it — the user must confirm first.

### Step 4: Check for dependencies

List any other open todo items linked to this comment. If fixing this will also resolve others, say so now — before implementing — so the user can decide to process them together.

### Step 5: Implement (HIGH or MEDIUM confidence only)

Apply the change. Implement the reviewer's **intent**, not necessarily the literal wording of their suggestion. If a `[SUGGESTION]` block exists, use it as a starting point but verify it compiles correctly — the surrounding code may have changed since it was written. Check that the suggestion covers all affected call sites, not just the single line it was placed on.

### Step 6: Find and run related tests

Set `$CHANGED_FILE` to the path of the file you edited in Step 5 (e.g., `messaging/src/main/java/org/axonframework/messaging/annotation/AnnotatedEventHandlingComponent.java`). Then find the relevant test files:

```bash
# Find test files by class name — use the short name to locate candidates
CHANGED_CLASS=$(basename "$CHANGED_FILE" .java)

find . \( -name "${CHANGED_CLASS}Test.java" \
       -o -name "${CHANGED_CLASS}Tests.java" \
       -o -name "${CHANGED_CLASS}IT.java" \
       -o -name "${CHANGED_CLASS}IntegrationTest.java" \) 2>/dev/null

# Also find test files that reference the class
grep -r "$CHANGED_CLASS" --include="*Test*.java" --include="*IT*.java" -l 2>/dev/null
```

Identify the Gradle module that owns the changed file:

```bash
# Walk up from the file's directory until a build.gradle or build.gradle.kts is found
FILE_DIR=$(dirname "$CHANGED_FILE")
MODULE_ROOT="$FILE_DIR"
while [ "$MODULE_ROOT" != "." ] && [ "$MODULE_ROOT" != "/" ]; do
  if [ -f "$MODULE_ROOT/build.gradle" ] || [ -f "$MODULE_ROOT/build.gradle.kts" ]; then
    break
  fi
  MODULE_ROOT=$(dirname "$MODULE_ROOT")
done
```

Convert the module root to a Gradle module path (e.g., `./messaging` → `:messaging`).

Before running the tests, extract the fully qualified class name from each test file — do not guess it from the filename alone:

```bash
# Read the package declaration from the test file
grep "^package " path/to/FooTest.java
# Output: package org.axonframework.messaging.annotation;
# Fully qualified name: org.axonframework.messaging.annotation.FooTest
```

Then run with the fully qualified name:

```bash
# module :messaging, class org.axonframework.messaging.annotation.FooTest
./gradlew :messaging:test --tests "org.axonframework.messaging.annotation.FooTest" 2>&1 | tail -40
```

**Tests must pass before marking the comment as done.**

If a test fails:
1. Read the failing test to understand what it verifies.
2. Determine whether your implementation is wrong, or whether the test is testing behavior that the reviewer's change intentionally alters.
3. Fix the implementation first (preferred). Only update a test if the behavioral change is intentional and clearly supported by the reviewer's stated intent.

### Step 7: Check for companion changes

After a successful test run, ask:

- **Documentation?** Does this change affect user-facing behavior, rename a concept, or change an API? If so, flag a `[DOCS]` item.
- **New test needed?** Does the change introduce a new code path not currently covered? If so, flag a `[TEST]` item.
- **Other callers affected?** Renames and signature changes require finding all call sites. Use the actual name of the method, class, or field you just changed — not a placeholder:

```bash
# Replace CHANGED_SYMBOL with the exact method/class/field name you modified
grep -r "CHANGED_SYMBOL" --include="*.java" -l 2>/dev/null
```

If the change was a rename, grep for both the old name (to find remaining references) and the new name (to confirm all sites were updated). If callers exist outside the changed file, list them for the user and ask whether they should also be updated.

### Step 8: Mark done

Mark the corresponding TodoWrite task as completed. State what was changed in one sentence.

Then wait. Move to the next item only when the user says `next` or `process #N`.

---

## Handling Special Cases

### Stale thread (`stale`)

Show the diff hunk (what the reviewer saw) alongside the current code. Explicitly state whether the current code addresses the reviewer's concern. Let the user decide: close it, or treat it as active.

### Questionable premise (`questionable`)

Do NOT implement. Explain what the code actually does. Draft a polite reply. Ask the user: "This looks like it may be based on a misread — does this explanation look right to you, or do you want to look deeper?"

### Question thread (`[QUESTION]`)

Two sub-cases:
- **No code change needed**: Draft a reply. User confirms before any posting.
- **Question reveals a real issue**: Re-classify as `[CHANGE]` and process accordingly.

### Suggestion block (`[SUGGESTION]`)

Use the suggestion as a starting point. Before applying:
1. Verify the surrounding code hasn't changed in a way that makes the suggestion incorrect.
2. Check whether the suggestion covers all affected call sites.
3. Run tests after applying.

### Linked comments

When two or more comments are dependency-linked, process them together in one step: implement all changes, run tests once, mark all linked items done together.

### `show thread #N`

Display the full thread for comment N (root comment and all replies in chronological order, plus `diff_hunk`) without entering the processing loop. Do not read files, assess, or implement anything. This is for inspection only.

### `run tests for #N`

Re-run the tests that were associated with comment N's change. Identify the changed file from the todo item description, re-derive the module and fully qualified class names using Step 6 logic, and run the Gradle command. Report pass/fail.

---

## Test Verification Principles

- **Never skip tests**, even for NITs or renames — a rename that breaks a test reveals a real dependency.
- If no test covers the changed code, flag it after implementing: "No test found for this path — consider adding one."
- Run only the tests for the affected Gradle module, not the full build, to keep feedback fast.
- If `./gradlew` is not available, check for `mvn` (Maven) or `make test` as alternatives.

---

## Output Format Per Comment

Use this structure when processing each comment:

```
---
## Comment #3 — [CHANGE] — AnnotatedEventHandlingComponent.java:115
Reviewer: reviewer-b | Thread: 2 messages | Status: valid

### Reviewer said:
> [root comment verbatim]

### Replies:
> [each reply in chronological order]

### Diff hunk (what the reviewer saw):
[diff_hunk from the comment]

### Current code at line 115 (±30 lines):
[current file content]

### Assessment:
- Still relevant: YES — code is unchanged since the comment
- Premise correct: YES — canHandleMessageType() is more robust here
- Reviewer intent: Ensure handler type detection works through wrapper chains
- Confidence: HIGH

### Dependencies:
- Linked to #6: same pattern in HandlerEnhancerDefinition.java:203 — process together?

### Proposed change:
[before/after block or unified diff]

### Tests to run:
- :messaging:test --tests "org.axonframework.messaging.annotation.AnnotatedEventHandlingComponentTest"

### Companion changes:
- HandlerEnhancerDefinition.java:203 (comment #6)
---
```

---

## Quick Reference

| User says | Action |
|---|---|
| `/axoniq-framework-contribute-pr-comments https://github.com/...` | Run phases 1–8, then wait |
| `start` / `next` | Process next open todo item |
| `process #N` | Process specific comment N |
| `skip #N` | Mark as skipped, move on |
| `show overview` | Re-display the overview table |
| `show thread #N` | Show full thread without processing |
| `which comments are linked?` | List dependency groups |
| `run tests for #N` | Re-run tests for the change made for comment N |
