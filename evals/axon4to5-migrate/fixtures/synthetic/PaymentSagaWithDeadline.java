package com.example.paymentsaga;

import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.deadline.DeadlineManager;
import org.axonframework.deadline.annotation.DeadlineHandler;
import org.axonframework.modelling.saga.EndSaga;
import org.axonframework.modelling.saga.SagaEventHandler;
import org.axonframework.modelling.saga.SagaLifecycle;
import org.axonframework.modelling.saga.StartSaga;
import org.axonframework.spring.stereotype.Saga;
import org.springframework.beans.factory.annotation.Autowired;

import java.time.Duration;

@Saga
public class PaymentSagaWithDeadline {

    @Autowired
    private transient CommandGateway commandGateway;

    @Autowired
    private transient DeadlineManager deadlineManager;

    private String bikeId;
    private String renter;

    @StartSaga
    @SagaEventHandler(associationProperty = "bikeId")
    public void on(BikeRequestedEvent event) {
        this.bikeId = event.bikeId();
        this.renter = event.renter();
        SagaLifecycle.associateWith("paymentReference", event.rentalReference());
        commandGateway.send(new PreparePaymentCommand(10, event.rentalReference()));
    }

    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentPreparedEvent event) {
        deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.paymentId());
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentConfirmedEvent event) {
        commandGateway.send(new ApproveRequestCommand(bikeId, renter));
    }

    @EndSaga
    @SagaEventHandler(associationProperty = "paymentReference")
    public void on(PaymentRejectedEvent event) {
        commandGateway.send(new RejectRequestCommand(bikeId, renter));
    }

    @DeadlineHandler(deadlineName = "cancelPayment")
    public void cancelPayment(String paymentId) {
        commandGateway.send(new RejectPaymentCommand(paymentId));
    }

    public record BikeRequestedEvent(String bikeId, String rentalReference, String renter) {}
    public record PaymentPreparedEvent(String paymentReference, String paymentId) {}
    public record PaymentConfirmedEvent(String paymentReference) {}
    public record PaymentRejectedEvent(String paymentReference) {}
    public record ApproveRequestCommand(String bikeId, String renter) {}
    public record RejectRequestCommand(String bikeId, String renter) {}
    public record PreparePaymentCommand(int amount, String rentalReference) {}
    public record RejectPaymentCommand(String paymentId) {}
}
