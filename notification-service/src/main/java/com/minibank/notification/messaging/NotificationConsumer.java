package com.minibank.notification.messaging;

import com.minibank.notification.service.NotificationService;

import org.springframework.jms.annotation.JmsListener;
import org.springframework.stereotype.Component;

@Component
public class NotificationConsumer {

    private final NotificationService notificationService;

    public NotificationConsumer(
            NotificationService notificationService) {

        this.notificationService =
                notificationService;
    }


    @JmsListener(
            destination = "minibank.notifications"
    )
    public void consume(
            NotificationEvent event) {

        System.out.println(
                "Received notification event: "
                        + event
        );

        notificationService.save(event);
    }
}
