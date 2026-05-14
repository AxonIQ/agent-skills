# Eval 2: spring-axoniq-projector-with-command-dispatch

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-projector-with-command-dispatch/without_skill/run-1/outputs/WhenCreatureRecruitedThenAddToArmyProcessor.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-projector-with-command-dispatch/without_skill/run-1/outputs/WhenCreatureRecruitedThenAddToArmyProcessor.java`. WhenCreatureRecruitedThenAddToArmyProcessor is an automation that listens to CreatureRecruited events and dispatches commands. It injects CommandGateway as a class-level field and calls sendAndWait inside the handler, with a try/catch for compensation. Apply the event-processor recipe per use-case 02: rewrite the CommandGateway field → CommandDispatcher method parameter; sendAndWait → async send(...).getResultMessage() chain; try/catch → .exceptionallyCompose(...); handler return type → CompletableFuture<? extends Message> (NOT CompletableFuture<? extends Message<?>> — AF5 Message is non-generic). Also: @ProcessingGroup → @Namespace, @DisallowReplay AF5 import, @MetaDataValue → @MetadataValue, and class-level @SequencingPolicy(MetadataSequencingPolicy with GameMetaData.GAME_ID_KEY). Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-projector-with-command-dispatch/without_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-projector-with-command-dispatch/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

