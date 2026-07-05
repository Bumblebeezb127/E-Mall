package com.emall.log.mq;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

@Component
public class OrderEventListener {

    private static final Logger log = LoggerFactory.getLogger(OrderEventListener.class);

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private Path resolveLogFile() {
        String logRoot = System.getProperty("emall.log.root");
        if (logRoot == null || logRoot.isEmpty()) {
            logRoot = System.getProperty("user.dir") + File.separator + "logs";
        }
        return Paths.get(logRoot, "order-events-" + LocalDate.now().format(DATE_FMT) + ".log");
    }

    @RabbitListener(queues = RabbitConfig.QUEUE_LOG_ORDER)
    public void handleOrderEvent(OrderEventMessage message) {
        try {
            String line = formatLine(message);
            Path file = resolveLogFile();
            if (file.getParent() != null) {
                Files.createDirectories(file.getParent());
            }
            try (BufferedWriter writer = Files.newBufferedWriter(file, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND)) {
                writer.write(line);
                writer.newLine();
            }
            log.info("[log-service] Persisted order event - type: {}, orderId: {}, file: {}",
                    message.getEventType(), message.getOrderId(), file);
        } catch (IOException e) {
            log.error("[log-service] Failed to persist order event: {}", message, e);
        }
    }

    private String formatLine(OrderEventMessage m) {
        return String.format("%s | %s | orderId=%d | orderNo=%s | userId=%d | productId=%d | qty=%d | amount=%s | status=%d (%s) | eventId=%s",
                m.getOccurredAt() == null ? "-" : m.getOccurredAt().toString(),
                m.getEventType(),
                m.getOrderId(),
                m.getOrderNo(),
                m.getUserId(),
                m.getProductId(),
                m.getQuantity(),
                m.getTotalAmount(),
                m.getStatus(),
                m.getStatusDesc(),
                m.getEventId());
    }
}
