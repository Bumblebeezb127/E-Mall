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
}
