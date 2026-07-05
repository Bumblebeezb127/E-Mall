package com.emall.product.service;

import com.emall.product.mq.OrderEventMessage;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

@Service
public class MqOrderStatsService {

    private static final int MAX_RETAIN = 100;

    private final List<OrderEventMessage> recent = new CopyOnWriteArrayList<>();

    public synchronized void recordEvent(OrderEventMessage message) {
        recent.add(0, message);
        if (recent.size() > MAX_RETAIN) {
            recent.remove(recent.size() - 1);
        }
    }

    public synchronized List<OrderEventMessage> listRecent(int limit) {
        int n = Math.min(limit, recent.size());
        return recent.stream()
                .sorted(Comparator.comparing(OrderEventMessage::getOccurredAt,
                        Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(n)
                .collect(Collectors.toList());
    }

    public synchronized int totalCount() {
        return recent.size();
    }

    public synchronized long countByType(String eventType) {
        return recent.stream().filter(e -> eventType.equals(e.getEventType())).count();
    }
}
