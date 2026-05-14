**Result:** 🚧 Blocker
**Source:** `com.example.inventory.Inventory`
**Recipe:** axon4to5-aggregate

**Notes:** 1 blocker detected. Caller must resolve before re-invoking.

1. **B2 (Map-typed @AggregateMember)** at `Inventory.java:20-21` — `@AggregateMember private Map<String, StockItem> items = new HashMap<>();`. AF5 `@EntityMember` supports `List<Value>` only (see [multi-entity-migration.adoc](../../docs/paths/aggregates/multi-entity-migration.adoc) § "Maps are not supported"). Migration path: rewrite as `List<StockItem>` with internal id lookup (or a custom resolver). The rewrite touches the parent's `@EventSourcingHandler` body (`items.put(e.sku(), ...)` → list add + id-equality lookup), any command-handler reads of `map.get(key)`, and every reader/projection/test outside the aggregate that observed the map shape — all outside this recipe's scope.

**Options:**

_For B2 (Map-typed @AggregateMember):_
- [ ] **skip** — leave `Inventory` in its current partial state; queue moves on.
- [ ] **revert** — undo this recipe's edits; restore the pre-recipe `@AggregateMember Map<String, StockItem>` shape.
- [ ] **solve-manually** — pause this item; caller fixes the blocker by hand outside the skill, then re-invokes to continue.
- [ ] **redesign-map-to-list** — pause; caller rewrites the `Map<String, StockItem>` member as `List<StockItem>` plus id-management logic, updates external readers/projections/tests, then re-invokes the skill with the new shape.
