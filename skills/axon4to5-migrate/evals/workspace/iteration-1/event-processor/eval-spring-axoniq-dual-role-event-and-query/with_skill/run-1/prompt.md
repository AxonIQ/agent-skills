# Eval 7: spring-axoniq-dual-role-event-and-query

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-dual-role-event-and-query/with_skill/run-1/outputs/GetAllDwellingsQueryHandler.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-dual-role-event-and-query/with_skill/run-1/outputs/GetAllDwellingsQueryHandler.java`. GetAllDwellingsQueryHandler has BOTH @QueryHandler AND @EventHandler methods on the same class — dual-role per use-case 07. Apply: @ProcessingGroup → @Namespace (preserve string), @SequencingPolicy(MetadataSequencingPolicy with GameMetaData.GAME_ID_KEY) at class level, AF5 @EventHandler / @QueryHandler imports (both must move — keep the file internally consistent), @MetaDataValue → @MetadataValue on every method (query AND event), preserve @Component. Do NOT touch method bodies, return types, or ResponseType. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-dual-role-event-and-query/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-dual-role-event-and-query/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

