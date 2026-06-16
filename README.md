# E-Mall 电商微服务系统

基于 Spring Cloud Alibaba 的微服务电商系统后端 + Vue 3 前端实践项目。

## 技术栈

- **后端**: Spring Boot 2.7 + Spring Cloud 2021 + Spring Cloud Alibaba 2021
- **服务治理**: Nacos（注册中心 + 配置中心）
- **服务调用**: OpenFeign + LoadBalancer
- **流量控制**: Sentinel
- **网关**: Spring Cloud Gateway
- **认证**: JWT (jjwt 0.9.1)
- **持久层**: MyBatis-Plus + MySQL 8
- **前端**: Vue 3 + Vite + Pinia + Vue Router + Axios

## 模块概览

| 模块 | 端口 | 功能 |
|------|------|------|
| `gateway` | 9000 | API 网关，统一入口、路由转发、JWT 鉴权、Sentinel 限流 |
| `user-service` | 8081 | 用户服务，注册、登录、JWT 签发、用户信息 |
| `product-service` | 8082 | 商品服务，商品增删改查、分页查询 |
| `inventory-service` | 8083 | 库存服务，库存查询、扣减、初始化 |
| `order-service` | 8084 | 订单服务，下单、查询；通过 Feign 调用库存服务 |

## 快速开始

### 1. 环境准备

- JDK 1.8+
- Maven 3.6+
- MySQL 8.0+
- Nacos 2.x
- Node.js 16+

### 2. 数据库配置

#### 2.1 初始化数据库

执行 `sql/init.sql` 即可完成**全部数据库初始化**：

```bash
# 用 root 身份执行 (脚本会自动创建专用用户 emall_app 和 149 条初始数据)
mysql -u root -p < sql/init.sql
```

> ⚠️ 脚本开头会**先 `DROP DATABASE` 再重建**，会清空 `db_user / db_product / db_order / db_inventory` 四个库中的所有表。**生产环境请慎用**。

#### 2.2 数据库账户信息

脚本运行后会自动创建如下专用账户（**替代 root，最小权限**）：

| 字段 | 值 |
|------|------|
| 用户名 | `emall_app` |
| 密码 | `Emall@2024` |
| 允许主机 | `localhost` 与 `%`（支持本地 + 远程） |
| 授权范围 | 4 个库（`db_user` / `db_product` / `db_order` / `db_inventory`）的 `SELECT/INSERT/UPDATE/DELETE` + 必要 DDL |

#### 2.3 初始数据概览

执行 `init.sql` 后会自动灌入 **149 条**业务数据（`/sql/init.sql`）：

| 表 | 记录数 | 内容 |
|----|--------|------|
| `db_product.product` | **50** | 涵盖手机/电脑/平板/家电/穿戴/配件 6 大类，¥9.9 - ¥14999 |
| `db_user.user` | **32** | 1 个 admin、3 个 merchant、28 个 user |
| `db_inventory.inventory` | **20** | 关联前 20 个商品，分布在 MAIN / BEIJING / SHANGHAI / GUANGZHOU / SHENZHEN 5 个仓库 |
| `db_order.order` | **20** | 时间跨度 2026-05-01 至 2026-05-10，状态分布齐全 |
| `db_order.order_item` | **27** | 与 order.total_amount 严格一致 |

**默认账号**：
- 管理员：`admin / admin123`
- 普通用户：`user001 / 123456` … `user028 / 123456`

#### 2.4 微服务配置

各微服务 `application.yml` 默认连接此专用账户（`emall_app / Emall@2024`），如果使用本地默认配置，**无需修改即可启动**。

如需修改数据库密码，编辑以下文件中的 `spring.datasource.username` / `spring.datasource.password`：

- `user-service/src/main/resources/application.yml`
- `product-service/src/main/resources/application.yml`
- `order-service/src/main/resources/application.yml`
- `inventory-service/src/main/resources/application.yml`

> 💡 提示：四个 `*-service.yaml` 是 **Nacos 远程拉取配置**，如果 Nacos 上也发布过同名配置，请同时在 Nacos 控制台同步更新密码，否则远程配置会覆盖本地。

### 3. 启动 Nacos

