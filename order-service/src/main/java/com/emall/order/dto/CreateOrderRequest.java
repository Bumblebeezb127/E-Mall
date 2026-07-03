package com.emall.order.dto;

import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Positive;
import javax.validation.constraints.Size;

@Data
public class CreateOrderRequest {

    @NotNull(message = "User ID cannot be null")
    private Long userId;

    @NotNull(message = "Product ID cannot be null")
    private Long productId;

    @NotNull(message = "Quantity cannot be null")
    @Positive(message = "Quantity must be positive")
    private Integer quantity;

    @NotBlank(message = "收货地址不能为空")
    @Size(min = 5, max = 200, message = "地址长度在5-200个字符")
    private String address;

    @Size(max = 100, message = "备注最多100个字符")
    private String remark;
}
