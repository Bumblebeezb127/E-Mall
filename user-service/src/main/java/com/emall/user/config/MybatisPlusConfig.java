package com.emall.user.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.emall.user.mapper")
public class MybatisPlusConfig {
}
