# Debug: Gateway CORS + 404 + 503

## Session
- ID: gateway-cors
- Status: [FIXED]

## Symptoms (3 separate issues)
1. Browser CORS preflight failed: `No 'Access-Control-Allow-Origin' header`
2. After CORS fix: 404 — route not matched
3. After route fix: 503 — `lb://` URI not resolved

## Root Causes
1. **CORS**: `AuthGlobalFilter` returned 401 for OPTIONS preflight (no token). No `CorsWebFilter` bean.
2. **404**: `application.yml` indentation wrong. `discovery`, `globalcors`, `routes` were at 2-space depth, making them children of `spring:` instead of `spring.cloud.gateway:`. Gateway loaded 0 routes (`New routes count: 0`).
3. **503**: `spring-cloud-starter-loadbalancer` dependency missing. Gateway used `GatewayNoLoadBalancerClientAutoConfiguration$NoLoadBalancerClientFilter` (returns 503 for `lb://` URIs).

## Fixes Applied
- Created `CorsConfig.java` registering `CorsWebFilter` with `HIGHEST_PRECEDENCE`.
- `AuthGlobalFilter` now skips `OPTIONS` method.
- `application.yml`: Moved `gateway` block to `spring.cloud.gateway` (correct 6-space indentation).
- Added `spring-cloud-starter-loadbalancer` to `gateway/pom.xml`.

## Verification
- Pre-flight `OPTIONS http://localhost:9000/api/product/list` → 200 + CORS headers
- `GET http://localhost:9000/api/product/list?page=1&size=12` → 200, returns product data
- Gateway log: `New routes count: 6` (4 explicit + 2 auto-discovered)
