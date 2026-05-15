# 07 — Dual-role class: `@EventHandler` + `@QueryHandler` on the same class

**Why this case is interesting:** "Cache-by-event" projectors expose both `@QueryHandler` methods (for serving queries from a cache) and `@EventHandler` methods (for keeping the cache fresh). Both recipes apply in tandem — the event-processor recipe owns `@Namespace`, `@SequencingPolicy`, and the AF5 `@EventHandler` import; the query-handler recipe (run separately) owns the `@QueryHandler` import. Splitting these into two recipe invocations would double-touch the file and risk drift. The event-processor recipe migrates the event-handler half AND surfaces the still-AF4 query-handler half as a Learning so the caller can route the file through the query-handler recipe next.

**Apply-condition:** `$SOURCE` has BOTH `@EventHandler` AND `@QueryHandler` methods (dual-role).

## Before (AF4)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository repository;

    public GetAllDwellingsQueryHandler(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @QueryHandler
    public List<DwellingReadModel> handle(GetAllDwellingsQuery query,
                                          @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        return repository.findAllByGameId(gameId);
    }

    @EventHandler
    public void on(DwellingBuilt event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

## After (AF5)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.core.annotation.SequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository repository;

    public GetAllDwellingsQueryHandler(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @QueryHandler
    public List<DwellingReadModel> handle(GetAllDwellingsQuery query,
                                          @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        return repository.findAllByGameId(gameId);
    }

    @EventHandler
    public void on(DwellingBuilt event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }
}
```

## What changed (event-processor recipe — this recipe's scope)

- `@ProcessingGroup` → `@Namespace` (string preserved).
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added (project's `@Bean SequencingPolicy gameIdSequencingPolicy` referenced this group — see use-case 03).
- `@EventHandler` import: AF4 → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- `@MetaDataValue` (capital `D`) → `@MetadataValue` (capital `M`) at `org.axonframework.messaging.core.annotation.MetadataValue`. This applies to BOTH the `@QueryHandler` AND the `@EventHandler` method parameters — the recipe rewrites the parameter annotation on every method in scope.

## What also changes here (technically the query-handler recipe's scope)

- `@QueryHandler` import: `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.

The event-processor recipe **also** swaps the `@QueryHandler` import in this dual-role case to keep the file internally consistent. The query-handler recipe will then re-visit the file (e.g. during a project-mode run) and confirm idempotency.

## What the recipe DOES NOT change

- Method bodies — repository calls, return types, parameter ordering all preserved verbatim.
- The Spring `@Component` stereotype.
- The constructor + field injection of `DwellingReadModelRepository` (this is not in-handler dispatch — it is a class-level dependency for both query AND event paths).

## Caveats

- **`@MetadataValue` capitalisation applies to both handler types.** The annotation rename catches every parameter site — `@QueryHandler` and `@EventHandler` alike. A grep for `@MetaDataValue(` after the rewrite must return zero.
- **The query-handler recipe owns response-type rewrites** (e.g. `ResponseType<List<X>>` to `List<X>` directly). The event-processor recipe must NOT touch return types or `ResponseType` constructs even when sitting in a dual-role file. If you see `ResponseType` usage, flag in Result NOTES; the query-handler recipe handles it.
- **`@SequencingPolicy` covers the EventHandler side only.** Queries are dispatched synchronously and do not respect sequencing policies. The annotation is still correct at class level — the framework applies it only when scheduling event handlers.
- **Do NOT split dual-role classes into two classes.** A class with both `@EventHandler` and `@QueryHandler` is a deliberate design choice (cache + query from same data). Splitting them is a refactor, not a migration; out of scope.
- **The class-level `@Component`** anchors Spring auto-discovery. Both `@EventHandler` and `@QueryHandler` rely on it (in Spring projects); preserve verbatim.
