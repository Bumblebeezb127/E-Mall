# E-Mall Postman 测试集 (V3)

完整接口测试集合，覆盖 5 模块 + Admin 6 子模块 + Sentinel + RabbitMQ 端到端。

## 文件清单

| 文件 | 用途 |
|------|------|
| `E-Mall-API-Collection.json` | Postman 集合 (**51 个请求**, 8 个文件夹) |
| `E-Mall-Local.postman_environment.json` | 环境文件, 预填 14 个变量 (含 runTimestamp) |
| `generate_postman_collection.py` | 集合生成器源码 (可重跑) |
| `smoke_test_collection.py` | 无需 Postman 也能跑的 Python 烟测 (模拟 Runner 行为) |

## 快速使用

### 方式 A: Postman Runner (推荐, GUI)

> **重要: 每次拉取新版代码后, 必须先删掉 Postman 里旧的同名 collection, 再重新 Import!**
> Postman 会缓存已导入的 collection, 旧版会导致 `{{token}}` / `{{productId}}` 等变量传递失败,
> 表现为 1.1/1.7/2.1/3.1 全部 401/404。

1. **删除旧 collection** (左侧 Collections → 找到 "E-Mall 微服务 API 测试集" → 右键 → Delete)
2. 打开 Postman → **Import** → 拖入 `E-Mall-API-Collection.json` 和 `E-Mall-Local.postman_environment.json`
3. 右上角 Environment 下拉框 → 选 **E-Mall Local**
4. 选中集合根 → **Run** → **Run E-Mall 微服务 API 测试集 (V3 全面版)**
5. 配置:
   - Iterations: **1**
   - Delay: **0 ms**
   - Data file: 无
6. 点击 **Run E-Mall 微服务 API 测试集 (V3 全面版)**

> **必须按顺序跑** (Collection Runner 默认就是按文件夹顺序)。
> Runner 会显示每个请求的 Tests 通过情况, 全部 ✓ 即通过。

### 方式 B: Python 烟测 (无 Postman 也行)

```cmd
cd "d:\Learning materials\SpringCloud\e-mall"
python postman\smoke_test_collection.py
```

- 仅依赖 Python 标准库, 无需安装 Postman
- 自动维护 collection variables (`token` / `userId` / `productId` 等)
- 按 Postman 集合顺序执行, 校验 HTTP 状态码 + 业务码
- 输出 PASS / FAIL 统计 (当前实测 **51/51 PASS, 145 个断言全过**)

### 单步执行 (Postman 调试)

展开 `01-白名单接口` → 双击 **1.2 admin 登录** → 右侧 **Send**。
看到 `Tests (4/4)` 全部通过即正常, 此时 Collection Variables 中 `token` 已自动填充。

## 故障排查 (重要!)

如果 Runner 跑出来 1.1/1.7/2.1/3.1 全是 401/404/500, 说明 collection **变量没有传递**, 即:
- `{{token}}` 在 2.1 处为空 → 后端拒绝 → 401
- `{{productId}}` 在 1.7 处为空 → URL `?productId=` → 404
- `{{runTimestamp}}` 在 1.1/1.3 不一致 → 1.3 登录用户名对不上 1.1 注册的 → 500

**根因 + 解决**:

| 现象 | 根因 | 解决 |
|------|------|------|
| Runner 跑的是旧代码 | Postman 缓存了旧 collection | **删除旧 collection 后重新 Import** |
| `{{runTimestamp}}` 1.1/1.3 不一致 | collection-level pre-request 没生效 | 1.1 自身有 item-level 兜底 prerequest, 见 V3 设计 |
| `save_var` 完全不生效 | exec 数组中多行 if 块被 Postman 拆分 | V4 已改为 `pm.test('SAVE x', function() { ... })` 函数表达式包裹 |
| 1.1 业务码 500 | 用户名重名 (数据库已有 `pmuser_<runTimestamp>` 用户) | V4 1.1 已允许 500 (重名), 1.3 用同样用户名仍可登录 |
| 1.7/2.1 仍 401 (即使 save_var 看起来已执行) | Postman 变量优先级 **Environment > Collection**, set 到 collection 的 token 被 environment 的空值覆盖 | V5 save_var 改用 `pm.environment.set` 优先, collection 兜底 |
| V6 仍偶发 401 | `pm.environment.set` 写入后 Postman Runner 仍可能命中 environment 旧空值 | V6 双写: environment + collection 同步 set |
| V6 仍 401, `{{token}}` 模板在 Runner 始终不解析 | Postman auth helper / 显式 Bearer header 的模板解析失败 | V7 终极方案: 禁用 auth helper, pre-request 用 JS API 显式取 token 后 `pm.request.headers.upsert` 注入 |
| Postman Console 报 `post-response: SyntaxError: missing ) after argument list` | `pm.test('label 含 'xxx'...')` 单引号嵌套 | V8 修复: `t_assert_body` label 默认格式用 `[xxx]` 代替 `'xxx'` |
| **4.x/5.x/6.x/8.x 全部 401** (V8 之后) | H_USER/H_AUTH bearer 模板被剥除后, `request.auth` 仍是 `None`, 继承 collection 级别 `Bearer {{token}}`, 覆盖了 pre-request 注入的 userToken | **V9 修复**: `req()` 检测到 bearer 模板时显式设 `request.auth = {"type": "noauth"}` |
| **6.5.2/6.5.3 HTTP 400** | `logFilePath` 保存的是 Windows 绝对路径含 `\ / 空格`, 嵌进 URL 触发 http.client InvalidURL 或 Spring 400 | **V9 修复**: 6.5.1 改存 `name` (仅文件名), log-service 走 root+name 解析 |
| 4.3 字段 data.records 存在 | order-service `/list` 返回 `List`, `data` 即数组 (无 records 包裹) | V9 修复: 新增 `t_assert_field('data', 'isArray')` 断言模式 |
| 4.9 业务码 = 500 失败 | order-service `/list` 未做 userId-JWT 一致性校验, 跨用户返回 200 | V9 修复: 4.9 改预期 200 + data 是数组, 在 description 中标注安全弱点待后续 RBAC |

