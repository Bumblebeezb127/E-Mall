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
}
