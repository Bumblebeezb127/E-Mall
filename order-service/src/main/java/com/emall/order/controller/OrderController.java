package com.emall.order.controller;

import com.emall.order.dto.CreateOrderRequest;
import com.emall.order.dto.OrderDetailResponse;
import com.emall.order.dto.ResponseResult;
import com.emall.order.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/order")
@Validated
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping("/create")
    public ResponseResult<OrderDetailResponse> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        OrderDetailResponse order = orderService.createOrder(request);
        return ResponseResult.success("Order created successfully", order);
    }

    @GetMapping("/list")
    public ResponseResult<List<OrderDetailResponse>> getOrders(@RequestParam Long userId) {
        List<OrderDetailResponse> orders = orderService.getOrdersByUserId(userId);
        return ResponseResult.success(orders);
    }

    @GetMapping("/detail/{orderId}")
    public ResponseResult<OrderDetailResponse> getOrderDetail(
            @PathVariable Long orderId,
            @RequestParam Long userId) {
        OrderDetailResponse order = orderService.getOrderDetail(orderId, userId);
        return ResponseResult.success(order);
    }

    @PutMapping("/cancel/{orderId}")
    public ResponseResult<OrderDetailResponse> cancelOrder(
            @PathVariable Long orderId,
            @RequestParam Long userId) {
        OrderDetailResponse order = orderService.cancelOrder(orderId, userId);
        return ResponseResult.success("Order cancelled", order);
    }

    @PutMapping("/pay/{orderId}")
    public ResponseResult<OrderDetailResponse> payOrder(
            @PathVariable Long orderId,
            @RequestParam Long userId) {
        OrderDetailResponse order = orderService.payOrder(orderId, userId);
        return ResponseResult.success("Order paid", order);
    }
}
