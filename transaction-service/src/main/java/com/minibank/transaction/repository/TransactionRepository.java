package com.minibank.transaction.repository;

import com.minibank.transaction.model.BankTransaction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TransactionRepository
        extends JpaRepository<BankTransaction, Long> {

    List<BankTransaction> findByAccountNumberOrderByCreatedAtDesc(
            String accountNumber
    );
}
