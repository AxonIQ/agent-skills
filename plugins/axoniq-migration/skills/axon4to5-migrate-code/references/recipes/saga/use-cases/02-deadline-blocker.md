# Use case 02 - Unsupported legacy deadlines block adaptation

`PaymentSagaWithDeadline` schedules a 30-second payment timeout, cancels it on payment confirmation, and compensates in an `@DeadlineHandler`.

The selected release is 5.4.0. Legacy deadline APIs are not ported in that release. A workflow timeout for new instances does not preserve the timeout of an already running saga.

## Expected outcome

Return a FLOW.md Blocker before Apply. Keep the scheduling code, cancellation code, handler, persisted scheduler data, and tests intact.

```markdown
**Result:** 🚧 Blocker
**Source:** `com.example.PaymentSagaWithDeadline`
**Recipe:** axon4to5-saga

**Notes:** `cancelPayment` schedules compensation after 30 seconds. The selected 5.4.0 legacy module does not provide its deadline APIs. Preserve AF4 execution until the existing deadline-dependent instances drain, or establish and verify equivalent deadline behavior before retrying. No deadline logic was removed.

**Learnings:**
## YYYY-MM-DD - Payment timeout controls compensation
**Trigger:** blocker
**Where:** `com.example.PaymentSagaWithDeadline:cancelPayment`
**Surprise:** This saga's payment timeout can trigger compensation without any further external event; upgrading only event handlers would leave orders pending indefinitely.
**Resolution:** Deferred adaptation pending a verified deadline plan.

**Options:**
- [ ] **skip** (Recommended) - retain the current source and report the unresolved deadline dependency.
- [ ] **revert** - undo this recipe's edits if this is a re-entry; do not alter runtime state.
- [ ] **solve-manually** - establish and test the deadline replacement outside this recipe, then retry.
```

## Resolution evidence

A separate replacement must preserve due times, correlation, cancellation, retries, compensation, and restart behavior for existing instances. Keep tests for those outcomes. Commented-out code, removed assertions, or a compile-only run do not resolve the blocker.

New workflow instances and the coordinated cutover are handled by `saga-to-workflow` once its prerequisites are met. Do not report this legacy item as successful merely because that later work is planned.
