# Eval 6: spring-axoniq-dwelling-snapshot-blocker-emitted

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-dwelling-snapshot-blocker-emitted/without_skill/run-1/outputs/Dwelling.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-dwelling-snapshot-blocker-emitted/without_skill/run-1/outputs/Dwelling.java`. Dwelling declares @Aggregate(snapshotTriggerDefinition="dwellingSnapshotTrigger"). AF5 has no portable equivalent → expect Blocker B1. No decision is pre-pinned — the recipe must emit the Blocker rather than silently dropping the attribute. Copy the Result block VERBATIM (must contain the Options list with skip/revert/solve-manually) to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-dwelling-snapshot-blocker-emitted/without_skill/run-1/result.md. The file MAY be partially rewritten by OpenRewrite — do not fail the eval if so; we only check the recipe's emitted Result.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-dwelling-snapshot-blocker-emitted/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

