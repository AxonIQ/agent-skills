# Eval 9: spring-axoniq-inventory-map-aggregatemember-blocker

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-inventory-map-aggregatemember-blocker/without_skill/run-1/outputs/Inventory.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-inventory-map-aggregatemember-blocker/without_skill/run-1/outputs/Inventory.java`. Inventory has `@AggregateMember private Map<String, StockItem> items` — AF5 @EntityMember does NOT support Map-typed members → expect Blocker B2. Copy the Result block verbatim to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-inventory-map-aggregatemember-blocker/without_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-inventory-map-aggregatemember-blocker/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

