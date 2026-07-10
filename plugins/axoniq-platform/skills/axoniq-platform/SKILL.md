---
name: axoniq-platform
description: Local implementation of an Axoniq Platform project. The project's journeys, components, and messages live on the Platform and are accessed via the `axoniq-platform` MCP server. This skill drives status reporting, dispatches the right per-type implementation skill, and owns the implement / implemented MCP markers. Use whenever the user asks "what's next", "what's the status", "implement <componentId>", "run the app", or asks anything about the project's journeys/components.
---

# Axoniq workflow

Entry point for any Axoniq work in this project.

## First-turn behavior (every new session)

At the start of every new conversation in this repo — before any other work — do this in order:

1. **Greet the user** in one short sentence that names the project. Example: *"Hi! You're working on the **Bike Rental** project — let me check what's ready to implement."* (Project name comes from `get_project`.)
2. **Retrieve components** by calling `get_project(projectId)` on the `axoniq-platform` MCP server. `projectId` and `workspaceId` are in `./.axoniq` at the repo root.
3. **Suggest one concrete component to start with**, named by id, and explain in one line why. Prefer components with status `APPROVED` and no local `.axoniq` marker yet. Example: *"I'd suggest starting with **`rent-bike`** — it's a `COMMAND` component, approved on the Platform, and nothing's been claimed locally yet. Want me to scaffold it?"*

If `get_project` fails (missing `.axoniq`, bad credentials, unreachable MCP server), say so plainly and stop — don't fall through to a generic greeting. If every component is already `IMPLEMENTED`, say so and point the user back to the Platform UI instead of suggesting work.

Keep the whole greet/retrieve/suggest exchange under 6 lines — it's an orienting handshake, not a status dump. The detailed status table in Step 5 below is for when the user explicitly asks "what's the status".

**Where the spec lives.** Journeys, components, messages, and notes live on the Axoniq Platform — not on disk. Everything is accessed through the `axoniq-platform` MCP server (configured in `.mcp.json`). There is no `./spec/` directory. To **edit** journey content, component handlers, or messages, the user goes back to the Platform chat at https://platform.axoniq.io/workspace/{{WORKSPACE_ID}}/projects/{{PROJECT_ID}}; you can read the spec, add/modify/remove notes, approve journeys/components, and mark components implementing/implemented from here.

**What lives locally.** Source code under `{{source_directory}}/{{source_path}}/` and per-component `.axoniq` marker files. That's it.

## Step 1 — Resolve project identity

Read `./.axoniq` at the repo root. It contains `workspaceId` and `projectId` — pass these to every MCP call.

```json
{ "workspaceId": "...", "projectId": "..." }
```

If either field is missing or still `{{...}}`, stop and ask the user. They likely downloaded the skeleton without going through the Platform's project setup.

## Step 2 — Read project state via MCP

Always start by fetching the current state:

| Call | Returns |
|---|---|
| `get_project(projectId)` | High-level snapshot: name, stage, journeys with statuses, components with statuses, messages, notes. **Cheapest entry point.** |
| `list_journeys(projectId)` | Journeys table: id, name, **type** (`EXECUTION`/`BROWSE`), **domains** (comma-separated, may be multiple), **actor**, **importance** (1-10), status, description. |
| `list_components(projectId)` | Components table: id, name, type, **domains** (comma-separated, may be multiple), status, **supports** (the top journeys that reference this component, with their importance scores in parentheses, e.g. `rent-bike (10), return-bike (9)`), description. |
| `get_journey_details(projectId, journeyId)` | Primary flow + alternative flows for one journey. |
| `get_component_details(projectId, componentId)` | Full component spec — handlers, messages, exceptions, scenarios. |

Prefer `get_project` once at the start of a turn; fall through to the focused calls only when you need a specific journey or component in depth.

**Journey tags** (`type` / `domains` / `actor` / `importance`) and the component `domains` tag form the project's triage system. Use them to scope the user's request:

- **Importance** — when the user says "what's next" without specifying, prefer high-importance journeys (8-10) over low-importance ones (1-3). It's the AI's best signal for what matters to the product.
- **Domain** — when the user references a business area ("the rentals stuff", "wallet things"), filter journeys/components whose `domains` cell **contains** that label. The cell may list multiple comma-separated labels — a row matches if any of them does. Domain labels are shared between journeys and components, so the same label scopes both.
- **Actor** — useful for "what does the operator do?" style queries.
- **Type (EXECUTION vs BROWSE)** — narrows from all journeys to just the state-changing ones (or just the read-only ones).

