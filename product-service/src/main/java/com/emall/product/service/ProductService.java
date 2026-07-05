package com.emall.product.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.emall.product.dto.AddProductRequest;
import com.emall.product.entity.Product;

public interface ProductService extends IService<Product> {

    Page<Product> getProductPage(int page, int size, String keyword, String category);

    Product getProductById(Long id);

    void addProduct(AddProductRequest request);

    /**
     * 新增商品并返回新生成的商品对象 (含 id).
     * 供 adminCreate controller 直接返回 data, 便于客户端链式调用 (update/delete).
     */
    Product addProductAndReturn(AddProductRequest request);

    void updateStock(Long productId, Integer delta);

    // Admin
    Page<Product> adminList(int page, int size, String keyword, String category, Integer status);

    void adminUpdate(Long id, AddProductRequest request);

    void adminDelete(Long id);
}
