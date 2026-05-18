---
id: query-handler
title: Query Handler
description: Migrates a single class declaring @QueryHandler methods to Axon Framework 5.
order: 5
argument-hint: $SOURCE
---

# Source

Java class with one or more `@QueryHandler`-annotated methods. May also carry `@EventHandler` methods (projection/view pattern), `QueryUpdateEmitter` injection, `@ProcessingGroup`, or `@MetaDataValue` parameters.

AF4 import: `org.axonframework.queryhandling.QueryHandler`
AF5 import: `org.axonframework.messaging.queryhandling.annotation.QueryHandler`

# Scope

`$SOURCE` class only + any new query payload records introduced for `queryName` removal + `$SOURCE` test file if colocated.

# Blocker

**B1** — `$SOURCE` implements `MessageHandlerInterceptor<QueryMessage<?,?>>`. No AF5 drop-in; requires architectural redesign.
Options: (a) skip — add `// TODO: migrate manually`, (b) revert, (c) escalate to user.

# Out of Scope

- Classes dispatching queries — query-gateway recipe
- `@CommandHandler`, `@SagaEventHandler` — other recipes
- `UnitOfWork` parameter injection — separate concern; skip and note
- Proactively migrating `@EventHandler` imports on methods NOT touched for QUE injection — event-processor recipe owns those

# Applicable

Top-down; first match wins:

1. `$SOURCE` has `@SagaEventHandler` or `@Saga` annotation → **Rejected** (predicate: is-saga)
2. `$SOURCE` has `@QueryHandler` (any import) → **continue**
3. `$SOURCE` imports `org.axonframework.queryhandling.QueryHandler` (no annotation found yet) → **continue** (partial migration)
4. None of above → **Rejected** (predicate: no-query-handler — if class dispatches queries, consider query-gateway recipe)

Tolerance: partial migration OK — apply delta only.

# Success Criteria

Aggregation: all (AND).

1. `org.axonframework.queryhandling.QueryHandler` import absent
2. `org.axonframework.messaging.queryhandling.annotation.QueryHandler` import present
3. No `@QueryHandler(queryName = …)` attributes remaining
4. If `@ProcessingGroup` was present → `@Namespace` from `org.axonframework.messaging.core.annotation.Namespace` present; `@ProcessingGroup` absent
5. If `@MetaDataValue` was present → `@MetadataValue` from `org.axonframework.messaging.core.annotation.MetadataValue` present; `@MetaDataValue` absent
6. If `QueryUpdateEmitter` was constructor-injected → field removed; injected as method param in each `@EventHandler` method that uses it
7. If `updateEmitter.emit(predicate, update)` 2-arg form present → replaced by `updateEmitter.emit(QueryClass.class, predicate, update)` 3-arg form

# References

- `references/docs/paths/messages.adoc` — package mapping for all messaging types
- `references/recipes/query-gateway/RECIPE.md` — companion recipe for query dispatch side

### Atoms (code-change recipes — single-responsibility API transformations)

Load each atom whose apply-condition matches current scope. Atoms are the **canonical** source for exact
imports, before/after patterns, and gotchas for each API change; they replace inline repetition in the Toolbox.

| Atom file | Apply-condition |
|-----------|-----------------|
| [../../atoms/query-handler-annotation.md](../../atoms/query-handler-annotation.md) | always |
| [../../atoms/query-payload-record.md](../../atoms/query-payload-record.md) | any `@QueryHandler(queryName = "…")` present |
| [../../atoms/query-update-emitter.md](../../atoms/query-update-emitter.md) | `QueryUpdateEmitter` is constructor-injected |
| [../../atoms/processing-group-annotation.md](../../atoms/processing-group-annotation.md) | `@ProcessingGroup` present |
| [../../atoms/metadata-value.md](../../atoms/metadata-value.md) | `@MetaDataValue` on any method parameter |
| [../../atoms/event-handler.md](../../atoms/event-handler.md) | `@EventHandler` imports touched by Step 3 (QUE migration) |

# Toolbox

> **Atom-based execution.** Atoms for this recipe are pre-loaded during Research (FLOW.md S3) per the
> `### Atoms` table above. Consult the loaded atom file for complete before/after, exact imports, and gotchas.
> The steps below provide ordering and apply-conditions; the atoms provide the HOW.

### Step 1 — @QueryHandler import swap
*Apply-condition:* always.