参考 [Nacos 官方文档](https://nacos.io/zh-cn/docs/quick-start.html) 启动单机模式：

```bash
# Linux / Mac
sh nacos/bin/startup.sh -m standalone

# Windows
nacos\bin\startup.cmd -m standalone
```

Nacos 启动后访问控制台：<http://localhost:8080/nacos>（默认账号 `nacos/nacos`）。

### 4. 启动后端服务

在项目根目录依次启动（按依赖顺序）：

```bash
# 1. 编译并安装到本地仓库
mvn clean install -DskipTests

# 2. 启动各服务（在各自模块目录执行 mvn spring-boot:run）
# gateway
cd gateway && mvn spring-boot:run

# user-service
cd user-service && mvn spring-boot:run

# product-service
cd product-service && mvn spring-boot:run

# inventory-service
cd inventory-service && mvn spring-boot:run

# order-service
cd order-service && mvn spring-boot:run
```

或使用 IDE 启动各模块的 `*Application.java` 启动类。

启动完成后，可在 Nacos 控制台「服务管理 → 服务列表」看到全部 5 个服务。

### 5. 启动前端

```bash
cd easybuy-frontend
npm install        # 安装依赖（首次必需）
npm run dev        # 启动开发服务器，默认 http://localhost:5173
```

## 项目结构

```
e-mall/
├── gateway/                    # API 网关
├── user-service/               # 用户服务
├── product-service/            # 商品服务
├── order-service/              # 订单服务
├── inventory-service/          # 库存服务
├── easybuy-frontend/           # 前端项目
├── sql/
│   └── init.sql                # 数据库初始化脚本 (含专用用户 emall_app + 149 条初始数据)
├── postman/
│   └── E-Mall-API-Collection.json  # 接口调试集合
├── jmeter/
│   └── E-Mall-Performance-Test.jmx # 性能测试脚本
├── scripts/                    # 测试脚本
└── pom.xml                     # 父 POM
```

## 接口示例

> 所有非 `/api/user/login`、`/api/user/register` 请求需在 Header 添加 `Authorization: Bearer <token>`

- 用户登录：`POST /api/user/login`
- 用户注册：`POST /api/user/register`
- 商品列表：`GET /api/product/list?page=1&size=10`
- 新增商品：`POST /api/product/add`
- 库存扣减：`POST /api/inventory/deduct`
- 创建订单：`POST /api/order/create`
- 订单详情：`GET /api/order/{id}`

完整接口见 `postman/E-Mall-API-Collection.json`。

## 测试账号 & 快速验证

完成数据库初始化与服务启动后，可通过以下账号验证：

| 账号 | 密码 | 角色 | 说明 |
|------|------|------|------|
| `admin` | `admin123` | ADMIN | 超级管理员 |
| `merchant1` | `123456` | MERCHANT | 华为旗舰店 |
| `merchant2` | `123456` | MERCHANT | 苹果旗舰店 |
| `merchant3` | `123456` | MERCHANT | 小米官方 |
| `user001` ~ `user028` | `123456` | USER | 普通用户（含 1 个已禁用的 `user026`） |

**冒烟测试命令**（需要服务全部启动后）：

```bash
# 1. 登录获取 token
curl -X POST http://localhost:9000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 通过网关获取商品列表（无需 token，白名单接口）
curl http://localhost:9000/api/product/list?page=1\&size=12

# 3. 查询用户订单（需在 Header 加 Bearer token）
curl http://localhost:9000/api/order/list/user/5 \
  -H "Authorization: Bearer <token>"
```

## 常见问题

**Q1：执行 `init.sql` 报 `Incorrect string value` 怎么办？**
A：MySQL 客户端默认使用 GBK 编码。Windows 下请用 `--default-character-set=utf8mb4` 参数：
```bash
mysql -u root -p --default-character-set=utf8mb4 < sql/init.sql
```

**Q2：商品列表返回 404？**
A：检查 `gateway/pom.xml` 是否包含 `spring-cloud-starter-loadbalancer` 依赖，以及 `application.yml` 中 `spring.cloud.gateway.routes` 的缩进（必须在 `spring.cloud` 下）。

**Q3：Nacos 远程配置覆盖了本地密码？**
A：登录 Nacos 控制台（<http://localhost:8080/nacos>），修改对应的 `user-service.yaml / product-service.yaml / order-service.yaml / inventory-service.yaml`，与本地保持一致。

## License

MIT
