# Evals — executable, self-contained

Real AF4↔AF5 file pairs are bundled into `evals/fixtures/`. The runner greps each AF5 fixture for `require:` patterns (must appear) and `forbid:` patterns (must NOT appear). One bash runner + one `.case` file per scenario + one manifest + one build script.

## Run

```bash
# From repo root
./skills/axon4to5-migrate/evals/run.sh             # all cases
./skills/axon4to5-migrate/evals/run.sh aggregate   # filter by name substring
```

Exit code: `0` = every case passed, `1` = at least one failed.

## Refresh fixtures from upstream

The skill ships its own copy of every referenced example. `manifest.tsv` lists every source path; `build.sh` does the copying.

```bash
./skills/axon4to5-migrate/evals/build.sh        # copy from .knowledge/repositories/ into evals/fixtures/
./skills/axon4to5-migrate/evals/build.sh check  # verify hashes (no copy) — exit 1 on drift
```

If upstream examples change, `build.sh check` will report drift; re-running `build.sh` refreshes the bundle.

## Case file format

```
recipe:  <recipe-name>                      # informational
af4:     evals/fixtures/<…>/<file>          # baseline (informational)
af5:     evals/fixtures/<…>/<file>          # required — grepped by runner
require: <literal substring>                # must appear in af5
forbid:  <literal substring>                # must NOT appear in af5
```

Lines starting with `#` are comments. Blank lines are ignored. Multiple `require:` / `forbid:` per case.

## Current coverage

| Case | Recipe | What it audits |
|---|---|---|
| `aggregate-heroes-dwelling` | aggregate | `@EventSourced`, `EventAppender`, `@EntityCreator`, snapshotting B1 dropped, all AF4 imports gone. |
| `aggregate-heroes-calendar` | aggregate | Second aggregate — different `tagKey`, same shape. |
| `event-processor-heroes-creature` | event-processor | `@Namespace`, `@SequencingPolicy(type = MetadataSequencingPolicy.class)`, class-level `CommandGateway` → method-parameter `CommandDispatcher`, no naked `.join()` / `.get()`. |
| `command-gateway-heroes-recruit` | command-gateway | Import-only swap in a Spring controller. Gateway stays. |
| `command-gateway-heroes-builddwelling-mcp` | command-gateway | Future-returning MCP tool — `commandGateway.send` chained, no blocking. |
| `query-gateway-heroes-mcp` | query-gateway | Sync callback bridges via `.orTimeout(30, TimeUnit.SECONDS).join()`. |
| `query-handler-heroes-getbyid` | query-handler | Import-only `@QueryHandler` rewrite, body untouched. |
| `event-storage-engine-heroes-entityscan` | event-storage-engine | Mandatory `@EntityScan(org.axonframework, io.axoniq.framework, …)` (A.JPA.5). |
| `event-storage-engine-heroes-gameconfig` | event-storage-engine | `SequencingPolicy` + correlation-provider package moves, `e.getMetaData()` → `e.metadata()`, `Optional` return. |
| `event-storage-engine-heroes-yaml` | event-storage-engine | YAML `axon.serializer.*` → `axon.converter.*`, per-processor `sequencing-policy:` removed. |
| `saga-bike-rental-payment` | saga | Shape B outcome: `@Component` + `@Scheduled` replacing `@DeadlineHandler`, all AF4 saga imports gone. |

## Add a case

1. Find a real before/after pair in `.knowledge/repositories/axon-examples/axon{4,5}/`.
2. Add two rows to `manifest.tsv` (af4 source + af5 source → `evals/fixtures/…`).
3. Run `./build.sh` to bundle.
4. Add a `cases/<recipe>-<short-name>.case` file with `require:` / `forbid:` patterns.
5. Run `./run.sh` — the new case should pass.
