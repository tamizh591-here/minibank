package com.minibank.notification.service;

import com.minibank.notification.messaging.NotificationEvent;
import com.minibank.notification.model.Notification;
import com.minibank.notification.repository.NotificationRepository;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class NotificationService {

    private final NotificationRepository repository;

    public NotificationService(
            NotificationRepository repository) {

        this.repository = repository;
    }


    public Notification save(
            NotificationEvent event) {

        Notification notification =
                new Notification();

        notification.setAccountNumber(
                event.accountNumber()
        );

        notification.setType(
                event.type()
        );

        notification.setAmount(
                event.amount()
        );

        notification.setTargetAccount(
                event.targetAccount()
        );

        notification.setStatus(
                event.status()
        );

        notification.setMessage(
                buildMessage(event)
        );

        return repository.save(notification);
    }


    public List<Notification> getNotifications(
            String accountNumber) {

        return repository
                .findByAccountNumberOrderByCreatedAtDesc(
                        accountNumber
                );
    }


    private String buildMessage(
            NotificationEvent event) {

        return switch (event.type()) {

            case "DEPOSIT" ->
                    "₹" + event.amount()
                            + " deposited successfully.";

            case "WITHDRAW" ->
                    "₹" + event.amount()
                            + " withdrawn successfully.";

            case "TRANSFER" ->
                    "₹" + event.amount()
                            + " transferred successfully to "
                            + event.targetAccount() + ".";

            default ->
                    "Transaction completed successfully.";
        };
    }
}
