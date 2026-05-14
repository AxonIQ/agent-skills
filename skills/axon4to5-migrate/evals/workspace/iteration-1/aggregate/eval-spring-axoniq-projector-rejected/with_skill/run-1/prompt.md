# Eval 18: spring-axoniq-projector-rejected

You have the `axon4to5-migrate` Skill loaded at:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-projector-rejected/with_skill/run-1/outputs/DwellingReadModelProjector.java`

## Task
Invoke axon4to5-migrate at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate with `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-projector-rejected/with_skill/run-1/outputs/DwellingReadModelProjector.java`. The source is a read-model projector (@ProcessingGroup + @EventHandler), NOT an aggregate. The orchestrator's Match step in single mode must EITHER ask which recipe to apply OR (if it forces aggregate based on the user's recipe hint) the aggregate recipe must reject. For this eval, assume the user pinned recipe=aggregate — the recipe's # Applicable predicate must reject. Copy the Result block verbatim to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-projector-rejected/with_skill/run-1/result.md.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/aggregate/eval-spring-axoniq-projector-rejected/with_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

