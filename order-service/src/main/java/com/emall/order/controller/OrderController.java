package com.emall.order.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.order.dto.CreateOrderRequest;
import com.emall.order.dto.OrderDetailResponse;
import com.emall.order.dto.ResponseResult;
import com.emall.order.entity.Order;
import com.emall.order.exception.BusinessException;
import com.emall.order.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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

    // ============== Admin 端点 ==============

    @GetMapping("/admin/list")
    public ResponseResult<Map<String, Object>> adminList(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam(defaultValue = "1") long page,
            @RequestParam(defaultValue = "20") long size,
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String orderNo,
            @RequestParam(required = false) Integer status) {
        requireAdmin(role);
        Page<Order> pg = orderService.adminList(page, size, userId, orderNo, status);
        List<Map<String, Object>> records = pg.getRecords().stream().map(this::toOrderMap).collect(Collectors.toList());
        Map<String, Object> data = new HashMap<>();
        data.put("records", records);
        data.put("total", pg.getTotal());
        data.put("page", pg.getCurrent());
        data.put("size", pg.getSize());
        return ResponseResult.success(data);
    }

    @GetMapping("/admin/stats")
    public ResponseResult<Map<String, Object>> adminStats(
            @RequestHeader(value = "X-User-Role", required = false) String role) {
        requireAdmin(role);
        return ResponseResult.success(orderService.adminStats());
    }

    @PutMapping("/admin/cancel/{orderId}")
    public ResponseResult<OrderDetailResponse> adminForceCancel(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long orderId) {
        requireAdmin(role);
        OrderDetailResponse order = orderService.adminForceCancel(orderId);
        return ResponseResult.success("Order force-cancelled", order);
    }

    @PutMapping("/admin/pay/{orderId}")
    public ResponseResult<OrderDetailResponse> adminForcePay(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long orderId) {
        requireAdmin(role);
        OrderDetailResponse order = orderService.adminForcePay(orderId);
        return ResponseResult.success("Order force-paid", order);
    }

    @DeleteMapping("/admin/delete/{orderId}")
    public ResponseResult<Void> adminDelete(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long orderId) {
        requireAdmin(role);
        orderService.adminDelete(orderId);
        return ResponseResult.success("Order deleted", null);
    }

    private Map<String, Object> toOrderMap(Order o) {
        Map<String, Object> m = new HashMap<>();
        m.put("orderId", o.getId());
        m.put("orderNo", o.getOrderNo());
        m.put("userId", o.getUserId());
        m.put("totalAmount", o.getTotalAmount());
        m.put("status", o.getStatus());
        m.put("statusDesc", statusDesc(o.getStatus()));
        m.put("address", o.getAddress());
        m.put("remark", o.getRemark());
        m.put("createdAt", o.getCreatedAt() == null ? null : o.getCreatedAt().toString());
        m.put("updatedAt", o.getUpdatedAt() == null ? null : o.getUpdatedAt().toString());
        return m;
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

    private void requireAdmin(String role) {
        if (!"ADMIN".equals(role)) {
            throw new BusinessException(403, "Admin role required");
        }
    }
}
