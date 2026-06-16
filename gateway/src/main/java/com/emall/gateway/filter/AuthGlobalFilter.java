package com.emall.gateway.filter;

import com.emall.gateway.utils.JwtUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.List;

@Component
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    private static final Logger log = LoggerFactory.getLogger(AuthGlobalFilter.class);

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String USER_ID_HEADER = "X-User-Id";
    private static final String BEARER_PREFIX = "Bearer ";

    private static final List<String> WHITE_LIST = Arrays.asList(
            "/api/user/login",
            "/api/user/register",
            "/api/product/list",
            "/api/product/detail"
    );

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        log.info("Authenticating request - path: {}", path);

        // CORS preflight requests should bypass auth
        if (request.getMethod() == org.springframework.http.HttpMethod.OPTIONS) {
            log.info("CORS preflight request, skipping authentication - path: {}", path);
            return chain.filter(exchange);
        }

        if (isWhiteListed(path)) {
            log.info("Path is whitelisted, skipping authentication - path: {}", path);
            return chain.filter(exchange);
        }

        String authHeader = request.getHeaders().getFirst(AUTHORIZATION_HEADER);

        if (authHeader == null || !authHeader.startsWith(BEARER_PREFIX)) {
            log.warn("Authorization header missing or invalid - path: {}", path);
            return unauthorized(exchange.getResponse());
        }

        String token = authHeader.substring(BEARER_PREFIX.length());

        try {
            if (!jwtUtil.validateToken(token)) {
                log.warn("Token validation failed - path: {}", path);
                return unauthorized(exchange.getResponse());
            }

            Long userId = jwtUtil.getUserIdFromToken(token);
            String username = jwtUtil.getUsernameFromToken(token);

            log.info("Token validated successfully - userId: {}, username: {}", userId, username);

            ServerHttpRequest mutatedRequest = request.mutate()
                    .header(USER_ID_HEADER, String.valueOf(userId))
                    .build();

            return chain.filter(exchange.mutate().request(mutatedRequest).build());

        } catch (Exception e) {
            log.error("Token parsing error - path: {}, error: {}", path, e.getMessage());
            return unauthorized(exchange.getResponse());
        }
    }

    private boolean isWhiteListed(String path) {
        return WHITE_LIST.stream().anyMatch(path::startsWith);
    }

    private Mono<Void> unauthorized(ServerHttpResponse response) {
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        return response.setComplete();
    }

    @Override
    public int getOrder() {
        return -100;
    }
}