Apply **[[query-handler-annotation]] atom** — `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.

### Step 2 — queryName removal + query payload record introduction
*Apply-condition:* any `@QueryHandler(queryName = "…")` present.

Apply **[[query-payload-record]] atom** — covers recording the `queryName` value, introducing a top-level
`@Query`-annotated payload record (never nested), updating the handler parameter + body references, and
removing the `queryName` attribute. Key rule: `@Query` name must match the AF4 string exactly.

### Step 3 — QueryUpdateEmitter: constructor → method parameter
*Apply-condition:* `QueryUpdateEmitter` is a constructor dependency.

Apply **[[query-update-emitter]] atom** — covers removing the field + constructor param, adding
`QueryUpdateEmitter updateEmitter` to each `@EventHandler` method that uses it, rewriting `emit(predicate, update)`
to `emit(QueryClass.class, predicate, update)`, swapping the import, and fixing `@EventHandler` imports on
**touched methods only**.

### Step 4 — @ProcessingGroup → @Namespace
*Apply-condition:* `@ProcessingGroup` present.

Apply **[[processing-group-annotation]] atom** — same string value, import swap only.

### Step 5 — @MetaDataValue → @MetadataValue
*Apply-condition:* `@MetaDataValue` on method parameters.

Apply **[[metadata-value]] atom** — annotation casing + import package change. Both must change together.

# Use cases

- [01-simple-import-swap.md](use-cases/01-simple-import-swap.md) — @QueryHandler with proper payload classes, no queryName, no QUE; import-only change.
- [02-named-query-removal.md](use-cases/02-named-query-removal.md) — `@QueryHandler(queryName = "…")` present; introduce payload records, remove queryName.
- [03-query-update-emitter-migration.md](use-cases/03-query-update-emitter-migration.md) — QueryUpdateEmitter constructor-injected; migrate to method param + update emit() signature.
- [04-processing-group-metadata.md](use-cases/04-processing-group-metadata.md) — @ProcessingGroup and/or @MetaDataValue migration; heroes-derived example.
- [05-rejected-no-query-handler.md](use-cases/05-rejected-no-query-handler.md) — class with no @QueryHandler; rejected, suggest query-gateway.

# Gotchas

- **queryName gone**: AF5 routes entirely by first method parameter type. Handler with no param must receive a marker record (`QueryClass ignored`).
- **emit() 2-arg vs 3-arg**: AF5 `QueryUpdateEmitter.emit()` requires `(Class<Q> queryClass, Predicate<Q>, update)`. AF4 2-arg `(Predicate<QueryMessage<Q,?>>, update)` does NOT compile in AF5. Do not confuse the two.
- **Predicate parameter change**: AF4 predicate receives `QueryMessage<Q, ?>` (the envelope); AF5 predicate receives `Q` (the payload directly). `q.getQueryName()` no longer exists on the predicate arg.
- **@Query name case-sensitivity**: `FindAllQuery` simple name "FindAllQuery" ≠ "findAll". Add `@Query(name="findAll")` when AF4 queryName string and the new record simple name differ.
- **EventHandler imports**: Fix `@EventHandler` import ONLY on methods physically modified for QUE injection. Do not touch untouched @EventHandler methods — event-processor recipe owns those.
- **Query records must be top-level classes**: Never nest them as inner classes of the handler. They are part of the shared API used by both dispatch and handler sides.
- **queryName + dispatch side coupling**: Step 2 changes the handler side. The dispatch side (`queryGateway.query("name", ...)`) must also change — that belongs to the query-gateway recipe (use-case 04). Coordinate both recipes when source is a projection + dispatcher.
- **`QueryUpdateEmitter.emit(String.class, predicate, update)` — `String.class` was an AF4 named-query workaround.** AF4 code that called `updateEmitter.emit(String.class, id::equals, update)` used `String.class` as a type marker for string-keyed named queries. This does NOT work in AF5. Replace `String.class` with the `@Query`-annotated payload record class introduced by the query-gateway recipe (e.g., `emit(FindBikeByIdQuery.class, q -> q.getBikeId().equals(id), update)`). The query-gateway recipe (Step 2) must run before this recipe so the payload record class exists.

# Result

## Success

```
**Result:** ✅ Success
**Recipe:** axon4to5-query-handler
**Notes:** <summary of changes applied>
```

## Blocker

```
**Result:** 🚧 Blocker
**Recipe:** axon4to5-query-handler
**Blocker:** <B-code> — <description>
**Options:**
  a. Skip — leave file untouched, add TODO comment
  b. Revert — undo any partial changes
  c. Solve manually — <specific guidance>
```

## Rejected

```
**Result:** ⏭️ Rejected
**Recipe:** axon4to5-query-handler
**Reason:** <failed predicate> — <routing suggestion>
```

## Failure

```
**Result:** ❌ Failure
**Recipe:** axon4to5-query-handler
**Failed criteria:** <list>
**Error:** <verbatim>
```
