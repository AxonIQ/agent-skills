package com.example.orders.api;

import com.example.orders.commands.CreateOrderCommand;
import com.example.orders.shared.RequestContext;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/orders")
class OrderRestController {

    private final CommandGateway commandGateway;

    OrderRestController(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @PostMapping
    CompletableFuture<Void> createOrder(
            @RequestHeader("X-User-Id") String userId,
            @RequestBody OrderRequest body
    ) {
        var command = new CreateOrderCommand(body.orderId(), body.product());
        return commandGateway.send(command, RequestContext.with(userId));
    }
}
