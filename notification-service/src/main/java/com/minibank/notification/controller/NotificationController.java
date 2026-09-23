package com.minibank.notification.controller;

import com.minibank.notification.model.Notification;
import com.minibank.notification.service.NotificationService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    private final NotificationService notificationService;

    public NotificationController(
            NotificationService notificationService) {

        this.notificationService =
                notificationService;
    }


    @GetMapping("/account/{accountNumber}")
    public ResponseEntity<List<Notification>> getNotifications(
            @PathVariable String accountNumber) {

        List<Notification> notifications =
                notificationService.getNotifications(
                        accountNumber
                );

        return ResponseEntity.ok(
                notifications
        );
    }
}
