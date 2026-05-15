package com.example.dwellings;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Component;

@Component
class DwellingsQueryService {

    private final QueryGateway queryGateway;

    DwellingsQueryService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    DwellingReadModel getDwelling(String dwellingId) {
        try {
            return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class).get();
        } catch (Exception e) {
            throw new RuntimeException("Query failed", e);
        }
    }
}
