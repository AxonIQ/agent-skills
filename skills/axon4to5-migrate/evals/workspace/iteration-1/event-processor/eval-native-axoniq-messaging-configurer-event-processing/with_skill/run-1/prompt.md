# Eval 5: native-axoniq-messaging-configurer-event-processing

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-native-axoniq-messaging-configurer-event-processing/with_skill/run-1/outputs/AxonProcessorConfigNative.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-native-axoniq-messaging-configurer-event-processing/with_skill/run-1/outputs/AxonProcessorConfigNative.java`. AxonProcessorConfigNative.java has an AF4 main()-based bootstrap calling configurer.eventProcessing().registerPooledStreamingEventProcessor(...). Per use-case 05: replace the AF4 chain with EventSourcingConfigurer.create().messaging(messaging -> messaging.eventProcessing(eventProcessing -> eventProcessing.pooledStreaming(pooledStreaming -> pooledStreaming.processor("ReadModel_Dwelling", module -> module.eventHandlingComponents(components -> components.autodetected(cfg -> new DwellingReadModelProjector(...))).customized((cfg, conf) -> conf.batchSize(100).initialSegmentCount(8)))))). Add MessagingConfigurer / EventSourcingConfigurer imports. Drop AF4 DefaultConfigurer / EventProcessingConfigurer / Configurer imports. Do NOT introduce the Spring-only EventProcessorDefinition. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-native-axoniq-messaging-configurer-event-processing/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-native-axoniq-messaging-configurer-event-processing/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

