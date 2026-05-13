# Recipe: event-storage-engine

Migrate the code wiring for the event store backend. This recipe never emits
SQL, DDL, data-copy scripts, token-store migration, or snapshot migration.

## Canonical reference

- [../../docs/paths/event-store.adoc](../../docs/paths/event-store.adoc)
- [../../docs/paths/configuration.adoc](../../docs/paths/configuration.adoc)
- [../../docs/paths/serializers.adoc](../../docs/paths/serializers.adoc)
- [not-supported.md](not-supported.md)
- [configuration.md](configuration.md) for generic configuration-class rewrites.

## Mandatory

Preserve AF4 aggregate-keyed event storage unless the user has explicitly
chosen a larger DCB migration outside this skill.

## Goal

The project declares or registers the correct AF5 `EventStorageEngine` code for
the existing backend and records any user-owned runtime/schema work.

## Inputs

- `target`: configuration class that owns event-store wiring.
- `wiring`: `spring-boot` or `framework-config`.
- `backend`: optional `jpa` or `axon-server`; derive from inspection when
  obvious.

## Preflight

1. Run blocker checks from `not-supported.md`.
2. Detect backend:

   | Signal | Backend |
   |---|---|
   | `JpaEventStorageEngine`, JPA event entry entities, JPA starter | `jpa` |
   | Axon Server connector/store beans | `axon-server` |
   | Mongo/JDBC/custom subclass | blocker or user decision from `not-supported.md` |

3. If AF5 aggregate-based engine is already wired and notes are recorded, emit
   `skipped`.

## Procedure

1. **Choose the AF5 engine.**

   | Backend | Preserve legacy aggregate storage | DCB path |
   |---|---|---|
   | JPA | `AggregateBasedJpaEventStorageEngine` | out of scope |
   | Axon Server | `AggregateBasedAxonServerEventStorageEngine` | only if explicitly chosen outside this skill |

2. **Apply the wiring path.**

   | `wiring` | JPA action | Axon Server action |
   |---|---|---|
   | `spring-boot` | Declare explicit `@Bean EventStorageEngine`; add `ConfigurationEnhancer` override when starter defaults would otherwise pick DCB/JPA defaults; ensure entity scan covers AF5 event-entry entities. | Declare explicit aggregate-based engine bean or remove AF4 storage bean only when connector auto-config and user choice support it. |
   | `framework-config` | Register aggregate-based JPA engine in the existing `EventSourcingConfigurer` / component registry. | Register aggregate-based Axon Server engine in the existing configurer chain. |

3. **Handle serializers/converters.**
   - If a custom AF4 `Serializer` is present, surface the required
     `Converter` port in `notes`.
   - Do not auto-port complex serializers unless the project already has an
     AF5 converter pattern.

4. **Record user-owned runtime work.**
   - JPA backend requires an out-of-band AF5 schema/data plan. Record it in
     `notes` and `learnings.md`; do not create SQL.
   - Axon Server aggregate-based path has no SQL step.

5. **Route generic configuration classes.**
   - During the same phase, classes that read `eventStore()` / `eventBus()` or
     declare generic configurer writes go through [configuration.md](configuration.md)
     as separate targets.

6. **Verify.**
   - Compile the configuration class in an isolated scope.
   - Runtime verification waits for final stabilization after user-owned schema
     work is complete.

## End condition

- AF4 storage-engine bean/registration is gone or intentionally blocked.
- AF5 aggregate-based engine is wired for the selected backend.
- User-owned schema/data work is recorded when required.
- No SQL or data-migration artifact was created.

## Output

```yaml
result: success | skipped | rejected | needs-decision | blocked | failed
target: <FQCN>
reason: <required except straightforward success>
decisions:
  wiring: spring-boot | framework-config
  backend: jpa | axon-server | blocked
  engine: AggregateBasedJpaEventStorageEngine | AggregateBasedAxonServerEventStorageEngine | none
  schema-work: user-owned | none
  serializer-ports-flagged: []
caller-expects:
  commit: true | false
  next: proceed | ask-user | record-and-skip | halt
notes: []
```

## Subagent guidelines

- `parallelism`: single.
- No test run is required here; use isolated compile and defer runtime checks to
  stabilization.