## Step 3 — Component status decision matrix

The dispatch hinges on `ComponentStatus` returned by MCP. Local-eligible statuses:

| Status | Local action |
|---|---|
| `GENERATING` | wait — Platform is still deriving. Re-run `get_project` after a short pause. |
| `NEEDS_APPROVAL` | legacy — components no longer go through a review gate, but in-flight ones from before the change may still show this status. Treat as `APPROVED` for the purposes of dispatch; if needed, the user can still call the legacy `approve_component` MCP tool. |
| `APPROVED` | **implement locally** — call `mark_component_implementing(...)`, dispatch to the type-specific implement skill, then `mark_component_implemented(...)` once tests pass. |
| `IMPLEMENTING` (claimed by us) | resume implementation. |
| `IMPLEMENTING` (claimed by someone else) | skip, surface a drift warning. |
| `IMPLEMENTED` | skip — done. |
| `CODE_GENERATING`, `CODE_GENERATED`, `CODE_GENERATION_FAILED` | **off-limits** — this project was built with the legacy server-side codegen pipeline. Local implementation is not safe; surface to the user and stop. |

Always re-check status before claiming a component — another contributor may have moved it.

## Step 4 — Classify the user's intent

| User said | Action |
|---|---|
| "What's the status?" / "Where am I?" / "What's next?" | Step 5 below — status report, no dispatch. |
| "Implement `<componentId>`" / "scaffold `<componentId>`" | Step 6 below — fetch spec via MCP, dispatch by type. |
| "Implement the next component" / "what should I implement?" | Step 6 — pick eligible (`APPROVED`, not yet `.axoniq`-markered locally), then dispatch. |
| "Add a journey / component / change a step / change a handler" | Call `chat_with_platform(projectId, "<request>")` — that forwards the change to the Platform's project AI, which edits journeys/components/messages server-side. See [refine-spec.md](refine-spec.md). |
| "Remember that …" / "this should always …" / "the user clarified …" | Same — use `chat_with_platform(projectId, "remember that …")` so the Platform's AI captures the context in the right place. |
| "Run the app" / "Start docker compose" | [run.md](run.md) |

If the user's request mixes "edit a journey" with implementation, do the implementable parts first, then surface the Platform-only changes.

## Step 5 — Status report

When the user asks "where am I?" / "what's next?" / "status":

1. Call `get_project(projectId)`.
2. Render a project header (name, journey counts by status, component counts by status):
   ```
   Project: Bike Rental
     Stage: COMPONENTS
     Journeys:    4  (1 DISCOVERY, 3 APPROVED)
     Components:  5  (3 APPROVED, 2 IMPLEMENTED locally)
   ```
3. **Components table** — local-implementable status only:
   ```
   STATUS              id                       type            local marker
   APPROVED            rent-bike                COMMAND         —              (eligible)
   IMPLEMENTING        return-bike-handler      COMMAND         claimed (us)
   IMPLEMENTED         available-bikes-view     QUERY           ✓
   ```
4. Cross-check `.axoniq` markers in the source tree against MCP status — flag drift (marker without spec, marker with mismatching id, marker missing for an `IMPLEMENTED` component).
5. **Suggested next action** — one line, named by id:
   - *"Implement `rent-bike` (APPROVED, no local marker yet)."*
   - *"`return-bike-handler` is claimed by us and partially implemented — resume?"*
   - *"All approved components are implemented locally — nothing left to do here."*

Keep status reports under 50 lines.

## Step 6 — Pick & dispatch a component to implement

1. If the user named a `<componentId>`, call `get_component_details(projectId, componentId)`.
2. If "next" / "what's next" — call `list_components(projectId)`, filter:
   - Status `APPROVED`.
   - No `.axoniq` marker for that componentId in the local source tree.
   - **Prefer components serving high-importance journeys.** Each row's `Supports` column already lists the related journeys with their importance scores (e.g. `rent-bike (10), return-bike (9)`) — pick the component whose top supports number is the highest. Ties: prefer the component listed in MORE journeys (broader impact). When `Supports` is `—` (no journey references this component's anchors yet), fall back to scanning journey descriptions; if still nothing, ask the user which component to start on. Don't waste the user's first implementation slot on an importance-3 admin chore when an importance-9 core flow is also `APPROVED` and unclaimed.
   - **Group by domain when the user signaled one.** If the user said "let's do the Rentals stuff first", scope the candidate set to components whose `domains` cell **contains** `"Rentals"` (it may also list other labels) before applying the importance sort.
