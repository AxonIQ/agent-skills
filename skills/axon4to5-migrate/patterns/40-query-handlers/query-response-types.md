# QueryGateway — Drop ResponseTypes Wrappers

AF4 typed the expected response of `queryGateway.query(...)` through the `ResponseTypes` SPI
(`ResponseTypes.instanceOf(Foo.class)`, `ResponseTypes.multipleInstancesOf(Foo.class)`,
`ResponseTypes.optionalInstanceOf(Foo.class)`). AF5 drops the `org.axonframework.messaging.responsetypes`
package entirely. The gateway accepts `Class<R>` directly for single-instance responses, and exposes
`queryMany(...)` for multi-instance responses.

## Import Mappings

| AF4 | AF5 |
|-----|-----|
| `org.axonframework.messaging.responsetypes.ResponseTypes` | *(remove import — package is gone)* |
| `org.axonframework.messaging.responsetypes.ResponseType` | *(remove)* |
| `ResponseTypes.instanceOf(Foo.class)` | `Foo.class` |
| `ResponseTypes.optionalInstanceOf(Foo.class)` | `Foo.class` (gateway still returns a `CompletableFuture`) |
| `ResponseTypes.multipleInstancesOf(Foo.class)` | use `queryGateway.queryMany(query, Foo.class)` |

## Detection

**Pre-migration (AF4 original):**

```bash
grep -rn 'ResponseTypes\.\|responsetypes\|multipleInstancesOf\|instanceOf' \
  --include='*.java' --include='*.kt' --include='*.scala' .
```

**Post-OpenRewrite (partial AF5 shape):**

```bash
# Sites the recipe could not finish — 3-argument named queries
grep -rn 'queryGateway\.query("' --include='*.java' --include='*.kt' --include='*.scala' .
# multipleInstancesOf sites — convert to queryMany
grep -rn 'multipleInstancesOf' --include='*.java' --include='*.kt' --include='*.scala' .
```

Use the AF4 grep during Step 2 Assessment to scope the work. Use the post-OR grep during Step 4 Validate when the compile loop points at this pattern.

## Axon Framework 4 Code

```java
// Single-instance, named query, 3-argument form
Future<Dwelling> result = queryGateway.query(
        "findDwellingById",
        new FindDwellingByIdQuery(id),
        ResponseTypes.instanceOf(Dwelling.class));

// Multi-instance — list of results
Future<List<Dwelling>> all = queryGateway.query(
        new FindAvailableDwellingsQuery(),
        ResponseTypes.multipleInstancesOf(Dwelling.class));
```

## Axon Framework 5 Code

```java
// Single-instance — 2-argument form, no name string
CompletableFuture<Dwelling> result = queryGateway.query(
        new FindDwellingByIdQuery(id),
        Dwelling.class);

// Multi-instance — explicit queryMany method
CompletableFuture<List<Dwelling>> all = queryGateway.queryMany(
        new FindAvailableDwellingsQuery(),
        Dwelling.class);
```

## Notes

- **The query-name string is gone.** AF5 routes purely by the payload type. If the AF4 site passed a name that
  differs from the payload's simple class name, annotate the payload record with `@Query(name = "…")` (see
  `query-named.md`).
- **`queryMany` is the only way to get a collection.** Calling `query(..., Class<R>)` with a list-shaped query
  binds to a single-instance handler at runtime and fails.
- **`CompletableFuture`, not `Future`.** AF4's return type widens to `CompletableFuture` so `.join()` /
  `.thenApply(...)` chains work without casting.
- **`ResponseType` field declarations** (e.g. cached `ResponseType<List<X>>` constants used across multiple
  query sites) become `Class<X>` references — drop the wrapper entirely.

## Partial migration state (post-OpenRewrite)

`Axon4ToAxon5QueryResponseTypes` in `axon4-to-axon5-messaging.yml` rewrites the **2-argument** typed-payload
form `query(payload, ResponseTypes.instanceOf(Foo.class))` → `query(payload, Foo.class)` and prunes the
`responsetypes` import when no references remain. The recipe deliberately leaves the **3-argument**
`query(name, payload, ResponseTypes…)` shape alone — that case needs the payload to gain `@Query(name = "…")`
(or to be renamed) before the wrapper can be removed safely. `RemoveUnusedImports` (composed in the same
recipe) cleans up any orphaned `responsetypes.*` imports after manual rewrites.

```bash
# Sites the recipe could not finish — 3-argument named queries
grep -rn 'queryGateway\.query("' --include='*.java' --include='*.kt' --include='*.scala' .
# multipleInstancesOf sites — convert to queryMany
grep -rn 'multipleInstancesOf' --include='*.java' --include='*.kt' --include='*.scala' .
```

## Notes (continued)

- **OpenRewrite status:** Partial — `Axon4ToAxon5QueryResponseTypes` (in `axon4-to-axon5-messaging.yml`)
  rewrites the 2-argument `query(payload, ResponseTypes.instanceOf(...))` form; AI rewrites the 3-argument named
  query form, converts `multipleInstancesOf` call sites to `queryMany`, and finishes any
  `ResponseType<R>`-typed local/field declarations.
