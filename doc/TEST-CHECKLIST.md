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

> **V10 修复**: Postman Runner 自动化用例中 6.1 序列重构为
> 6.1.1 列用户 → 6.1.2 admin 改 → USER → 6.1.3 USER 访问期望 403 →
> 6.1.4 admin 提权 ADMIN → **6.1.5 admin 降回 USER (关键清理步骤, 不要删!)**.
> 缺少 6.1.5 会导致 6.2.5/6.3.4/6.4.3/6.5.4/6.6.2 这 5 个 USER 越权测试拿到 200 而非 403.

### 6.2 商品管理
| # | Method | Path | Body | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|------|
| 6.2.1 | GET  | `/api/product/admin/list?page=1&size=20` | - | 200 | 业务码 403 |
| 6.2.2 | POST | `/api/product/admin/create` | `{name, price, stock, description, imageUrl, category}` | 200, data.id | 业务码 403 |
| 6.2.3 | PUT  | `/api/product/admin/update/{id}` | 同上 | 200 | 业务码 403 |
| 6.2.4 | DELETE | `/api/product/admin/delete/{id}` | - | 200 | 业务码 403 |
| 6.2.5 | POST | `/api/product/admin/create` (USER) | 同上 | 业务码 403 | - |

### 6.3 库存管理
| # | Method | Path | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|
| 6.3.1 | GET  | `/api/inventory/admin/list?page=1&size=20` | 200 | 业务码 403 |
| 6.3.2 | POST | `/api/inventory/admin/init?productId={pid}&stock={n}` | 200 | 业务码 403 |
| 6.3.3 | PUT  | `/api/inventory/admin/update?productId={pid}&stock={n}` | 200 | 业务码 403 |
| 6.3.4 | GET  | `/api/inventory/admin/list?page=1&size=20` (USER) | 业务码 403 | - |

### 6.4 订单管理
| # | Method | Path | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|
| 6.4.1 | GET  | `/api/order/admin/list?page=1&size=20` | 200 | 业务码 403 |
| 6.4.2 | GET  | `/api/order/admin/stats` | 200, data.total / pending / paid / cancelled | 业务码 403 |
| 6.4.3 | GET  | `/api/order/admin/list?page=1&size=20` (USER) | 业务码 403 | - |

### 6.5 日志查看
| # | Method | Path | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|
| 6.5.1 | GET  | `/api/log/files` | 200, data.files[] | 业务码 403 |
| 6.5.2 | GET  | `/api/log/tail?file={name}&lines=50` | 200, data.content | 业务码 403 |
| 6.5.3 | GET  | `/api/log/search?file={name}&keyword=ERROR&max=20` | 200, data.hits | 业务码 403 |
| 6.5.4 | GET  | `/api/log/files` (USER) | 业务码 403 | - |

> **V9 修复**: 6.5.x 的 file 参数只存文件名 (`{{logFileName}}`), 不存绝对路径.
> Windows 绝对路径含反斜杠/空格, 嵌进 URL 会触发 http.client InvalidURL 或 Spring @RequestParam 400.

### 6.6 RabbitMQ 事件查看
| # | Method | Path | 期望 (ADMIN) | 期望 (USER) |
|---|--------|------|------|------|
| 6.6.1 | GET  | `/api/product/admin/mq/events?limit=20` | 200, data.events[] (含 eventType/orderId/eventTime) | 业务码 403 |
| 6.6.2 | GET  | `/api/product/admin/mq/events?limit=20` (USER) | 业务码 403 | - |

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
- [ ] **Postman 集合必须用 V4 (`e-mall-api-v4-noauth`)**: 旧 V3 集合有 Runner auth fallback 陷阱
  (V11 修复), 必须**先彻底删除** Postman 侧边栏旧集合再 Import 新 JSON, 否则 6 个 USER 越权
  测试会拿到 200 而非 403

---

## 11. Postman 自动化测试

> 详细报告见 `04-测试报告.docx 八点九、Postman 接口验证` 章节.
> 简要说明:
>
> - **集合**: `postman/E-Mall-API-Collection.json` (52 个请求, 8 个文件夹, 148 条断言)
> - **环境**: `postman/E-Mall-Local.postman_environment.json` (14 个变量)
> - **生成器**: `postman/generate_postman_collection.py` (可重跑, 改完代码后 `python postman/generate_postman_collection.py` 重新生成)
> - **新man 验证**: `newman run postman/E-Mall-API-Collection.json -e postman/E-Mall-Local.postman_environment.json --reporters cli` → **52 requests / 148 assertions / 0 failed**
> - **Postman Runner 验证**: 142 / 6 失败 → V10 角色状态管理 + V11 集合缓存 + noauth 修复 → **148 / 0 失败**
> - **Python 模拟**: `python postman/simulate_runner.py` 端到端模拟 1.1-6.6.2 完整 Runner 流程, 用于快速复现 RBAC 问题

### 11.1 集合结构 (52 个请求)

| 文件夹 | 数量 | 说明 |
|--------|------|------|
| 01-白名单接口 (无需 Token) | 7 | 注册 / 登录 / 商品分页 / 库存初始化 |
| 02-用户模块 | 3 | 获取信息 / 错误密码 |
| 03-商品模块 (需 Token) | 2 | 详情 / 不存在 |
| 04-订单模块 (USER Token) | 9 | 创建 / 支付 / 取消 / 列表 / 详情 / 跨用户 |
| 05-库存模块 | 2 | 查询 / 不存在 |
| 06-Admin 后台 (RBAC) | 24 | 6 子模块 × admin 操作 + USER 越权 |
| 07-Sentinel 限流 | 1 | 50 次密集请求 |
| 08-RabbitMQ 事件流 (端到端) | 5 | 触发 3 类事件 + 查统计 |

### 11.2 关键修复 (V5-V11)

| 版本 | 修复 | 涉及用例 |
|------|------|----------|
| V5 | t_save_var 改 pm.test 包裹 + 1.1 接受 500 业务码 | 1.1-1.7 |
| V6 | 双写 pm.environment.set + pm.collectionVariables.set | 1.7 / 2.1 |
| V7 | H_USER/H_AUTH 模板剥除 + pre-request 注入 | 4.x / 5.x / 6.x / 8.x |
| V8 | t_assert_body label 用方括号避免引号嵌套 | 3.2 |
| V9 | request.auth = {"type": "noauth"} + logFileName 改存文件名 + isArray 断言 | 4.x/5.x/6.x/8.x (54 失败 → 全过) |
| V10 | 6.1 角色状态管理 + 6.1.5 显式降权 | 6.1.2/6.2.5/6.3.4/6.4.3/6.5.4/6.6.2 |
| V11 | 删除 collection.auth + 改 collection ID/name | 上述 6 个 RBAC 测试 |

---

**变更日志**

| 日期 | 修订人 | 修订内容 |
|------|--------|----------|
| 2026-07-05 | 后端组 | 初版 (覆盖 5 模块 + Admin + Sentinel + RabbitMQ + JMeter 建议) |
| 2026-07-06 | 后端组 | V9-V11 修复: 同步 6.1.2/6.2.5/6.3.4/6.4.3/6.5.4/6.6.2 实际 403 行为, logFileName 字段名, 6.5.x/6.6.x 表格扩展 USER 越权列, 新增 §11 Postman 自动化测试章节 |
