package com.minibank.transaction.client;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.util.Map;

@Component
public class AccountClient {

    private final RestClient restClient;

    public AccountClient(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("http://localhost:8082/account-service/api/accounts")
                .build();
    }

    public Map deposit(String accountNumber, BigDecimal amount) {

        return restClient.post()
                .uri("/{accountNumber}/deposit", accountNumber)
                .body(Map.of("amount", amount))
                .retrieve()
                .body(Map.class);
    }

    public Map withdraw(String accountNumber, BigDecimal amount) {

        return restClient.post()
                .uri("/{accountNumber}/withdraw", accountNumber)
                .body(Map.of("amount", amount))
                .retrieve()
                .body(Map.class);
    }
}
