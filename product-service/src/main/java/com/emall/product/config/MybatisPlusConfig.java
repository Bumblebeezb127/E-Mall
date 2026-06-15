package com.emall.product.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.emall.product.mapper")
public class MybatisPlusConfig {
}
