package com.minibank.customer.controller;

import com.minibank.customer.dto.LoginRequest;
import com.minibank.customer.dto.RegisterRequest;
import com.minibank.customer.model.Customer;
import com.minibank.customer.service.CustomerService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/customers")
public class CustomerController {

    private final CustomerService service;

    public CustomerController(CustomerService service) {
        this.service = service;
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(
            @RequestBody RegisterRequest request) {

        Customer customer = service.register(request);

        return ResponseEntity.ok(Map.of(
                "message", "Customer registered successfully",
                "customerId", customer.getId(),
                "email", customer.getEmail()
        ));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(
            @RequestBody LoginRequest request) {

        Customer customer = service.login(request);

        return ResponseEntity.ok(Map.of(
                "message", "Login successful",
                "customerId", customer.getId(),
                "firstName", customer.getFirstName(),
                "email", customer.getEmail()
        ));
    }
}
