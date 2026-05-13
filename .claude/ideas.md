# Ideas / TODOs

Refactor candidates, future simplifications, "thought about it, parked it" notes.
**Never live in SKILL.md** (skills are user-facing runtime instructions, not work backlog).
Group by skill / area; each entry: idea → trade-off → "revisit when".

---

## `skills/axon4to5-migrate`

### Ask → fix retry as a decorator around `Recipe`

Today the orchestrator diagram shows `needs-decision` looping back through `Ask → fix → Recipe`, which means **two arrows leaving `Act`** (one direct loop-back, one to `Ask`). A pure-flow alternative: wrap the `Recipe` node in a "decorator" that intercepts `needs-decision`, asks, and re-invokes itself transparently. Outwardly `Recipe` would have a single deterministic outcome (`success / skipped / rejected / blocked / failed`); `needs-decision` would never leak to the orchestrator.

**Pros.** Drops one arrow + one node from the main flow. Orchestrator switch shrinks from 6-way to 5-way.

**Cons.** Hides the retry from the diagram entirely — debugging "why did the user get re-prompted?" becomes one indirection deeper. Also the recipe's `Output` schema today exposes `needs-decision` as a first-class outcome; folding it into the decorator means a recipe author can no longer emit `needs-decision` directly without going through the wrapper.

**Revisit when.** ≥ 1 user-facing report of confusion around the existing two-arrow shape. Until then the explicit retry stays — its visibility is the feature.

### State persistence as `state.yaml`

Separate machine-readable Pinned-decisions + queue cursor from human-readable `progress.md`. Today the orchestrator parses markdown headings to recover state; fragile.

**Trade-off.** Extra file (`state.yaml`) and a load/save step vs. removing the "parse markdown to get pinned license/wiring/build-tool" fragility.

**Revisit when.** A real drift bug surfaces (e.g. progress.md edited by user breaks orchestrator resume).

### Parallel `next_batch(phased)` discovery

Dispatch one subagent per routing-table row, fan in their candidate lists. Today discovery is sequential.

**Trade-off.** Parallelism savings vs. `AskUserQuestion` serialization when saga-blocker fires mid-discovery (parallel runs would race on the same prompt).

**Revisit when.** Users report discovery latency as the bottleneck.

---

## (Other skills, when relevant)

Add a `## skills/<name>` section per skill that accumulates ideas.
