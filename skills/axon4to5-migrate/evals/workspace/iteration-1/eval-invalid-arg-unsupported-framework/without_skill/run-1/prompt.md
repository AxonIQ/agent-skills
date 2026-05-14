# Eval 28: invalid-arg-unsupported-framework

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=spring configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-invalid-arg-unsupported-framework/without_skill/run-1/outputs/Calendar.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=spring configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-invalid-arg-unsupported-framework/without_skill/run-1/outputs/Calendar.java`. `framework=spring` is NOT supported (must be `axon` or `axoniq`). Per SKILL.md pre-step 1, the orchestrator MUST STOP and report unsupported framework — no migration runs. Write whatever message the orchestrator produces verbatim to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-invalid-arg-unsupported-framework/without_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-invalid-arg-unsupported-framework/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

