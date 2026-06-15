package com.emall.order.feign;

import com.emall.order.dto.DeductRequest;
import com.emall.order.dto.ResponseResult;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = "inventory-service",
        fallbackFactory = InventoryFeignClientFallbackFactory.class)
public interface InventoryFeignClient {

    @PostMapping("/inventory/deduct")
    ResponseResult<Void> deduct(@RequestBody DeductRequest request);
}
