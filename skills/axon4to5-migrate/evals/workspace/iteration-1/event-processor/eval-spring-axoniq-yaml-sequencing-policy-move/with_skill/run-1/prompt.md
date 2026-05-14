# Eval 3: spring-axoniq-yaml-sequencing-policy-move

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-yaml-sequencing-policy-move/with_skill/run-1/outputs/application.yaml`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-yaml-sequencing-policy-move/with_skill/run-1/outputs/application.yaml`. The source is application.yaml. Per use-case 03: delete every `sequencing-policy:` key under `axon.eventhandling.processors.<group>.` (it moves to class-level @SequencingPolicy on each projector — out of THIS eval's scope); rename `axon.serializer.*` → `axon.converter.*`; rewrite `mode: tracking` → `mode: pooled` (AF5 has no TrackingEventProcessor). Preserve every other key byte-for-byte. Copy the Result block to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-yaml-sequencing-policy-move/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/event-processor/eval-spring-axoniq-yaml-sequencing-policy-move/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

