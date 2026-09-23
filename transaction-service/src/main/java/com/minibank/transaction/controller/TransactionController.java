package com.minibank.transaction.controller;

import com.minibank.transaction.dto.TransactionRequest;
import com.minibank.transaction.model.BankTransaction;
import com.minibank.transaction.service.TransactionService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import com.minibank.transaction.dto.TransferRequest;

@RestController
@RequestMapping("/api/transactions")
public class TransactionController {

    private final TransactionService service;

    public TransactionController(TransactionService service) {
        this.service = service;
    }


    @PostMapping("/deposit")
    public ResponseEntity<?> deposit(
            @RequestBody TransactionRequest request) {

        BankTransaction transaction =
                service.deposit(
                        request.accountNumber(),
                        request.amount()
                );

        return ResponseEntity.ok(Map.of(
                "message", "Deposit successful",
                "transactionId", transaction.getId(),
                "accountNumber", transaction.getAccountNumber(),
                "amount", transaction.getAmount(),
                "status", transaction.getStatus()
        ));
    }


    @PostMapping("/withdraw")
    public ResponseEntity<?> withdraw(
            @RequestBody TransactionRequest request) {

        BankTransaction transaction =
                service.withdraw(
                        request.accountNumber(),
                        request.amount()
                );

        return ResponseEntity.ok(Map.of(
                "message", "Withdrawal successful",
                "transactionId", transaction.getId(),
                "accountNumber", transaction.getAccountNumber(),
                "amount", transaction.getAmount(),
                "status", transaction.getStatus()
        ));
    }

    @GetMapping("/history/{accountNumber}")
    public ResponseEntity<?> history(
        @PathVariable String accountNumber) {

    return ResponseEntity.ok(
            service.getHistory(accountNumber)
    );
  }

  @PostMapping("/transfer")
  public ResponseEntity<?> transfer(
        @RequestBody TransferRequest request) {

    BankTransaction transaction =
            service.transfer(
                    request.sourceAccount(),
                    request.targetAccount(),
                    request.amount()
            );

    return ResponseEntity.ok(Map.of(
            "message", "Transfer successful",
            "transactionId", transaction.getId(),
            "sourceAccount", transaction.getAccountNumber(),
            "targetAccount", transaction.getTargetAccount(),
            "amount", transaction.getAmount(),
            "status", transaction.getStatus()
    ));
   }
}
