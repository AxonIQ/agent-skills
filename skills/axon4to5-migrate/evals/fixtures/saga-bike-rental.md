# Eval fixture — `saga` on `PaymentSaga`

**AF4:** `axon4/bike-rental-extended/rental/.../paymentsaga/PaymentSaga.java`
**AF5:** `axon5/bike-rental-extended/rental/.../paymentsaga/PaymentSaga.java`

Reference: the AF5 file is the **Shape B** outcome — `@Component` + JPA `PaymentStateRepository` + `@Scheduled` cancellation poll replacing `@DeadlineHandler`. The recipe itself NEVER produces this rewrite — it surfaces the decision and exits with `result: needs-decision` / `blocked`. The AF5 reference shows what the user produces afterwards.

## Trigger (INIT detection)

```
/axon4to5-migrate
```

(saga is a `not-supported` row — fires at INIT against any project, then per-saga when reached)

## Must-haves at INIT / per-saga

### Detection

- ✅ Grep `@Saga\b|@SagaEventHandler|@StartSaga|@EndSaga|SagaConfigurer` finds `PaymentSaga.java`.
- ✅ Blocker grep `@DeadlineHandler|DeadlineManager|DeadlineMessage|deadlineManager\.schedule|cancelSchedule|cancelAllWithinScope` fires → `decisions.deadline-handler-in-saga: present`.
- ✅ `AskUserQuestion` surfaces the four options:
  - `migrate-to-event-handler-with-state` (BLOCKED because `deadline-handler-in-saga: present` — unless Shape B is picked)
  - `accept-stays-af4`
  - `pause-migration` *(Recommended)*
  - `remove-feature-first`

### When user picks `migrate-to-event-handler-with-state` + `shape-b-jpa-state-with-scheduler`

- ✅ `result: blocked` with `caller-expects.next: route-to:event-processor`.
- ✅ `decisions.saga = migrate-to-event-handler-with-state`, `decisions.shape = shape-b-jpa-state-with-scheduler`.
- ✅ Recipe DOES NOT write code — emits worked-example reference and exits. The user creates the JPA `PaymentState`, `PaymentStateRepository`, and migrated `PaymentSaga` themselves; the `event-processor` recipe then runs on the rewritten file.
- ✅ A new dated `learnings.md` entry is appended with the FQN + decision + reason.

### When user picks `accept-stays-af4`

- ✅ `result: blocked`, `caller-expects.next: record-and-skip`.
- ✅ No code changes. AF4 source unchanged.
- ✅ `progress.md` Pinned-decisions records: `saga (PaymentSaga): accept-stays-af4`.
- ✅ `learnings.md` notes the slice must be excluded from the AF5 build path at stabilization.

## Anti-patterns

- ❌ Recipe **auto-rewrites** the saga (it never produces `result: success`).
- ❌ AF4 saga code (`@Saga`, `@SagaEventHandler`, `@StartSaga`, `@EndSaga`, `DeadlineManager`) **silently deleted**.
- ❌ Routing to `event-processor` BEFORE the user picks `migrate-to-event-handler-with-state` (the route-to is a post-decision instruction, not a default).
- ❌ Recipe ignores the `@DeadlineHandler` blocker and suggests Shape A (`@InjectEntity` + event-sourced state) — Shape A has no deadline mechanism; deadlines are present here.
- ❌ Recipe writes the JPA `PaymentState` / `PaymentStateRepository` for the user — out of scope; only the user produces them.

## Output contract

```yaml
result: needs-decision | blocked     # never success
target: io.axoniq.demo.bikerental.rental.paymentsaga.PaymentSaga
reason: "saga has @DeadlineHandler — four-way choice required"
decisions:
  saga: pending | migrate-to-event-handler-with-state | accept-stays-af4 | pause-migration | remove-feature-first
  shape: n/a | shape-b-jpa-state-with-scheduler         # only when migrate
  deadline-handler-in-saga: present
caller-expects:
  commit: false                       # needs-decision; or true on blocked with rewrite trail
  next: ask-user | record-and-skip | route-to:event-processor
notes: |
  Verbatim AskUserQuestion options. When migrate + Shape B picked, names the target component
  class + JPA state entity + repository the user will create (PaymentState, PaymentStateRepository).
```
