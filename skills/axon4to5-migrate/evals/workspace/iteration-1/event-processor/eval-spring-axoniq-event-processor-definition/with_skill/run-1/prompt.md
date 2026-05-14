# Eval 4: spring-axoniq-event-processor-definition

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-event-processor-definition/with_skill/run-1/outputs/AxonProcessorConfigSpring.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-event-processor-definition/with_skill/run-1/outputs/AxonProcessorConfigSpring.java`. AxonProcessorConfigSpring.java has an AF4 @Bean ConfigurerModule wiring a pooled streaming processor + handler matcher + customisation. Per use-case 04: replace the @Bean ConfigurerModule with @Bean EventProcessorDefinition (import org.axonframework.extension.spring.config.EventProcessorDefinition) using the fluent builder .pooledStreaming("ReadModel_Dwelling").assigningHandlers(...).customized(...). Delete the AF4 ConfigurerModule/EventProcessingConfigurer imports. The @Bean method name is free choice; the AF4 method is named configureProjectors. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-event-processor-definition/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-event-processor-definition/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

