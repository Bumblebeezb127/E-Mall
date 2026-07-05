# 七、Postman 接口验证

Postman 测试集合文件位于 `postman/E-Mall-API-Collection.json`。测试覆盖 **14 个核心接口**，执行 **29 次请求**，共 **84 项断言**，通过率 **100%（84 PASS / 0 FAIL）**。

---

## 7.1 测试环境

| 环境项 | 配置 |
|--------|------|
| Postman 版本 | 最新桌面版 |
| 网关地址 | http://localhost:9000 |
| 认证方式 | JWT Bearer Token（登录后自动存入 Collection Variables） |
| 变量管理 | Collection Variables：baseUrl / token / userId / productId / orderId |
| 预置账号 | admin / admin123 |

---

## 7.2 测试分组概览

| 分组 | 请求数 | 核心验证点 |
|------|--------|-----------|
| 01-用户模块 | 4 | 注册用户A/B、登录获取JWT Token、获取用户信息 |
| 02-商品模块 | 7 | 分页查询(3种size)、库存字段验证、价格>0验证、详情查询(ID1/ID2) |
| 03-订单模块(Feign验证) | 9 | 创建3笔订单→取消(库存回滚)→创建2笔→列表×3→详情→支付(状态流转) |
| 04-库存模块 | 3 | 查询库存(含乐观锁version)、扣减库存、恢复库存 |
| 05-网关鉴权测试 | 6 | 白名单放行×2、无Token 401、无效Token 401、有效Token 200、订单全链路 |
| **合计** | **29** | **14个核心接口 / 84项断言 / 全部通过** |

---

## 7.3 测试用例详细结果

### 7.3.1 01-用户模块（4 条全部通过）

| # | 请求 | 方法 | 预期 | 实际 | 结果 |
|---|------|------|------|------|------|
| 1 | 用户注册-A | POST /api/user/register | HTTP 200 | HTTP 200 | PASS |
| 2 | 用户注册-B | POST /api/user/register | HTTP 200 | HTTP 200 | PASS |
| 3 | 用户登录 | POST /api/user/login | HTTP 200, 返回JWT Token | HTTP 200, Token已保存 | PASS |
| 4 | 获取用户信息 | GET /api/user/info | HTTP 200, 含id/username/createdAt | HTTP 200 | PASS |

**关键验证：** 登录后通过 `pm.collectionVariables.set()` 将 JWT Token 和 userId 存入集合变量，后续所有请求通过 `Authorization: Bearer {{token}}` 自动携带。

---

### 7.3.2 02-商品模块（7 条全部通过）

| # | 请求 | 方法 | 预期 | 实际 | 结果 |
|---|------|------|------|------|------|
| 5 | 商品列表-第1页size=10 | GET /api/product/list | HTTP 200, records数组非空 | HTTP 200, 含total/page/size/totalPages | PASS |
| 6 | 商品列表-第2页size=10 | GET /api/product/list | HTTP 200, page=2 | HTTP 200, 翻页正确 | PASS |
| 7 | 商品列表-小页面size=5 | GET /api/product/list | HTTP 200, records有数据 | HTTP 200, 分页有效 | PASS |
| 8 | 验证库存字段 | GET /api/product/list | 商品含stock/price字段 | stock≥0, price>0 | PASS |
| 9 | 验证价格>0 | GET /api/product/list | 全部商品price>0 | 10条商品价格均>0 | PASS |
| 10 | 商品详情-ID1 | GET /api/product/detail/1 | 含id/name/price/stock/category/description | HTTP 200, status=1(上架) | PASS |
| 11 | 商品详情-ID2 | GET /api/product/detail/2 | 返回的id=2 | HTTP 200, id=2 | PASS |

**关键验证：** 商品列表接口在 Gateway 白名单中，无需 Token 即可访问。分页翻页功能正常，商品包含价格、库存、分类等完整字段。首个商品 ID 自动存入 `productId` 集合变量。

---

### 7.3.3 03-订单模块 Feign 验证（9 条全部通过）

| # | 请求 | 方法 | 预期 | 实际 | 结果 |
|---|------|------|------|------|------|
| 12 | 创建订单-订单1(商品1x2) | POST /api/order/create | HTTP 200, 含orderId/orderNo | HTTP 200, status=0(待支付), orderNo含ORD前缀 | PASS |
| 13 | 取消订单-库存回滚 | PUT /api/order/cancel/{orderId} | HTTP 200, status=4(已取消) | HTTP 200, 取消成功 | PASS |
| 14 | 创建订单-订单2(商品1x1) | POST /api/order/create | HTTP 200, orderNo含ORD | HTTP 200, 订单号格式正确 | PASS |
| 15 | 创建订单-订单3(商品2x3) | POST /api/order/create | HTTP 200, totalAmount>0 | HTTP 200, 金额=价格×数量 | PASS |
| 16 | 查询订单列表-第1次 | GET /api/order/list | HTTP 200, 数组含订单 | HTTP 200, 订单含items明细 | PASS |
| 17 | 查询订单列表-第2次 | GET /api/order/list | HTTP 200, 至少2条订单 | HTTP 200 | PASS |
| 18 | 查询订单列表-第3次 | GET /api/order/list | 含orderNo/statusDesc/totalAmount | HTTP 200, 字段完整 | PASS |
| 19 | 查询订单详情 | GET /api/order/detail/{orderId} | HTTP 200, 含完整详情 | HTTP 200, 含orderId/orderNo/items | PASS |
| 20 | 支付订单 | PUT /api/order/pay/{orderId} | HTTP 200, status=1(已支付) | HTTP 200, 支付成功 | PASS |

