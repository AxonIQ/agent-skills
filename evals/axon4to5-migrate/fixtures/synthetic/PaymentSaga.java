package com.example.payment;

import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.spring.stereotype.Saga;

@Saga
public class PaymentSaga {

    private transient CommandGateway commandGateway;

    private String paymentId;

    @StartSaga
    @SagaEventHandler(associationProperty = "paymentId")
    public void on(PaymentRequestedEvent event) {
        this.paymentId = event.paymentId();
        commandGateway.send(new ChargeCardCommand(event.paymentId(), event.amount()));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentId")
    public void on(PaymentCompletedEvent event) {
    }

    public record PaymentRequestedEvent(String paymentId, int amount) {}
    public record PaymentCompletedEvent(String paymentId) {}
    public record ChargeCardCommand(String paymentId, int amount) {}
}
