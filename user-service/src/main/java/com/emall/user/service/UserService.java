package com.emall.user.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.emall.user.dto.LoginResponse;
import com.emall.user.dto.RegisterRequest;
import com.emall.user.dto.UserInfoResponse;
import com.emall.user.entity.User;

public interface UserService extends IService<User> {

    void register(RegisterRequest request);

    LoginResponse login(String username, String password);

    UserInfoResponse getUserInfo(Long userId);

    User findByUsername(String username);
}
