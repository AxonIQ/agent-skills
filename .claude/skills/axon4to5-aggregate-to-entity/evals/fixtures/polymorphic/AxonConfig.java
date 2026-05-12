package fixtures.polymorphic;

import org.axonframework.config.AggregateConfigurer;
import org.axonframework.config.Configurer;
import org.axonframework.config.DefaultConfigurer;

import java.util.Set;

public class AxonConfig {

    public Configurer buildConfigurer() {
        Configurer configurer = DefaultConfigurer.defaultConfiguration();

        Set<Class<? extends GiftCard>> subtypes = Set.of(
                OpenLoopGiftCard.class,
                RechargeableGiftCard.class
        );

        configurer.configureAggregate(
                AggregateConfigurer.defaultConfiguration(GiftCard.class)
                                   .withSubtypes(subtypes)
        );

        return configurer;
    }
}
