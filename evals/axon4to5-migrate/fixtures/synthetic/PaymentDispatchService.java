package com.example.payment.service;

import org.axonframework.queryhandling.QueryGateway;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
public class PaymentDispatchService {

    private final QueryGateway queryGateway;

    public PaymentDispatchService(QueryGateway queryGateway) {
        this.queryGateway = queryGateway;
    }

    public CompletableFuture<PaymentStatus> getStatus(String paymentId) {
        return queryGateway.query(new GetPaymentStatus(paymentId), PaymentStatus.class);
    }
}
