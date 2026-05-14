# Eval 24: native-axoniq-polymorphic-card-hierarchy

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-native-axoniq-polymorphic-card-hierarchy/with_skill/run-1/outputs/Card.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=native mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-native-axoniq-polymorphic-card-hierarchy/with_skill/run-1/outputs/Card.java`. Card is an abstract @AggregateRoot with two concrete subtypes (OpenLoopGiftCard, RechargeableGiftCard, both @Aggregate). AF5 shape: base class carries @EventSourcedEntity(concreteTypes = {OpenLoopGiftCard.class, RechargeableGiftCard.class}), subtypes are NOT annotated. Migrate the base AND the two subtypes. Copy the Result block verbatim to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-native-axoniq-polymorphic-card-hierarchy/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-native-axoniq-polymorphic-card-hierarchy/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

