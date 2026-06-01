# Use case 03 — `XStreamSerializer` (Blocker B1)

**Why interesting:** XStream is removed in AF5 with no format-compatible successor. The code *can* move to `JacksonConverter` with an `XmlMapper`, but events already written by XStream will not deserialize with Jackson — the event store must be reprocessed. That data decision is the caller's, so the recipe halts with Blocker B1 rather than silently swapping.

## Before (AF4)

```java
@Bean
@Primary
public Serializer eventSerializer() {
    return XStreamSerializer.builder()
            .xStream(new XStream())
            .build();
}
```

## Why it blocks

A mechanical rewrite to:

```java
XmlMapper xmlMapper = new XmlMapper();
Converter xmlConverter = new JacksonConverter(xmlMapper);
```

compiles, but the produced XML is **not** byte-compatible with XStream's output. Any existing event store written by `XStreamSerializer` becomes unreadable. The recipe cannot decide whether to reprocess the store, dual-read during a transition, or accept the break — so it surfaces the choice.

## Result block

```
return BLOCKER

> **Result:** 🚧 Blocker
> **Source:** `com.example.AxonSerializationConfig`
> **Recipe:** axon4to5-serializer
>
> **Notes:** 1 blocker detected. B1 (XStreamSerializer) at `AxonSerializationConfig.java:21` — `XStreamSerializer.builder()…build()`. AF5 removed XStream; `JacksonConverter(new XmlMapper())` compiles but produces a different on-disk format. Existing XStream-serialized events will not deserialize — the event store must be reprocessed out-of-band before the swap is safe. Caller must choose a data path.
>
> **Learnings:**
> ## 2026-05-28 — XStream removal is a data-migration decision, not a code swap
> **Trigger:** blocker
> **Where:** `com.example.AxonSerializationConfig:21`
> **Surprise:** The code rewrite (`JacksonConverter` + `XmlMapper`) is trivial, but the resulting XML is incompatible with XStream's format — silently swapping would corrupt reads against the legacy store.
> **Resolution:** Halted with Options; caller owns the event-store reprocessing/migration before the converter swap.
>
> **Options:**
> - [ ] **move-to-jackson-xml** — rewrite to `new JacksonConverter(new XmlMapper())`; caller reprocesses/migrates the event store out-of-band (XStream format differs).
> - [ ] **move-to-jackson-json** — rewrite to a JSON `JacksonConverter`; caller owns the data reprocessing.
> - [ ] **skip** — keep the config as-is; queue moves on (project stays on a removed type — will not compile against AF5).
> - [ ] **revert** — undo any edits; restore pre-recipe state.
> - [ ] **solve-manually** — pause; caller handles the data migration and rewrite by hand, then re-invokes.
```

## Caveats

- `JacksonConverter` lives in `org.axonframework.conversion.jackson`; `XmlMapper` comes from the `jackson-dataformat-xml` artifact (must be on the classpath).
- This blocker is about **event** serialization. If XStream was used only for a message/snapshot serializer that never touched persisted data, the format risk is lower — but the recipe still surfaces B1; the caller decides.
