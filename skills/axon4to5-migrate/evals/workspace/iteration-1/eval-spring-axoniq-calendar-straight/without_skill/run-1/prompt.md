# Eval 1: spring-axoniq-calendar-straight

NO migration skill is loaded. Migrate from general AF5 knowledge — handler/annotation moves, @EventSourced / @EventSourcedEntity, @EntityCreator on the no-arg constructor, EventAppender as a method parameter on @CommandHandlers, drop AggregateLifecycle.apply.

## Skill invocation arguments (use exactly)
`framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-calendar-straight/without_skill/run-1/outputs/Calendar.java`

## Task
You are inside an interactive Claude Code session. The axon4to5-migrate Skill lives at /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate. Open SKILL.md there, then invoke the orchestrator with arguments exactly `framework=axoniq configuration=spring mode=single source=/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-calendar-straight/without_skill/run-1/outputs/Calendar.java`. The orchestrator must: run its OpenRewrite pre-step, match the aggregate recipe (Calendar is annotated @Aggregate + @EventSourcingHandler), execute the recipe sub-flow, and rewrite /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-calendar-straight/without_skill/run-1/outputs/Calendar.java IN PLACE to AF5 shape. After it finishes, copy the orchestrator's emitted Result block VERBATIM to /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-calendar-straight/without_skill/run-1/result.md (the block starts with `**Result:**` and ends after the last bullet). Do not invent content for result.md — it must be the literal block. No blocker is expected. No pinned decisions are needed.

## Result capture
When the orchestrator finishes, COPY its final Result block VERBATIM (starts with `**Result:**`, ends after the last bullet) to:
  /Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-calendar-straight/without_skill/run-1/outputs/result.md
Do not paraphrase or summarise. If the orchestrator STOPs at the pre-step (invalid arg), copy that stop message instead.

