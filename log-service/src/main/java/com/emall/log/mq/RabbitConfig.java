package com.emall.log.mq;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitConfig {

    public static final String EXCHANGE_ORDER_EVENT = "emall.order.exchange";
    public static final String QUEUE_LOG_ORDER = "emall.log.order.queue";

    @Bean
    public TopicExchange orderExchange() {
        return new TopicExchange(EXCHANGE_ORDER_EVENT, true, false);
    }

    @Bean
    public Queue logOrderQueue() {
        return new Queue(QUEUE_LOG_ORDER, true);
    }

    @Bean
    public Binding logOrderBinding(Queue logOrderQueue, TopicExchange orderExchange) {
        return BindingBuilder.bind(logOrderQueue)
                .to(orderExchange)
                .with("order.*");
    }

    @Bean
    public MessageConverter messageConverter() {
        com.fasterxml.jackson.databind.ObjectMapper mapper =
                new com.fasterxml.jackson.databind.ObjectMapper();
        mapper.registerModule(new com.fasterxml.jackson.datatype.jsr310.JavaTimeModule());
        mapper.disable(com.fasterxml.jackson.databind.SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return new Jackson2JsonMessageConverter(mapper);
    }
}
