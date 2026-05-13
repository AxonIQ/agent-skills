# Evals — executable

Real AF4↔AF5 file pairs from `.knowledge/repositories/axon-examples/` drive the suite. The runner greps each AF5 reference for `require:` patterns (must appear) and `forbid:` patterns (must NOT appear). One short bash script + one `.case` file per scenario.

## Run

```bash
./skills/axon4to5-migrate/evals/run.sh          # all cases
./skills/axon4to5-migrate/evals/run.sh aggregate # cases whose name contains "aggregate"
```

Exit code: `0` = every case passed, `1` = at least one failed.

## Case format

```
recipe:  <recipe-name>
af4:     <repo-relative path under .knowledge/repositories/axon-examples/>
af5:     <repo-relative path>
require: <literal substring that MUST appear in af5>
forbid:  <literal substring that MUST NOT appear in af5>
```

Lines starting with `#` are comments. Blank lines are ignored. Multiple `require:` and `forbid:` lines per case.

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
2. Run greps on the AF5 file to confirm patterns you want to assert.
3. Drop a `cases/<recipe>-<short-name>.case` file.
4. Re-run `./run.sh` — the new case should pass.
