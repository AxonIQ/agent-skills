# Polymorphic aggregate hierarchy, plain Axon → axon-configuration

Observable shape that triggers this variant:

- Root class annotated with `@AggregateRoot` (no Spring stereotype).
- Configuration code registers the root with
  `AggregateConfigurer.defaultConfiguration(<Root>.class).withSubtypes(...)`.
- One or more subclasses extend the root; they do not carry their own
  `@AggregateRoot` annotation in this variant (in the Spring variant
  they each carry `@Aggregate` — see notes below).

AF4 source flavor: plain Axon
AF5 target flavor (`--configuration-mode`): `axon-configuration`

## Before (Java)

```java
// Root + subtypes (class bodies omitted — same shape as a simple
// event-sourced aggregate; @CommandHandler / @EventSourcingHandler
// methods live on root or subtypes as appropriate).

@AggregateRoot
public abstract class Card { /* ... */ }

public class GiftCard extends Card { /* ... */ }

public class OpenLoopGiftCard extends GiftCard { /* ... */ }
public class RechargeableGiftCard extends GiftCard { /* ... */ }

// Configuration:

import java.util.Set;
import org.axonframework.config.AggregateConfigurer;
import org.axonframework.config.Configurer;

public class AxonConfig {
    public void configure(Configurer configurer) {
        Set<Class<? extends GiftCard>> subtypes = Set.of(
                OpenLoopGiftCard.class,
                RechargeableGiftCard.class
        );

        configurer.configureAggregate(
                AggregateConfigurer.defaultConfiguration(GiftCard.class)
                                   .withSubtypes(subtypes)
        );
    }
}
```

## After (Java)

```java
// Root + subtypes — after Topic 1/3/4/5 transformations on the root.
// Drop @AggregateRoot from the root. Subtypes were unannotated and
// stay unannotated.

@EventSourcedEntity
public abstract class Card { /* ... */ }

public class GiftCard extends Card { /* ... */ }

public class OpenLoopGiftCard extends GiftCard { /* ... */ }
public class RechargeableGiftCard extends GiftCard { /* ... */ }

// Configuration:

import org.axonframework.configuration.ParameterResolverFactory;
import org.axonframework.eventsourcing.configuration.EventSourcingConfigurer;
import org.axonframework.eventsourcing.configuration.EventSourcedEntityModule;
import org.axonframework.eventstreaming.EventConverter;
import org.axonframework.messaging.MessageConverter;
import org.axonframework.messaging.MessageTypeResolver;
import org.axonframework.modelling.entity.annotation.AnnotatedEntityMetamodel;
import org.axonframework.modelling.entity.PolymorphicEntityMetamodel;

public class AxonConfig {
    public void configure(EventSourcingConfigurer configurer) {
        configurer.modelling().registerEventSourcedEntity(
            EventSourcedEntityModule.declarative(String.class, GiftCard.class)
                .messagingModel((configuration, builder) ->
                    PolymorphicEntityMetamodel.forSuperType(GiftCard.class)
                        .addConcreteType(AnnotatedEntityMetamodel.forConcreteType(
                                OpenLoopGiftCard.class,
                                configuration.getComponent(ParameterResolverFactory.class),
                                configuration.getComponent(MessageTypeResolver.class),
                                configuration.getComponent(MessageConverter.class),
                                configuration.getComponent(EventConverter.class)
                        ))
                        .addConcreteType(AnnotatedEntityMetamodel.forConcreteType(
                                RechargeableGiftCard.class,
                                configuration.getComponent(ParameterResolverFactory.class),
                                configuration.getComponent(MessageTypeResolver.class),
                                configuration.getComponent(MessageConverter.class),
                                configuration.getComponent(EventConverter.class)
                        ))
                        .build())
        );
    }
}
```

## Notes

- The Spring Boot variant of polymorphism uses
  `@EventSourced(concreteTypes = { OpenLoopGiftCard.class,
  RechargeableGiftCard.class })` on the root, plus
  `EventSourcedEntityModule.autodetected(String.class, GiftCard.class)`
  for any explicit registration that remains. Drop per-subtype
  `@Aggregate` annotations in that case.
- The four `configuration.getComponent(...)` calls are required by
  `AnnotatedEntityMetamodel.forConcreteType(...)`; copy them verbatim
  from the migration-path doc rather than improvising the signatures.
- `AggregateConfigurer.defaultConfiguration(GiftCard.class).withSubtypes(...)`
  must be removed; if you leave both registrations in place, AF5 will
  complain about duplicate entity registrations.
