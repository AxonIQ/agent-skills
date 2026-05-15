package com.example.capacity.api;

import com.example.capacity.commands.ReserveCapacityCommand;
import com.example.capacity.dto.ReservationResult;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/capacity")
class CapacityRestController {

    private final CommandGateway commandGateway;

    CapacityRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PutMapping("/{courseId}")
    ReservationResult reserveCapacity(
            @PathVariable String courseId,
            @RequestParam int seats
    ) {
        return commandGateway.sendAndWait(
                new ReserveCapacityCommand(courseId, seats),
                ReservationResult.class
        );
    }
}
