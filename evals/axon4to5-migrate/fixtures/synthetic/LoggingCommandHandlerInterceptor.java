package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    private static final Logger logger = LoggerFactory.getLogger(LoggingCommandHandlerInterceptor.class);

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> command = unitOfWork.getMessage();
        logger.info("Handling command: {}", command.getCommandName());

        unitOfWork.onCommit(uow -> {
            logger.info("Command committed: {}", command.getCommandName());
        });

        unitOfWork.onRollback(uow -> {
            logger.error("Command rolled back: {}", command.getCommandName());
        });

        return interceptorChain.proceed();
    }
}
