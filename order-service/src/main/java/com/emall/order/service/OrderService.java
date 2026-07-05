package com.emall.order.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.order.dto.CreateOrderRequest;
import com.emall.order.dto.OrderDetailResponse;
import com.emall.order.entity.Order;

import java.util.List;
import java.util.Map;

public interface OrderService {

    OrderDetailResponse createOrder(CreateOrderRequest request);

    List<OrderDetailResponse> getOrdersByUserId(Long userId);

    OrderDetailResponse getOrderDetail(Long orderId, Long userId);

    OrderDetailResponse cancelOrder(Long orderId, Long userId);

    OrderDetailResponse payOrder(Long orderId, Long userId);

    // Admin
    Page<Order> adminList(long page, long size, Long userId, String orderNo, Integer status);

    Map<String, Object> adminStats();

    OrderDetailResponse adminForceCancel(Long orderId);

    OrderDetailResponse adminForcePay(Long orderId);

    void adminDelete(Long orderId);
}
