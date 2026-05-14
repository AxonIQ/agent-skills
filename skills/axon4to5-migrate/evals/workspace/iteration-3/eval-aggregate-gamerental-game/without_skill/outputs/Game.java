package io.axoniq.demo.gamerental.command;

import io.axoniq.demo.gamerental.coreapi.ExceptionStatusCode;
import io.axoniq.demo.gamerental.coreapi.GameRegisteredEvent;
import io.axoniq.demo.gamerental.coreapi.GameRentedEvent;
import io.axoniq.demo.gamerental.coreapi.GameReturnedEvent;
import io.axoniq.demo.gamerental.coreapi.RegisterGameCommand;
import io.axoniq.demo.gamerental.coreapi.RentGameCommand;
import io.axoniq.demo.gamerental.coreapi.RentalCommandException;
import io.axoniq.demo.gamerental.coreapi.ReturnGameCommand;
import org.axonframework.commandhandling.annotation.CommandHandler;
import org.axonframework.eventhandling.EventHandler;
import org.axonframework.eventsourcing.annotation.EventSourcedEntity;
import org.axonframework.eventsourcing.annotation.EventCriteriaBuilder;
import org.axonframework.eventstreaming.EventCriteria;
import org.axonframework.eventstreaming.Tag;
import org.axonframework.messaging.interceptors.ExceptionHandler;
import org.axonframework.modelling.annotation.EntityId;
import org.axonframework.modelling.command.EntityEvolver;

import java.time.Instant;
import java.util.HashSet;
import java.util.Set;

@EventSourcedEntity
class Game {

    @EntityId
    private String gameIdentifier;
    private int stock;
    private Instant releaseDate;
    private Set<String> renters = new HashSet<>();

    public Game() {
        // Required by Axon
    }

    @EventCriteriaBuilder
    static EventCriteria resolveCriteria(String gameIdentifier) {
        return EventCriteria.havingTags(Tag.of("Game", gameIdentifier));
    }

    @CommandHandler
    public static Game handle(RegisterGameCommand command, EventAppender eventAppender) {
        eventAppender.append(new GameRegisteredEvent(command.getGameIdentifier(),
                                                     command.getTitle(),
                                                     command.getReleaseDate(),
                                                     command.getDescription(),
                                                     command.isSingleplayer(),
                                                     command.isMultiplayer()));
        return new Game();
    }

    @CommandHandler
    public void handle(RentGameCommand command, EventAppender eventAppender) {
        if (stock <= 0) {
            throw new IllegalStateException(
                    "Insufficient items in stock for game with identifier [" + gameIdentifier + "]"
            );
        }
        if (Instant.now().isBefore(releaseDate)) {
            throw new IllegalStateException(
                    "Game with identifier [" + gameIdentifier + "] cannot be rented out as it has not been released yet"
            );
        }
        eventAppender.append(new GameRentedEvent(gameIdentifier, command.getRenter()));
    }

    @CommandHandler
    public void handle(ReturnGameCommand command, EventAppender eventAppender) {
        if (!renters.contains(command.getReturner())) {
            throw new IllegalStateException("A game should be returned by someone who has actually rented it");
        }
        eventAppender.append(new GameReturnedEvent(gameIdentifier, command.getReturner()));
    }

    @EventHandler
    public void on(GameRegisteredEvent event) {
        this.gameIdentifier = event.getGameIdentifier();
        this.stock = 1;
        this.releaseDate = event.getReleaseDate();
        this.renters = new HashSet<>();
    }

    @EventHandler
    public void on(GameRentedEvent event) {
        this.stock--;
        this.renters.add(event.getRenter());
    }

    @EventHandler
    public void on(GameReturnedEvent event) {
        this.stock++;
        this.renters.remove(event.getReturner());
    }

    @ExceptionHandler(resultType = IllegalStateException.class)
    public void handle(IllegalStateException exception) {
        ExceptionStatusCode statusCode;
        if (exception.getMessage().contains("Insufficient")) {
            statusCode = ExceptionStatusCode.INSUFFICIENT;
        } else if (exception.getMessage().contains("not been released")) {
            statusCode = ExceptionStatusCode.UNRELEASED;
        } else if (exception.getMessage().contains("actually rented it")) {
            statusCode = ExceptionStatusCode.DIFFERENT_RETURNER;
        } else {
            statusCode = ExceptionStatusCode.UNKNOWN_EXCEPTION;
        }
        throw new RentalCommandException(exception.getMessage(), exception, statusCode);
    }
}