3. **Re-check status** right before claiming — another contributor may have moved it.
4. Call `mark_component_implementing(projectId, componentId)`. This sets the component to `IMPLEMENTING` on the Platform so the UI surfaces who's working on it.
5. Fetch full details with `get_component_details(projectId, componentId)` and route by `type`:

   | `type` | Implementation skill |
   |---|---|
   | `COMMAND` | [implement-command-component.md](implement-command-component.md) |
   | `QUERY` | [implement-query-component.md](implement-query-component.md) |
   | `EXTERNAL_SYSTEM` | [implement-external-system-component.md](implement-external-system-component.md) |
   | `WORKFLOW` | [implement-workflow-component.md](implement-workflow-component.md) — the spec carries `triggerEvent`, `idProperty`, `entryStep`, and a structured list of steps (Wait/Dispatch/Sleep/Multi/When/Choice/Fail/Cancel), which may form business loops. |

   All four also load [implementation-base.md](implementation-base.md) for package layout, decision trees, fixture setup, etc.

6. **Marker first, build last.** The implementation skill creates `<component_pkg>/.axoniq` as the **first** step when scaffolding a new package — that link from package to MCP component is what lets the system recover if the run is interrupted. After all files are written and tests pass, call `mark_component_implemented(projectId, componentId, version)` with the component **version you implemented** (the **Latest version** shown by the `get_component_details` you built against). The Platform flips that version to `IMPLEMENTED`. **If the call is rejected because a newer version exists**, the spec was edited while you were working: re-fetch `get_component_details`, reconcile your code with the new spec, and call `mark_component_implemented` again with the new version. Repeat until it's accepted.

7. **After the component is done**: re-run `list_components` and suggest the next concrete step by name:
   - *"`rent-bike` done — implement `available-bikes-view` next (also from the rent-bike journey)."*
   - *"All approved components implemented — nothing left in the queue."*
   - Never end with a generic *"all done"* without naming what comes next.

## Local drift detection

When listing components, cross-check MCP status vs `.axoniq` marker in source:

| MCP status | Local marker | Verdict |
|---|---|---|
| `APPROVED` | absent | **ready to implement** |
| `APPROVED` | present | **drift — MCP doesn't reflect implementation**; offer to call `mark_component_implemented(projectId, componentId, version)` with the latest version |
| `sync: PENDING_CHANGES` (from get_component_details) | present | **spec moved on** — implemented at an earlier version than the latest; re-fetch, reconcile your code with the latest spec, and `mark_component_implemented` at the new latest version |
| `IMPLEMENTING` (us) | absent | **scaffolding interrupted** — resume by re-running the type-specific implement skill |
| `IMPLEMENTING` (us) | present | **in progress** — fine |
| `IMPLEMENTING` (other) | absent | another contributor is working; skip |
| `IMPLEMENTING` (other) | present | **collision** — surface to user |
| `IMPLEMENTED` | absent | **drift — implementation deleted locally**; either restore code or ask Platform to flip back |
| `IMPLEMENTED` | present with matching id | **done** |
| `IMPLEMENTED` | present with different id | **drift — package collision**; surface, don't auto-fix |
| `CODE_GENERATED` / `CODE_GENERATING` / `CODE_GENERATION_FAILED` | any | **off-limits — server-side project**; report and stop |

## Spec smells — bounce back to Platform, don't paper over

If the spec is asking you to write code that feels structurally wrong — model inconsistencies, impossible-to-implement shapes, things only resolvable by local workarounds — STOP and route the user back via `chat_with_platform(projectId, message)`. The Platform is the source of truth for the model; fixing model issues locally creates drift you'll pay for on the next regeneration. Trust the smell.

How to bounce well: quote the specific directives or fields that conflict, name the architectural rule being violated if you can identify it, and propose a concrete corrected shape. Describe the model inconsistency, not the implementation symptom ("the implementation is hard" is not a useful prompt). After the call returns, re-fetch via MCP before resuming — the Platform may have updated the spec.

