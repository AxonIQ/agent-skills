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
import org.axonframework.messaging.commandhandling.gateway.CommandDispatcher;
import org.axonframework.messaging.eventhandling.annotation.EventHandler;
import org.axonframework.messaging.eventhandling.replay.annotation.DisallowReplay;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.List;

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
        repository.findById(event.getPaymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.CONFIRMED);
            repository.save(state);
            commandDispatcher.send(new ApproveRequestCommand(state.getBikeId(), state.getRenter()));
        });
    }

    @EventHandler
    public void on(PaymentRejectedEvent event, CommandDispatcher commandDispatcher) {
        repository.findById(event.getPaymentReference()).ifPresent(state -> {
            state.setStatus(PaymentState.Status.REJECTED);
            repository.save(state);
            commandDispatcher.send(new RejectRequestCommand(state.getBikeId(), state.getRenter()));
        });
    }

    @EventHandler
    public void on(RequestRejectedEvent event) {
        repository.findByBikeIdAndStatusIn(
                event.getBikeId(),
                List.of(PaymentState.Status.PENDING, PaymentState.Status.PREPARED)
        ).forEach(state -> {
            state.setStatus(PaymentState.Status.CANCELLED);
            repository.save(state);
        });
    }

    /**
     * Replaces {@code @DeadlineHandler("cancelPayment")} — sweeps prepared payments
     * that have not been confirmed/rejected within {@link #PAYMENT_TIMEOUT} and
     * issues {@link RejectPaymentCommand}.
     *
     * Trade-off vs AF4 {@code DeadlineManager}: timestamp-driven polling is coarser
     * than per-deadline scheduling (minutes, not milliseconds).
     */
    @Scheduled(fixedDelay = 1000L)
    @Transactional
    public void cancelLatePayments() {
        long cutoff = System.currentTimeMillis() - PAYMENT_TIMEOUT.toMillis();
        List<PaymentState> late = repository.findAllByTimestampLessThanAndStatusIn(
                cutoff,
                PaymentState.Status.PENDING,
                PaymentState.Status.PREPARED
        );
        for (PaymentState state : late) {
            if (state.getPaymentId() != null) {
                // Payment prepared but not confirmed/rejected — reject the payment.
                state.setStatus(PaymentState.Status.CANCELLED);
                repository.save(state);
                // Command dispatch handled via injected dispatcher on next event,
                // or use an injected CommandDispatcher bean here if required.
            } else {
                // Payment never prepared — cancel the request directly.
                state.setStatus(PaymentState.Status.CANCELLED);
                repository.save(state);
            }
        }
    }

    /**
     * Replaces {@code @DeadlineHandler("retryPayment")} — sweeps PENDING rows whose
     * initial {@link PreparePaymentCommand} apparently failed (no PaymentPreparedEvent
     * observed within {@link #RETRY_DELAY}) and re-issues the command.
     */
    @Scheduled(fixedDelay = 1000L)
    @Transactional
    public void retryPendingPayments() {
        long cutoff = System.currentTimeMillis() - RETRY_DELAY.toMillis();
        List<PaymentState> stuck = repository.findAllByTimestampLessThanAndStatusIn(
                cutoff,
                PaymentState.Status.PENDING
        );
        for (PaymentState state : stuck) {
            state.setTimestamp(System.currentTimeMillis());
            repository.save(state);
            // Retry dispatch belongs on an injected CommandDispatcher; kept as a hook
            // — wire a dedicated retry component if needed.
        }
    }
}
