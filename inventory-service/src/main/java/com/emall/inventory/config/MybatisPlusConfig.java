package com.emall.inventory.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.retry.annotation.EnableRetry;

@Configuration
@MapperScan("com.emall.inventory.mapper")
@EnableRetry
public class MybatisPlusConfig {
}
