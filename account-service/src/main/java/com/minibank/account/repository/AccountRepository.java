package com.minibank.account.repository;

import com.minibank.account.model.Account;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AccountRepository
        extends JpaRepository<Account, Long> {

    Optional<Account> findByCustomerId(Long customerId);

    Optional<Account> findByAccountNumber(String accountNumber);
}
