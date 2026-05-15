package com.example.dwellings.mcp;

import com.example.dwellings.queries.GetAllDwellings;
import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
class DwellingsMcpResource {

    private final QueryGateway queryGateway;

    DwellingsMcpResource(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    List<DwellingReadModel> fetchDwellings(String gameId) {
        try {
            return queryGateway.query(new GetAllDwellings(gameId), DwellingReadModel.class).get();
        } catch (Exception e) {
            throw new RuntimeException("Query failed", e);
        }
    }
}
