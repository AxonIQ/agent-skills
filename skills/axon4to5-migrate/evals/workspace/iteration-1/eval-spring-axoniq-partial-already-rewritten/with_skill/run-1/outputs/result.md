**Result:** ✅ Success
**Source:** `/Users/mateusznowak/GitRepos/AxonIQ/migration-skills-clones/agent-skills-final/skills/axon4to5-migrate/evals/workspace/iteration-1/eval-spring-axoniq-partial-already-rewritten/with_skill/run-1/outputs/PartialCalendarSpring.java`
**Recipe:** axon4to5-aggregate

**Notes:** Partial-state source (OpenRewrite Phase 1 had swapped `@Aggregate` → `@EventSourced` but left AF4 imports, `@AggregateIdentifier`, `@CreationPolicy(CREATE_IF_MISSING)`, `AggregateLifecycle.apply(...)`, no `@EntityCreator`, no `EventAppender`). Applicable predicate 5 matched (partially-migrated event-sourced aggregate). Pre-Apply Success Criteria check failed; Plan-Apply ran once (use case 01-spring-boot-straight) and finished the migration to a fully-AF5 Path A shape. Post-Apply criteria all match.

**Learnings:**
- `@CreationPolicy(CREATE_IF_MISSING)` mapped to AF5 default semantics: instance `@CommandHandler` + no-arg `@EntityCreator` (per `aggregates/index.adoc` § Removal of `@CreationPolicy`); no static factory needed.
- `tagKey = "PartialCalendarSpring"` and `idType = CalendarId.class` emitted explicitly per recipe convention (never rely on defaults).
