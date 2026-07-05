package com.emall.inventory.controller;

import com.emall.inventory.dto.DeductRequest;
import com.emall.inventory.dto.InventoryResponse;
import com.emall.inventory.dto.ResponseResult;
import com.emall.inventory.service.InventoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;

@RestController
@RequestMapping("/inventory")
@Validated
public class InventoryController {

    @Autowired
    private InventoryService inventoryService;

    @PostMapping("/deduct")
    public ResponseResult<Void> deduct(@Valid @RequestBody DeductRequest request) {
        inventoryService.deductWithOptimisticLock(request.getProductId(), request.getQuantity());
        return ResponseResult.success("Inventory deducted successfully", null);
    }

    @PostMapping("/restore")
    public ResponseResult<Void> restore(@Valid @RequestBody DeductRequest request) {
        inventoryService.restoreStock(request.getProductId(), request.getQuantity());
        return ResponseResult.success("Inventory restored successfully", null);
    }

    @GetMapping("/get/{productId}")
    public ResponseResult<InventoryResponse> getInventory(@PathVariable Long productId) {
        InventoryResponse inventory = inventoryService.getInventory(productId);
        return ResponseResult.success(inventory);
    }

    @PostMapping("/timeout")
    public ResponseResult<Void> timeout() {
        inventoryService.simulateTimeout();
        return ResponseResult.success("Timeout simulation completed", null);
    }

    // ============== Admin 端点 ==============

    @GetMapping("/admin/list")
    public ResponseResult<java.util.Map<String, Object>> adminList(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam(defaultValue = "1") long page,
            @RequestParam(defaultValue = "20") long size,
            @RequestParam(required = false) Long productId) {
        requireAdmin(role);
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<com.emall.inventory.entity.Inventory> pg =
                inventoryService.adminList(page, size, productId);
        java.util.Map<String, Object> data = new java.util.HashMap<>();
        data.put("records", pg.getRecords());
        data.put("total", pg.getTotal());
        data.put("page", pg.getCurrent());
        data.put("size", pg.getSize());
        return ResponseResult.success(data);
    }

    @PostMapping("/admin/init")
    public ResponseResult<Void> adminInit(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam Long productId,
            @RequestParam Integer stock) {
        requireAdmin(role);
        inventoryService.adminInit(productId, stock);
        return ResponseResult.success("Inventory initialized", null);
    }

    @PutMapping("/admin/update")
    public ResponseResult<Void> adminUpdate(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam Long productId,
            @RequestParam Integer stock) {
        requireAdmin(role);
        inventoryService.adminSetStock(productId, stock);
        return ResponseResult.success("Inventory set", null);
    }

    private void requireAdmin(String role) {
        if (!"ADMIN".equals(role)) {
            throw new com.emall.inventory.exception.BusinessException(403, "Admin role required");
        }
    }
}
