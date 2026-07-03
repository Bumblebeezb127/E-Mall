package com.emall.order.feign;

import com.emall.order.dto.ResponseResult;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.math.BigDecimal;

/**
 * 商品服务远程调用客户端
 * 用于在创建订单时获取商品真实价格、名称等信息
 */
@FeignClient(name = "product-service", fallbackFactory = ProductFeignClientFallbackFactory.class)
public interface ProductFeignClient {

    @GetMapping("/product/detail/{id}")
    ResponseResult<ProductDTO> getProductDetail(@PathVariable("id") Long id);

    @PutMapping("/product/stock/update")
    ResponseResult<Void> updateStock(@RequestParam("productId") Long productId,
                                     @RequestParam("delta") Integer delta);

    /**
     * 商品 DTO, 仅承载订单所需的字段
     */
    class ProductDTO {
        private Long id;
        private String name;
        private BigDecimal price;
        private Integer stock;
        private Integer status;

        public Long getId() { return id; }
        public void setId(Long id) { this.id = id; }
        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public BigDecimal getPrice() { return price; }
        public void setPrice(BigDecimal price) { this.price = price; }
        public Integer getStock() { return stock; }
        public void setStock(Integer stock) { this.stock = stock; }
        public Integer getStatus() { return status; }
        public void setStatus(Integer status) { this.status = status; }
    }
}
