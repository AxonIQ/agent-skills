# Recipe: debug

Debug mode uses compile output to choose the next migration target. It is a
router, not a separate migration phase.

## Goal

Turn a failing full compile into one concrete recipe target at a time until the
project is green or only deferred/manual work remains.

## Inputs

- `build-tool`: pinned `maven` or `gradle`.
- `target`: optional module/project path.

## Preflight

1. Run compile without isolated scopes:
   - Maven: `./mvnw test-compile -DskipTests`
   - Gradle: `./gradlew testClasses`
2. If green, emit `skipped`.

## Procedure

1. Normalize diagnostics to `{file, symbol, missing type/method, line}`.
2. Group by root cause:

   | Error clue | Route |
   |---|---|
   | aggregate annotations/fixtures/apply | `aggregate` |
   | `@EventHandler`, processing group, token/DLQ | `event-processor` |
   | `CommandGateway` | `command-gateway` |
   | `QueryGateway` / `ResponseTypes` | `query-gateway` |
   | `@QueryHandler` | `query-handler` |
   | interceptor interfaces/chains | `interceptors` |
   | event store/configurer/root `Configuration` | `event-storage-engine` or `configuration.md` |
   | saga annotations | `saga` |

3. Pick the highest-leverage cluster: the one blocking the most downstream
   files, with generated/build output ignored.
4. Route the owning source file through the normal recipe loop.
5. Re-run compile.
6. If output is unchanged, ask once: surface details, defer cluster, or stop.

## End condition

- Compile green; or
- all remaining errors are recorded as deferred/manual; or
- the user stops after an unchanged/error cluster.

## Output

```yaml
result: success | skipped | needs-decision | failed
target: <project root or module>
reason: <compile summary>
decisions:
  routed-clusters: []
  deferred-clusters: []
caller-expects:
  commit: false
  next: proceed | ask-user | halt
notes: []
```