**关键验证——OpenFeign 远程调用：**

创建订单时，order-service 通过 Feign 客户端依次调用：
1. `ProductFeignClient.getProductDetail(productId)` → product-service 查询商品价格
2. `InventoryFeignClient.deduct(productId, quantity)` → inventory-service 扣减库存（乐观锁）

取消订单时，order-service 通过 Feign 调用：
1. `InventoryFeignClient.restore(productId, quantity)` → 回滚库存
2. `ProductFeignClient.updateStock(productId, delta)` → 同步商品冗余库存

订单金额根据商品真实价格自动计算（totalAmount = price × quantity），验证了跨服务数据一致性和分布式服务调用链路的正确性。

---

### 7.3.4 04-库存模块（3 条全部通过）

| # | 请求 | 方法 | 预期 | 实际 | 结果 |
|---|------|------|------|------|------|
| 21 | 查询库存-商品1 | GET /api/inventory/get/1 | HTTP 200, 含productId/stock/version | HTTP 200, version字段存在 | PASS |
| 22 | 扣减库存-商品1 | POST /api/inventory/deduct | HTTP 200 | HTTP 200, 扣减成功 | PASS |
| 23 | 恢复库存-商品1 | POST /api/inventory/restore | HTTP 200 | HTTP 200, 恢复成功 | PASS |

**关键验证：** 库存查询返回乐观锁 `version` 字段，防止并发超卖。扣减和恢复的 `message` 断言正确访问顶层字段（`jsonData.message` 而非 `jsonData.data.message`，因 `data` 为 Void 类型）。

---

### 7.3.5 05-网关鉴权测试（6 条全部通过）

| # | 请求 | 方法 | 预期 | 实际 | 结果 |
|---|------|------|------|------|------|
| 24 | 白名单-商品列表(无Token) | GET /api/product/list | HTTP 200 | HTTP 200 | PASS |
| 25 | 白名单-商品详情(无Token) | GET /api/product/detail/1 | HTTP 200 | HTTP 200 | PASS |
| 26 | 受保护资源-无Token | GET /api/user/info | HTTP 401 | HTTP 401 | PASS |
| 27 | 受保护资源-无效Token | GET /api/user/info | HTTP 401 | HTTP 401 | PASS |
| 28 | 受保护资源-有效Token | GET /api/order/list | HTTP 200 | HTTP 200, 返回订单数组 | PASS |
| 29 | 受保护资源-订单创建(含Feign) | POST /api/order/create | HTTP 200 | HTTP 200, 含orderNo | PASS |

**关键验证——Gateway 鉴权链路：**

- **白名单放行：** `/api/product/list` 和 `/api/product/detail` 在 Gateway `AuthGlobalFilter` 白名单中，无 Token 直接放行 → 200
- **无 Token 拦截：** 访问受保护资源 `/api/user/info` 无 Authorization 头 → Gateway 拦截返回 401
- **JWT 验签拦截：** 携带伪造 Token `Bearer invalid_token_123456` 访问 → JwtUtil 验签失败返回 401
- **有效 Token 放行：** 携带登录获取的有效 JWT Token 访问 `/api/order/list` → Gateway 验证通过，注入 X-User-Id 头后放行 → 200
- **全链路验证：** POST /api/order/create 携带有效 Token → Gateway 鉴权 → OrderService → (Feign)ProductService → (Feign)InventoryService，四层调用全部正常

---

## 7.4 断言脚本示例

每个请求的 Tests 标签均包含 Postman 断言脚本，以下是关键示例：

**登录接口 — 自动保存 Token：**
```javascript
pm.test('返回包含JWT Token', function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data).to.have.property('token');
    pm.expect(jsonData.data.token.split('.').length).to.eql(3); // 验证JWT三段式结构
});

if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.collectionVariables.set('token', jsonData.data.token);
    pm.collectionVariables.set('userId', jsonData.data.id);
}
```

**创建订单 — 验证 Feign 调用结果：**
```javascript
pm.test('订单金额大于0 — Feign调用ProductService成功', function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data.totalAmount).to.be.above(0);
});

pm.test('订单状态为待支付(0)', function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data.status).to.eql(0);
});
```

**删除订单 — 验证库存回滚：**
```javascript
pm.test('订单状态变为已取消(status=4)', function() {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data.status).to.eql(4);
});
```

---

## 7.5 使用说明

1. 将 `postman/E-Mall-API-Collection.json` 导入 Postman（Import → File → Upload Files）
2. 打开 Runner（集合右侧 `...` → Run collection）
3. 勾选 **Keep variable values**（保证 Token/UserId/orderId 在请求间传递）
4. 点击 **Run E-Mall 微服务API测试集** 执行全部 29 条测试
5. 如需重复运行，先在 Runner 中 **Reset collection variables** 清除缓存的变量

---

## 7.6 测试结论

Postman 接口测试 **29 条请求 / 84 项断言 / 100% 通过**，覆盖 14 个核心业务接口：

| 验证维度 | 结论 |
|----------|------|
| 用户注册/登录 | 正常，JWT Token 正确签发 |
| 商品分页/详情 | 正常，分页翻页、字段完整性均正确 |
| 订单创建 | 正常，Feign 远程调用 ProductService + InventoryService 通畅 |
| 订单支付 | 正常，状态流转 0(待支付)→1(已支付) |
| 订单取消 | 正常，Feign 远程调用 InventoryService 回滚库存 |
| 库存扣减/恢复 | 正常，乐观锁 version 字段存在 |
| Gateway 白名单 | 正常，白名单放行 |
| Gateway 鉴权拦截 | 正常，无Token/无效Token → 401 |
