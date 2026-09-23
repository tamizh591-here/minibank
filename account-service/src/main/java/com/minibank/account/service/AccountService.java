package com.minibank.account.service;

import com.minibank.account.model.Account;
import com.minibank.account.repository.AccountRepository;

import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Service
public class AccountService {

    private final AccountRepository repository;

    public AccountService(AccountRepository repository) {
        this.repository = repository;
    }

    public Account getOrCreateAccount(Long customerId) {

        return repository.findByCustomerId(customerId)
                .orElseGet(() -> createAccount(customerId));
    }

    private Account createAccount(Long customerId) {

        Account account = new Account();

        account.setCustomerId(customerId);

        account.setAccountNumber(
                String.format("MB%08d", customerId)
        );

        account.setBalance(BigDecimal.ZERO);

        return repository.save(account);
    }

    public Account deposit(String accountNumber, BigDecimal amount) {

    if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
        throw new RuntimeException("Amount must be greater than zero");
    }

    Account account = repository.findByAccountNumber(accountNumber)
            .orElseThrow(() -> new RuntimeException("Account not found"));

    account.setBalance(
            account.getBalance().add(amount)
    );

    return repository.save(account);
}


    public Account withdraw(String accountNumber, BigDecimal amount) {

    if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
        throw new RuntimeException("Amount must be greater than zero");
    }

    Account account = repository.findByAccountNumber(accountNumber)
            .orElseThrow(() -> new RuntimeException("Account not found"));

    if (account.getBalance().compareTo(amount) < 0) {
        throw new RuntimeException("Insufficient balance");
    }

    account.setBalance(
            account.getBalance().subtract(amount)
    );

    return repository.save(account);
}
}
