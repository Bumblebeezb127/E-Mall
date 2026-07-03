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
import com.emall.order.feign.ProductFeignClient;
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

    @Autowired
    private ProductFeignClient productFeignClient;

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

        // 1. 查询商品真实价格/名称 (Feign 远程调用 product-service)
        ResponseResult<ProductFeignClient.ProductDTO> productResp =
                productFeignClient.getProductDetail(request.getProductId());
        if (productResp == null || productResp.getCode() != 200 || productResp.getData() == null) {
            String msg = productResp != null ? productResp.getMessage() : "商品服务无响应";
            log.error("Product service call failed - code: {}, message: {}",
                    productResp != null ? productResp.getCode() : "null", msg);
            throw new BusinessException(503, "获取商品信息失败: " + msg);
        }
        ProductFeignClient.ProductDTO product = productResp.getData();
        if (product.getStatus() != null && product.getStatus() != 1) {
            throw new BusinessException("商品已下架，无法购买");
        }

        // 2. 扣减库存 (Feign 远程调用 inventory-service)
        DeductRequest deductRequest = new DeductRequest();
        deductRequest.setProductId(request.getProductId());
        deductRequest.setQuantity(request.getQuantity());

        ResponseResult<Void> deductResponse = inventoryFeignClient.deduct(deductRequest);

        if (deductResponse == null || deductResponse.getCode() != 200) {
            String msg = deductResponse != null ? deductResponse.getMessage() : "库存服务无响应";
            log.error("Inventory deduction failed - code: {}, message: {}",
                    deductResponse != null ? deductResponse.getCode() : "null", msg);
            throw new BusinessException(deductResponse != null ? deductResponse.getCode() : 503, msg);
        }

        // 2.5 同步 product.stock 冗余字段 (best-effort: 失败仅记日志, 不阻断订单创建)
        try {
            ResponseResult<Void> syncResp = productFeignClient.updateStock(
                    request.getProductId(), -request.getQuantity());
            if (syncResp == null || syncResp.getCode() != 200) {
                log.warn("Product stock sync failed - productId: {}, delta: -{}, msg: {}",
                        request.getProductId(), request.getQuantity(),
                        syncResp != null ? syncResp.getMessage() : "null");
            }
        } catch (Exception e) {
            log.warn("Product stock sync exception - productId: {}, delta: -{}",
                    request.getProductId(), request.getQuantity(), e);
        }

        // 3. 创建订单 (使用商品真实价格)
        String orderNo = generateOrderNo();
        BigDecimal unitPrice = product.getPrice() != null ? product.getPrice() : BigDecimal.ZERO;
        BigDecimal totalAmount = unitPrice.multiply(BigDecimal.valueOf(request.getQuantity()));

        Order order = new Order();
        order.setOrderNo(orderNo);
        order.setUserId(request.getUserId());
        order.setTotalAmount(totalAmount);
        order.setStatus(0);
        order.setAddress(request.getAddress());
        order.setRemark(request.getRemark());
        order.setCreatedAt(java.time.LocalDateTime.now());
        order.setUpdatedAt(java.time.LocalDateTime.now());

        orderMapper.insert(order);

        OrderItem orderItem = new OrderItem();
        orderItem.setOrderId(order.getId());
        orderItem.setProductId(request.getProductId());
        orderItem.setProductName(product.getName() != null ? product.getName() : ("Product-" + request.getProductId()));
        orderItem.setPrice(unitPrice);
        orderItem.setQuantity(request.getQuantity());
        orderItem.setSubtotal(totalAmount);
        orderItem.setCreatedAt(java.time.LocalDateTime.now());

        orderItemMapper.insert(orderItem);

        log.info("Order created successfully - orderId: {}, orderNo: {}, amount: {}",
                order.getId(), orderNo, totalAmount);

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

    @Override
    public OrderDetailResponse getOrderDetail(Long orderId, Long userId) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException("订单不存在");
        }
        if (!order.getUserId().equals(userId)) {
            throw new BusinessException(403, "无权查看该订单");
        }

        LambdaQueryWrapper<OrderItem> itemWrapper = new LambdaQueryWrapper<>();
        itemWrapper.eq(OrderItem::getOrderId, orderId);
        List<OrderItem> orderItems = orderItemMapper.selectList(itemWrapper);

        return buildOrderDetailResponse(order, orderItems);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrderDetailResponse cancelOrder(Long orderId, Long userId) {
        log.info("Cancelling order - orderId: {}, userId: {}", orderId, userId);
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException("订单不存在");
        }
        if (!order.getUserId().equals(userId)) {
            throw new BusinessException(403, "无权操作该订单");
        }
        if (order.getStatus() == 4) {
            throw new BusinessException("订单已取消，无需重复操作");
        }
        if (order.getStatus() != 0) {
            throw new BusinessException("仅待支付订单可取消");
        }

        LambdaQueryWrapper<OrderItem> itemWrapper = new LambdaQueryWrapper<>();
        itemWrapper.eq(OrderItem::getOrderId, orderId);
        List<OrderItem> orderItems = orderItemMapper.selectList(itemWrapper);

        // 回滚库存：先调 inventory-service 还原，失败则抛异常让本地事务回滚
        for (OrderItem item : orderItems) {
            try {
                ResponseResult<Void> restoreResponse = inventoryFeignClient.restore(
                        new DeductRequest(item.getProductId(), item.getQuantity()));
                if (restoreResponse == null || restoreResponse.getCode() != 200) {
                    String msg = restoreResponse != null ? restoreResponse.getMessage() : "库存服务无响应";
                    log.error("Restore inventory failed - productId: {}, qty: {}, msg: {}",
                            item.getProductId(), item.getQuantity(), msg);
                    throw new BusinessException(503, "回滚库存失败: " + msg);
                }
                log.info("Inventory restored - orderId: {}, productId: {}, qty: {}",
                        orderId, item.getProductId(), item.getQuantity());

                // 同步 product.stock 冗余字段 (best-effort)
                try {
                    ResponseResult<Void> syncResp = productFeignClient.updateStock(
                            item.getProductId(), item.getQuantity());
                    if (syncResp == null || syncResp.getCode() != 200) {
                        log.warn("Product stock sync (restore) failed - productId: {}, delta: +{}, msg: {}",
                                item.getProductId(), item.getQuantity(),
                                syncResp != null ? syncResp.getMessage() : "null");
                    }
                } catch (Exception e) {
                    log.warn("Product stock sync (restore) exception - productId: {}, delta: +{}",
                            item.getProductId(), item.getQuantity(), e);
                }
            } catch (BusinessException e) {
                throw e;
            } catch (Exception e) {
                log.error("Restore inventory exception - productId: {}, qty: {}",
                        item.getProductId(), item.getQuantity(), e);
                throw new BusinessException(503, "回滚库存异常: " + e.getMessage());
            }
        }

        order.setStatus(4);
        order.setUpdatedAt(java.time.LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("Order cancelled - orderId: {}", orderId);

        return buildOrderDetailResponse(order, orderItems);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrderDetailResponse payOrder(Long orderId, Long userId) {
        log.info("Paying order - orderId: {}, userId: {}", orderId, userId);
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new BusinessException("订单不存在");
        }
        if (!order.getUserId().equals(userId)) {
            throw new BusinessException(403, "无权操作该订单");
        }
        if (order.getStatus() == 1) {
            throw new BusinessException("订单已支付，无需重复支付");
        }
        if (order.getStatus() != 0) {
            throw new BusinessException("仅待支付订单可支付");
        }

        order.setStatus(1);
        order.setUpdatedAt(java.time.LocalDateTime.now());
        orderMapper.updateById(order);

        log.info("Order paid - orderId: {}", orderId);

        LambdaQueryWrapper<OrderItem> itemWrapper = new LambdaQueryWrapper<>();
        itemWrapper.eq(OrderItem::getOrderId, orderId);
        List<OrderItem> orderItems = orderItemMapper.selectList(itemWrapper);

        return buildOrderDetailResponse(order, orderItems);
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
        response.setAddress(order.getAddress());
        response.setRemark(order.getRemark());

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
