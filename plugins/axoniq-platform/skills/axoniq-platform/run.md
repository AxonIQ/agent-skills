
# Run the local Axoniq stack

## Procedure

### 1. Pre-flight

Check the project root for:
- `compose.yml` — must exist (it's part of the skeleton)
- `pom.xml` (Maven) **or** `build.gradle.kts` (Gradle)
- A `*Application.{kt,java}` main class

If any are missing, stop and tell the user the skeleton is incomplete.

Detect the build platform from which file is present.

### 2. Start docker compose

```bash
docker compose up -d
```

Then wait for Axon Server to be ready. Don't poll in a tight loop — sleep 2s between checks, give up after 60s. Readiness check:

```bash
curl -fsS http://localhost:6024/actuator/health > /dev/null
```

(Port `6024` is the local-profile UI port; the skeleton's `compose.yml` maps it.)

If readiness times out, surface the docker logs and stop:

```bash
docker compose logs --tail=50 axonserver
```

### 3. Run the app

Maven:
```bash
./mvnw spring-boot:run
```

Gradle:
```bash
./gradlew bootRun
```

Run this **in the background** so it doesn't block the conversation. Stream the first 30 seconds of logs and stop streaming once you see "Started <Application> in N.NNN seconds" or any error stack trace.

### 4. Report

Print three URLs for the user:

- App + Swagger: http://localhost:8080/swagger-ui/index.html
- Axon Server console: http://localhost:6024
- Project root in the Platform UI: https://platform.axoniq.io/workspace/<workspaceId>/project/<projectId> (read both ids from `./.axoniq`).

If the app failed to start, print the last 30 log lines and stop — don't attempt to "fix" the failure unless the user asks.

## What this skill never does

- Run `docker compose down -v` (would wipe the event store).
- Modify `compose.yml`, `pom.xml`, or `build.gradle.kts`.
- Restart a healthy app "just to be sure".
- Open the URLs in a browser — just print them.

## When to stop and ask

- Port `8080`, `6024`, or `6124` already in use → ask whether to free the port or change the app's port. Don't kill processes on the user's behalf.
- Docker daemon not running → tell the user to start Docker Desktop / `systemctl start docker`. Don't try to start it yourself.
- The app starts but immediately exits with a connection error → check that step 2 completed; if it did, surface the stack trace and stop.
