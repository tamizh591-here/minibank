package com.minibank.transaction.dto;

import java.math.BigDecimal;

public record TransferRequest(
        String sourceAccount,
        String targetAccount,
        BigDecimal amount
) {
}
