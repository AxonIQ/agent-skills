# 04 — @ProcessingGroup → @Namespace and @MetaDataValue → @MetadataValue

**Why this case is interesting:** Heroes-of-DDD and similar projects annotate query handler classes with `@ProcessingGroup` for grouping, and use `@MetaDataValue` for injecting metadata into handler method parameters. Both annotation names and packages changed in AF5.

**Apply-condition:** `$SOURCE` has `@ProcessingGroup` or `@MetaDataValue` (or both).

---

## Before (AF4) — from heroes-of-ddd

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings;

import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@ProcessingGroup("Read_GetAllDwellings_QueryCache")
@Component
class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository dwellingReadModelRepository;

    GetAllDwellingsQueryHandler(DwellingReadModelRepository dwellingReadModelRepository) {
        this.dwellingReadModelRepository = dwellingReadModelRepository;
    }

    @QueryHandler
    GetAllDwellings.Result handle(GetAllDwellings query) {
        var dwellings = dwellingReadModelRepository.findAllByGameId(query.gameId());
        return new GetAllDwellings.Result(dwellings);
    }

    @EventHandler
    void evolve(DwellingBuilt event, @MetaDataValue("gameId") String gameId) {
        var item = new DwellingReadModel(gameId, event.dwellingId(), event.creatureId(), event.costPerTroop(), 0);
        dwellingReadModelRepository.save(item);
    }
}
```

## After (AF5)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read.getalldwellings;

import org.axonframework.messaging.core.annotation.Namespace;
import org.axonframework.messaging.core.annotation.MetadataValue;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.queryhandling.annotation.QueryHandler;
import org.springframework.stereotype.Component;

@Namespace("Read_GetAllDwellings_QueryCache")
@Component
class GetAllDwellingsQueryHandler {

    private final DwellingReadModelRepository dwellingReadModelRepository;

    GetAllDwellingsQueryHandler(DwellingReadModelRepository dwellingReadModelRepository) {
        this.dwellingReadModelRepository = dwellingReadModelRepository;
    }

    @QueryHandler
    GetAllDwellings.Result handle(GetAllDwellings query) {
        var dwellings = dwellingReadModelRepository.findAllByGameId(query.gameId());
        return new GetAllDwellings.Result(dwellings);
    }

    @EventHandler
    void evolve(DwellingBuilt event, @MetadataValue("gameId") String gameId) {
        var item = new DwellingReadModel(gameId, event.dwellingId(), event.creatureId(), event.costPerTroop(), 0);
        dwellingReadModelRepository.save(item);
    }
}
```

## What changed

- `@ProcessingGroup("Read_GetAllDwellings_QueryCache")` → `@Namespace("Read_GetAllDwellings_QueryCache")`.
  - Remove `org.axonframework.config.ProcessingGroup`.
  - Add `org.axonframework.messaging.core.annotation.Namespace`.
- `@MetaDataValue("gameId")` → `@MetadataValue("gameId")` (capital D removed; same key string).
  - Remove `org.axonframework.messaging.annotation.MetaDataValue`.
  - Add `org.axonframework.messaging.core.annotation.MetadataValue`.
- `@QueryHandler` import: `org.axonframework.queryhandling.QueryHandler` → `org.axonframework.messaging.queryhandling.annotation.QueryHandler`.
- `@EventHandler` import also updated here since the method is being touched: `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- Method bodies and logic: unchanged.

## Caveats

- **`MetaData` type rename**: If `MetaData` appears as a parameter type (not just the annotation), it also renames to `Metadata` with new import `org.axonframework.messaging.core.Metadata`.
- **Namespace value preserved verbatim**: Copy the string from `@ProcessingGroup` exactly — it controls event processor thread pool assignment in AF5.
