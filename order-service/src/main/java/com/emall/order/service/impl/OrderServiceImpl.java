package com.emall.order.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.emall.order.dto.CreateOrderRequest;
import com.emall.order.dto.DeductRequest;
import com.emall.order.dto.OrderDetailResponse;
import com.emall.order.dto.ResponseResult;
import com.emall.order.entity.Order;
import com.emall.order.entity.OrderItem;
import com.emall.order.exception.BusinessException;
import com.emall.order.feign.InventoryFeignClient;
import com.emall.order.mapper.OrderItemMapper;
import com.emall.order.mapper.OrderMapper;
import com.emall.order.service.OrderService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class OrderServiceImpl extends ServiceImpl<OrderMapper, Order> implements OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderServiceImpl.class);

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private OrderItemMapper orderItemMapper;

    @Autowired
    private InventoryFeignClient inventoryFeignClient;

    private static final String STATUS_PENDING = "待支付";
    private static final String STATUS_PAID = "已支付";
    private static final String STATUS_SHIPPED = "已发货";
    private static final String STATUS_COMPLETED = "已完成";
    private static final String STATUS_CANCELLED = "已取消";

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrderDetailResponse createOrder(CreateOrderRequest request) {
        log.info("Creating order - userId: {}, productId: {}, quantity: {}",
                request.getUserId(), request.getProductId(), request.getQuantity());

        DeductRequest deductRequest = new DeductRequest();
        deductRequest.setProductId(request.getProductId());
        deductRequest.setQuantity(request.getQuantity());

        ResponseResult<Void> deductResponse = inventoryFeignClient.deduct(deductRequest);

        if (deductResponse.getCode() != 200) {
            log.error("Inventory deduction failed - code: {}, message: {}",
                    deductResponse.getCode(), deductResponse.getMessage());
            throw new BusinessException(deductResponse.getCode(), deductResponse.getMessage());
        }

        String orderNo = generateOrderNo();
        BigDecimal totalAmount = BigDecimal.ZERO;

        Order order = new Order();
        order.setOrderNo(orderNo);
        order.setUserId(request.getUserId());
        order.setTotalAmount(totalAmount);
        order.setStatus(0);
        order.setCreatedAt(java.time.LocalDateTime.now());
        order.setUpdatedAt(java.time.LocalDateTime.now());

        orderMapper.insert(order);

        OrderItem orderItem = new OrderItem();
        orderItem.setOrderId(order.getId());
        orderItem.setProductId(request.getProductId());
        orderItem.setProductName("Product-" + request.getProductId());
        orderItem.setPrice(BigDecimal.valueOf(100));
        orderItem.setQuantity(request.getQuantity());
        orderItem.setCreatedAt(java.time.LocalDateTime.now());

        orderItemMapper.insert(orderItem);

        totalAmount = orderItem.getPrice().multiply(BigDecimal.valueOf(orderItem.getQuantity()));
        order.setTotalAmount(totalAmount);
        orderMapper.updateById(order);

        log.info("Order created successfully - orderId: {}, orderNo: {}", order.getId(), orderNo);

        return buildOrderDetailResponse(order, Collections.singletonList(orderItem));
    }

    @Override
    public List<OrderDetailResponse> getOrdersByUserId(Long userId) {
        LambdaQueryWrapper<Order> orderWrapper = new LambdaQueryWrapper<>();
        orderWrapper.eq(Order::getUserId, userId);
        orderWrapper.orderByDesc(Order::getCreatedAt);
        List<Order> orders = orderMapper.selectList(orderWrapper);

        if (orders.isEmpty()) {
            return new ArrayList<>();
        }

        List<Long> orderIds = orders.stream().map(Order::getId).collect(Collectors.toList());

        LambdaQueryWrapper<OrderItem> itemWrapper = new LambdaQueryWrapper<>();
        itemWrapper.in(OrderItem::getOrderId, orderIds);
        List<OrderItem> orderItems = orderItemMapper.selectList(itemWrapper);

        return orders.stream()
                .map(order -> {
                    List<OrderItem> items = orderItems.stream()
                            .filter(item -> item.getOrderId().equals(order.getId()))
                            .collect(Collectors.toList());
                    return buildOrderDetailResponse(order, items);
                })
                .collect(Collectors.toList());
    }

    private String generateOrderNo() {
        return "ORD" + System.currentTimeMillis() + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    private OrderDetailResponse buildOrderDetailResponse(Order order, List<OrderItem> items) {
        OrderDetailResponse response = new OrderDetailResponse();
        response.setOrderId(order.getId());
        response.setOrderNo(order.getOrderNo());
        response.setUserId(order.getUserId());
        response.setTotalAmount(order.getTotalAmount());
        response.setStatus(order.getStatus());
        response.setStatusDesc(getStatusDesc(order.getStatus()));
        response.setCreatedAt(order.getCreatedAt().format(DATE_FORMATTER));

        List<OrderDetailResponse.OrderItemDetail> itemDetails = items.stream()
                .map(item -> new OrderDetailResponse.OrderItemDetail(
                        item.getProductId(),
                        item.getProductName(),
                        item.getPrice(),
                        item.getQuantity()
                ))
                .collect(Collectors.toList());
        response.setItems(itemDetails);

        return response;
    }

    private String getStatusDesc(Integer status) {
        switch (status) {
            case 0: return STATUS_PENDING;
            case 1: return STATUS_PAID;
            case 2: return STATUS_SHIPPED;
            case 3: return STATUS_COMPLETED;
            case 4: return STATUS_CANCELLED;
            default: return "未知状态";
        }
    }
}
