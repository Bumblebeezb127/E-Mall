package com.emall.gateway.config;

import com.alibaba.csp.sentinel.adapter.gateway.common.rule.GatewayFlowRule;
import com.alibaba.csp.sentinel.adapter.gateway.common.rule.GatewayRuleManager;
import com.alibaba.csp.sentinel.adapter.gateway.sc.SentinelGatewayFilter;
import com.alibaba.csp.sentinel.adapter.gateway.sc.exception.SentinelGatewayBlockExceptionHandler;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.codec.ServerCodecConfigurer;
import org.springframework.web.reactive.result.view.ViewResolver;

import javax.annotation.PostConstruct;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Configuration
public class SentinelGatewayConfig {

    @Bean
    public GatewayFilter sentinelGatewayFilter() {
        return new SentinelGatewayFilter();
    }

    @Bean
    public SentinelGatewayBlockExceptionHandler sentinelGatewayBlockExceptionHandler(
            ObjectProvider<List<ViewResolver>> viewResolvers,
            ServerCodecConfigurer serverCodecConfigurer) {
        return new SentinelGatewayBlockExceptionHandler(
                viewResolvers.getIfAvailable(Collections::emptyList),
                serverCodecConfigurer
        );
    }

    @PostConstruct
    public void initRules() {
        Set<GatewayFlowRule> rules = new HashSet<>();

        rules.add(new GatewayFlowRule("user-service")
                .setCount(5000)
                .setIntervalSec(1));

        rules.add(new GatewayFlowRule("product-service")
                .setCount(5000)
                .setIntervalSec(1));

        rules.add(new GatewayFlowRule("order-service")
                .setCount(5000)
                .setIntervalSec(1));

        rules.add(new GatewayFlowRule("inventory-service")
                .setCount(5000)
                .setIntervalSec(1));

        GatewayRuleManager.loadRules(rules);
    }
}