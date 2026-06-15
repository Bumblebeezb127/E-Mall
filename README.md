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

执行 `sql/init.sql` 创建数据库与表结构。

#### 2.2 修改数据库账户密码

> 默认配置：`username=root`，`password=dflc72131`，`url=jdbc:mysql://localhost:3306/db_xxx`

如需修改，编辑以下 4 个服务的 `application.yml`：

- `user-service/src/main/resources/application.yml`
- `product-service/src/main/resources/application.yml`
- `order-service/src/main/resources/application.yml`
- `inventory-service/src/main/resources/application.yml`

修改 `spring.datasource` 下的 `username` / `password` / `url` 即可。

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
│   └── init.sql                # 数据库初始化脚本
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

## License

MIT
