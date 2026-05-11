# Template — `axonframework` per-repo detail file

Use this template when `repo_type: axonframework`. The detail file lives at:

```
.knowledge/repositories/axonframework/axonframework_<RepoName>.md
```

`<RepoName>` is the submodule directory name as cloned (e.g. `AxonFramework4`, `AxonFramework5`).

## Filled-in example

```markdown
---
repo_type: axonframework
repo_name: AxonFramework5
submodule_path: .knowledge/repositories/axonframework/AxonFramework5
url: https://github.com/AxonIQ/AxonFramework.git
branch: feat/migration-skills
commit: <short-hash if pinned>
keywords:
  - axon 5
  - dynamic consistency boundary
  - reactive
  - event sourcing
  - migration target
---

# AxonFramework5

## Purpose

Source tree for Axon Framework 5. This is the canonical reference for the new
APIs that migration skills target — command/event handling, the new event store,
DCB, and the reactive primitives that replace Axon 4 sagas.

## Feature highlights

- **Dynamic Consistency Boundary (DCB)** — replaces the aggregate root pattern as
  the unit of consistency.
- **Reactive command/event handlers** — `CompletableFuture` and `Mono` return
  types are first-class.
- **New event store SPI** — see `axon-eventsourcing/` for the storage engine
  contracts.
- **AxonTestFixture** — Spring-Boot-friendly test harness; see
  `axon-spring-boot-starter/`.

## Key paths

- `axon-messaging/` — message buses and gateway interfaces.
- `axon-modelling/` — DCB, aggregates, state-based modelling.
- `axon-eventsourcing/` — event store and snapshotting.
- `axon-test/` — `AxonTestFixture` and assertion DSL.

## Highlights

- Reference docs (in-repo): `docs/` — start with `docs/README.md` and
  `docs/getting-started/`. Prefer these over the public site; this tree
  is the source of truth for the branch checked out here.
- Start with the `axon-modelling` module when reasoning about state — DCB is
  the new mental model and most migration confusion lives there.
- Skip the deprecated `axon-saga/` package under `axon-modelling/legacy/` —
  retained for source-compat only; sagas are replaced by repository-based
  state.
- The reactive return-types pattern is illustrated end-to-end in
  `axon-spring-boot-autoconfigure/` integration tests.
```

## Empty scaffold (copy this when creating a new file)

```markdown
---
repo_type: axonframework
repo_name: <RepoName>
submodule_path: .knowledge/repositories/axonframework/<RepoName>
url: <git URL>
branch: <branch or omit>
commit: <short-hash or omit>
keywords:
  - <term>
  - <term>
  - <term>
---

# <RepoName>

## Purpose

<1–2 sentences on what this repo is and why it's tracked here.>

## Feature highlights

- **<Feature 1>** — <one line>
- **<Feature 2>** — <one line>
- **<Feature 3>** — <one line>

## Key paths

- `<path/inside/repo>` — <why it matters>
- `<path/inside/repo>` — <why it matters>

## Highlights

- <Curated callout — documentation URL, what to read first, what to skip, etc.>
- <Curated callout>
```

## Field rules

- `branch` and `commit` are both optional. If neither is set, the submodule
  tracks the default branch — that's fine for stable references.
- `keywords` must be 3–7 short terms. They are also surfaced in the type-level
  `INDEX.md` (`Keywords:` line), so they should be discriminative — terms a
  future Claude session would actually search.
- `## Highlights` is mandatory as a section heading. It may contain `- _none_`
  only when the curator explicitly has nothing to flag.
- **Docs pointer rule.** If the submodule contains a `docs/` tree (Axon
  Framework repos do), the first Highlight bullet MUST point at the
  in-repo path — not the public docs site. Rationale: we typically
  track WIP branches whose `docs/` tree IS the source of truth, while
  the public site is version-pinned and may diverge. Use a public URL
  only when the submodule has no in-repo documentation, and call out
  that the URL is version-pinned.
