package com.emall.product.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.product.config.PageConfig;
import com.emall.product.dto.AddProductRequest;
import com.emall.product.dto.PageResult;
import com.emall.product.dto.ResponseResult;
import com.emall.product.entity.Product;
import com.emall.product.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.Positive;

@RestController
@RequestMapping("/product")
@Validated
public class ProductController {

    @Autowired
    private ProductService productService;

    @Autowired
    private PageConfig pageConfig;

    @GetMapping("/list")
    public ResponseResult<PageResult<Product>> getProductList(
            @RequestParam(defaultValue = "1") @Positive int page,
            @RequestParam(defaultValue = "10") @Positive int size) {

        if (size > pageConfig.getMaxSize()) {
            size = pageConfig.getMaxSize();
        }

        Page<Product> productPage = productService.getProductPage(page, size);

        PageResult<Product> pageResult = new PageResult<>(
                productPage.getRecords(),
                productPage.getTotal(),
                productPage.getCurrent(),
                productPage.getSize(),
                productPage.getPages()
        );

        return ResponseResult.success(pageResult);
    }

    @GetMapping("/detail/{id}")
    public ResponseResult<Product> getProductDetail(@PathVariable Long id) {
        Product product = productService.getProductById(id);
        return ResponseResult.success(product);
    }

    @PostMapping("/add")
    public ResponseResult<Void> addProduct(@Valid @RequestBody AddProductRequest request) {
        productService.addProduct(request);
        return ResponseResult.success("Product added successfully", null);
    }
}
