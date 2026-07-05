package com.emall.user.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.emall.user.dto.*;
import com.emall.user.entity.User;
import com.emall.user.exception.BusinessException;
import com.emall.user.service.UserService;
import com.emall.user.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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
            throw new BusinessException(401, "Token is missing");
        }

        if (!jwtUtil.validateToken(token)) {
            throw new BusinessException(401, "Invalid or expired token");
        }

        Long userId = jwtUtil.getUserIdFromToken(token);
        UserInfoResponse userInfo = userService.getUserInfo(userId);
        return ResponseResult.success(userInfo);
    }

    // ============== Admin 端点 ==============

    @GetMapping("/admin/list")
    public ResponseResult<Map<String, Object>> adminList(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @RequestParam(defaultValue = "1") long page,
            @RequestParam(defaultValue = "10") long size,
            @RequestParam(required = false) String keyword) {
        requireAdmin(role);
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.select(User::getId, User::getUsername, User::getRole, User::getCreatedAt);
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(User::getUsername, keyword);
        }
        wrapper.orderByDesc(User::getCreatedAt);
        Page<User> result = userService.page(new Page<>(page, size), wrapper);
        List<Map<String, Object>> records = result.getRecords().stream().map(u -> {
            Map<String, Object> m = new HashMap<>();
            m.put("id", u.getId());
            m.put("username", u.getUsername());
            m.put("role", u.getRole());
            m.put("createdAt", u.getCreatedAt() == null ? null : u.getCreatedAt().toString());
            return m;
        }).collect(Collectors.toList());
        Map<String, Object> data = new HashMap<>();
        data.put("records", records);
        data.put("total", result.getTotal());
        data.put("page", result.getCurrent());
        data.put("size", result.getSize());
        return ResponseResult.success(data);
    }

    @PutMapping("/admin/role/{id}")
    public ResponseResult<Void> adminUpdateRole(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long id,
            @RequestParam String roleValue) {
        requireAdmin(role);
        if (!"USER".equals(roleValue) && !"ADMIN".equals(roleValue)) {
            throw new BusinessException(400, "role must be USER or ADMIN");
        }
        User u = userService.getById(id);
        if (u == null) throw new BusinessException(404, "User not found");
        u.setRole(roleValue);
        userService.updateById(u);
        return ResponseResult.success("Role updated", null);
    }

    @DeleteMapping("/admin/{id}")
    public ResponseResult<Void> adminDelete(
            @RequestHeader(value = "X-User-Role", required = false) String role,
            @PathVariable Long id) {
        requireAdmin(role);
        User u = userService.getById(id);
        if (u == null) throw new BusinessException(404, "User not found");
        if ("admin".equals(u.getUsername())) {
            throw new BusinessException(400, "Cannot delete built-in admin");
        }
        userService.removeById(id);
        return ResponseResult.success("User deleted", null);
    }

    private void requireAdmin(String role) {
        if (!"ADMIN".equals(role)) {
            throw new BusinessException(403, "Admin role required");
        }
    }

    private String extractToken(String authorization) {
        if (authorization != null && authorization.startsWith("Bearer ")) {
            return authorization.substring(7);
        }
        return null;
    }
}
