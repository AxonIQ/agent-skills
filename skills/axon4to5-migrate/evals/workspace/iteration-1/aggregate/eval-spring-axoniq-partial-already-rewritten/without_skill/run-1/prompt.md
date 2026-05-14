# Eval 29: spring-axoniq-partial-already-rewritten

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-partial-already-rewritten/without_skill/run-1/outputs/PartialCalendarSpring.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-partial-already-rewritten/without_skill/run-1/outputs/PartialCalendarSpring.java`. PartialCalendarSpring.java is a realistic OpenRewrite-Phase-1 partial state: `@EventSourced` annotation is present (mechanically swapped from `@Aggregate`) but tagKey/idType attributes are missing; `@AggregateIdentifier` annotation + import still there; `@CreationPolicy(CREATE_IF_MISSING)` still there; `AggregateLifecycle.apply(...)` still in handler bodies; no `@EntityCreator`; no `EventAppender` parameter; AF4 `@CommandHandler` / `@EventSourcingHandler` imports. The recipe MUST apply # Applicable predicate 5 (partially-migrated event-sourced aggregate — continue to Research), find that the Success Criteria pre-Apply check fails (AF4 imports present, no EntityCreator, no EventAppender threading), run Plan-Apply once, and finish the migration to a fully-AF5 shape. Copy the Result block verbatim to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-partial-already-rewritten/without_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-partial-already-rewritten/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

