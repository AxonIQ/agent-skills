# Use case 03 - Source is not a saga

`$SOURCE` is `CreatureRecruitmentAggregate.java`, annotated `@Aggregate` with `@EventSourcingHandler` methods.

## Expected outcome

```markdown
**Result:** ⏭️ Rejected
**Source:** `com.example.CreatureRecruitmentAggregate`
**Recipe:** axon4to5-saga

**Notes:** The source is an event-sourced aggregate with no saga annotations. Route to the aggregate recipe. No edits made.

**Learnings:** none - routine source mismatch.
```

Leave the source unchanged. For an ordinary projector without saga annotations, route to `event-processor`. If a class already uses legacy saga annotations, evaluate it for idempotent Success instead of rejecting it based on its unchanged package names.
