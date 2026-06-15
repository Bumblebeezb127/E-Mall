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

@Service
public class ProductServiceImpl extends ServiceImpl<ProductMapper, Product> implements ProductService {

    private static final int STATUS_ACTIVE = 1;

    @Override
    public Page<Product> getProductPage(int page, int size) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Product::getStatus, STATUS_ACTIVE);
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
        if (product.getStatus() != STATUS_ACTIVE) {
            throw new BusinessException("Product is not available");
        }
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
        product.setStatus(STATUS_ACTIVE);

        this.save(product);
    }
}
