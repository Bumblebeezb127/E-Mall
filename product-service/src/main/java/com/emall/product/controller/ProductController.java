package com.emall.product.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.product.config.PageConfig;
import com.emall.product.dto.AddProductRequest;
import com.emall.product.dto.PageResult;
import com.emall.product.dto.ResponseResult;
import com.emall.product.entity.Product;
import com.emall.product.mq.OrderEventMessage;
import com.emall.product.service.MqOrderStatsService;
import com.emall.product.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.Positive;

@RestController
@RequestMapping("/product")
@Validated
public class ProductController {

    @Autowired
    private ProductService productService;

    @Autowired
    private PageConfig pageConfig;

    @Autowired
    private MqOrderStatsService mqOrderStatsService;

    @GetMapping("/list")
    public ResponseResult<PageResult<Product>> getProductList(
            @RequestParam(defaultValue = "1") @Positive int page,
            @RequestParam(required = false) Integer size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String category) {

        int actualSize = (size == null || size <= 0) ? pageConfig.getDefaultSize() : size;
        if (actualSize > pageConfig.getMaxSize()) {
            actualSize = pageConfig.getMaxSize();
        }

        Page<Product> productPage = productService.getProductPage(page, actualSize, keyword, category);

        PageResult<Product> pageResult = new PageResult<>(
                productPage.getRecords(),
                productPage.getTotal(),
                productPage.getCurrent(),
                productPage.getSize(),
                productPage.getPages()
        );

        return ResponseResult.success(pageResult);
    }

    @GetMapping("/detail/{id}")
    public ResponseResult<Product> getProductDetail(@PathVariable Long id) {
        Product product = productService.getProductById(id);
        return ResponseResult.success(product);
    }

    @PostMapping("/add")
    public ResponseResult<Void> addProduct(@Valid @RequestBody AddProductRequest request) {
        productService.addProduct(request);
        return ResponseResult.success("Product added successfully", null);
    }

    @PutMapping("/stock/update")
    public ResponseResult<Void> updateStock(
            @RequestParam Long productId,
            @RequestParam Integer delta) {
        productService.updateStock(productId, delta);
        return ResponseResult.success("Product stock updated", null);
    }

    // ============== Admin 端点 ==============

    @PostMapping("/admin/create")
    public ResponseResult<Product> adminCreate(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @Valid @RequestBody AddProductRequest request) {
        requireAdmin(role);
        Product created = productService.addProductAndReturn(request);
        return ResponseResult.success("Product created", created);
    }

    @PutMapping("/admin/update/{id}")
    public ResponseResult<Void> adminUpdate(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long id,
            @RequestBody AddProductRequest request) {
        requireAdmin(role);
        productService.adminUpdate(id, request);
        return ResponseResult.success("Product updated", null);
    }

    @DeleteMapping("/admin/delete/{id}")
    public ResponseResult<Void> adminDelete(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long id) {
        requireAdmin(role);
        productService.adminDelete(id);
        return ResponseResult.success("Product deleted", null);
    }

    @GetMapping("/admin/list")
    public ResponseResult<PageResult<Product>> adminList(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(required = false) Integer size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Integer status) {
        requireAdmin(role);
        int actualSize = (size == null || size <= 0) ? pageConfig.getMaxSize() : size;
        Page<Product> result = productService.adminList(page, actualSize, keyword, category, status);
        PageResult<Product> pr = new PageResult<>(result.getRecords(), result.getTotal(),
                result.getCurrent(), result.getSize(), result.getPages());
        return ResponseResult.success(pr);
    }

    // ============== MQ 事件查询 (Admin) ==============

    @GetMapping("/admin/mq/events")
    public ResponseResult<java.util.Map<String, Object>> adminMqEvents(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam(defaultValue = "20") int limit) {
        requireAdmin(role);
        java.util.List<OrderEventMessage> events = mqOrderStatsService.listRecent(limit);
        java.util.Map<String, Object> data = new java.util.HashMap<>();
        data.put("total", mqOrderStatsService.totalCount());
        data.put("created", mqOrderStatsService.countByType("order.created"));
        data.put("paid", mqOrderStatsService.countByType("order.paid"));
        data.put("cancelled", mqOrderStatsService.countByType("order.cancelled"));
        data.put("events", events);
        return ResponseResult.success(data);
    }

    private void requireAdmin(String role) {
        if (!"ADMIN".equals(role)) {
            throw new com.emall.product.exception.BusinessException(403, "Admin role required");
        }
    }
}
