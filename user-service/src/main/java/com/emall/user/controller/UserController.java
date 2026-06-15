package com.emall.user.controller;

import com.emall.user.dto.*;
import com.emall.user.service.UserService;
import com.emall.user.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;

@RestController
@RequestMapping("/user")
@Validated
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private JwtUtil jwtUtil;

    @PostMapping("/register")
    public ResponseResult<Void> register(@Valid @RequestBody RegisterRequest request) {
        userService.register(request);
        return ResponseResult.success("User registered successfully", null);
    }

    @PostMapping("/login")
    public ResponseResult<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        LoginResponse loginResponse = userService.login(request.getUsername(), request.getPassword());
        return ResponseResult.success(loginResponse);
    }

    @GetMapping("/info")
    public ResponseResult<UserInfoResponse> getUserInfo(@RequestHeader("Authorization") String authorization) {
        String token = extractToken(authorization);
        if (token == null) {
            throw new com.emall.user.exception.BusinessException(401, "Token is missing");
        }

        if (!jwtUtil.validateToken(token)) {
            throw new com.emall.user.exception.BusinessException(401, "Invalid or expired token");
        }

        Long userId = jwtUtil.getUserIdFromToken(token);
        UserInfoResponse userInfo = userService.getUserInfo(userId);
        return ResponseResult.success(userInfo);
    }

    private String extractToken(String authorization) {
        if (authorization != null && authorization.startsWith("Bearer ")) {
            return authorization.substring(7);
        }
        return null;
    }
}
