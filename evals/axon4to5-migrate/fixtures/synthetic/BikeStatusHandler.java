package io.axoniq.demo.bikerental.rental.query;

import org.axonframework.queryhandling.QueryHandler;
import org.springframework.stereotype.Component;

@Component
public class BikeStatusHandler {

    private final BikeStatusRepository bikeStatusRepository;

    public BikeStatusHandler(BikeStatusRepository bikeStatusRepository) {
        this.bikeStatusRepository = bikeStatusRepository;
    }

    @QueryHandler
    public Iterable<BikeStatus> findAll(FindAllBikes query) {
        return bikeStatusRepository.findAll();
    }

    @QueryHandler
    public BikeStatus findOne(FindBikeById query) {
        return bikeStatusRepository.findById(query.bikeId()).orElse(null);
    }
}
