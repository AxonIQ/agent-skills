package io.example.interceptors;

import org.axonframework.commandhandling.CommandMessage;
import org.axonframework.messaging.InterceptorChain;
import org.axonframework.messaging.MessageHandlerInterceptor;
import org.axonframework.messaging.unitofwork.UnitOfWork;

public class AuditCommandHandlerInterceptor implements MessageHandlerInterceptor<CommandMessage<?>> {

    @Override
    public Object handle(UnitOfWork<? extends CommandMessage<?>> unitOfWork,
                         InterceptorChain interceptorChain) throws Exception {
        CommandMessage<?> command = unitOfWork.getMessage();
        // pre-handle audit: record command type
        String commandName = command.getCommandName();

        unitOfWork.onPrepareCommit(uow -> {
            // capture audit snapshot before commit
        });

        unitOfWork.onCommit(uow -> {
            // persist audit record on successful commit
        });

        Object result = interceptorChain.proceed();
        return result;
    }
}
