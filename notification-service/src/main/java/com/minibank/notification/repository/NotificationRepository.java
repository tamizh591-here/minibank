package com.minibank.notification.repository;

import com.minibank.notification.model.Notification;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NotificationRepository
        extends JpaRepository<Notification, Long> {

    List<Notification>
    findByAccountNumberOrderByCreatedAtDesc(
            String accountNumber
    );
}
