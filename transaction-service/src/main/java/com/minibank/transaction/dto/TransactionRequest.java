package com.minibank.transaction.dto;

import java.math.BigDecimal;

public record TransactionRequest(
        String accountNumber,
        BigDecimal amount
) {}
