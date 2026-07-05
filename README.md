# E-Mall 电商微服务系统 (Windows)

> 基于 Spring Cloud Alibaba + RabbitMQ + Vue 3 的电商微服务实践。
> 本 README **仅针对 Windows**，其他系统请自行调整命令。

---

## 1. 端口分配 (启动前请确认未被占用)

| 端口 | 用途 | 备注 |
|------|------|------|
| **9000** | API 网关 (Gateway) | 唯一对外入口 |
| 8081 | user-service | 用户 / 鉴权 |
| 8082 | product-service | 商品 |
| 8083 | order-service | 订单 / MQ 发布 |
| 8084 | inventory-service | 库存 |
| 8085 | log-service | 日志查看 (Admin) |
| 8848 | Nacos 控制台 | nacos / nacos |
| 8858 | Sentinel Dashboard | - |
| 15672 | RabbitMQ 管理界面 | guest / guest |
| 5672 | RabbitMQ AMQP | - |
| 3306 | MySQL 8 | - |

> 8080 已被 Trae IDE 占用，故网关改用 9000。

---

## 2. 环境依赖

| 依赖 | 版本 | 验证命令 |
|------|------|----------|
| JDK | 17+ | `java -version` |
| Maven | 3.6+ | `mvn -v` |
| MySQL | 8.0+ | `mysql --version` |
| Nacos | 2.x | 启动后访问 `http://localhost:8848/nacos` |
| RabbitMQ | 3.x | 启动后访问 `http://localhost:15672` |
| Node.js | 16+ | `node -v` |
| Python | 3.8+ | `python --version` (用于测试) |

> 脚本会优先读 `JAVA_HOME` / `MAVEN_HOME` / `NODE_HOME`，缺失时再通过 `where` 自动探测。

---

## 3. 初始化 (首次部署)

### 3.1 启动基础设施

```cmd
:: 1) 启动 MySQL (确保 3306 监听)
:: 2) 启动 Nacos (standalone)
nacos\bin\startup.cmd -m standalone

:: 3) 启动 RabbitMQ (如未启动)
::    默认 guest/guest, 端口 5672 + 15672
```

### 3.2 初始化数据库

```cmd
mysql -u root -p --default-character-set=utf8mb4 < sql\init.sql
mysql -u root -p < sql\upgrade.sql
```

### 3.3 一键前端初始化 (推荐)

```cmd
scripts\frontend-init.bat
```

> 该脚本自动完成: Node 探测 → `npm install` → Nacos 配置推送 → 数据库升级。

### 3.4 一键后端编译

```cmd
scripts\mvn-build.bat
```

> 该脚本自动完成: JDK / Maven 探测 → `mvn clean install -DskipTests`。

---

## 4. 启动 / 停止服务

### 4.1 启动全部 6 个微服务

```cmd
scripts\start-all-services.bat
```

> 后台启动 user / product / inventory / order / log / gateway，
> 启动顺序: user → product → inventory → order → log → gateway。

### 4.2 健康检查

```cmd
:: 网关 + 商品列表 (无需 token)
curl http://localhost:9000/api/product/list?page=1&size=5
```

应返回 HTTP 200 + 商品 JSON 数组。

### 4.3 停止全部服务

```cmd
scripts\stop-all-services.bat
```

---

## 5. 启动前端

```cmd
cd easybuy-frontend
npm run dev
```

浏览器打开: <http://localhost:3000>

测试账号:
- 管理员: `admin` / `admin123`
- 普通用户: 在前端注册页自注册 (用户名 `tester_<时间戳>`, 密码任意)

---

## 6. 验证

### 6.1 自动化测试 (Python)

```cmd
:: 交互模式 (默认): 每按一次回车跑一个测试
scripts\run-all-tests.bat

:: 一次性跑完全部
scripts\run-all-tests.bat --all
```

| 脚本 | 用例数 | 说明 |
|------|--------|------|
| test_product_stock_sync.py | 1 | 商品冗余库存同步 |
| test_cancel_restore_stock.py | 3 | 取消订单库存回滚 |
| sentinel_test.py | 4 | 限流 / 熔断 |
| rabbitmq_test.py | 11 | 消息端到端 |
| admin_test.py | 21 | Admin RBAC |
| integration_test.py | 12 | 鉴权 + 下单 |
| api_test.py | 16 | API 端到端 |
| **Python 小计** | **68** | 全过 |

> 前端另有 6 项 Vitest 单元测试 (`easybuy-frontend\tests\`),
> 全项目测试用例合计 **74** 项, 全部通过。

详细日志: `test\results\*.log`

### 6.2 RabbitMQ 持续观察 (供 Postman / JMeter 配合)

```cmd
scripts\rabbitmq-observe.bat
```

> 持续创建 / 支付 / 取消订单, 让 RabbitMQ 一直有消息流过。
> 浏览器打开 <http://localhost:15672> (guest/guest) 即可看到
> Exchange `emall.order.exchange` 上的实时消息。
> 按 **Ctrl+C** 退出。

### 6.3 接口测试清单 (Postman / JMeter 团队)

参见 [`doc\TEST-CHECKLIST.md`](doc/TEST-CHECKLIST.md) — 涵盖 5 模块 + Admin + Sentinel + RabbitMQ + JMeter 压测建议。

---

## 7. 常用访问地址

| 服务 | 地址 | 凭证 |
|------|------|------|
| 前端 SPA | <http://localhost:3000> | - |
| API 网关 | <http://localhost:9000> | - |
| Nacos 控制台 | <http://localhost:8848/nacos> | nacos / nacos |
| Sentinel Dashboard | <http://localhost:8858> | - |
| RabbitMQ Management | <http://localhost:15672> | guest / guest |

---

## 8. 完整文档

| 文档 | 路径 |
|------|------|
| 需求规格说明书 | `doc\01-需求规格说明书.docx` |
| 系统设计文档 | `doc\02-系统设计文档.docx` |
| 部署文档 | `doc\03-部署文档.docx` |
| 测试报告 | `doc\04-测试报告.docx` |
| 项目总结报告 | `doc\05-项目总结报告.docx` |
| 项目报告 (汇总) | `doc\06-项目报告.docx` |
| 接口测试清单 | `doc\TEST-CHECKLIST.md` |

---

## 9. 目录结构

```
e-mall\
├── gateway\                API 网关
├── user-service\           用户服务
├── product-service\        商品服务
├── inventory-service\      库存服务
├── order-service\          订单服务 (含 RabbitMQ 发布)
├── log-service\            日志服务 (含 RabbitMQ 消费)
├── easybuy-frontend\       Vue 3 前端
├── sql\                    init.sql / upgrade.sql
├── scripts\                启动 / 停止 / 编译 / 观察 / 测试脚本
├── test\                   Python 自动化测试
├── doc\                    项目文档
├── pom.xml                 Maven 父 POM
└── README.md
```
