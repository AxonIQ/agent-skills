# Eval 30: native-axoniq-partial-already-rewritten

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-native-axoniq-partial-already-rewritten/with_skill/run-1/outputs/PartialOrderNative.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-native-axoniq-partial-already-rewritten/with_skill/run-1/outputs/PartialOrderNative.java`. PartialOrderNative.java is the framework-Configurer (Path B) equivalent of eval 29: `@EventSourcedEntity` annotation already present (swapped from `@AggregateRoot`) but with NO tagKey/idType attributes; `@AggregateIdentifier` still there; `@CreationPolicy(ALWAYS)` still there; `AggregateLifecycle.apply(...)` in handler bodies; AF4 `@CommandHandler` / `@EventSourcingHandler` imports; no `@EntityCreator`; no `EventAppender` parameter. The recipe MUST apply predicate 5 (partial), see Success Criteria mismatch, run Plan-Apply once, and finish the migration. The `@CreationPolicy(ALWAYS)` should become a **static** `@CommandHandler` factory per the recipe's # Common steps § @CreationPolicy mapping. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-native-axoniq-partial-already-rewritten/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-native-axoniq-partial-already-rewritten/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

