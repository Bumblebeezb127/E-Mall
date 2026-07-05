# E-Mall 接口测试清单 (Postman / JMeter)

> 本清单由后端开发组整理，供接口测试组 (Postman / JMeter) 单独执行。
> 任何变更请同步更新本文件。

---

## 0. 测试环境

| 项目 | 值 |
|------|-----|
| Gateway | `http://localhost:9000` |
| 管理员账号 | `admin` / `admin123` (已预置, 角色 `ADMIN`) |
| 普通账号 | 测试时自注册 `POST /api/user/register` (用户名 `tester_<timestamp>`, 密码 `pass1234`) |
| 鉴权方式 | `Authorization: Bearer <token>` (登录后获取) |
| 统一响应 | `{"code": 业务码, "message": "msg", "data": {...}}` |
| 业务成功 | HTTP 200 + `code=200` |
| 业务失败 | HTTP 200 + `code=4001/4003/4004/4005/5001...` (见各端点备注) |
| 未鉴权 | HTTP 401 + `code=401` |
| 越权访问 | HTTP 200 + `code=403` (部分场景) 或 HTTP 403 |

> 注：所有请求经 Gateway (9000) 转发，白名单接口无需 Token。

---

## 1. 白名单接口 (无需 Token)

| # | Method | Path | 说明 | 期望 |
|---|--------|------|------|------|
| 1.1 | POST | `/api/user/register` | 用户注册 | 200 / 业务 200 |
| 1.2 | POST | `/api/user/login` | 用户登录 | 200 / 业务 200, data.token 非空 |
| 1.3 | GET  | `/api/product/list?page=1&size=10` | 商品分页 (白名单) | 200, data.records 数组 |
| 1.4 | GET  | `/api/product/list?page=1&size=10&keyword=xxx` | 关键字搜索 | 200, records 数量合理 |
| 1.5 | GET  | `/api/product/list?page=1&size=10&category=xxx` | 按分类搜索 | 200 |

**Postman 用例要点**
- 1.1 重复注册同名用户 → 业务码非 200 (一般为 5001)
- 1.2 错误密码登录 → 业务码非 200 (一般为 4001)
- 1.4 keyword=`<不存在的关键字>` → records 长度为 0

---

## 2. 用户模块 (需 Token, USER 或 ADMIN 角色)

| # | Method | Path | Body / Query | 期望 |
|---|--------|------|------|------|
| 2.1 | GET  | `/api/user/info` | - | 200, data 含 id/username/role |
| 2.2 | GET  | `/api/user/info` | 无 Token | 业务码 401 |
| 2.3 | GET  | `/api/user/info` | 过期 / 伪造 Token | 业务码 401 |

---

## 3. 商品模块 (需 Token, USER 角色)

| # | Method | Path | 期望 |
|---|--------|------|------|
| 3.1 | GET  | `/api/product/detail/{id}` | 200, data 含 id/name/price/stock |
| 3.2 | GET  | `/api/product/detail/999999` | 业务码非 200 (商品不存在) |
| 3.3 | GET  | `/api/product/list?page=1&size=20` (Token 方式) | 200 |

---

## 4. 订单模块 (需 Token, USER 角色)

| # | Method | Path | Body / Query | 期望 |
|---|--------|------|------|------|
| 4.1 | POST | `/api/order/create` | `{userId, productId, quantity:1, address:"5-200字符", remark}` | 200, data.orderId |
| 4.2 | POST | `/api/order/create` | 缺 address | 业务码非 200 (参数校验) |
| 4.3 | POST | `/api/order/create` | quantity 超库存 | 业务码非 200 (库存不足) |
| 4.4 | GET  | `/api/order/list?userId={uid}` | - | 200, records 数组 |
| 4.5 | GET  | `/api/order/detail/{oid}?userId={uid}` | - | 200, 含 items[] |
| 4.6 | PUT  | `/api/order/pay/{oid}?userId={uid}` | - | 200, 状态 0→1 |
| 4.7 | PUT  | `/api/order/pay/{oid}?userId={uid}` | 重复支付 | 业务码非 200 (状态非法) |
| 4.8 | PUT  | `/api/order/cancel/{oid}?userId={uid}` | - | 200, 状态 0→4, 库存回滚 |
| 4.9 | GET  | `/api/order/list?userId={otherUid}` | 跨用户访问 | 业务码 403 |

**业务约束**: 创建订单 address 5~200 字符；quantity 必须 ≥1。

---

## 5. 库存模块 (需 Token, USER 角色)

| # | Method | Path | 期望 |
|---|--------|------|------|
| 5.1 | GET  | `/api/inventory/get/{productId}` | 200, data 含 stock + version |
| 5.2 | GET  | `/api/inventory/get/999999` | 业务码非 200 |

---

## 6. Admin 后台 (需 Token, **ADMIN** 角色, USER 角色应为 403)

### 6.1 用户管理
| # | Method | Path | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|
| 6.1.1 | GET | `/api/user/admin/list?page=1&size=20` | 200, data.records | 业务码 403 |
| 6.1.2 | PUT | `/api/user/admin/role/{uid}?roleValue=USER` | 200 | 业务码 403 |
| 6.1.3 | PUT | `/api/user/admin/role/{uid}?roleValue=ADMIN` | 200 | 业务码 403 |
| 6.1.4 | DELETE | `/api/user/admin/delete/{uid}` | 200 | 业务码 403 |

