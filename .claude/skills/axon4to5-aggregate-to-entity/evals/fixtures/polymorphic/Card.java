package fixtures.polymorphic;

import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateRoot;

@AggregateRoot
public abstract class Card {

    @AggregateIdentifier
    protected String cardId;

    protected int balance;

    protected Card() {
    }

    public String getCardId() {
        return cardId;
    }

    public int getBalance() {
        return balance;
    }
}
