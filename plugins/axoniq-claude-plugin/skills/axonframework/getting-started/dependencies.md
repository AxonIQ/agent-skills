# Maven Dependencies for Axon Framework 5

This guide covers the Maven coordinates, current versions, and purpose of every AF5 artifact. Use the BOM whenever possible — it keeps all module versions consistent.

Only Axon Framework 5.0 and later is covered here.

---

## Version overview

| Framework | GroupId | Latest stable | Notes |
|---|---|---|---|
| Axon Framework (open source) | `org.axonframework` | `5.1.1` | Apache 2.0 license |
| AxonIQ Framework (commercial) | `io.axoniq.framework` | tracks AF5 version | Free for non-production; paid subscription for production |

Both frameworks use the same version numbering line (e.g., `5.1.0`, `5.1.1`). AxonIQ Framework's BOM imports the matching AF5 BOM, so a single BOM import covers everything.

---

## Axon Framework 5 (open source)

### Using the BOM (recommended)

Import the BOM in `dependencyManagement`. This sets all `org.axonframework` module versions consistently — you omit `<version>` from each subsequent dependency.

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.axonframework</groupId>
      <artifactId>axon-framework-bom</artifactId>
      <version>5.1.1</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

### Spring Boot starter (recommended entry point)

For Spring Boot applications, pull in one starter — it transitively includes `axon-messaging`, `axon-modelling`, `axon-eventsourcing`, `axon-spring`, `axon-spring-boot-autoconfigure`, and `axon-common`.

```xml
<dependency>
  <groupId>org.axonframework.extensions.spring</groupId>
  <artifactId>axon-spring-boot-starter</artifactId>
  <!-- version managed by BOM -->
</dependency>
```

### Individual modules

Use individual modules when you are not using Spring Boot or when you need fine-grained control.

| ArtifactId | GroupId | Purpose |
|---|---|---|
| `axon-messaging` | `org.axonframework` | Core command/event/query buses, gateway, handler annotations (`@CommandHandler`, `@EventHandler`, `@QueryHandler`), `EventAppender`, `ProcessingContext`, `Metadata`, `CommandHandlingModule`, `QueryHandlingModule`, `EventProcessingConfigurer`, `MessagingConfigurer` |
| `axon-modelling` | `org.axonframework` | Entity modelling: `@InjectEntity`, `@TargetEntityId`, `ModellingConfigurer` |
| `axon-eventsourcing` | `org.axonframework` | Event store, DCB: `EventStore`, `EventSourcingConfigurer`, `@EventSourcedEntity`, `@EventSourcingHandler`, `@EntityCreator`, `@EventTag`, `EventSourcedEntityModule`, `SourcingCondition`, `AppendCondition`, `EventCriteria`, `Tag`, `AnnotationBasedTagResolver` |
| `axon-common` | `org.axonframework` | Shared utilities: `AxonConfiguration`, `ComponentRegistry`, `QualifiedName`, `MessageType`, `Metadata` |
| `axon-conversion` | `org.axonframework` | Message serialisation and conversion (Jackson by default) |
| `axon-test` | `org.axonframework` | `AxonTestFixture`, `GenericTaggedEventMessage`, test matchers. Use in `test` scope. |
| `axon-spring` | `org.axonframework.extensions.spring` | Core Spring integration (component scanning, bean wiring) |
| `axon-spring-boot-autoconfigure` | `org.axonframework.extensions.spring` | Spring Boot auto-configuration for all AF5 components |
| `axon-spring-boot-starter` | `org.axonframework.extensions.spring` | Convenience starter: includes all of the above |
| `axon-spring-boot-starter-test` | `org.axonframework.extensions.spring` | Spring Boot test support for AF5 (`@SpringBootTest` + fixture integration). Use in `test` scope. |
| `axon-tracing-opentelemetry` | `org.axonframework.extensions.tracing` | OpenTelemetry tracing integration for distributed traces across command/event/query handlers |
| `axon-metrics-micrometer` | `org.axonframework.extensions.metrics` | Micrometer metrics for message processing rates, latencies |
| `axon-metrics-dropwizard` | `org.axonframework.extensions.metrics` | Dropwizard Metrics integration (alternative to Micrometer) |
| `axon-update` | `org.axonframework` | Event upcasting utilities for schema evolution |

### Typical plain Java setup

