package io.example.handlers;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.interceptors.MessageHandlerInterceptor;
import org.springframework.stereotype.Component;

@Component
public class AnnotationInterceptorHandler {

    @CommandHandler
    public String handle(CreateOrderCommand cmd) {
        return "order-" + cmd.getOrderId();
    }

    @MessageHandlerInterceptor(messageType = CommandMessage.class)
    public Object intercept(CommandMessage<?> message, InterceptorChain chain) throws Exception {
        // inline interceptor declared via annotation — not supported in AF5 < 5.2.0
        return chain.proceed();
    }
}
