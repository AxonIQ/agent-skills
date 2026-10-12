# Saga to workflow

This skill derives workflows from existing saga behavior, ports behavioral tests, and prepares coexistence and retirement. Start after the AF5 legacy-saga and DCB prerequisites are ready.

Use [SKILL.md](SKILL.md) for the agent instructions. The [Saga to Workflow Upgrade guide](https://docs.axoniq.io/axon-framework-reference/development/migration/paths/sagas-to-workflows/) contains saga/workflow comparisons and the persistent cutover procedure.

## Process overview

The skill reads the saga and its command handlers, reconstructs the observable state machine, proposes a workflow model, and checks the implementation against the recorded behavior. Tools extract and check evidence; agents write code and resolve decisions the tools cannot make. Work on one saga type at a time through planning, implementation, and verification.

See the [process diagram](https://docs.axoniq.io/axon-framework-reference/development/migration/paths/sagas-to-workflows/#process-overview). The sections below describe the original automation and identify which assets are included in the public skill.

The orchestrator records verification results; it cannot override a failed machine check. Model equivalence covers supported modeled behavior and declared changes. Unsupported cases require explicit review. A passing result is ready for review; it does not authorize a commit. Follow the code-conversion loop with [persistent cutover and restart verification](https://docs.axoniq.io/axon-framework-reference/development/migration/paths/sagas-to-workflows/#coexistence).

## 0. Orchestrator

In the original automation, the main agent takes one saga through the three phases. It assigns a fresh doer for each build round, a separate verifier, and a separate scorer. It copies verification evidence into the plan rather than editing code or deciding that a failing check has passed.

The original plan file is `MIGRATION-PLAN.md`; that is an existing tool interface. It records each saga, declared behavior changes, late-event decisions, unresolved items, and the results of the checks. The public skill currently asks for project upgrade notes without requiring this filename or an orchestration runtime.

## Plan: before writing code

| Step | Input | Tool or role | Output |
| --- | --- | --- | --- |
| **1. Read the saga's code** | Saga Java source and command handlers that affect it | OpenRewrite syntax-tree analysis | Per-handler facts: handled events, sent commands, deadlines scheduled or cancelled, and changed state. Per-command facts: events it can produce. Original outputs include `saga-facts/` and `command-emits.csv`. |
| **2. Build the flow graph** | Extracted facts | Graph and state-machine extraction | Modeled states and transitions for success, failure, and timeout; events still accepted after another path advances. Original outputs include `saga-machine.csv`, `late-events.csv`, and `saga-graph.csv`. |
| **3. Recognise patterns and plan** | Graph, facts, and pattern rules | Pattern rules implemented as Java records | Patterns for handlers and deadlines, including timeout, retry, compensation, and races; a step-by-step workflow skeleton. Original outputs include `saga-patterns.csv` and `saga-skeleton.md`. |
| **3a. Resolve leftovers** | Cases the deterministic rules cannot decide | Independent agent review with source quotes | Evidence-backed decisions; rerunning analysis checks whether the cited source and pattern still match. Unresolved cases remain visible. |
| **3b. Check consumers** | Changed events and downstream handlers | Consumer analyst, followed by deterministic checks | A decision for each changed event: preserve its contract or adapt the affected consumers. Consumer checks confirm that every affected handler has been accounted for. |

The prepared build input includes the plan, API information for the selected release, templates, explicit behavior changes, and the existing test-failure baseline. A recorded baseline explains pre-existing failures; it must not hide a newly introduced failure.

## Build loop: one saga at a time

| Step | Input | Tool or role | Output |
| --- | --- | --- | --- |
| **4. Write the workflow** | Plan, API sheet, templates, and the previous round's failure evidence | Fresh doer agent | Workflow class and tests. The doer runs the code and behavior checks before handing over. A separate verifier reruns the checks. |
| **5. Check the code** | Workflow, tests, plan, deadline and late-event decisions, baseline | Maven compilation, JUnit tests, and OpenRewrite rules | Findings with rule identifiers and source locations. Checks cover forbidden edits, workflow API use, command/wait ordering, compensation guards, readability, and adherence to the declared behavior. |
| **6. Compare behavior** | Saga model, workflow code, declared behavior changes | State-machine comparison using AutomataLib | Equivalent behavior within the supported model, the shortest separating input sequence, or an explicit unsupported-model result. The comparison observes inputs such as events, command outcomes, and timeouts, and outputs such as commands and terminal outcomes. |
| **7. Answer judged items** | Rules requiring judgment and the changed code | Independent verifier | Answers backed by code quotes, including data-condition meaning and behavior the model cannot represent. Judgment cannot erase a failed deterministic check. |

An example counterexample is a command failure that ends the saga but makes the workflow send `RejectPayment`. Such a difference must be fixed or explicitly accepted as a behavior change; it cannot silently pass as equivalent.

The original checker also examines compensation failures, terminal steps inside compensating blocks, and modeled states that cannot reach an end. These checks are bounded by what the source-to-model extractor supports. They do not prove arbitrary Java behavior or external service effects.

The loop has three outcomes:

- **A check fails:** give a fresh doer the failing lines, judged item, or separating input sequence and repeat the round.
- **The same rule fails in three rounds:** record the blocker and continue with another saga; do not report that saga as complete.
- **All checks pass:** record a review-ready result, then score it. Commits follow the user's requested workflow; reproducing this diagram does not enable automatic commits.

After this loop, complete [persistent coexistence and retirement checks](https://docs.axoniq.io/axon-framework-reference/development/migration/paths/sagas-to-workflows/#coexistence). Fixture success and model comparison do not establish durable token behavior, safe cutover, or restart recovery.

## Score: one result per saga

A fresh scorer uses the original saga, workflow, verification reports, and rubric. It neither edits the code nor replaces the build-loop verifier.

| Part | Evidence |
| --- | --- |
| **Required gates** | Compilation, tests/runtime evidence, no silent behavior change, and no workflow created from a historical start event. A failed gate sets the score to zero. |
| **Measured dimensions** | Rule adherence, correct workflow features, completeness, and behavior-check results. |
| **Judged dimension** | Readability, with a source quote for each deduction. |
| **Result** | A score out of 10 with evidence. The original report file is `migration-scorecard.md`. Scoring reports quality after verification; it cannot make a failed check pass. |

## Hooks in the original automation

The original Claude Code hooks reject forbidden edits such as stubs or commented-out behavior, run lint before commits, check for unfinished plan rows, and guard connections outside the configured sandbox. They are implementation-specific checks, not a claim that the public skill automatically enforces those restrictions in every agent runtime.

The public plugin does not currently install these hooks. Their integration needs to preserve the user's control over commits, stopping work, and authorized infrastructure access.

## Prepared assets and current packaging

The diagram's asset categories are listed below. Counts such as the number of lint rules or patterns are deliberately not fixed in the diagram because they change with the implementation.

| Prepared asset | Used by | Original implementation | Current public package |
| --- | --- | --- | --- |
| **Upgrade rules and review checklist** | Checks 5 and 7 | `references/rules.md`, `references/review-checklist.md` | Focused constraints in [SKILL.md](SKILL.md), [derivation](references/derive-workflow.md), and [verification](references/verification.md); not the full machine-linked catalog. |
| **Lint rules** | Check 5 | `lint/` and `saga-lint.yml` | Not bundled. The original composite gates still contain prerequisite-stage assumptions. |
| **Pattern catalogue** | Plan 3 | `references/patterns.md` | Behavioral guidance in [derivation](references/derive-workflow.md); the full deterministic catalogue is not bundled. |
| **Pattern rules** | Plan 3 | `PatternRules.java` and related analyzer classes | Not bundled. |
| **Renames and API sheet** | Build 4 | Official OpenRewrite recipe plus `scripts/api-sheet.sh` | [Version and API guidance](references/api-and-assets.md). Framework-wide rename work belongs to the earlier upgrade stages. |
| **Templates and helpers** | Build 4 | `Steps.java`, workflow and test templates | Four [portable Java assets](assets/java/), with fixture tests and context-aware command dispatch. |
| **Agent briefs** | Orchestrator, leftovers, consumers, build and review | `references/orchestration.md` | A scoped skill workflow and [behavior inventory](references/behavior-inventory.md); no mandatory subagent controller. |
| **Scoring rubric** | Score 8 | `references/scoring.md` | Verification reporting guidance; the original automated scorecard is not bundled. |
