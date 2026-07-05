package com.emall.log.exception;

import com.emall.log.dto.ResponseResult;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ResponseResult<Void>> handleBusiness(BusinessException e) {
        return ResponseEntity.status(HttpStatus.OK)
                .body(ResponseResult.error(e.getCode(), e.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ResponseResult<Void>> handleIllegal(IllegalArgumentException e) {
        return ResponseEntity.status(HttpStatus.OK)
                .body(ResponseResult.error(400, e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ResponseResult<Void>> handleAll(Exception e) {
        return ResponseEntity.status(HttpStatus.OK)
                .body(ResponseResult.error(500, e.getMessage()));
    }
}
