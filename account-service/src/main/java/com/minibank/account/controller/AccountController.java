package com.minibank.account.controller;

import com.minibank.account.model.Account;
import com.minibank.account.service.AccountService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.math.BigDecimal;

@RestController
@RequestMapping("/api/accounts")
public class AccountController {

    private final AccountService service;

    public AccountController(AccountService service) {
        this.service = service;
    }

    @GetMapping("/customer/{customerId}")
    public ResponseEntity<?> getAccount(
            @PathVariable Long customerId) {

        Account account =
                service.getOrCreateAccount(customerId);

        return ResponseEntity.ok(Map.of(
                "accountId", account.getId(),
                "customerId", account.getCustomerId(),
                "accountNumber", account.getAccountNumber(),
                "balance", account.getBalance()
        ));
    }
    @PostMapping("/{accountNumber}/deposit")
 public ResponseEntity<?> deposit(
        @PathVariable String accountNumber,
        @RequestBody Map<String, BigDecimal> request) {

    Account account = service.deposit(
            accountNumber,
            request.get("amount")
    );

    return ResponseEntity.ok(Map.of(
            "accountNumber", account.getAccountNumber(),
            "balance", account.getBalance()
    ));
}


	@PostMapping("/{accountNumber}/withdraw")
  public ResponseEntity<?> withdraw(
        @PathVariable String accountNumber,
        @RequestBody Map<String, BigDecimal> request) {

    Account account = service.withdraw(
            accountNumber,
            request.get("amount")
    );

    return ResponseEntity.ok(Map.of(
            "accountNumber", account.getAccountNumber(),
            "balance", account.getBalance()
    ));
}
}
