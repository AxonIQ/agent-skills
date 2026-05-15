package com.example.statestored;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.spring.stereotype.Aggregate;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
@Aggregate
public class Customer {

    @Id
    @AggregateIdentifier
    private String customerId;

    private String name;
    private String email;

    @CommandHandler
    public Customer(RegisterCustomerCommand cmd) {
        this.customerId = cmd.customerId();
        this.name = cmd.name();
        this.email = cmd.email();
    }

    @CommandHandler
    public void handle(ChangeEmailCommand cmd) {
        this.email = cmd.newEmail();
    }

    protected Customer() {
    }

    public record RegisterCustomerCommand(String customerId, String name, String email) {}
    public record ChangeEmailCommand(String customerId, String newEmail) {}
}
