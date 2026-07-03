package com.emall.order.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class OrderDetailResponse {

    private Long orderId;
    private String orderNo;
    private Long userId;
    private BigDecimal totalAmount;
    private Integer status;
    private String statusDesc;
    private String createdAt;
    private String address;
    private String remark;
    private List<OrderItemDetail> items;

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class OrderItemDetail {
        private Long productId;
        private String productName;
        private BigDecimal price;
        private Integer quantity;
    }
}
