package com.minibank.transaction.service;

import com.minibank.transaction.client.AccountClient;
import com.minibank.transaction.messaging.NotificationEvent;
import com.minibank.transaction.messaging.NotificationProducer;
import com.minibank.transaction.model.BankTransaction;
import com.minibank.transaction.repository.TransactionRepository;

import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;

@Service
public class TransactionService {

    private final TransactionRepository repository;
    private final AccountClient accountClient;
    private final NotificationProducer notificationProducer;


    // ==========================================
    // CONSTRUCTOR INJECTION
    // ==========================================
    public TransactionService(
            TransactionRepository repository,
            AccountClient accountClient,
            NotificationProducer notificationProducer) {

        this.repository = repository;
        this.accountClient = accountClient;
        this.notificationProducer = notificationProducer;
    }


    // ==========================================
    // DEPOSIT
    // ==========================================
    public BankTransaction deposit(
            String accountNumber,
            BigDecimal amount) {

        validateAmount(amount);

        // Call Account Service
        accountClient.deposit(
                accountNumber,
                amount
        );

        // Save transaction in database
        BankTransaction transaction =
                saveTransaction(
                        accountNumber,
                        "DEPOSIT",
                        amount
                );

        // Publish notification event to ActiveMQ
        sendNotification(transaction);

        return transaction;
    }


    // ==========================================
    // WITHDRAW
    // ==========================================
    public BankTransaction withdraw(
            String accountNumber,
            BigDecimal amount) {

        validateAmount(amount);

        // Call Account Service
        accountClient.withdraw(
                accountNumber,
                amount
        );

        // Save transaction in database
        BankTransaction transaction =
                saveTransaction(
                        accountNumber,
                        "WITHDRAW",
                        amount
                );

        // Publish notification event to ActiveMQ
        sendNotification(transaction);

        return transaction;
    }


    // ==========================================
    // TRANSFER
    // ==========================================
    public BankTransaction transfer(
            String sourceAccount,
            String targetAccount,
            BigDecimal amount) {

        validateAmount(amount);

        if (sourceAccount.equals(targetAccount)) {

            throw new RuntimeException(
                    "Source and target accounts cannot be same"
            );
        }


        // Step 1:
        // Withdraw money from source account
        accountClient.withdraw(
                sourceAccount,
                amount
        );


        try {

            // Step 2:
            // Deposit money into target account
            accountClient.deposit(
                    targetAccount,
                    amount
            );

        } catch (Exception e) {

            /*
             * V1 Compensation Logic
             *
             * If depositing into the target account fails,
             * return the withdrawn amount back to source.
             */

            accountClient.deposit(
                    sourceAccount,
                    amount
            );

            throw new RuntimeException(
                    "Transfer failed. Amount returned to source account."
            );
        }


        // Step 3:
        // Create transaction record
        BankTransaction transaction =
                new BankTransaction();

        transaction.setAccountNumber(
                sourceAccount
        );

        transaction.setTargetAccount(
                targetAccount
        );

        transaction.setType(
                "TRANSFER"
        );

        transaction.setAmount(
                amount
        );

        transaction.setStatus(
                "SUCCESS"
        );


        // Step 4:
        // Save transaction
        BankTransaction savedTransaction =
                repository.save(transaction);


        // Step 5:
        // Publish event to ActiveMQ
        sendNotification(savedTransaction);


        return savedTransaction;
    }


    // ==========================================
    // TRANSACTION HISTORY
    // ==========================================
    public List<BankTransaction> getHistory(
            String accountNumber) {

        return repository
                .findByAccountNumberOrderByCreatedAtDesc(
                        accountNumber
                );
    }


    // ==========================================
    // SAVE DEPOSIT / WITHDRAW TRANSACTION
    // ==========================================
    private BankTransaction saveTransaction(
            String accountNumber,
            String type,
            BigDecimal amount) {

        BankTransaction transaction =
                new BankTransaction();

        transaction.setAccountNumber(
                accountNumber
        );

        transaction.setType(
                type
        );

        transaction.setAmount(
                amount
        );

        transaction.setStatus(
                "SUCCESS"
        );


        return repository.save(
                transaction
        );
    }


    // ==========================================
    // VALIDATE TRANSACTION AMOUNT
    // ==========================================
    private void validateAmount(
            BigDecimal amount) {

        if (amount == null ||
                amount.compareTo(BigDecimal.ZERO) <= 0) {

            throw new RuntimeException(
                    "Amount must be greater than zero"
            );
        }
    }


    // ==========================================
    // ACTIVEMQ NOTIFICATION PRODUCER
    // ==========================================
    private void sendNotification(
            BankTransaction transaction) {

        NotificationEvent event =
                new NotificationEvent(

                        transaction.getAccountNumber(),

                        transaction.getType(),

                        transaction.getAmount(),

                        transaction.getTargetAccount(),

                        transaction.getStatus()
                );


        notificationProducer.send(
                event
        );
    }
}
