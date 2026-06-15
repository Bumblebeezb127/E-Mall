package com.emall.order.config;

import com.alibaba.csp.sentinel.slots.block.RuleConstant;
import com.alibaba.csp.sentinel.slots.block.flow.FlowRule;
import com.alibaba.csp.sentinel.slots.block.flow.FlowRuleManager;
import org.springframework.context.annotation.Configuration;

import javax.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.List;

@Configuration
public class SentinelConfig {

    @PostConstruct
    public void initSentinelRules() {
        List<FlowRule> rules = new ArrayList<>();

        FlowRule createOrderRule = new FlowRule();
        createOrderRule.setResource("createOrder");
        createOrderRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        createOrderRule.setCount(5);
        createOrderRule.setLimitApp("default");
        createOrderRule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT);
        rules.add(createOrderRule);

        FlowRuleManager.loadRules(rules);
        System.out.println("Sentinel flow rules initialized for order-service");
    }
}
