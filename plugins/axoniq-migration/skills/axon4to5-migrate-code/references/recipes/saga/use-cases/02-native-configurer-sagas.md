# Use case 02 - Native configuration: registering a saga with `Sagas.of(...)`

**Why interesting:** without Spring Boot there is no `@Saga` discovery, so the saga needs explicit registration. AF5
has no dedicated saga-configuration construct: `Sagas.of(...)` builds an ordinary `EventHandlingComponent` that goes on
a normal event processor, so the saga inherits everything the processor offers.

**Apply-condition:** `configuration=native`.

## Before (AF4)

```java
Configurer configurer = DefaultConfigurer.defaultConfiguration()
        .registerComponent(SagaStore.class, c -> JpaSagaStore.builder()
                                                             .entityManagerProvider(entityManagerProvider)
                                                             .build())
        .eventProcessing(processing -> processing.registerSaga(OrderSaga.class));
```

The saga's processing group defaulted to the saga's simple name plus `Processor`, unless changed with
`assignProcessingGroup` / `@ProcessingGroup`.

## After (AF5, `axon-legacy`)

```java
MessagingConfigurer.create()
                   .componentRegistry(cr -> cr.registerComponent(
                           SagaStore.class,
                           c -> JpaSagaStore.builder()
                                            .entityManagerProvider(entityManagerProvider)
                                            .converter(c.getComponent(Converter.class))
                                            .build()
                   ))
                   .eventProcessing(processing -> processing.pooledStreaming(
                           pooled -> pooled.defaultProcessor(
                                   "OrderSagaProcessor",
                                   components -> components.declarative("Saga[OrderSaga]",
                                                                        Sagas.of(OrderSaga.class))
                           )
                   ));
```

`Sagas` is `org.axonframework.modelling.saga.configuration.Sagas`. The saga class itself migrates exactly as in
[use case 01](01-spring-boot-legacy-module.md) - lifecycle parameter, `CommandDispatcher` parameter, collaborators as
handler parameters.

## Processor name is the token-store key

The processor name passed to `defaultProcessor(...)` **must be the name the AF4 deployment used**. Anything else and
the pooled processor finds no token, starts at the head of the stream, and in-flight sagas never see the events
published before that point. When the AF4 name cannot be read from the source, that is Blocker B2 - ask, do not guess.

## Several sagas on one processor

`Sagas.of(...)` returns a plain component builder, so a processor can carry several sagas beside other event-handling
components, and the whole set can be decorated:

```java
components -> components.declarative("Saga[OrderSaga]", Sagas.of(OrderSaga.class))
                        .declarative("Saga[ShipmentSaga]", Sagas.of(ShipmentSaga.class))
                        .withExceptionHandler(c -> loggingExceptionHandler)
```

This reproduces the AF4 behaviour of co-locating sagas in one processing group.

## Variants of `Sagas.of(...)`

| Signature | Use when |
|---|---|
| `of(sagaType)` | the saga has a no-argument constructor and uses the registered `SagaStore` |
| `of(sagaType, sagaFactory)` | the saga lacks a no-arg constructor, or needs a collaborator its handler methods cannot receive as a parameter |
| `of(sagaType, sagaStore)` | this saga type belongs in a different store than the registered component |

Prefer `of(sagaType)` plus handler parameters. A `sagaFactory` re-introduces field-held collaborators, which is the AF4
`ResourceInjector` habit the migration is moving away from.

## Subscribing vs pooled streaming

A subscribing processor keeps handling on the publishing thread, inside the publisher's `ProcessingContext` - closest
to the AF4 default for a saga driven by a local event bus. A pooled streaming processor is the choice for a saga that
has to keep up with a stream rather than with its publisher, and is what an AF4 `TrackingEventProcessor`-backed saga
maps onto. Either way, match what AF4 did; a pooled processor needs a `TokenStore` component.

## What did NOT happen

- No `SagaConfiguration` / `registerSaga` equivalent was looked for - it does not exist in AF5; `Sagas.of(...)` on a
  processor is the whole registration surface.
- The saga class was not annotated `@Namespace` - in native configuration the processor name is the string passed to
  `defaultProcessor(...)`.
