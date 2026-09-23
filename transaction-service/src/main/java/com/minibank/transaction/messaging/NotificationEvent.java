package com.minibank.transaction.messaging;

import java.math.BigDecimal;

public record NotificationEvent(
        String accountNumber,
        String type,
        BigDecimal amount,
        String targetAccount,
        String status
) {
}
