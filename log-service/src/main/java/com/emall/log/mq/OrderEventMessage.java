package com.emall.log.mq;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class OrderEventMessage implements Serializable {
    private String eventId;
    private String eventType;
    private Long orderId;
    private String orderNo;
    private Long userId;
    private Long productId;
    private String productName;
    private Integer quantity;
    private BigDecimal totalAmount;
    private Integer status;
    private String statusDesc;
    private LocalDateTime occurredAt;
}
