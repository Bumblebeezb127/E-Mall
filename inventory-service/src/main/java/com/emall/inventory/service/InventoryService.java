package com.emall.inventory.service;

import com.emall.inventory.dto.InventoryResponse;

public interface InventoryService {

    void deductWithOptimisticLock(Long productId, Integer quantity);

    void restoreStock(Long productId, Integer quantity);

    InventoryResponse getInventory(Long productId);

    void simulateTimeout();
}
