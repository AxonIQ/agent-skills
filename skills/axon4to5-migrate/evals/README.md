# Evals — axon4to5-migrate

Each eval pairs a real **AF4 source file** with its **AF5 target file** from the example repositories under `.knowledge/repositories/axon-examples/`. Both ends are checked-in; the orchestrator is graded on whether running the recipe on the AF4 file produces a result that matches the AF5 file (modulo whitespace).

Project pairs available:
- `axon-examples/axon{4,5}/heroes/` — Spring Boot, JPA event store, rich domain (aggregates, projectors, gateway callers, query handlers, an interceptor).
- `axon-examples/axon{4,5}/gamerental/` — Spring Boot, Axon Server, command + query side.
- `axon-examples/axon{4,5}/bike-rental-extended/` — multi-module Spring Boot, Axon Server, contains the **PaymentSaga** + `@DeadlineHandler` reference.

Each scenario in [scenarios.md](scenarios.md) names:

1. **Trigger** — the user invocation against the AF4 project.
2. **AF4 source** — repo-relative path under the AF4 example.
3. **Recipe expected** — exactly one routing-table row.
4. **AF5 reference** — the matching file in the paired AF5 example.
5. **Must-haves** — concrete assertions on the AF5 output (annotations, imports, method shapes, `Output.decisions` keys).
6. **Anti-patterns** — what the recipe MUST NOT do (silent deletions, wrong recipe routing, etc.).

Scenarios are grouped by recipe so when a recipe changes, the relevant evals run.

## How to run manually

1. Copy the AF4 example tree to a scratch dir: `cp -r .knowledge/repositories/axon-examples/axon4/<project> /tmp/<project>-af4-clone`.
2. Initialize git there: `cd /tmp/<project>-af4-clone && git init && git add -A && git commit -m 'baseline'`.
3. Invoke the skill against the scratch dir per the scenario's **Trigger**.
4. After the recipe commits, diff the migrated file against the AF5 reference:
   ```bash
   diff -u /tmp/<project>-af4-clone/<af4-source> .knowledge/repositories/axon-examples/axon5/<project>/<af5-reference>
   ```
5. **Pass** when every must-have holds. **Fail** when any anti-pattern triggers OR a must-have is missing.

## How to add a scenario

1. Find a real before/after pair in the repos above.
2. Add a row in [scenarios.md](scenarios.md).
3. If the scenario needs more than one assertion line, drop a `fixtures/<recipe>-<short-name>.md` file with the full check list.
