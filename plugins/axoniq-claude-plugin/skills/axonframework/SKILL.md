---
name: axonframework
description: Building applications with Axon Framework 5 (AF5) and AxonIQ Framework. Covers all aspects of AF5 application development: writing command handlers (stateless and DCB/stateful), event handling and projections, query handling and subscription queries, event store primitives (EventStoreTransaction, SourcingCondition, AppendCondition, ConsistencyMarker, EventCriteria, Tag, @EventTag), application configuration (plain Java and Spring Boot), message interceptors and cross-cutting concerns, testing with AxonTestFixture, dead letter queues, distributed messaging, and multi-source event streaming. Use when implementing or debugging any part of an AF5 or AxonIQ Framework application.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Edit, Write
---

# Axon Framework 5 — Application Developer Guide

This skill covers everything needed to build an application with Axon Framework 5 (AF5) and its optional commercial extension, AxonIQ Framework. When working on a specific topic, use the Read tool to load the relevant guide file from the subdirectories listed in the routing table below.

---

## Framework choices

**Axon Framework 5** (`org.axonframework`, Apache 2.0) is fully open source and provides the complete core feature set: command handling, DCB decision models, event sourcing, event handling, query handling, interceptors, dead letter queue (in-memory, JDBC, JPA), Spring Boot integration, and testing utilities. It is the default choice.

**AxonIQ Framework** (`io.axoniq.framework`, commercial license) is an optional extension layer that adds production infrastructure features on top of AF5:
- **PostgreSQL event store** — a production-grade `EventStorageEngine` backed by PostgreSQL with optimised DCB tag indexing
- **Distributed messaging** — `DistributedCommandBus` and `DistributedQueryBus` for spreading load across multiple application instances
- **Multi-source event streaming** — `MultiStreamableEventSource` for consuming events from multiple independent event stores simultaneously

AxonIQ Framework is free for non-production use; production deployments require a paid subscription. Users who prefer to stay on open-source only can cover all core use cases with AF5 alone — AxonIQ Framework features should only be suggested when the user asks for them or their use case clearly requires them.

## Detecting which frameworks the user has

Before suggesting AxonIQ Framework features, check the project's build file (`pom.xml`, `build.gradle`, or `build.gradle.kts`) for the groupId prefixes:

| GroupId prefix | Framework | Notes |
|---|---|---|
| `org.axonframework` | Axon Framework 5 (open source) | Always present in AF5 projects |
| `io.axoniq.framework` | AxonIQ Framework (commercial) | Only present if user explicitly added it |
| `io.axoniq` (other) | Other AxonIQ commercial products | e.g. Axon Server connector, Inspector |

**If the build file contains only `org.axonframework` dependencies**: the user is on Axon Framework only. Give AF5-only advice. Do not suggest `io.axoniq.framework` modules unless the user asks.

**If the build file contains `io.axoniq.framework` dependencies**: AxonIQ Framework is available. It is safe to reference its APIs (`PostgresqlEventStorageEngine`, `DistributedCommandBus`, `MultiStreamableEventSource`, etc.).

When no build file is visible and the question is ambiguous, default to AF5 open-source advice and note that AxonIQ Framework provides commercial alternatives where relevant.

---

## DCB Philosophy — the primary stateful pattern

The primary model for stateful command handling in AF5 is **DCB (Decision Consistent Boundary)**, not aggregates. Aggregates are a specialization of DCB, not the default.

**Core idea**: for each command, identify the minimum state needed to make the decision, source only the events relevant to that decision using tag-based criteria, then append the resulting events with a condition that detects concurrent conflicts on that same boundary.

**Why DCB over aggregates**: an aggregate loads everything ever recorded for an identity. A DCB decision model loads only the events that are relevant to the specific decision being made — nothing more. This is more precise, more performant, and avoids the overhead of identity-scoped loading when only a subset of that history is needed.

**The workflow**:
1. Tag events with `@EventTag` so they can be found later by meaningful keys (e.g., `"course"`, `"student"`)
2. Define a minimal decision state record that holds only what the command needs to decide
3. In the command handler, open an `EventStoreTransaction`, source the relevant events using `SourcingCondition` + `EventCriteria`, fold them into the decision state, apply business rules, then append the result
4. The transaction automatically enforces that no conflicting event was written concurrently — if one was, `AppendEventsTransactionRejectedException` is thrown and the command should be retried

**Key AF5 primitives**: `EventStore`/`EventStoreTransaction`, `SourcingCondition`, `AppendCondition`, `ConsistencyMarker`, `EventCriteria`/`Tag`/`@EventTag`, `AppendEventsTransactionRejectedException`

---

## Routing table

When working on a topic, read the corresponding guide file. The guides contain full API reference, code examples, and patterns.

| Topic | Guide file | Framework |
|---|---|---|
| Stateless command handling | `command-handling/guide.md` | AF5 (open source) |
| Stateful command handling (DCB) | `command-decision-models/guide.md` | AF5 (open source) |
| Event store API reference | `event-store-primitives/guide.md` | AF5 (open source) |
| Event handling and projections | `event-handling/guide.md` | AF5 (open source) |
| Query handling | `query-handling/guide.md` | AF5 (open source) |
| Application configuration | `configuration/guide.md` | AF5 + AxonIQ Framework options |
| Interceptors | `interceptors/guide.md` | AF5 (open source) |
| Testing | `testing/guide.md` | AF5 (open source) |
| Distributed messaging | `distributed-messaging/guide.md` | AxonIQ Framework (commercial) |
| Multi-source event streaming | `event-streaming/guide.md` | AxonIQ Framework (commercial) |

**To load a guide**: use the Read tool with the path relative to this file, e.g.:

```
Read: skills/axonframework/command-decision-models/guide.md
```

---

## Quick orientation

- Start with **`command-handling/guide.md`** for any command handler that does not need to read past state.
- Start with **`command-decision-models/guide.md`** for any command handler that must validate against prior events. This is the more common case.
- Use **`event-store-primitives/guide.md`** alongside the DCB guide when you need exact API details for sourcing or append conditions.
- Use **`event-handling/guide.md`** when building projections, reactions, or configuring event processors.
- Use **`query-handling/guide.md`** when serving read requests or pushing live updates via subscription queries.
- Use **`configuration/guide.md`** when wiring up a new application or adding components to an existing one. Includes event store options (in-memory, PostgreSQL) and dead letter queue configuration.
- Use **`interceptors/guide.md`** when adding cross-cutting behaviour (validation, logging, retry, correlation propagation).
- Use **`testing/guide.md`** when writing or debugging tests for any of the above.
- Use **`distributed-messaging/guide.md`** when distributing command or query load across multiple application nodes (requires AxonIQ Framework).
- Use **`event-streaming/guide.md`** when consuming events from multiple independent event stores simultaneously (requires AxonIQ Framework).
