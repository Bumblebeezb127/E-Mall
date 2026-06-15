# E-Mall 微服务异常场景测试手册

## 目录

1. [熔断降级测试流程](#场景一熔断降级测试)
2. [配置热更新测试流程](#场景二配置热更新测试)
3. [自动化脚本说明](#脚本说明)

---

## 场景一：熔断降级测试

### 测试目标

验证当 `inventory-service` 不可用时，`order-service` 通过 OpenFeign 调用库存服务会触发 Sentinel 熔断降级，返回友好的错误信息而非直接失败。

### 手动操作步骤

#### STEP 1: 准备测试环境

确保所有服务正常运行：

| 服务 | 端口 | 验证方式 |
|------|------|----------|
| gateway | 8080 | `curl http://localhost:8080/actuator/health` |
| user-service | 8081 | `curl http://localhost:8081/actuator/health` |
| product-service | 8082 | `curl http://localhost:8082/actuator/health` |
| order-service | 8083 | `curl http://localhost:8083/actuator/health` |
| inventory-service | 8084 | `curl http://localhost:8084/actuator/health` |

```bash
# 验证所有服务健康
curl http://localhost:8080/actuator/health
```

#### STEP 2: 正常调用创建订单接口

获取 Token：

```bash
curl -X POST http://localhost:8080/api/user/login ^
     -H "Content-Type: application/json" ^
     -d "{\"username\":\"loadtest\",\"password\":\"password123\"}"
```

响应示例：
```json
{"code":200,"message":"success","data":{"id":1,"username":"loadtest","token":"eyJhbGci..."}}
```

创建订单（正常情况）：

```bash
curl -X POST http://localhost:8080/api/order/create ^
     -H "Content-Type: application/json" ^
     -H "Authorization: Bearer <YOUR_TOKEN>" ^
     -d "{\"userId\":1,\"productId\":1,\"quantity\":1}"
```

响应示例：
```json
{"code":200,"message":"success","data":{"orderId":1,"orderNo":"ORD20240101120000001","totalAmount":3999.00,"status":0}}
```

#### STEP 3: 停止 inventory-service

**方式一：杀掉进程**

```bash
# 查找8084端口进程
netstat -ano | findstr ":8084"

# 假设PID是12345，杀掉进程
taskkill /F /PID 12345
```

**方式二：Docker 方式**

```bash
docker stop inventory-service-container
```

#### STEP 4: 连续调用10次，观察降级响应

```bash
for /L %i in (1,1,10) do @echo === 第 %i 次 === && curl -s -X POST http://localhost:8080/api/order/create -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d "{\"userId\":1,\"productId\":1,\"quantity\":1}" && timeout /t 1 /nobreak > nul
```

**期望的降级响应示例**：

```json
{"code":503,"message":"库存服务繁忙，请稍后重试","data":null}
```

或

```json
{"code":429,"message":"Blocked by Sentinel","data":null}
```

或

```json
{"code":500,"message":"库存服务暂不可用","data":null}
```

#### STEP 5: 验证 Sentinel 控制台

1. 访问 Sentinel Dashboard：`http://localhost:8080` 或 `http://localhost:8858`
2. 进入 **熔断规则** 或 **实时监控**
3. 查看 `inventory-service` 或 `createOrder` 资源
4. 确认熔断器状态为 **OPEN**

#### STEP 6: 重启 inventory-service 并验证恢复

**启动服务**：

```bash
# IDE中启动或命令行启动
java -jar inventory-service.jar
```

或

```bash
docker start inventory-service-container
```

**等待10秒让服务完全启动**：

```bash
timeout /t 10 /nobreak
```

**再次调用订单接口**：

```bash
curl -X POST http://localhost:8080/api/order/create ^
     -H "Content-Type: application/json" ^
     -H "Authorization: Bearer <TOKEN>" ^
     -d "{\"userId\":1,\"productId\":1,\"quantity\":1}"
```

**期望响应**：订单创建成功，`code:200`

---

## 场景二：配置热更新测试

### 测试目标

验证 `product-service` 在不重启服务的情况下，通过 Nacos Config 动态更新配置（如分页大小），业务无中断。

### 手动操作步骤

#### STEP 1: 查看当前配置

调用商品列表接口，记录当前每页返回的记录数：

```bash
curl -s "http://localhost:8080/api/product/list?page=1&size=10"
```

响应示例：
```json
{
  "code": 200,
  "data": {
    "records": [
      {"id": 1, "name": "华为手机", "price": 3999.00, ...},
      ... (共10条)
    ],
    "total": 100,
    "page": 1,
    "size": 10
  }
}
```

#### STEP 2: 修改 Nacos 配置

1. 访问 Nacos 控制台：`http://localhost:8848/nacos`
2. 登录（默认账号：`nacos` / `nacos`）
3. 进入 **配置管理** → **配置列表**
4. 选择 **product** 或 **DEFAULT_GROUP**
5. 找到 Data ID：`product-service.yaml`
6. 修改配置：

**修改前**：
```yaml
page:
  default-size: 10
  max-size: 100
```

**修改后**：
```yaml
page:
  default-size: 20
  max-size: 100
```

7. 点击 **发布**

#### STEP 3: 验证热更新生效

**等待3秒让配置推送生效**：

```bash
timeout /t 3 /nobreak
```

**调用商品列表接口**：

```bash
curl -s "http://localhost:8080/api/product/list?page=1&size=20"
```

或调用默认分页：

```bash
curl -s "http://localhost:8080/api/product/list?page=1"
```

**期望结果**：每页返回的记录数变为 20 条

#### STEP 4: 再次修改配置为5

1. 在 Nacos 控制台再次修改 `product-service.yaml`：

```yaml
page:
  default-size: 5
  max-size: 100
```

2. 点击 **发布**

3. **等待3秒**

4. **验证**：

```bash
curl -s "http://localhost:8080/api/product/list?page=1"
```

**期望结果**：每页返回5条记录

#### STEP 5: 恢复配置

将配置恢复为默认值 `page.size=10`，确保后续测试不受影响。

---

## 脚本说明

### 脚本文件

- **路径**：`scripts/test-scenarios.bat`
- **依赖**：`curl`、`netstat`（Windows自带）

### 使用方法

```bash
cd d:\Learning materials\SpringCloud\e-mall
scripts\test-scenarios.bat
```

### 菜单选项

```
================================================
             请选择测试场景
================================================
  1. 熔断降级测试 (Circuit Breaker)
  2. 配置热更新测试 (Config Hot Update)
  3. 执行全部测试
  4. 退出
================================================
```

### 脚本功能

| 功能 | 说明 |
|------|------|
| 自动获取Token | 调用登录接口并解析token |
| 熔断测试 | 自动调用10次创建订单接口，检测降级响应 |
| 配置测试 | 引导用户手动修改Nacos，验证热更新 |
| 报告生成 | 自动生成测试报告 `test_report_*.txt` |

### 注意事项

1. **inventory-service重启**：脚本提供停止服务命令，但启动需要手动在IDE或命令行中执行

2. **Nacos配置修改**：由于Nacos Open API需要认证，脚本会提示用户手动在控制台修改

3. **报告文件**：测试完成后会在当前目录生成带时间戳的报告文件

---

## 快速验证命令汇总

### 熔断测试

```bash
# 1. 获取Token
curl -X POST http://localhost:8080/api/user/login -H "Content-Type: application/json" -d "{\"username\":\"loadtest\",\"password\":\"password123\"}"

# 2. 正常调用（服务正常时）
curl -X POST http://localhost:8080/api/order/create -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d "{\"userId\":1,\"productId\":1,\"quantity\":1}"

# 3. 停止inventory-service
netstat -ano | findstr ":8084"
taskkill /F /PID <PID>

# 4. 降级测试（服务停止后）
for /L %i in (1,1,10) do @curl -X POST http://localhost:8080/api/order/create -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" -d "{\"userId\":1,\"productId\":1,\"quantity\":1}"

# 5. 验证Sentinel控制台
# 访问 http://localhost:8858 (或配置的Sentinel端口)

# 6. 重启后验证
java -jar inventory-service.jar
curl -X POST http://localhost:8080/api/order/create ...
```

### 配置热更新测试

```bash
# 1. 验证当前配置
curl -s "http://localhost:8080/api/product/list?page=1&size=10" | findstr /C:"id"

# 2. Nacos控制台修改 page.size=20

# 3. 验证热更新
curl -s "http://localhost:8080/api/product/list?page=1&size=20" | findstr /C:"id"

# 4. Nacos控制台修改 page.size=5

# 5. 再次验证
curl -s "http://localhost:8080/api/product/list?page=1&size=5" | findstr /C:"id"
```

---

## 预期测试结果

### 熔断降级测试

| 阶段 | 预期结果 |
|------|----------|
| 正常调用 | `code:200`，订单创建成功 |
| 服务停止后调用 | 部分或全部返回降级信息（`code:503/429`） |
| Sentinel控制台 | 显示熔断器OPEN |
| 重启后调用 | `code:200`，订单创建成功 |

### 配置热更新测试

| 配置值 | 预期每页记录数 |
|--------|----------------|
| `page.size=10` | 10条 |
| `page.size=20` | 20条 |
| `page.size=5` | 5条 |

---

## 故障排查

### 熔断未触发

1. 检查 Sentinel 是否正确集成
2. 确认 Feign Client 配置了 `fallbackFactory`
3. 检查 Sentinel 规则是否正确配置

### 热更新未生效

1. 确认 `@RefreshScope` 注解已添加
2. 检查 Nacos 配置的 Data ID 和 Group 是否匹配
3. 确认 bootstrap.yml 中的 `refresh-enabled: true`
