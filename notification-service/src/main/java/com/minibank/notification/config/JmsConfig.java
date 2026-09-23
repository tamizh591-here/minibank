package com.minibank.notification.config;
import com.minibank.notification.messaging.NotificationEvent;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import org.springframework.jms.support.converter.MappingJackson2MessageConverter;
import org.springframework.jms.support.converter.MessageConverter;
import org.springframework.jms.support.converter.MessageType;

@Configuration
public class JmsConfig {

    @Bean
    public MessageConverter jacksonJmsMessageConverter() {

        MappingJackson2MessageConverter converter =
                new MappingJackson2MessageConverter();

        converter.setTargetType(
                MessageType.TEXT
        );

        converter.setTypeIdPropertyName(
                "_type"
        );

        /*
         * Producer sends:
         *
         * com.minibank.transaction.messaging.NotificationEvent
         *
         * Consumer uses:
         *
         * com.minibank.notification.messaging.NotificationEvent
         *
         * Map producer type -> consumer type.
         */

        converter.setTypeIdMappings(
                java.util.Map.of(
                        "com.minibank.transaction.messaging.NotificationEvent",
                        NotificationEvent.class
                )
        );

        return converter;
    }
}
