# Topic 9 — Snapshotting (worked example)

Observable shape:

- AF4 `@Aggregate(snapshotTriggerDefinition = "<beanName>")` on the
  root.
- A Spring `@Component("<beanName>")` (or plain `@Bean`) extending
  `EventCountSnapshotTriggerDefinition` (or
  `AggregateLoadTimeSnapshotTriggerDefinition`), with a numeric
  threshold passed to `super(snapshotter, N)`.

Two before/after pairs below — one for each AF5 target flavor — because
the wiring change differs.

## Before — Spring Boot AF4

```java
// Bike.java
@Aggregate(snapshotTriggerDefinition = "bikeSnapshotDefinition")
public class Bike { ... }

// BikeSnapshotDefinition.java
@Component("bikeSnapshotDefinition")
public class BikeSnapshotDefinition extends EventCountSnapshotTriggerDefinition {
    public BikeSnapshotDefinition(Snapshotter snapshotter) {
        super(snapshotter, 10);
    }
}
```

## After — `--configuration-mode=spring-boot` (Topic 9 forces an explicit module bean)

```java
// Bike.java — note: NO @EventSourced; the module bean below registers it
public class Bike { ... }   // class-body migration from Topics 1–5 still applied

// BikeConfiguration.java — replaces BikeSnapshotDefinition.java
@Configuration
class BikeConfiguration {

    @Bean
    EventSourcedEntityModule<String, Bike> bikeModule() {
        return EventSourcedEntityModule.declarative(String.class, Bike.class)
                .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10))
                .build();
    }

    @Bean
    SnapshotStore snapshotStore() {
        return new InMemorySnapshotStore();
        // switch to new AxonServerSnapshotStore(...) if the AF4 setup used Axon Server
    }
}
```

Notes for the Spring Boot path:

- The `@EventSourced` annotation in AF5 does **not** expose
  `snapshotPolicy`. The only way to keep snapshotting on Spring Boot is
  the explicit `EventSourcedEntityModule` `@Bean`. The entity class
  therefore drops its `@EventSourced` annotation — registration moves
  to the bean.
- The original AF4 `BikeSnapshotDefinition` class becomes dead code and
  should be deleted in the same diff.
- The diff summary in step 7 must surface (a) the dropped
  `@EventSourced` annotation, (b) the new `@Configuration` class, and
  (c) the deleted snapshot bean — these are non-trivial structural
  changes the human needs to see.

## After — `--configuration-mode=axon-configuration`

```java
// Bike.java — already on @EventSourcedEntity from Topic 2
@EventSourcedEntity
public class Bike { ... }

// AxonConfig.java — snapshot policy on the existing module registration
public class AxonConfig {

    public void configure(EventSourcingConfigurer configurer) {
        configurer
            .componentRegistry(cr -> cr.registerComponent(
                    SnapshotStore.class,
                    c -> new InMemorySnapshotStore()))
            .modelling()
            .registerEventSourcedEntity(
                EventSourcedEntityModule.declarative(String.class, Bike.class)
                    .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10))
            );
    }
}
```

Notes for the axon-configuration path:

- The `EventSourcedEntityModule.declarative(...)` registration from
  Topic 2 simply gains a `.snapshotPolicy(...)` call.
- A `SnapshotStore` component must be registered on the
  `EventSourcingConfigurer`. Default to `InMemorySnapshotStore`; use
  `AxonServerSnapshotStore` only if the AF4 application was running
  with Axon Server as event store.
- The original `BikeSnapshotDefinition` class becomes dead code — same
  rule as the Spring Boot path.

## Translation table

| AF4 trigger | AF5 `SnapshotPolicy` |
|-------------|----------------------|
| `EventCountSnapshotTriggerDefinition(snapshotter, N)` | `SnapshotPolicy.afterEvents(N)` |
| `AggregateLoadTimeSnapshotTriggerDefinition(snapshotter, Duration)` | `SnapshotPolicy.whenSourcingTimeExceeds(Duration)` |
| Custom subclass | Surface to the human; only auto-translate if the threshold is obvious in the constructor body. |

The threshold value (the `N` / `Duration`) is **carried over** from the
AF4 bean — never invented.