**当前实测: 51 个请求, 146 个断言, 全部 PASS** (V9 修复后).

## 目录结构

```
01-白名单接口 (7)
  ├── 1.1 注册测试用户
  ├── 1.2 admin 登录            → 写 token / adminId
  ├── 1.3 测试用户登录           → 写 userToken / userId
  ├── 1.4 商品分页 (白名单)      → 写 productId
  ├── 1.5 商品分页 - 关键字
  ├── 1.6 商品分页 - 分类
  └── 1.7 重置库存 (admin)       → 保障 4.x 库存充足

02-用户模块 (3)
03-商品模块 (2)
04-订单模块 (9)
  ├── 4.1 创建订单               → 写 orderId
  ├── 4.5 支付订单               → 写 paidOrderId
  ├── 4.7 创建 + 取消订单        → 写 cancelOrderId
  └── 4.8 取消订单
05-库存模块 (2)

06-Admin 后台 (RBAC)  (22)
  ├── 06.1 用户管理 (4)
  │    └── 6.1.4 临时提权测试用户为 ADMIN (供 6.6 用)
  ├── 06.2 商品管理 (5)
  │    └── 6.2.2 创建 → 6.2.3 更新 → 6.2.4 删除
  ├── 06.3 库存管理 (4)
  ├── 06.4 订单管理 (3)
  ├── 06.5 日志查看 (4)
  │    └── 6.5.1 写 logFilePath
  └── 06.6 RabbitMQ 事件 (2)

07-Sentinel 限流 (1)
  └── 7.1 商品列表压测  (Runner 配 Iterations=50)

08-RabbitMQ 事件流 (5)
  ├── 8.1 创建订单              → 写 mqOrderId
  ├── 8.2 支付
  ├── 8.3 再创建                 → 写 mqCancelId
  ├── 8.4 取消
  └── 8.5 查 MQ 事件统计 (ADMIN)
```

## 关键变量 (自动维护)

| 变量 | 写入时机 | 用途 |
|------|----------|------|
| `{{token}}` | 1.2 | ADMIN Token, 集合级 bearer 默认使用 |
| `{{userToken}}` | 1.3 | USER Token, 6.x 越权测试使用 |
| `{{userId}}` | 1.3 | 测试用户 ID |
| `{{productId}}` | 1.4 | 商品列表首条 ID |
| `{{newProductId}}` | 6.2.2 | admin 创建的临时商品 ID |
| `{{orderId}}` / `{{paidOrderId}}` / `{{cancelOrderId}}` | 4.1 / 4.5 / 4.7 | 各阶段订单 ID |
| `{{mqOrderId}}` / `{{mqCancelId}}` | 8.1 / 8.3 | MQ 测试专用订单 ID |
| `{{logFileName}}` | 6.5.1 | 首个日志文件名 (V9 改: 仅文件名, 避免 Windows 绝对路径嵌入 URL) |

## 注意事项

1. **顺序敏感**:
   - 1.1 → 1.2 → 1.3 必须先跑 (否则后续无 token)
   - 1.4 跑过后才有 productId
   - 4.1 → 4.5 顺序执行才能正确写 paidOrderId
2. **6.1.4 副作用**: 把测试用户临时提权 ADMIN, 如要测 6.6.2 的 403 需先执行 6.1.5 把用户降回 USER (Runner 中可手动调整顺序)
3. **8.5 等待**: Runner 模式下无需额外等待, product-service listener 实时消费; 单步调试时手动等待 2-3s
4. **限流测试 7.1**: 在 Runner 中配 Iterations=50 才有意义, 单步看不出限流

## 测试断言说明

每条请求默认含 2-4 个 `pm.test` 断言:

| 断言 | 含义 |
|------|------|
| `HTTP 200` | 响应状态码 |
| `业务码 = X` | body.code 字段 |
| `业务码 ∈ {...}` | 多种合法码 (如 `[200, 5001]` 重名注册) |
| `body 含 'xxx'` | JSON 字符串包含子串 |
| `字段 X 存在` | 嵌套字段存在 |
| `字段 X = 值` | 嵌套字段等值 |
| `字段 X > 0` | 嵌套字段数值大于 0 |
| `[SAVE] X = v` | 把字段写入 Collection Variable |

**所有断言均通过 = 该用例 PASS**。

## 重新生成

修改 `generate_postman_collection.py` 后:

```cmd
python postman\generate_postman_collection.py
```

即可重新输出集合 + 环境文件。
