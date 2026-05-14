package com.dddheroes.heroesofddd;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;

@SpringBootApplication
@EntityScan(basePackages = {
		"com.dddheroes.heroesofddd",
		"org.axonframework.eventsourcing.eventstore.jpa",
		"org.axonframework.eventstreaming.tokenstore.jpa",
		"org.axonframework.messaging.deadletter.jpa"
})
public class HeroesOfDDDApplication {

	public static void main(String[] args) {
		SpringApplication.run(HeroesOfDDDApplication.class, args);
	}

}