When NOT to bounce: taste differences (verbose names, suboptimal id casing, scenario phrasing) are not smells. The bounce trigger is **a structural issue you cannot resolve with local code alone**.

## Reference files (read on demand)

| File | When to load |
|---|---|
| [implementation-base.md](implementation-base.md) | Before any type-specific implementation file. Has package layout, decision trees, AxonTestFixture setup, gotchas. |
| [implement-command-component.md](implement-command-component.md) | `type == COMMAND` |
| [implement-query-component.md](implement-query-component.md) | `type == QUERY` |
| [implement-external-system-component.md](implement-external-system-component.md) | `type == EXTERNAL_SYSTEM` |
| [implement-workflow-component.md](implement-workflow-component.md) | `type == WORKFLOW` |
| [refine-spec.md](refine-spec.md) | Editing notes via MCP, or directing the user back to the Platform for content edits. |
| [run.md](run.md) | Start docker compose + the Spring Boot app. |
| the **`axoniq-app-development`** plugin (install it alongside this one from the `axoniq` marketplace) — its `SKILL.md` | All Axon Framework 5 API questions — annotations, fixture API, processors, etc. |

## MCP — full tool inventory

The `axoniq-platform` MCP server exposes:

**Project & spec read (always available)**
- `list_projects(workspaceId)` — workspace-wide overview.
- `get_project(projectId)` — full snapshot for this project (journeys, components, messages, notes).
- `list_journeys(projectId)` / `get_journey_details(projectId, journeyId)`.
- `list_components(projectId)` / `get_component_details(projectId, componentId)`.

**Component lifecycle (we drive)**
- `mark_component_implementing(projectId, componentId)` — call before scaffolding.
- `mark_component_implemented(projectId, componentId, version)` — call after tests pass, with the version you implemented. Rejected if a newer version exists (spec edited mid-implementation) — re-fetch, reconcile, and call again with the new version.
- `unmark_component_implementing(projectId, componentId)` — release the claim if the user decides to stop. Status returns to APPROVED so someone else (or they themselves later) can pick it up. Idempotent.
- `approve_component(projectId, componentId)` — legacy; new components ship as APPROVED. Only relevant for in-flight components from before the review gate was removed.

**Journey lifecycle**
- `analyze_journey(projectId, journeyId)` / `approve_journey(projectId, journeyId)` — Platform-driven; only call if the user explicitly says so. These are the MCP equivalents of the Platform UI's **Refine Journey** and **Confirm Design** actions.

**Platform AI chat (for journey/component/message edits AND notes)**
- `chat_with_platform(projectId, message)` — send a focused request to the Platform's project AI (max 1000 chars). Use when the user wants to change journey flows, component handlers, scenarios, or message shapes — i.e. anything the local MCP tools can't edit directly. Blocks until the Platform AI finishes (max ~3 min). After it returns, re-fetch `get_project` to see what changed.

**Skill feedback (when this skill led you astray)**
- `skill_feedback(skillName, description, [projectId])` — file a report when something in *this skill bundle* (a sample, an import, a path, a step) was wrong or confusing. Call it once per concrete issue, with the path of the offending file as `skillName` and a specific description of what's wrong + what it should say. `projectId` is optional; include it if the issue surfaced while working on a Platform project. **Use this only for skill content issues**, never for bugs in the user's project code.

**Pattern catalog (reference reading)**
- `list_patterns()`, `get_pattern_overview(name)`, `get_pattern_journeys(name)`, `get_pattern_components(name)`, `get_pattern_messages(name)`, `get_pattern_code(name)`, `get_pattern_tests(name)`. Patterns are **reference only** — never paste pattern files into `src/`.

## What this skill does NOT do

- It does NOT maintain a local `./spec/` directory. The spec lives on the Platform, accessed only via MCP.
- It does NOT directly edit journey content, component handlers, message shapes, or notes — every spec edit goes through `chat_with_platform`, which forwards the request to the Platform's project AI.
- It does NOT do top-down "design every journey first, then implement everything" passes. Implement components one at a time, re-fetching `get_project` between dispatches so you see the latest Platform state.
- It does NOT cache MCP responses across turns. The Platform is the source of truth; always re-fetch at the start of a new turn.
