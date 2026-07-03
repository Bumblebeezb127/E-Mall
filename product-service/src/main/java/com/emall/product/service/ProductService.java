package com.emall.product.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.emall.product.dto.AddProductRequest;
import com.emall.product.entity.Product;

public interface ProductService extends IService<Product> {

    Page<Product> getProductPage(int page, int size, String keyword, String category);

    Product getProductById(Long id);

    void addProduct(AddProductRequest request);

    void updateStock(Long productId, Integer delta);
}
