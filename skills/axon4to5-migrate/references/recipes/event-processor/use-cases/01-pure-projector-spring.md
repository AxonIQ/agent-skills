# 01 — Pure projector (Spring)

**Why this case is interesting:** Baseline of the event-processor recipe. `@EventHandler`-only class with no `CommandGateway` injection — common read-model projection. Tests the four "always" steps (Namespace swap, annotation import moves, metadata accessor rename) and proves the recipe skips command-dispatch steps when not needed. Class-level `@Component` (Spring stereotype) is preserved.

**Apply-condition:** `configuration=spring` AND `$SOURCE` has only `@EventHandler` / `@ResetHandler` methods (no `CommandGateway` field, no in-handler dispatch).

## Before (AF4)

```java
package com.dddheroes.heroesofddd.creaturerecruitment.read;

import com.dddheroes.heroesofddd.creaturerecruitment.events.AvailableCreaturesChanged;
import com.dddheroes.heroesofddd.creaturerecruitment.events.DwellingBuilt;
import com.dddheroes.heroesofddd.shared.metadata.GameMetaData;
import org.axonframework.config.ProcessingGroup;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventhandling.ResetHandler;
import org.axonframework.messaging.annotation.MetaDataValue;
import org.springframework.stereotype.Component;

@Component
@ProcessingGroup("ReadModel_Dwelling")
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    public DwellingReadModelProjector(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(DwellingBuilt event, @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetaDataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }

    @ResetHandler
    public void onReset() {
        repository.deleteAll();
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
import org.axonframework.messaging.core.sequencing.annotation.SequencingPolicy;
import org.axonframework.messaging.core.sequencing.MetadataSequencingPolicy;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler;
import org.springframework.stereotype.Component;

@Component
@Namespace("ReadModel_Dwelling")
@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)
public class DwellingReadModelProjector {

    private final DwellingReadModelRepository repository;

    public DwellingReadModelProjector(DwellingReadModelRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(DwellingBuilt event, @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.save(new DwellingReadModel(gameId, event.dwellingId(), event.creatureId()));
    }

    @EventHandler
    public void on(AvailableCreaturesChanged event,
                   @MetadataValue(GameMetaData.GAME_ID_KEY) String gameId) {
        repository.findById(new DwellingReadModelId(gameId, event.dwellingId()))
                  .ifPresent(rm -> rm.setAvailable(event.changedTo()));
    }

    @ResetHandler
    public void onReset() {
        repository.deleteAll();
    }
}
```

## What changed

- `@ProcessingGroup("ReadModel_Dwelling")` → `@Namespace("ReadModel_Dwelling")` (string preserved exactly).
- Import swap: `org.axonframework.config.ProcessingGroup` → `org.axonframework.messaging.core.annotation.Namespace`.
- `@EventHandler` import: `org.axonframework.eventhandling.EventHandler` → `org.axonframework.messaging.eventhandling.annotation.EventHandler`.
- `@ResetHandler` import: `org.axonframework.eventhandling.ResetHandler` → `org.axonframework.messaging.eventhandling.replay.annotation.ResetHandler`.
- `@MetaDataValue` (capital `D`) → `@MetadataValue` (capital `M`, lowercase `d`) at `org.axonframework.messaging.core.annotation.MetadataValue`. Case-sensitive — the annotation symbol AND the import package change.
- `@SequencingPolicy(type = MetadataSequencingPolicy.class, parameters = GameMetaData.GAME_ID_KEY)` added at class level because the AF4 project had a `@Bean SequencingPolicy gameIdSequencingPolicy` keyed on the same metadata key. See use-case 03 for the YAML / @Bean → annotation move.
- `@Component` preserved (Spring stereotype, not Axon).
- Constructor + field injection of `DwellingReadModelRepository` preserved — no in-handler command dispatch, so no `CommandDispatcher` parameter is introduced.

## Caveats

- **`@Namespace` string IS the binding contract.** Match the AF4 `@ProcessingGroup` value exactly. Mismatch silently drops events at runtime; there is no compile signal.
- **`@MetaDataValue` (AF4) vs `@MetadataValue` (AF5)** — typos compile cleanly and the parameter silently receives `null`. Grep for the AF4 form after the rewrite to confirm zero remain.
- **`@SequencingPolicy` annotation is recipe-derived**, not present in the AF4 source. The recipe adds it only when the AF4 wiring referenced a custom policy for this processing group (Step 6). For projectors without a sequencing policy, omit it.
- **Do NOT introduce `CommandDispatcher` here.** Pure projectors do not dispatch commands; threading the dispatcher parameter is wasted ceremony AND surfaces a stale code-smell for reviewers.
