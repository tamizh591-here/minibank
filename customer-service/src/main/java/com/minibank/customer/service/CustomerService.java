package com.minibank.customer.service;

import com.minibank.customer.dto.LoginRequest;
import com.minibank.customer.dto.RegisterRequest;
import com.minibank.customer.model.Customer;
import com.minibank.customer.repository.CustomerRepository;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class CustomerService {

    private final CustomerRepository repository;
    private final BCryptPasswordEncoder passwordEncoder =
            new BCryptPasswordEncoder();

    public CustomerService(CustomerRepository repository) {
        this.repository = repository;
    }

    public Customer register(RegisterRequest request) {

        if (repository.existsByEmail(request.email())) {
            throw new RuntimeException("Email already registered");
        }

        Customer customer = new Customer();

        customer.setFirstName(request.firstName());
        customer.setLastName(request.lastName());
        customer.setEmail(request.email());

        customer.setPasswordHash(
                passwordEncoder.encode(request.password())
        );

        return repository.save(customer);
    }

    public Customer login(LoginRequest request) {

        Customer customer = repository.findByEmail(request.email())
                .orElseThrow(() ->
                        new RuntimeException("Invalid email or password"));

        if (!passwordEncoder.matches(
                request.password(),
                customer.getPasswordHash())) {

            throw new RuntimeException("Invalid email or password");
        }

        return customer;
    }
}
