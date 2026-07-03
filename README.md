# E-Mall 电商微服务系统

基于 Spring Cloud Alibaba + Vue 3 的电商微服务实践项目。后端拆分为 5 个 Spring Boot 服务，通过 Nacos 做服务治理、Sentinel 做流量控制、OpenFeign 做服务调用；前端是 Vue 3 + Vite + Element Plus 单页应用。

## 技术栈

| 类别 | 选型 |
|------|------|
| 后端框架 | Spring Boot 2.7 / Spring Cloud 2021 / Spring Cloud Alibaba 2021 |
| 服务治理 | Nacos (注册中心 + 配置中心) |
| 服务调用 | OpenFeign + Spring Cloud LoadBalancer |
| 流量控制 | Sentinel |
| API 网关 | Spring Cloud Gateway |
| 认证鉴权 | JWT (jjwt 0.9.1) |
| 持久层 | MyBatis-Plus + MySQL 8 |
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Axios + Element Plus |

## 模块概览

| 模块 | 端口 | 职责 |
|------|------|------|
| `gateway` | **9000** | API 网关，唯一对外入口，路由转发 + JWT 鉴权 + Sentinel 限流 |
| `user-service` | 8081 | 用户服务，注册/登录、JWT 签发 |
| `product-service` | 8082 | 商品服务，商品 CRUD、分页查询、库存同步 |
| `order-service` | 8083 | 订单服务，下单/支付/取消，通过 Feign 调用 product + inventory |
| `inventory-service` | 8084 | 库存服务，库存查询/扣减/回滚，乐观锁防超卖 |

> ⚠️ 端口 8080 已被 Trae IDE 占用，故网关改用 9000；Sentinel Dashboard 使用 8858。

## 目录结构

```
e-mall/
├── gateway/                # API 网关模块
├── user-service/           # 用户服务
├── product-service/        # 商品服务
├── inventory-service/      # 库存服务
├── order-service/          # 订单服务
├── easybuy-frontend/       # Vue 3 前端项目
├── sql/                    # 数据库脚本 (init.sql / upgrade.sql)
├── scripts/                # 启动/停止/配置推送等运维脚本
├── postman/                # Postman 接口集合
├── jmeter/                 # JMeter 性能测试脚本
├── pom.xml                 # Maven 父 POM
└── README.md
```

## 1. 环境准备

| 依赖 | 版本 |
|------|------|
| JDK | 17+ (项目使用 JDK_17.0.12) |
| Maven | 3.6+ |
| MySQL | 8.0+ |
| Nacos Server | 2.x |
| Node.js | 16+ |

## 2. 初始化

### 2.1 数据库

```bash
mysql -u root -p --default-character-set=utf8mb4 < sql/init.sql
```

脚本会先 `DROP` 再重建 4 个库 `db_user / db_product / db_order / db_inventory`，并创建专用账户 `emall_app / Emall@2024`，灌入 149 条初始数据。

> 详细账号、数据分布、字符集问题见 [`scripts/TEST-GUIDE.md`](scripts/TEST-GUIDE.md)。

### 2.2 Nacos 配置推送（可选）

如使用本地 `application.yml` 默认值可跳过。如需将仓库内的 Nacos 配置推到 Nacos Server：

```bash
python scripts/push_nacos_configs.py
```

## 3. 构建

### 3.1 后端

```bash
# 在项目根目录一次性编译并安装所有模块到本地 Maven 仓库
mvn clean install -DskipTests
```

构建产物在 `<module>/target/<module>-1.0.0-SNAPSHOT.jar`。

### 3.2 前端

```bash
cd easybuy-frontend
npm install
```

## 4. 运行

### 4.1 启动 Nacos

```bash
# Linux / macOS
sh nacos/bin/startup.sh -m standalone

# Windows
nacos\bin\startup.cmd -m standalone
```

控制台：<http://localhost:8848/nacos> （`nacos / nacos`）

### 4.2 启动后端（任选其一）

**方式 A：一键脚本（推荐）**

```bash
# Windows
scripts\start-all-services.bat

# 或 Python 版（跨平台）
python scripts/start_services.py
```

**方式 B：手动启动**

按依赖顺序在各模块目录执行 `mvn spring-boot:run`，或用 IDE 启动各模块的 `*Application.java`。

启动顺序：`user-service` → `product-service` → `inventory-service` → `order-service` → `gateway`

```bash
# user-service
cd user-service && mvn spring-boot:run
# 另起终端
cd product-service && mvn spring-boot:run
# 另起终端
cd inventory-service && mvn spring-boot:run
# 另起终端
cd order-service && mvn spring-boot:run
# 另起终端
cd gateway && mvn spring-boot:run
```

**停止所有服务：**

```bash
python scripts/stop_services.py
```

### 4.3 启动前端

```bash
cd easybuy-frontend
npm run dev
```

默认访问：<http://localhost:3000>（Vite 配置）

### 4.4 健康检查

| 服务 | 端点 |
|------|------|
| 网关 | <http://localhost:9000/api/product/list?page=1&size=5> |
| 用户 | <http://localhost:8081/actuator/health> |
| 商品 | <http://localhost:8082/actuator/health> |
| 订单 | <http://localhost:8083/actuator/health> |
| 库存 | <http://localhost:8084/actuator/health> |
| Nacos | <http://localhost:8848/nacos> |

## 5. 快速验证

```bash
# 登录获取 token
curl -X POST http://localhost:9000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 通过网关拉取商品列表（白名单，无需 token）
curl http://localhost:9000/api/product/list?page=1&size=12
```

完整接口见 [`postman/E-Mall-API-Collection.json`](postman/E-Mall-API-Collection.json)。

## License

MIT