### 6.2 商品管理
| # | Method | Path | Body | 期望 (ADMIN) |
|---|--------|------|------|------|
| 6.2.1 | GET  | `/api/product/admin/list?page=1&size=20` | - | 200 |
| 6.2.2 | POST | `/api/product/admin/create` | `{name, price, stock, description, imageUrl, category}` | 200, data.id |
| 6.2.3 | PUT  | `/api/product/admin/update/{id}` | 同上 | 200 |
| 6.2.4 | DELETE | `/api/product/admin/delete/{id}` | - | 200 |

### 6.3 库存管理
| # | Method | Path | 期望 (ADMIN) |
|---|--------|------|------|
| 6.3.1 | GET  | `/api/inventory/admin/list?page=1&size=20` | 200 |
| 6.3.2 | POST | `/api/inventory/admin/init?productId={pid}&stock={n}` | 200 |
| 6.3.3 | PUT  | `/api/inventory/admin/update?productId={pid}&stock={n}` | 200 |

### 6.4 订单管理
| # | Method | Path | 期望 (ADMIN) |
|---|--------|------|------|
| 6.4.1 | GET  | `/api/order/admin/list?page=1&size=20` | 200 |
| 6.4.2 | GET  | `/api/order/admin/stats` | 200, data.total / pending / paid / cancelled |
| 6.4.3 | PUT  | `/api/order/admin/pay/{oid}` | 200 |
| 6.4.4 | PUT  | `/api/order/admin/cancel/{oid}` | 200 |
| 6.4.5 | DELETE | `/api/order/admin/delete/{oid}` | 200 |

### 6.5 日志查看
| # | Method | Path | 期望 (ADMIN) |
|---|--------|------|------|
| 6.5.1 | GET  | `/api/log/files` | 200, data.files[] |
| 6.5.2 | GET  | `/api/log/tail?file={path}&lines=50` | 200, data.content |
| 6.5.3 | GET  | `/api/log/search?file={path}&keyword=ERROR&max=20` | 200, data.hits |

### 6.6 RabbitMQ 事件查看
| # | Method | Path | 期望 (ADMIN) |
|---|--------|------|------|
| 6.6.1 | GET  | `/api/product/admin/mq/events?limit=20` | 200, data.events[] (含 eventType/orderId/eventTime) |
| 6.6.2 | GET  | `/api/product/admin/mq/events?limit=20` (USER) | 业务码 403 |

---

## 7. Sentinel 限流 (Gateway 维度)

| # | Method | Path | 期望 |
|---|--------|------|------|
| 7.1 | 50 次 / 秒密集请求 `/api/product/list` | - | 部分请求被限流 (业务码 429 或 503) |
| 7.2 | 检查 Sentinel Dashboard `http://localhost:8858` | - | 实时 QPS/拒绝数 与测试吻合 |

---

## 8. RabbitMQ 事件流 (端到端)

| # | 步骤 | 期望 |
|---|------|------|
| 8.1 | 登录 admin, 创建/支付/取消订单 (触发 3 类事件) | 业务 200 |
| 8.2 | `GET /api/product/admin/mq/events?limit=20` | 200, total≥3, created/paid/cancelled 各≥1 |
| 8.3 | 等待 2s, 查看 `log-service` 落盘文件 `logs/order-events-YYYY-MM-DD.log` | 出现 3 条以上事件, 含 `orderId=`, `eventId=`, `eventType=` |
| 8.4 | RabbitMQ Management UI `http://localhost:15672` | Exchange `emall.order.exchange` 出现新消息, Queues 各有累积 |

> 持续观察请运行 `scripts\rabbitmq-observe.bat`。

---

## 9. JMeter 性能测试建议

| 场景 | 线程数 | Ramp-Up | 循环 | 目标 |
|------|--------|---------|------|------|
| 商品分页 (GET, 白名单) | 200 | 5s | 50 | P99 < 200ms, 错误率 < 1% |
| 用户登录 (POST) | 50 | 5s | 20 | P99 < 500ms, 错误率 < 1% |
| 下单 (POST, 需鉴权) | 50 | 5s | 20 | P99 < 800ms, 错误率 < 2% (含库存乐观锁重试) |
| 订单查询 (GET) | 100 | 5s | 30 | P99 < 300ms |
| Sentinel 压测 | 500 | 1s | 10 | 验证限流触发, 错误率符合阈值 |

> 通过 `python scripts/jmeter_setup.py` 或 GUI 启动 JMeter；
> 结果文件放 `jmeter/results/` (已在 .gitignore 中排除)。

---

## 10. 验收清单 (Tester 自检)

- [ ] 所有 §1 ~ §6 用例 (合计 ~50 个) 全部 PASS
- [ ] §7 限流测试中至少看到 1 次拒绝
- [ ] §8 RabbitMQ 端到端测试 4 个步骤全过
- [ ] §9 JMeter 5 个场景结果文件均产出
- [ ] 异常路径 (§1.1 重名, §2.2 无 Token, §3.2 商品不存在, §4.3 库存不足, §6.x USER 越权) 全部返回预期错误码
- [ ] 截图保存 Postman Runner / JMeter Summary Report / RabbitMQ Management → 提交给后端组归档

---

**变更日志**

| 日期 | 修订人 | 修订内容 |
|------|--------|----------|
| 2026-07-05 | 后端组 | 初版 (覆盖 5 模块 + Admin + Sentinel + RabbitMQ + JMeter 建议) |
