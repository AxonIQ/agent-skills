# Eval 6: spring-axoniq-custom-sequencing-policy-rewrite

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-custom-sequencing-policy-rewrite/with_skill/run-1/outputs/TenantAndGameSequencingPolicy.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-custom-sequencing-policy-rewrite/with_skill/run-1/outputs/TenantAndGameSequencingPolicy.java`. TenantAndGameSequencingPolicy.java is a custom AF4 SequencingPolicy<EventMessage<?>> reading two metadata keys. Per use-case 06: swap interface to org.axonframework.messaging.core.sequencing.SequencingPolicy (no generic parameter); rename method getSequenceIdentifierFor → sequenceIdentifierFor; add ProcessingContext context parameter; return type Object → Optional<Object>; replace return null with Optional.empty() and bare returns with Optional.of(...); replace event.getMetaData() with message.metaData(); rename EventMessage import to AF5 location. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-custom-sequencing-policy-rewrite/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-custom-sequencing-policy-rewrite/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

