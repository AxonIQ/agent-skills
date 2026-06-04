---
id: serializer
title: Serializer
description: Migrates AF4 Serializer wiring (JacksonSerializer beans, configureSerializer, axon.serializer.* YAML) to the AF5 Converter API (General/Message/Event converters).
order: 9
argument-hint: $SOURCE
---

# Serializer

> AF4's `org.axonframework.serialization.Serializer` SPI is **entirely removed** in AF5 — not renamed. `JacksonSerializer` / `XStreamSerializer` and the whole `RevisionResolver` family (`FixedValueRevisionResolver`, `MavenArtifactRevisionResolver`) no longer exist. AF5 replaces them with the `Converter` API: a general `Converter` plus dedicated `MessageConverter` and `EventConverter`. This recipe swaps the serialization wiring (Spring `@Bean`s or native `configureSerializer`) and renames `axon.serializer.*` → `axon.converter.*`.
>
> 🚨 **Event-store data / SQL / schema migration is OUT OF SCOPE.** This recipe rewrites Java + YAML config only. Changing the on-disk event format (esp. XStream → Jackson) is the caller's out-of-band concern.

## Source

- `$SOURCE` (required) — FQN, file path, or simple class name of the `@Configuration` class (Spring) or Configurer setup class (native) that declares the AF4 `Serializer` bean(s) / calls `configureSerializer`. Pass the main application class if no dedicated config class exists and only `axon.serializer.*` YAML is present.

## Scope

- `$SOURCE` configuration class — the `Serializer` bean methods / `configureSerializer*` calls only.
- `application.yaml` / `application.properties` keys under `axon.serializer.*` (renamed to `axon.converter.*`).

