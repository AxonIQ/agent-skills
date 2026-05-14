package io.axoniq.demo.bikerental.rental.paymentsaga;

import io.axoniq.demo.bikerental.coreapi.payment.PaymentConfirmedEvent;
import io.axoniq.demo.bikerental.coreapi.payment.PaymentPreparedEvent;
import io.axoniq.demo.bikerental.coreapi.payment.PaymentRejectedEvent;
import io.axoniq.demo.bikerental.coreapi.payment.PreparePaymentCommand;
import io.axoniq.demo.bikerental.coreapi.payment.RejectPaymentCommand;
import io.axoniq.demo.bikerental.coreapi.rental.ApproveRequestCommand;
import io.axoniq.demo.bikerental.coreapi.rental.BikeRequestedEvent;
import io.axoniq.demo.bikerental.coreapi.rental.RejectRequestCommand;
import io.axoniq.demo.bikerental.coreapi.rental.RequestRejectedEvent;
import org.axonframework.eventhandling.annotation.DisallowReplay;
import org.axonframework.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.List;
import java.util.Optional;

@Component
@DisallowReplay
public class PaymentSaga {

    private static final Duration PAYMENT_TIMEOUT = Duration.ofSeconds(30);
    private static final Duration RETRY_DELAY = Duration.ofSeconds(5);

    private final PaymentStateRepository repository;

    public PaymentSaga(PaymentStateRepository repository) {
        this.repository = repository;
    }

    @EventHandler
    public void on(BikeRequestedEvent event, CommandDispatcher commandDispatcher) {
        PaymentState state = new PaymentState(event.getRentalReference());
        state.setBikeId(event.getBikeId());
        state.setRenter(event.getRenter());
        repository.save(state);
        commandDispatcher.send(new PreparePaymentCommand(10, event.getRentalReference()));
    }

    @EventHandler
    public void on(PaymentPreparedEvent event) {
        repository.findById(event.getPaymentReference()).ifPresent(state -> {
            state.setPaymentId(event.getPaymentId());
            state.setStatus(PaymentState.Status.PREPARED);
            state.setTimestamp(System.currentTimeMillis());
            repository.save(state);
        });
    }

    @EventHandler
    public void on(PaymentConfirmedEvent event, CommandDispatcher commandDispatcher) {
        Optional<PaymentState> opt = repository.findById(event.getPaymentReference());
        if (opt.isEmpty()) {
            return;
        }
        PaymentState state = opt.get();
        state.setStatus(PaymentState.Status.CONFIRMED);
        repository.save(state);
        commandDispatcher.send(new ApproveRequestCommand(state.getBikeId(), state.getRenter()));
    }

    @EventHandler
    public void on(PaymentRejectedEvent event, CommandDispatcher commandDispatcher) {
        Optional<PaymentState> opt = repository.findById(event.getPaymentReference());
        if (opt.isEmpty()) {
            return;
        }
        PaymentState state = opt.get();
        state.setStatus(PaymentState.Status.REJECTED);
        repository.save(state);
        commandDispatcher.send(new RejectRequestCommand(state.getBikeId(), state.getRenter()));
    }

    @EventHandler
    public void on(RequestRejectedEvent event) {
        repository.findAllByBikeIdAndStatusIn(
                event.getBikeId(),
                List.of(PaymentState.Status.PENDING, PaymentState.Status.PREPARED)
        ).forEach(state -> {
            state.setStatus(PaymentState.Status.CANCELLED);
            repository.save(state);
        });
    }

    @Scheduled(fixedDelay = 1000L)
    @Transactional
    public void cancelLatePayments() {
        long cutoff = System.currentTimeMillis() - PAYMENT_TIMEOUT.toMillis();
        List<PaymentState> late = repository.findAllByTimestampLessThanAndStatusIn(
                cutoff,
                List.of(PaymentState.Status.PENDING, PaymentState.Status.PREPARED)
        );
        for (PaymentState state : late) {
            if (state.getPaymentId() != null) {
                // delegate via Spring scheduler — dispatched out-of-band of the event handler
                commandSender().send(new RejectPaymentCommand(state.getPaymentId()));
            } else {
                state.setStatus(PaymentState.Status.CANCELLED);
                repository.save(state);
            }
        }
    }

    @Scheduled(fixedDelay = 5000L)
    @Transactional
    public void retryPendingPayments() {
        long cutoff = System.currentTimeMillis() - RETRY_DELAY.toMillis();
        List<PaymentState> stuck = repository.findAllByTimestampLessThanAndStatusIn(
                cutoff,
                List.of(PaymentState.Status.PENDING)
        );
        for (PaymentState state : stuck) {
            state.setTimestamp(System.currentTimeMillis());
            repository.save(state);
            commandSender().send(new PreparePaymentCommand(10, state.getPaymentReference()));
        }
    }

    // CommandDispatcher injected per-handler; out-of-band sweeps obtain it via a setter or a separate
    // dispatcher bean. Project wiring decides; placeholder accessor below isolates the dependency.
    private CommandDispatcher commandDispatcher;

    public void setCommandDispatcher(CommandDispatcher commandDispatcher) {
        this.commandDispatcher = commandDispatcher;
    }

    private CommandDispatcher commandSender() {
        return commandDispatcher;
    }
}
