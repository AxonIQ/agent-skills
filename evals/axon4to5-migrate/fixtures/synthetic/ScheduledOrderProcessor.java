package com.example.jobs;

import com.example.jobs.commands.ProcessPendingOrdersCommand;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
class ScheduledOrderProcessor {

    private final CommandGateway commandGateway;

    ScheduledOrderProcessor(CommandGateway commandGateway) {
        this.commandGateway = commandGateway;
    }

    @Scheduled(fixedDelay = 60_000)
    void processOrders() {
        commandGateway.sendAndWait(new ProcessPendingOrdersCommand());
    }
}