```xml
<dependencies>
  <!-- Core framework -->
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-messaging</artifactId>
  </dependency>
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-modelling</artifactId>
  </dependency>
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-eventsourcing</artifactId>
  </dependency>

  <!-- Testing -->
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-test</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>
```

### Typical Spring Boot setup

```xml
<dependencies>
  <dependency>
    <groupId>org.axonframework.extensions.spring</groupId>
    <artifactId>axon-spring-boot-starter</artifactId>
  </dependency>

  <!-- Testing -->
  <dependency>
    <groupId>org.axonframework</groupId>
    <artifactId>axon-test</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>
```

---

## AxonIQ Framework (commercial)

AxonIQ Framework adds production infrastructure on top of AF5. Its BOM imports `axon-framework-bom`, so a single BOM covers both.

### Using the BOM

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>io.axoniq.framework</groupId>
      <artifactId>axoniq-framework-bom</artifactId>
      <version>5.1.1</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

This transitively imports `axon-framework-bom` at the matching version, so you do not need to declare both BOMs.

### Modules

| ArtifactId | GroupId | Purpose |
|---|---|---|
| `axoniq-postgresql` | `io.axoniq.framework` | Production-grade PostgreSQL event store (`PostgresqlEventStorageEngine`) with optimised DCB tag indexing. Replaces the in-memory default. |
| `axoniq-distributed-messaging` | `io.axoniq.framework` | `DistributedCommandBus` and `DistributedQueryBus` for spreading message load across multiple application instances. |
| `axoniq-event-streaming` | `io.axoniq.framework` | `MultiStreamableEventSource` — consumes events from multiple independent event stores simultaneously in a single event processor. |
| `axoniq-dead-letter` | `io.axoniq.framework` | Dead-letter queue implementations: in-memory, JDBC, JPA, and PostgreSQL backends for event processors. |
| `axon-server-connector` | `io.axoniq.framework` | Connector for Axon Server as the event store and message broker. Auto-detected on the classpath (connects to `localhost:8124` by default). Connection/disable config: see `configuration/spring-boot.md` and `configuration/plain-java.md`. |
| `axoniq-spring-boot-autoconfigure` | `io.axoniq.framework` | Spring Boot auto-configuration for all AxonIQ Framework modules. |
| `axoniq-spring-boot-starter` | `io.axoniq.framework` | Convenience starter: includes all AxonIQ Framework modules and the AF5 Spring Boot starter. |

### Typical AxonIQ Framework setup (Spring Boot)

```xml
<dependency>
  <groupId>io.axoniq.framework</groupId>
  <artifactId>axoniq-spring-boot-starter</artifactId>
</dependency>

<!-- Choose the storage backend you need: -->
<dependency>
  <groupId>io.axoniq.framework</groupId>
  <artifactId>axoniq-postgresql</artifactId>
</dependency>

<!-- Distributed messaging (if running multiple nodes): -->
<dependency>
  <groupId>io.axoniq.framework</groupId>
  <artifactId>axoniq-distributed-messaging</artifactId>
</dependency>
```

---

## Dependency relationships

```
axon-spring-boot-starter
  └── axon-spring-boot-autoconfigure
      └── axon-spring
          └── axon-eventsourcing
              └── axon-modelling
                  └── axon-messaging
                      └── axon-common

axoniq-spring-boot-starter
  └── axoniq-spring-boot-autoconfigure
      ├── axon-spring-boot-starter  (all of above)
      ├── axoniq-postgresql
      ├── axoniq-distributed-messaging
      └── axoniq-event-streaming
```

`axon-test` and `axoniq-dead-letter` are separate opt-in dependencies not included in any starter.

---

## Gradle

```kotlin
// BOM (Axon Framework only):
implementation(platform("org.axonframework:axon-framework-bom:5.1.1"))

// BOM (AxonIQ Framework, includes AF5 BOM):
implementation(platform("io.axoniq.framework:axoniq-framework-bom:5.1.1"))

// Spring Boot:
implementation("org.axonframework.extensions.spring:axon-spring-boot-starter")
testImplementation("org.axonframework:axon-test")

// Plain Java:
implementation("org.axonframework:axon-messaging")
implementation("org.axonframework:axon-modelling")
implementation("org.axonframework:axon-eventsourcing")
testImplementation("org.axonframework:axon-test")
```
