package com.emall.product.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.emall.product.dto.AddProductRequest;
import com.emall.product.entity.Product;
import com.emall.product.exception.BusinessException;
import com.emall.product.mapper.ProductMapper;
import com.emall.product.service.ProductService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class ProductServiceImpl extends ServiceImpl<ProductMapper, Product> implements ProductService {

    private static final int STATUS_ACTIVE = 1;

    @Override
    public Page<Product> getProductPage(int page, int size, String keyword, String category) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Product::getStatus, STATUS_ACTIVE);
        if (StringUtils.hasText(keyword)) {
            wrapper.like(Product::getName, keyword);
        }
        if (StringUtils.hasText(category)) {
            wrapper.eq(Product::getCategory, category);
        }
        wrapper.orderByDesc(Product::getId);

        Page<Product> productPage = new Page<>(page, size);
        return this.page(productPage, wrapper);
    }

    @Override
    public Product getProductById(Long id) {
        Product product = this.getById(id);
        if (product == null) {
            throw new BusinessException("Product not found");
        }
        // 在 getProductById 中允许返回商品详情包括下架的, 以便订单服务创建订单时仍可查到
        return product;
    }

    @Override
    public void addProduct(AddProductRequest request) {
        Product product = new Product();
        product.setName(request.getName());
        product.setPrice(request.getPrice());
        product.setStock(request.getStock());
        product.setDescription(request.getDescription());
        product.setImageUrl(request.getImageUrl());
        product.setCategory(request.getCategory());
        product.setStatus(STATUS_ACTIVE);

        this.save(product);
    }

    @Override
    public void updateStock(Long productId, Integer delta) {
        Product product = this.getById(productId);
        if (product == null) {
            throw new BusinessException("Product not found");
        }
        int newStock = product.getStock() + delta;
        if (newStock < 0) {
            throw new BusinessException("Stock cannot be negative");
        }
        product.setStock(newStock);
        this.updateById(product);
    }

    @Override
    public Page<Product> adminList(int page, int size, String keyword, String category, Integer status) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(Product::getName, keyword);
        }
        if (StringUtils.hasText(category)) {
            wrapper.eq(Product::getCategory, category);
        }
        if (status != null) {
            wrapper.eq(Product::getStatus, status);
        }
        wrapper.orderByDesc(Product::getId);
        return this.page(new Page<>(page, size), wrapper);
    }

    @Override
    public void adminUpdate(Long id, AddProductRequest request) {
        Product p = this.getById(id);
        if (p == null) throw new BusinessException("Product not found");
        if (StringUtils.hasText(request.getName())) p.setName(request.getName());
        if (request.getPrice() != null) p.setPrice(request.getPrice());
        if (request.getStock() != null) p.setStock(request.getStock());
        if (StringUtils.hasText(request.getDescription())) p.setDescription(request.getDescription());
        if (StringUtils.hasText(request.getImageUrl())) p.setImageUrl(request.getImageUrl());
        if (StringUtils.hasText(request.getCategory())) p.setCategory(request.getCategory());
        this.updateById(p);
    }

    @Override
    public void adminDelete(Long id) {
        Product p = this.getById(id);
        if (p == null) throw new BusinessException("Product not found");
        this.removeById(id);
    }
}