Scope grows during Research; never shrinks. Sibling aggregates, projectors, sagas, the `EventStorageEngine` bean (that is the event-store recipe's) are NOT in scope.

## Blocker

All detected during Research before any edit. If any fire → emit Blocker and stop (partial YAML/bean rewrite of the non-blocked parts is allowed first, as noted).

### B1 — `XStreamSerializer` used for event serialization

`XStreamSerializer` is removed and has **no format-compatible** successor. Code can move to `JacksonConverter` with an `XmlMapper`, but data written by XStream will not deserialize with Jackson — the event store must be reprocessed. The recipe cannot make that data decision. Detect: `grep -RnE 'XStreamSerializer|com\.thoughtworks\.xstream' --include='*.java' --include='*.kt' src`.

Options (in addition to the three defaults):
- `move-to-jackson-xml` — rewrite to `new JacksonConverter(new XmlMapper())`; caller reprocesses/migrates the event store out-of-band (format differs).
- `move-to-jackson-json` — rewrite to JSON `JacksonConverter`; caller owns the data reprocessing.

### B2 — Custom `Serializer` implementation or custom `ContentTypeConverter`

A class implementing `org.axonframework.serialization.Serializer` directly, or a custom `ContentTypeConverter`. The AF5 `Converter` SPI has a different shape; the port is not mechanical. Detect: `grep -RnE '(implements|:).*\bSerializer\b|implements\s+ContentTypeConverter|:\s*ContentTypeConverter' --include='*.java' --include='*.kt' src` (Java `implements`, Kotlin `:`).

### Unmet project prerequisites

- Project does not compile pre-recipe → Blocker `prerequisite-not-compiling`.

## Out of Scope

- The `EventStorageEngine` / event-store bean swap — that is the **event-store** recipe. This recipe only provides the `EventConverter` the engine consumes.
- SQL / DDL / event-store data migration / format reprocessing — caller owns out-of-band.
- `@Revision` annotations on payload classes / event upcasters / versioning logic.
- Logging, formatting, package renames.

## Applicable

Surface check on `$SOURCE` + project resources. Cheap reads only.

Decision rule (top-down; first match wins):

1. **AF4 serializer wiring detected** — any of: a `@Bean`-returning `org.axonframework.serialization.Serializer`; a `JacksonSerializer` / `XStreamSerializer` reference; a `configureSerializer` / `configureMessageSerializer` / `configureEventSerializer` call; or an `axon.serializer.*` key in YAML/properties. → **continue**.
2. **Already migrated** — `$SOURCE` already declares `GeneralConverter` / `MessageConverter` / `EventConverter` beans (or `registerComponent(...Converter.class, ...)`) and YAML uses `axon.converter.*`, with no AF4 `Serializer` remnants. → **continue** (idempotent Success-Criteria check decides).
3. **No serializer wiring found** — none of the above. → **Rejected** with NOTES naming the failed predicate.

## Success Criteria

Extends DEFAULT.md baseline. Split by `configuration` input.

### Common — both configurations

1. **No AF4 serializer references** as live (uncommented) code: none of `org.axonframework.serialization.Serializer`, `JacksonSerializer`, `XStreamSerializer`, `RevisionResolver` (type names or imports).
2. **YAML/properties renamed** — no `axon.serializer.*` keys remain; equivalent `axon.converter.*` keys present when serializer keys existed.

### configuration=spring (Path A)

3. A `@Bean @Primary GeneralConverter` is present (typically `new DelegatingGeneralConverter(new JacksonConverter(objectMapper))`), plus `MessageConverter` and `EventConverter` beans when the AF4 config wired message/event serializers explicitly.

### configuration=native (Path B)

3. `registry.registerComponent(GeneralConverter.class, ...)` present on the `MessagingConfigurer` componentRegistry, plus `MessageConverter` / `EventConverter` registrations matching what AF4 wired.

Aggregation rule: **all match (AND)** — DEFAULT.md baseline AND all applicable items above.

### Verification

`axon4to5-isolatedtest` with `test-sources: []` (compile-only) — config classes have no isolated test; "no test coverage" → Learning. `extra-deps`: `org.axonframework:axon-conversion`, `org.axonframework:axon-messaging`; add `org.axonframework.extensions.spring:axon-spring-boot-starter` (or the `io.axoniq.framework:…` coordinate when `framework=axoniq`) for `configuration=spring`.

## References

- [serializers.adoc](../../docs/paths/serializers.adoc) — *apply-condition:* always. Converter levels (General/Message/Event), declarative + Spring + properties config, XStream removal, `axon.serializer.*` → `axon.converter.*` property type table (`jackson` / `jackson2` / `avro` / `cbor`).
- [event-store.adoc](../../docs/paths/event-store.adoc) — *apply-condition:* the `EventStorageEngine` bean is co-located in `$SOURCE` and needs the `EventConverter`. Read-only context; the engine swap stays with the event-store recipe.

## Toolbox

### FQNs — where the converter types live (verified against AF5 jars)

*Apply-condition:* always — consult before writing any import.

The `serializers.adoc` examples use simple class names, but the concrete types are split across **two artifacts**. Importing them all from `org.axonframework.conversion.*` will NOT compile — `MessageConverter` / `EventConverter` are under `messaging`. Verified locations:

| Type(s) | Fully-qualified name | Artifact |
|---|---|---|
| `Converter`, `GeneralConverter`, `DelegatingGeneralConverter` | `org.axonframework.conversion.{Converter, GeneralConverter, DelegatingGeneralConverter}` | `axon-conversion` |
| `JacksonConverter` | `org.axonframework.conversion.jackson.JacksonConverter` | `axon-conversion` |
| `MessageConverter`, `DelegatingMessageConverter` | `org.axonframework.messaging.core.conversion.{MessageConverter, DelegatingMessageConverter}` | `axon-messaging` |
| `EventConverter`, `DelegatingEventConverter` | `org.axonframework.messaging.eventhandling.conversion.{EventConverter, DelegatingEventConverter}` | `axon-messaging` |

Constructors (verified): `JacksonConverter()` / `JacksonConverter(ObjectMapper)`; `DelegatingGeneralConverter(Converter)`; `DelegatingMessageConverter(Converter)`; `DelegatingEventConverter(Converter)` or `DelegatingEventConverter(MessageConverter)`.

### Step 1 — Path A: Spring `@Bean` swap (configuration=spring)

*Apply-condition:* `configuration=spring`.

**Delete** the AF4 `@Bean Serializer` method(s) (`serializer` / `messageSerializer` / `eventSerializer`) and any `RevisionResolver` wiring. **Add** converter beans — auto-config picks them up:

```java
@Configuration
public class ConversionConfig {
    @Bean
    @Primary
    public GeneralConverter converter(ObjectMapper objectMapper) {
        return new DelegatingGeneralConverter(new JacksonConverter(objectMapper));
    }

    @Bean
    public MessageConverter messageConverter(GeneralConverter generalConverter) {
        return new DelegatingMessageConverter(generalConverter);
    }

    @Bean
    public EventConverter eventConverter(MessageConverter messageConverter) {
        return new DelegatingEventConverter(messageConverter);
    }
}
```

Imports (note the two artifacts):
```java
import org.axonframework.conversion.GeneralConverter;
import org.axonframework.conversion.DelegatingGeneralConverter;
import org.axonframework.conversion.jackson.JacksonConverter;
import org.axonframework.messaging.core.conversion.MessageConverter;
import org.axonframework.messaging.core.conversion.DelegatingMessageConverter;
import org.axonframework.messaging.eventhandling.conversion.EventConverter;
import org.axonframework.messaging.eventhandling.conversion.DelegatingEventConverter;
```

If AF4 only declared a single general `@Bean Serializer` (no message/event specialisation), the `GeneralConverter` bean alone is enough — auto-config derives the message/event converters. Keep all three only when AF4 wired them separately.

### Step 2 — Path B: native `MessagingConfigurer` (configuration=native)

*Apply-condition:* `configuration=native`.

Replace `configurer.configureSerializer(...)` / `configureMessageSerializer(...)` / `configureEventSerializer(...)` with componentRegistry registration:

```java
public void configure(MessagingConfigurer configurer, ObjectMapper objectMapper) {
    configurer.componentRegistry(registry -> {
        Converter generalConverter = new JacksonConverter(objectMapper);
        registry.registerComponent(GeneralConverter.class, c -> new DelegatingGeneralConverter(generalConverter));
        registry.registerComponent(MessageConverter.class, c -> new DelegatingMessageConverter(generalConverter));
        registry.registerComponent(EventConverter.class, c -> new DelegatingEventConverter(generalConverter));
    });
}
```

Imports: the `conversion.*` + `messaging.*.conversion.*` FQNs above, plus `org.axonframework.conversion.Converter`.

### Step 3 — YAML/properties rename

*Apply-condition:* `axon.serializer.*` key present in `application.yaml` / `application.properties`.

Rename the `axon.serializer` block to `axon.converter`, preserving the `general` / `messages` / `events` sub-keys verbatim. Valid type values per `serializers.adoc`: `jackson` (Jackson 3), `jackson2` (legacy Jackson 2), `avro` (`messages`/`events` only), `cbor`.

```yaml
# before
axon:
  serializer:
    general: jackson
    events: jackson
# after
axon:
  converter:
    general: jackson
    events: jackson
```

### Step 4 — RevisionResolver removal

*Apply-condition:* AF4 config wired a `RevisionResolver` (`FixedValueRevisionResolver`, `MavenArtifactRevisionResolver`, or `.revisionResolver(...)` on a builder).

The `RevisionResolver` SPI is gone with no successor. Drop the wiring entirely — there is no `revisionResolver(...)` on the converter side. If event versioning genuinely depended on revisions (upcasting keyed on `@Revision`), surface that as a Learning for follow-up; do NOT invent a replacement.

## Use cases

- [01-spring-boot-jackson-bean.md](use-cases/01-spring-boot-jackson-bean.md) — *apply-condition:* `configuration=spring` AND a `@Bean Serializer` using `JacksonSerializer`. Full before/after of the bean swap + imports.
- [02-native-configurer.md](use-cases/02-native-configurer.md) — *apply-condition:* `configuration=native` AND `configureSerializer` calls. Shows the `componentRegistry` registration.
- [03-xstream-blocker.md](use-cases/03-xstream-blocker.md) — *apply-condition:* `XStreamSerializer` detected. Shows the B1 Blocker result + Options.

## Gotchas

- **The converter types are NOT all in `org.axonframework.conversion.*`.** This is the most common silent failure. `MessageConverter` / `DelegatingMessageConverter` live in `org.axonframework.messaging.core.conversion`, and `EventConverter` / `DelegatingEventConverter` in `org.axonframework.messaging.eventhandling.conversion` (both in `axon-messaging`). Only the general `Converter` family + `JacksonConverter` are in `axon-conversion`. The `serializers.adoc` examples use unqualified names and imply a single package — they don't compile as written. Always use the FQN table above.
- **`Serializer` is removed, not renamed.** OpenRewrite moves the import prefix `org.axonframework.serialization.*` → `org.axonframework.conversion.*`, but the class names (`JacksonSerializer`, `XStreamSerializer`) no longer exist — the rewritten import points at a non-existent type. The recipe must replace the type, not trust the moved import.
- **`RevisionResolver` family is gone** — `RevisionResolver`, `FixedValueRevisionResolver`, `MavenArtifactRevisionResolver` have no AF5 successor. A `JacksonSerializer.builder().revisionResolver(...).build()` becomes plain converter beans with the resolver dropped.
- **XStream is a data problem, not just a code problem.** `JacksonConverter(new XmlMapper())` compiles, but XStream-written events won't deserialize with Jackson XML. Always B1 + flag event-store reprocessing in Notes; never silently swap.
- **Single vs three beans.** If AF4 had only one `@Bean Serializer`, a single `@Bean @Primary GeneralConverter` suffices — auto-config derives the rest. Add `MessageConverter`/`EventConverter` beans only when AF4 specialised them (`configureMessageSerializer` / `configureEventSerializer` / separate `axon.serializer.messages|events`).
- **Don't migrate the `EventStorageEngine` here.** If the same `@Configuration` also declares the event-store bean, leave it for the event-store recipe — this recipe only supplies the `EventConverter` it depends on.

## Result

Inherits DEFAULT.md baseline.

### Success

Say **"return SUCCESS"**, then **MUST emit** the result block (schema: FLOW.md § Result). `Recipe:` field is `axon4to5-serializer`. NOTES must include: (a) which path (A.spring / B.native) and whether one or three converter beans were emitted; (b) whether YAML keys were renamed; (c) if a `RevisionResolver` was dropped, say so; (d) no test coverage (Learning).

### Blocker

Say **"return BLOCKER"**, then **MUST emit** the result block. `Recipe:` field is `axon4to5-serializer`. NOTES name each detected blocker + location. Options: three DEFAULT.md baselines + any recipe-specific options (B1's `move-to-jackson-xml` / `move-to-jackson-json`).

### Rejected

Say **"return REJECTED"**, then **MUST emit** the result block. NOTES name the failed `# Applicable` predicate (3 — no serializer wiring found).

### Failure

Say **"return FAILURE"**, then **MUST emit** the result block. NOTES: failing Success Criteria + last error verbatim. LEARNINGS nearly always present — a wrong converter import package (`MessageConverter` under `conversion` instead of `messaging.core.conversion`) is the likely first-attempt compile error; record it.
