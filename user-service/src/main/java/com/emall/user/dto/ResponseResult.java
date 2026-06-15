package com.emall.user.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ResponseResult<T> {

    private int code;
    private String message;
    private T data;

    public static <T> ResponseResult<T> success(T data) {
        return new ResponseResult<>(200, "Success", data);
    }

    public static <T> ResponseResult<T> success(String message, T data) {
        return new ResponseResult<>(200, message, data);
    }

    public static <T> ResponseResult<T> fail(int code, String message) {
        return new ResponseResult<>(code, message, null);
    }

    public static <T> ResponseResult<T> fail(String message) {
        return new ResponseResult<>(500, message, null);
    }
}
