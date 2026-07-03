package com.emall.order.feign;

import com.emall.order.dto.DeductRequest;
import com.emall.order.dto.ResponseResult;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class InventoryFeignClientFallbackFactory implements FallbackFactory<InventoryFeignClient> {

    private static final Logger log = LoggerFactory.getLogger(InventoryFeignClientFallbackFactory.class);

    @Override
    public InventoryFeignClient create(Throwable cause) {
        log.error("InventoryFeignClient fallback triggered, reason: {}", cause.getMessage());

        return new InventoryFeignClient() {
            @Override
            public ResponseResult<Void> deduct(DeductRequest request) {
                log.warn("Inventory service is unavailable, returning fallback response. ProductId: {}, Quantity: {}",
                        request.getProductId(), request.getQuantity());
                return ResponseResult.fail(503, "库存服务繁忙，请稍后重试");
            }

            @Override
            public ResponseResult<Void> restore(DeductRequest request) {
                log.error("Inventory service unavailable during restore. ProductId: {}, Quantity: {}",
                        request.getProductId(), request.getQuantity());
                return ResponseResult.fail(503, "库存服务不可用，回滚失败，请联系客服");
            }
        };
    }
}
