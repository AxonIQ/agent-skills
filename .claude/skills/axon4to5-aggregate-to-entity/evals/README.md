# Evals for axon4to5-aggregate-to-entity

The evals here validate that the skill's **transformation rules** match
the real-world AF4 → AF5 migrations captured in
`.knowledge/repositories/axon-examples/`.

Each eval is a triple:

- **Input**: an AF4 candidate file (path under `.knowledge/.../axon4/...`)
- **Expected output**: the migrated AF5 form (path under `.knowledge/.../axon5/...`)
- **Run config**: `--configuration-mode` value the skill should be invoked with

The skill itself is not executed automatically — running it is what the
human reviewer does in an interactive session. The eval script instead
asserts that the **set of structural changes** the skill's procedure
prescribes is present when diffing input → expected output. If the
diff between AF4 and AF5 lacks any of the prescribed changes, the eval
fails and the procedure needs adjustment.

## Cases

| # | AF4 source | AF5 expected output | `--configuration-mode` | Notes |
|---|------------|---------------------|-------------------------|-------|
| 01 | `axon4/bike-rental-extended/rental/.../command/Bike.java` | `axon5/bike-rental-extended/rental/.../command/Bike.java` | `spring-boot` | Event-sourced aggregate in Spring Boot, snapshotTriggerDefinition attribute dropped, `@CreationPolicy(ALWAYS)` dropped, canonical case |
| 02 | `axon4/bike-rental-extended/payment/.../Payment.java` | `axon5/bike-rental-extended/payment/.../Payment.java` | `spring-boot` | Second event-sourced aggregate; same structural changes |

## Running

```bash
bash .claude/skills/axon4to5-aggregate-to-entity/evals/run.sh
```

The script:

1. For each case, computes the prescribed-changes checklist from the AF4
   input + the chosen `--configuration-mode`.
2. Reads the AF5 expected output.
3. Asserts each checklist item is satisfied in the AF5 file.
4. Prints a summary and exits non-zero on any failure.

## Discrepancies handled out-of-band

These differences between AF4 and AF5 in the example projects are **not**
caused by this skill and the eval ignores them:

- Command/event payloads moving from Java POJO `getXxx()` accessors to
  Java record accessors (`xxx()`). That migration belongs to a
  separate core-api skill.
- `@EventSourced(tagKey = "Bike")` in the AF5 example carries a `tagKey`
  attribute used by DCB-related features. This skill's minimal output
  is `@EventSourced` with no attributes; adding `tagKey` is an opt-in
  follow-up step, not part of the atomic aggregate-to-entity transform.
