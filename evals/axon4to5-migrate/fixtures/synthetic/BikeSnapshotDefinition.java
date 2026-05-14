package com.example.bike;

// AF4 Spring bean providing the snapshot trigger for Bike aggregate.
// Referenced by @Aggregate(snapshotTriggerDefinition = "bikeSnapshotDefinition").
// AF5 migration: this class becomes dead code once BikeWithSnapshot.java is migrated
// to EventSourcedEntityModule.declarative(String.class, Bike.class)
//     .snapshotPolicy(c -> SnapshotPolicy.afterEvents(10)).build().

import org.axonframework.eventsourcing.EventCountSnapshotTriggerDefinition;
import org.axonframework.eventsourcing.Snapshotter;
import org.springframework.stereotype.Component;

@Component("bikeSnapshotDefinition")
public class BikeSnapshotDefinition extends EventCountSnapshotTriggerDefinition {

    public BikeSnapshotDefinition(Snapshotter snapshotter) {
        super(snapshotter, 10);
    }
}
