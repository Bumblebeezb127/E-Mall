package com.emall.order.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.emall.order.mapper")
public class MybatisPlusConfig {
}
