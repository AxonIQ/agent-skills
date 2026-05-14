**Result:** 🚧 Blocker
**Source:** `com.example.shipment.Shipment`
**Recipe:** axon4to5-aggregate

**Notes:** 1 blocker detected. Caller must resolve before re-invoking.

1. **B4 (deadline handler)** at `Shipment.java:47` — `@DeadlineHandler` method `onOverdue(...)`. Also `DeadlineManager` constructor injection at `Shipment.java:23`, `DeadlineManager` parameter at `Shipment.java:36`, `deadlineManager.schedule(...)` at `Shipment.java:25`, and `deadlineManager.cancelSchedule(...)` at `Shipment.java:39`. AF5 has no direct deadline successor — the caller decides whether to redesign the deadline flow, remove it, or leave it on AF4 deps.

**Options:**

_For B4 (deadline):_
- [ ] **skip** — keep `Shipment` in its current partial state; queue moves on. The blocked item is reported so the caller can revisit.
- [ ] **revert** — undo any edits this recipe applied to `Shipment`; restore the pre-recipe `@DeadlineHandler` + `DeadlineManager` shape.
- [ ] **solve-manually** — pause this item; caller redesigns or removes the deadline flow (drops `@DeadlineHandler` `onOverdue`, the `DeadlineManager` constructor/handler parameters, and the `schedule` / `cancelSchedule` calls) and re-invokes the skill to continue.
