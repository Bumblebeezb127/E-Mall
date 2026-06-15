package com.emall.inventory.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.emall.inventory.dto.InventoryResponse;
import com.emall.inventory.entity.Inventory;
import com.emall.inventory.exception.BusinessException;
import com.emall.inventory.mapper.InventoryMapper;
import com.emall.inventory.service.InventoryService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;

@Service
public class InventoryServiceImpl extends ServiceImpl<InventoryMapper, Inventory> implements InventoryService {

    private static final Logger log = LoggerFactory.getLogger(InventoryServiceImpl.class);

    private static final int MAX_RETRY_TIMES = 3;

    @Autowired
    private InventoryMapper inventoryMapper;

    @Override
    @Retryable(value = BusinessException.class, maxAttempts = 3,
            backoff = @Backoff(delay = 100, multiplier = 2))
    public void deductWithOptimisticLock(Long productId, Integer quantity) {
        log.info("Attempting to deduct inventory - productId: {}, quantity: {}", productId, quantity);

        LambdaQueryWrapper<Inventory> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Inventory::getProductId, productId);
        Inventory inventory = this.getOne(wrapper);

        if (inventory == null) {
            throw new BusinessException("Inventory not found for productId: " + productId);
        }

        if (inventory.getStock() < quantity) {
            throw new BusinessException("Insufficient stock for productId: " + productId);
        }

        int updatedRows = inventoryMapper.deductStockWithOptimisticLock(
                productId, quantity, inventory.getVersion());

        if (updatedRows == 0) {
            log.warn("Optimistic lock failed, retrying... - productId: {}", productId);
            throw new BusinessException("Concurrent modification detected, please retry");
        }

        log.info("Inventory deducted successfully - productId: {}, remaining stock: {}",
                productId, inventory.getStock() - quantity);
    }

    @Override
    public InventoryResponse getInventory(Long productId) {
        LambdaQueryWrapper<Inventory> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Inventory::getProductId, productId);
        Inventory inventory = this.getOne(wrapper);

        if (inventory == null) {
            throw new BusinessException("Inventory not found for productId: " + productId);
        }

        return new InventoryResponse(
                inventory.getProductId(),
                inventory.getStock(),
                inventory.getVersion()
        );
    }

    @Override
    public void simulateTimeout() {
        try {
            log.info("Simulating slow request - starting sleep for 3 seconds");
            Thread.sleep(3000);
            log.info("Simulating slow request - completed");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new BusinessException("Timeout simulation interrupted");
        }
    }
}
