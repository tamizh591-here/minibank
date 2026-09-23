package com.minibank.customer.dto;

public record LoginRequest(
        String email,
        String password
) {}
