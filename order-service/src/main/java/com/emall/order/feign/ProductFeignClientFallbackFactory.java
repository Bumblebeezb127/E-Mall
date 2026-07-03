package com.emall.order.feign;

import com.emall.order.dto.ResponseResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

@Component
public class ProductFeignClientFallbackFactory implements FallbackFactory<ProductFeignClient> {

    private static final Logger log = LoggerFactory.getLogger(ProductFeignClientFallbackFactory.class);

    @Override
    public ProductFeignClient create(Throwable cause) {
        log.error("ProductFeignClient fallback triggered, reason: {}", cause.getMessage());

        return new ProductFeignClient() {
            @Override
            public ResponseResult<ProductFeignClient.ProductDTO> getProductDetail(Long id) {
                log.warn("Product service is unavailable, returning fallback. ProductId: {}", id);
                return ResponseResult.fail(503, "商品服务繁忙，请稍后重试");
            }

            @Override
            public ResponseResult<Void> updateStock(Long productId, Integer delta) {
                log.error("Product service unavailable during stock sync. ProductId: {}, delta: {}",
                        productId, delta);
                return ResponseResult.fail(503, "商品库存同步失败，请联系客服");
            }
        };
    }
}
