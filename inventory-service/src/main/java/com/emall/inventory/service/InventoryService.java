package com.emall.inventory.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.inventory.dto.InventoryResponse;
import com.emall.inventory.entity.Inventory;

public interface InventoryService {

    void deductWithOptimisticLock(Long productId, Integer quantity);

    void restoreStock(Long productId, Integer quantity);

    InventoryResponse getInventory(Long productId);

    void simulateTimeout();

    // Admin
    Page<Inventory> adminList(long page, long size, Long productId);

    void adminInit(Long productId, Integer stock);

    void adminSetStock(Long productId, Integer stock);
}
