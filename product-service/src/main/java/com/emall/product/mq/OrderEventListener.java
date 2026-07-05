package com.emall.product.mq;

import com.emall.product.service.MqOrderStatsService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.concurrent.ConcurrentLinkedQueue;

@Component
public class OrderEventListener {

    private static final Logger log = LoggerFactory.getLogger(OrderEventListener.class);

    @Autowired
    private MqOrderStatsService mqOrderStatsService;

    @RabbitListener(queues = RabbitConfig.QUEUE_PRODUCT_ORDER)
    public void handleOrderEvent(OrderEventMessage message) {
        try {
            log.info("[product-service] Received order event - type: {}, orderId: {}, productId: {}, qty: {}, amount: {}",
                    message.getEventType(),
                    message.getOrderId(),
                    message.getProductId(),
                    message.getQuantity(),
                    message.getTotalAmount());

            mqOrderStatsService.recordEvent(message);
        } catch (Exception e) {
            log.error("[product-service] Failed to handle order event: {}", message, e);
        }
    }
}
