package com.example.ingest;

import org.axonframework.eventhandling.EventBus;
import org.axonframework.eventhandling.GenericEventMessage;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * AF4 REST controller that publishes an event to the EventBus from outside any aggregate.
 * Migration target: AF4 EventBus -> AF5 EventSink, field rename eventBus -> eventSink.
 */
@RestController
public class ExternalEventPublisher {

    private final EventBus eventBus;

    public ExternalEventPublisher(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    @PostMapping("/orders/ingest")
    public void ingest(@RequestBody OrderImported event) {
        eventBus.publish(new GenericEventMessage<>(event));
    }

    public record OrderImported(String orderId, String source) {
    }
}
