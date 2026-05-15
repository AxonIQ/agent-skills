package com.example.dwellings.api;

import com.example.dwellings.read.DwellingReadModel;
import org.axonframework.queryhandling.QueryGateway;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/dwellings")
class DwellingRestController {

    private final QueryGateway queryGateway;

    DwellingRestController(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    @GetMapping("/{dwellingId}")
    CompletableFuture<DwellingReadModel> getDwelling(@PathVariable String dwellingId) {
        return queryGateway.query(new GetDwellingById(dwellingId), DwellingReadModel.class);
    }
}
