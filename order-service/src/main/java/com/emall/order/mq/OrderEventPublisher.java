package com.emall.order.mq;

import com.emall.order.entity.Order;
import com.emall.order.entity.OrderItem;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
public class OrderEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(OrderEventPublisher.class);

    @Autowired
    private RabbitTemplate rabbitTemplate;

    public void publishCreated(Order order, List<OrderItem> items) {
        OrderEventMessage message = buildMessage(
                RabbitConfig.ROUTING_KEY_ORDER_CREATED,
                order, items);
        send(message);
    }

    public void publishPaid(Order order, List<OrderItem> items) {
        OrderEventMessage message = buildMessage(
                RabbitConfig.ROUTING_KEY_ORDER_PAID,
                order, items);
        send(message);
    }

    public void publishCancelled(Order order, List<OrderItem> items) {
        OrderEventMessage message = buildMessage(
                RabbitConfig.ROUTING_KEY_ORDER_CANCELLED,
                order, items);
        send(message);
    }

    private OrderEventMessage buildMessage(String eventType, Order order, List<OrderItem> items) {
        OrderEventMessage msg = new OrderEventMessage();
        msg.setEventId(UUID.randomUUID().toString());
        msg.setEventType(eventType);
        msg.setOrderId(order.getId());
        msg.setOrderNo(order.getOrderNo());
        msg.setUserId(order.getUserId());
        msg.setStatus(order.getStatus());
        msg.setStatusDesc(statusDesc(order.getStatus()));
        msg.setOccurredAt(LocalDateTime.now());
        if (items != null && !items.isEmpty()) {
            OrderItem first = items.get(0);
            msg.setProductId(first.getProductId());
            msg.setProductName(first.getProductName());
            msg.setQuantity(first.getQuantity());
            msg.setTotalAmount(order.getTotalAmount());
        }
        return msg;
    }

    private void send(OrderEventMessage message) {
        try {
            rabbitTemplate.convertAndSend(
                    RabbitConfig.EXCHANGE_ORDER_EVENT,
                    message.getEventType(),
                    message);
            log.info("Published MQ event - type: {}, orderId: {}, orderNo: {}",
                    message.getEventType(), message.getOrderId(), message.getOrderNo());
        } catch (Exception e) {
            log.error("Failed to publish MQ event - type: {}, orderId: {}",
                    message.getEventType(), message.getOrderId(), e);
        }
    }

    private String statusDesc(Integer status) {
        switch (status) {
            case 0: return "待支付";
            case 1: return "已支付";
            case 2: return "已发货";
            case 3: return "已完成";
            case 4: return "已取消";
            default: return "未知";
        }
    }
}
