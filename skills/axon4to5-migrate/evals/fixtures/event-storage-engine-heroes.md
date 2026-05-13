# Eval fixture — `event-storage-engine` on heroes project

**AF4:** `axon4/heroes/.../resources/application.yaml` + `axon4/heroes/.../GameConfiguration.java` + `axon4/heroes/.../HeroesOfDDDApplication.java`.
**AF5:** corresponding files in `axon5/heroes/`.

Heroes uses JPA event store with Axon Server **disabled** (`axon.axonserver.enabled: false`), so the recipe must pick Path A.JPA. Phase 8 also bundles a configuration sweep (sequencing-policy `@Bean` rewrite, `EntityScan`).

## Trigger

```
/axon4to5-migrate
```

(phase 8 reached during PHASED run)

## Must-haves

### Main bean swap (Path A.JPA)

Heroes has NO explicit `@Bean EventStorageEngine` in AF4 (relied on Spring Boot auto-config). Per the recipe's A.JPA preamble, AF5 with `axoniq-spring-boot-starter` on the classpath does NOT reliably auto-pick the JPA engine — the connector's enhancer wins. **Recipe MUST add an explicit `@Bean EventStorageEngine`**:

- ✅ A new `@Bean EventStorageEngine` method exists, constructing `AggregateBasedJpaEventStorageEngine(new JpaTransactionalExecutorProvider(emf), eventConverter, UnaryOperator.identity())`.
- ✅ Imports: `org.axonframework.eventsourcing.eventstore.EventStorageEngine`, `…jpa.AggregateBasedJpaEventStorageEngine`, `…transaction.jpa.JpaTransactionalExecutorProvider`, `…conversion.EventConverter`, `jakarta.persistence.EntityManagerFactory`, `java.util.function.UnaryOperator`.

### `@EntityScan` (A.JPA.5)

- ✅ The main application class is annotated `@EntityScan(basePackages = {"com.dddheroes.heroesofddd", "org.axonframework", "io.axoniq.framework"})` (matches the AF5 reference exactly).
- ✅ Import `org.springframework.boot.autoconfigure.domain.EntityScan` added.

### YAML migration (`application.yaml`)

- ✅ `axon.serializer.*` keys renamed to `axon.converter.*`.
- ✅ Each processor's `sequencing-policy: gameIdSequencingPolicy` YAML entry **removed** (moved to class-level `@SequencingPolicy` annotation in Step 7 of the relevant processors).
- ✅ Processor `mode: pooled` stays — `pooled` is valid AF5.
- ✅ `Read_GetAllDwellings_QueryCache.sequencing-policy` also removed (line-by-line consistent with AF5 reference).

### Configuration sweep — `GameConfiguration.java`

AF4 has `@Bean SequencingPolicy<EventMessage<?>>` reading metadata. AF5 reference rewrites the signature and lambda body. Recipe must:

- ✅ Import `org.axonframework.eventhandling.async.SequencingPolicy` → `org.axonframework.messaging.core.sequencing.SequencingPolicy`.
- ✅ Import `org.axonframework.eventhandling.EventMessage` → `org.axonframework.messaging.eventhandling.EventMessage`.
- ✅ Imports `org.axonframework.messaging.correlation.*` → `org.axonframework.messaging.core.correlation.*` (three classes: `CorrelationDataProvider`, `MessageOriginProvider`, `SimpleCorrelationDataProvider`).
- ✅ The `gameIdSequencingPolicy()` bean's lambda updated from `e -> e.getMetaData().get(...)` to `(e, ctx) -> Optional.ofNullable(e.metadata().get(...))`. Two-param lambda, `Optional` wrap, AF5 accessor `metadata()` (not `getMetaData()`).
- ✅ Return type stays `SequencingPolicy<EventMessage>` (or `EventMessage<?>` — AF5 reference uses the raw form).
- ✅ Import `java.util.Optional` added.

### Snapshotting & dependencies

- ✅ `Output.decisions.schema-change-flagged: true` (JPA backend) and a learnings entry created (`aggregate_event_entry` table needed, user-owned out-of-band).
- ✅ `serializer-ports-flagged: none` (Jackson default — no custom `Serializer`).
- ✅ `mongo-event-store: none`, `jdbc-event-store: none`, `custom-storage-engine-subclass: none`.

## Anti-patterns

- ❌ Skipping the explicit `@Bean EventStorageEngine` because "Spring Boot auto-configures it" — the recipe's A.JPA preamble explicitly warns this is wrong with `axon-server-connector` on the classpath.
- ❌ Producing any `.sql` / Flyway / Liquibase artifact for the `aggregate_event_entry` schema change — the recipe is **code only**.
- ❌ Partial `@EntityScan` (missing one of the three roots). Per A.JPA.5, partial is worse than none.
- ❌ Leaving the AF4 `axon.serializer.*` keys in YAML alongside AF5 `axon.converter.*`.
- ❌ Leaving YAML `sequencing-policy: gameIdSequencingPolicy` after moving the policy to a class annotation.
- ❌ Leaving the `@Bean SequencingPolicy<...>` method body still calling `e.getMetaData()` (AF4 accessor) — fails to compile on AF5.

## Output contract

```yaml
result: success
target: com.dddheroes.heroesofddd.GameConfiguration       # primary target; recipe touches multiple files
decisions:
  path: A (Spring Boot)
  backend: jpa
  bean-replaced: eventStorageEngine
  schema-change-flagged: true
  serializer-ports-flagged: none
  mongo-event-store: none
  jdbc-event-store: none
  custom-storage-engine-subclass: none
caller-expects: { commit: true, next: proceed }
notes: |
  JPA backend selected — user must apply AF5 schema change for `aggregate_event_entry` before runtime.
  @EntityScan covers com.dddheroes.heroesofddd + org.axonframework + io.axoniq.framework.
  Sequencing policy moved from YAML keys to @SequencingPolicy on each processor class.
```
