package com.minibank.customer.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/api/customer/hello")
    public String hello() {
        return "MiniBank Customer Service is running";
    }
}
