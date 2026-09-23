package com.minibank.transaction.messaging;

import org.springframework.jms.core.JmsTemplate;
import org.springframework.stereotype.Component;

@Component
public class NotificationProducer {

    private static final String QUEUE =
            "minibank.notifications";

    private final JmsTemplate jmsTemplate;

    public NotificationProducer(JmsTemplate jmsTemplate) {
        this.jmsTemplate = jmsTemplate;
    }

    public void send(NotificationEvent event) {

        jmsTemplate.convertAndSend(
                QUEUE,
                event
        );
    }
}
