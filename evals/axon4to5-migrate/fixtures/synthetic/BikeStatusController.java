package com.example.bikes.api;

import com.example.bikes.query.BikeStatus;
import org.axonframework.messaging.responsetypes.ResponseTypes;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/bikes")
class BikeStatusController {

    private final QueryGateway queryGateway;

    BikeStatusController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{bikeId}")
    CompletableFuture<BikeStatus> findOne(@PathVariable String bikeId) {
        return queryGateway.query(
                new FindBikeById(bikeId),
                ResponseTypes.instanceOf(BikeStatus.class)
        );
    }

    @GetMapping
    CompletableFuture<List<BikeStatus>> findAll() {
        return queryGateway.query(
                new FindAllBikes(),
                ResponseTypes.multipleInstancesOf(BikeStatus.class)
        );
    }
}
