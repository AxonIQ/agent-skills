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
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.axonframework.commandhandling.gateway.CommandGateway;
import org.axonframework.eventhandling.annotation.EventHandler;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

/**
 * AF5 migration of the former {@code PaymentSaga}.
 *
 * AF5 has no Saga SPI; this is reimplemented as a Spring {@code @Component} with
 * {@code @EventHandler} methods that read/write per-payment state in a JPA repository.
 *
 * Deadlines are replaced by:
 *   - {@code cancelPayment}  -> a {@code cancelAt} timestamp polled by a {@code @Scheduled} sweeper
 *   - {@code retryPayment}   -> a {@code retryAt}  timestamp polled by the same sweeper
 *
 * Cancellation (formerly {@code deadlineManager.cancelAllWithinScope}) is done by
 * nulling the timestamp columns / marking the row terminated.
 */
@Component
public class PaymentSaga {

    private final CommandGateway commandGateway;
    private final PaymentStateRepository repository;

    @Autowired
    public PaymentSaga(CommandGateway commandGateway,
                       PaymentStateRepository repository) {
        this.commandGateway = commandGateway;
        this.repository = repository;
    }

    // ---------------------------------------------------------------------
    // Event handlers (replace @SagaEventHandler / @StartSaga / @EndSaga)
    // ---------------------------------------------------------------------

    /** Was @StartSaga @SagaEventHandler(associationProperty = "bikeId"). */
    @EventHandler
    @Transactional
    public void on(BikeRequestedEvent event) {
        PaymentState state = repository.findById(event.getRentalReference())
                                       .orElseGet(PaymentState::new);
        state.setPaymentReference(event.getRentalReference());
        state.setBikeId(event.getBikeId());
        state.setRenter(event.getRenter());
        state.setTerminated(false);
        repository.save(state);

        preparePayment(event.getRentalReference());
    }

    /** Was @EndSaga @SagaEventHandler(associationProperty = "paymentReference"). */
    @EventHandler
    @Transactional
    public void on(PaymentConfirmedEvent event) {
        Optional<PaymentState> maybe = repository.findById(event.getPaymentId());
        if (maybe.isEmpty()) {
            return;
        }
        PaymentState state = maybe.get();
        commandGateway.send(new ApproveRequestCommand(state.getBikeId(), state.getRenter()));
        endSaga(state);
    }

    /** Was @SagaEventHandler(associationProperty = "paymentReference"). */
    @EventHandler
    @Transactional
    public void on(PaymentRejectedEvent event) {
        repository.findById(event.getPaymentId()).ifPresent(state -> {
            commandGateway.send(new RejectRequestCommand(state.getBikeId(), state.getRenter()));
            endSaga(state);
        });
    }

    /** Was @EndSaga @SagaEventHandler(associationProperty = "bikeId"). */
    @EventHandler
    @Transactional
    public void on(RequestRejectedEvent event) {
        // Was: deadlineManager.cancelAllWithinScope("cancelPayment");
        for (PaymentState state : repository.findByBikeIdAndTerminatedFalse(event.getBikeId())) {
            state.setCancelAt(null);
            state.setRetryAt(null);
            endSaga(state);
        }
    }

    /** Was @SagaEventHandler(associationProperty = "paymentReference"). */
    @EventHandler
    @Transactional
    public void on(PaymentPreparedEvent event) {
        repository.findById(event.getPaymentId()).ifPresent(state -> {
            // Was: deadlineManager.schedule(Duration.ofSeconds(30), "cancelPayment", event.getPaymentId());
            state.setCancelAt(Instant.now().plusSeconds(30));
            repository.save(state);
        });
    }

    // ---------------------------------------------------------------------
    // Scheduled sweeper (replaces @DeadlineHandler)
    // ---------------------------------------------------------------------

    /**
     * Replaces the {@code cancelPayment} and {@code retryPayment} deadline handlers.
     * Polls due rows and fires the appropriate command.
     */
    @Scheduled(fixedDelay = 1000L)
    @Transactional
    public void sweepDeadlines() {
        Instant now = Instant.now();

        // cancelPayment deadline
        for (PaymentState state : repository.findByCancelAtLessThanEqualAndTerminatedFalse(now)) {
            String paymentId = state.getPaymentReference();
            state.setCancelAt(null);
            repository.save(state);
            commandGateway.send(new RejectPaymentCommand(paymentId));
        }

        // retryPayment deadline
        for (PaymentState state : repository.findByRetryAtLessThanEqualAndTerminatedFalse(now)) {
            String rentalReference = state.getPaymentReference();
            state.setRetryAt(null);
            repository.save(state);
            preparePayment(rentalReference);
        }
    }

    // ---------------------------------------------------------------------
    // Internals
    // ---------------------------------------------------------------------

    private void preparePayment(String rentalReference) {
        commandGateway.send(new PreparePaymentCommand(10, rentalReference))
                      .whenComplete((r, e) -> {
                          if (e != null) {
                              // Was: deadlineManager.schedule(Duration.ofSeconds(5), "retryPayment", rentalReference, scope);
                              scheduleRetry(rentalReference);
                          }
                      });
    }

    @Transactional
    protected void scheduleRetry(String rentalReference) {
        repository.findById(rentalReference).ifPresent(state -> {
            state.setRetryAt(Instant.now().plusSeconds(5));
            repository.save(state);
        });
    }

    private void endSaga(PaymentState state) {
        state.setTerminated(true);
        state.setCancelAt(null);
        state.setRetryAt(null);
        repository.save(state);
    }

    // ---------------------------------------------------------------------
    // JPA entity — one row per payment / saga instance
    // ---------------------------------------------------------------------

    @Entity
    @Table(name = "payment_saga_state")
    public static class PaymentState {

        /** Equivalent to the former "paymentReference" association. */
        @Id
        private String paymentReference;

        /** Equivalent to the former "bikeId" association. */
        private String bikeId;

        private String renter;

        /** Timestamp at which the cancelPayment deadline is due (null = not scheduled). */
        private Instant cancelAt;

        /** Timestamp at which the retryPayment deadline is due (null = not scheduled). */
        private Instant retryAt;

        /** True after the saga has ended (replaces @EndSaga). */
        private boolean terminated;

        public PaymentState() {
        }

        public String getPaymentReference() {
            return paymentReference;
        }

        public void setPaymentReference(String paymentReference) {
            this.paymentReference = paymentReference;
        }

        public String getBikeId() {
            return bikeId;
        }

        public void setBikeId(String bikeId) {
            this.bikeId = bikeId;
        }

        public String getRenter() {
            return renter;
        }

        public void setRenter(String renter) {
            this.renter = renter;
        }

        public Instant getCancelAt() {
            return cancelAt;
        }

        public void setCancelAt(Instant cancelAt) {
            this.cancelAt = cancelAt;
        }

        public Instant getRetryAt() {
            return retryAt;
        }

        public void setRetryAt(Instant retryAt) {
            this.retryAt = retryAt;
        }

        public boolean isTerminated() {
            return terminated;
        }

        public void setTerminated(boolean terminated) {
            this.terminated = terminated;
        }
    }

    // ---------------------------------------------------------------------
    // Spring Data JPA repository — keyed by paymentReference
    // ---------------------------------------------------------------------

    @Repository
    public interface PaymentStateRepository extends JpaRepository<PaymentState, String> {

        List<PaymentState> findByBikeIdAndTerminatedFalse(String bikeId);

        List<PaymentState> findByCancelAtLessThanEqualAndTerminatedFalse(Instant now);

        List<PaymentState> findByRetryAtLessThanEqualAndTerminatedFalse(Instant now);
    }
}
