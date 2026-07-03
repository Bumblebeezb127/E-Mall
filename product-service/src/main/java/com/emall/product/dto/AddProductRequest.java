package com.emall.product.dto;

import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Positive;
import java.math.BigDecimal;

@Data
public class AddProductRequest {

    @NotBlank(message = "Product name cannot be blank")
    private String name;

    @NotNull(message = "Price cannot be null")
    @Positive(message = "Price must be positive")
    private BigDecimal price;

    @NotNull(message = "Stock cannot be null")
    @Positive(message = "Stock must be positive")
    private Integer stock;

    private String description;

    private String imageUrl;

    private String category;
}
