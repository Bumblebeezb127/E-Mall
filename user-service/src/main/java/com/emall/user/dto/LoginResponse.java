package com.emall.user.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class LoginResponse {

    private String token;
    private String tokenType = "Bearer";
    private Long expiresIn;
    // 登录时一并返回用户基础信息, 避免前端再请求一次 /info
    private Long id;
    private String username;
    private String role = "USER";
}
