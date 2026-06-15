package com.emall.order.service;

import com.emall.order.dto.CreateOrderRequest;
import com.emall.order.dto.OrderDetailResponse;

import java.util.List;

public interface OrderService {

    OrderDetailResponse createOrder(CreateOrderRequest request);

    List<OrderDetailResponse> getOrdersByUserId(Long userId);
}
