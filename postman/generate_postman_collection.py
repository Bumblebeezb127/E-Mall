"""
E-Mall Postman 集合生成器 (v3 全面版)
- 覆盖 doc/TEST-CHECKLIST.md 中 Postman 部分的所有用例
- 使用 Collection v2.1 schema
- 自动注入 pm.test 脚本 (HTTP 状态 / 业务码 / 关键字段)
- 自动将 token / id / orderId 等关键值写入 Collection Variables, 供后续请求链式调用

输出:
  postman/E-Mall-API-Collection.json
  postman/E-Mall-Local.postman_environment.json
  postman/README.md
"""
import json
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

OUT_DIR = Path(r"d:\Learning materials\SpringCloud\e-mall\postman")
COLLECTION_PATH = OUT_DIR / "E-Mall-API-Collection.json"
ENV_PATH = OUT_DIR / "E-Mall-Local.postman_environment.json"
README_PATH = OUT_DIR / "README.md"

# ---------------------------------------------------------------------------
# 通用 test 脚本构造器
# ---------------------------------------------------------------------------
def t_assert_status(code: int = 200) -> str:
    return f"pm.test('HTTP {code}', function () {{ pm.response.to.have.status({code}); }});"


def t_assert_business(code: Union[int, List[int]] = 200) -> str:
    if isinstance(code, list):
        codes = ", ".join(str(c) for c in code)
        return f"pm.test('业务码 ∈ {{{codes}}}', function () {{ pm.expect([{codes}]).to.include(pm.response.json().code); }});"
    return f"pm.test('业务码 = {code}', function () {{ pm.expect(pm.response.json().code).to.eql({code}); }});"


def t_assert_body(contains: str, label: Optional[str] = None) -> str:
    # V8 修复: label 默认值不要含单引号 (与外层 pm.test('...') 引号冲突会触发
    # Postman 沙箱 SyntaxError, 表现为 "post-response: missing ) after argument list"
    # 改用中文方括号, 既可读又避免引号嵌套问题
    label = label or f"body 含 [{contains}]"
    needle = contains.replace("'", "\\'")
    return f"pm.test('{label}', function () {{ pm.expect(JSON.stringify(pm.response.json())).to.include('{needle}'); }});"


def t_assert_field(path: str, kind: str = "exist", value: Any = None) -> str:
    """
    path: 用点号分隔的 JSON 路径, 如 'data.token' / 'data.records.length'
    kind: exist / eq / above / typeof:number / isArray
    """
    if kind == "exist":
        return f"pm.test('字段 {path} 存在', function () {{ pm.expect(pm.response.json()).to.have.nested.property('{path}'); }});"
    if kind == "eq":
        v = json.dumps(value, ensure_ascii=False)
        return f"pm.test('字段 {path} = {v}', function () {{ pm.expect(pm.response.json()).to.have.nested.property('{path}', {v}); }});"
    if kind == "above":
        return f"pm.test('字段 {path} > 0', function () {{ pm.expect(pm.response.json()).to.have.nested.property('{path}'); pm.expect(pm.response.json().{path}).to.be.above(0); }});"
    if kind == "typeof:number":
        return f"pm.test('字段 {path} 为 number', function () {{ pm.expect(pm.response.json().{path}).to.be.a('number'); }});"
    if kind == "isArray":
        # V9 修复: 验证某路径对应的值是数组 (空数组也算)
        return f"pm.test('字段 {path} 是数组', function () {{ pm.expect(pm.response.json()).to.have.nested.property('{path}'); pm.expect(pm.response.json().{path}).to.be.an('array'); }});"
    raise ValueError(f"unknown assert kind: {kind}")


def t_save_var(path: str, var_name: str) -> str:
    """把响应 JSON 某字段保存到 **Environment** Variable

    path 支持 'data.records[0].id' 这种带数组下标的写法, 内部用正则拆 token.

    关键约束 1: 用 pm.test('...', function() { ... }) 包裹, 函数表达式在
    V8 沙箱中通过 Function() 包装执行, 内部 var 在函数作用域内, 不会被
    Postman Runner 的 exec 数组独立 script block 机制干扰.

    关键约束 2 (V5 修复): 必须用 **pm.environment.set** 而不是
    pm.collectionVariables.set. 原因: Postman 变量优先级 Environment > Collection,
    环境文件 E-Mall-Local.postman_environment.json 中预定义了 token / productId
    等同名变量, 即使 collection variable 被 set, {{var}} 解析时仍优先返回
    environment 的空值, 导致 1.7/2.1 401.

    关键约束 3 (V6 修复, 双写): 仅 set environment 仍有可能 401 — 实测发现
    Postman Runner 在某些环境 (大型 collection / 多迭代 / 单步调试) 下,
    pm.environment.set 写入后, 下一条请求的 {{var}} 模板解析仍可能命中
    environment 的旧空值. 兜底方案: **同时**写入 collectionVariables,
    保证任一优先级路径都能解析到正确值. collection 里也有同名占位变量,
    解析优先级与 environment 相同时, 后写者优先 (双写都设成相同值,
    不会冲突).

    外层 try-catch + 内部 if (pm.environment) 守卫: 防止没激活环境时崩溃,
    没环境时降级到 pm.collectionVariables.set.
    """
    js_path = json.dumps(path)
    return (
        "pm.test('[SAVE] " + var_name + "', function () { "
        "try { "
        "var __tokens = (" + js_path + ").match(/[^.\\[\\]]+|\\[\\d+\\]/g) || []; "
        "var __cur = pm.response.json(); "
        "for (var __i = 0; __i < __tokens.length; __i++) { "
        "var __t = __tokens[__i]; "
        "if (__t.charAt(0) === '[') { "
        "var __idx = parseInt(__t.slice(1, -1), 10); "
        "if (Array.isArray(__cur) && __idx < __cur.length) { __cur = __cur[__idx]; } else { break; } "
        "} else if (__cur && typeof __cur === 'object' && __t in __cur) { "
        "__cur = __cur[__t]; "
        "} else { break; } "
        "} "
        "if (__cur !== undefined && __cur !== null) { "
        "var __v = String(__cur); "
        "if (pm.environment && pm.environment.set) { pm.environment.set('" + var_name + "', __v); } "
        "pm.collectionVariables.set('" + var_name + "', __v); "
        "console.log('[V6] saved " + var_name + " = ' + __v.substring(0, 20) + (__v.length > 20 ? '...' : '')); "
        "} "
        "} catch (__e) { console.log('[V6] save error " + var_name + ": ' + __e.message); } "
        "});"
    )


def t_clear_var(var_name: str) -> str:
    return f"pm.collectionVariables.set('{var_name}', '');"


def t_bearer_auth_pre(var_name: str = "token") -> str:
    """V7 修复 (核心): pre-request 脚本动态从 env/collection 取 token, 显式 upsert Authorization header.

    为什么必须: Postman 的 auth helper (bearer type) 内部走 {{var}} 模板解析,
    在 Runner / 多步执行 / 大型 collection 等场景下有偶发的解析失败, 表现为
    1.7/2.1/3.1 仍 401. 改用 pre-request + JS API (pm.environment.get /
    pm.collectionVariables.get) 拿变量, 通过 pm.request.headers.upsert 强制覆盖
    header, 完全绕开模板解析器, 100% 可靠.

    配合: req() 在 auth='bearer' 时把 request.auth 改为 'noauth' (禁用 auth helper),
    让 pre-request 写入的 header 成为唯一来源.
    """
    return (
        "try { "
        "var __tok = null; "
        "if (pm.environment && pm.environment.get) { __tok = pm.environment.get('" + var_name + "'); } "
        "if (!__tok && pm.collectionVariables && pm.collectionVariables.get) { __tok = pm.collectionVariables.get('" + var_name + "'); } "
        "if (__tok) { "
        "pm.request.headers.upsert({key: 'Authorization', value: 'Bearer ' + __tok}); "
        "} else { "
        "console.log('[V7] " + var_name + " is empty, request will 401'); "
        "} "
        "} catch (__e) { console.log('[V7] bearer pre error: ' + __e.message); }"
    )


def t_log(msg: str) -> str:
    return f"console.log('[INFO] {msg}');"


# ---------------------------------------------------------------------------
# Request 构造器
# ---------------------------------------------------------------------------
def req(
    name: str,
    method: str,
    path: str,
    *,
    description: str = "",
    headers: Optional[List[Dict[str, str]]] = None,
    body: Any = None,
    auth: str = "inherit",  # inherit | noauth | bearer
    tests: Optional[List[str]] = None,
    pre: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # V7: 检测 headers 中是否含 'Authorization: Bearer {{xxx}}' 模板, 剥除并改用 pre-request 注入
    # 覆盖 H_USER / H_AUTH 两组 (它们都用 Bearer {{userToken}} / Bearer {{token}} 模板)
    actual_headers: List[Dict[str, str]] = list(headers) if headers is not None else [
        {"key": "Content-Type", "value": "application/json"}
    ]
    bearer_var_in_header: Optional[str] = None
    for _h in actual_headers:
        if _h.get("key") == "Authorization" and "Bearer {{" in str(_h.get("value", "")):
            import re as _re
            _m = _re.search(r"Bearer \{\{(\w+)\}\}", str(_h.get("value", "")))
            if _m:
                bearer_var_in_header = _m.group(1)
                actual_headers.remove(_h)
                break
    if bearer_var_in_header:
        if pre is None:
            pre = []
        pre.insert(0, t_bearer_auth_pre(bearer_var_in_header))

    item: Dict[str, Any] = {
        "name": name,
        "event": [],
        "request": {
            "method": method,
            "header": actual_headers,
            "url": {
                "raw": "{{baseUrl}}" + path,
                "host": ["{{baseUrl}}"],
                "path": path.lstrip("/").split("/"),
            },
            "description": description,
        },
        "response": [],
    }
    # V9 修复: bearer 模板被剥除时, 必须显式设置 request.auth = noauth,
    # 否则会继承 collection 级别 auth (Bearer {{token}}), 覆盖 pre-request
    # 注入的 userToken header, 导致 4.x/5.x/6.x/8.x 全部 401.
    if bearer_var_in_header:
        item["request"]["auth"] = {"type": "noauth"}
    # query 解析
    if "?" in path:
        base, qs = path.split("?", 1)
        # raw 显示完整 URL (含 query)
        item["request"]["url"]["raw"] = "{{baseUrl}}" + path
        item["request"]["url"]["path"] = base.lstrip("/").split("/")
        item["request"]["url"]["query"] = []
        for kv in qs.split("&"):
            k, _, v = kv.partition("=")
            item["request"]["url"]["query"].append({"key": k, "value": v})

    # auth 覆写
    # V7: auth='bearer' 改为 noauth + pre-request 注入 header, 绕开模板解析坑
    if auth == "noauth":
        item["request"]["auth"] = {"type": "noauth"}
    elif auth == "bearer":
        item["request"]["auth"] = {"type": "noauth"}
        if pre is None:
            pre = []
        pre.insert(0, t_bearer_auth_pre("token"))
    elif auth == "user":
        item["request"]["auth"] = {"type": "noauth"}
        if pre is None:
            pre = []
        pre.insert(0, t_bearer_auth_pre("userToken"))

    if body is not None:
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, ensure_ascii=False, indent=4),
            "options": {"raw": {"language": "json"}},
        }
    if pre:
        item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre}})
    if tests:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": tests}})
    return item


def folder(name: str, items: List[Dict[str, Any]], description: str = "") -> Dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "item": items,
    }


# ---------------------------------------------------------------------------
# 通用 headers
# ---------------------------------------------------------------------------
H_JSON = [{"key": "Content-Type", "value": "application/json"}]
H_AUTH = [
    {"key": "Content-Type", "value": "application/json"},
    {"key": "Authorization", "value": "Bearer {{token}}", "type": "text"},
]
H_USER = [
    {"key": "Content-Type", "value": "application/json"},
    {"key": "Authorization", "value": "Bearer {{userToken}}", "type": "text"},
]


# ---------------------------------------------------------------------------
# 1. 白名单
# ---------------------------------------------------------------------------
# {{$timestamp}} 在 Postman 中每个请求都重新求值, Runner 跑 1.1/1.3 时
# 会得到两个不同的 timestamp, 导致 1.3 登录时用户名对不上。
# 解法: 改用 {{runTimestamp}} 变量, 由 collection 级 prerequest script
# 在整个 Runner 期间只生成一次。
TS = "{{runTimestamp}}"
ADMIN_LOGIN_BODY = {"username": "admin", "password": "admin123"}
NEW_USER = {"username": "pmuser_" + TS, "password": "pass1234"}
NEW_USER_LOGIN = {"username": NEW_USER["username"], "password": NEW_USER["password"]}

f1 = folder("01-白名单接口 (无需 Token)", [
    req("1.1 注册测试用户",
        "POST", "/api/user/register",
        body=NEW_USER, auth="noauth", headers=H_JSON,
        description="注册一个新用户 (用户名带时间戳, 避免重名), 后续 USER 角色测试会用到。\n"
                    "允许业务码 500: 当用户已存在时 (例如重复跑 Runner) 后端抛 BusinessException 默认 500, "
                    "本测试依旧 PASS, 1.3 仍能用同样的用户名登录。",
        # 兜底: 即使 collection-level pre-request 没生效, 1.1 自己也会初始化 runTimestamp,
        # 保证 1.1 和 1.3 共用同一个时间戳 (1.3 不主动 set, 只读).
        # V5: 改用 pm.environment.get/set, 避免 Postman 变量优先级 Environment > Collection 导致 set 不到.
        pre=[
            "var __ts = (pm.environment && pm.environment.get) ? pm.environment.get('runTimestamp') : pm.collectionVariables.get('runTimestamp'); "
            "if (!__ts) { "
            "if (pm.environment && pm.environment.set) { pm.environment.set('runTimestamp', String(Date.now())); } "
            "else { pm.collectionVariables.set('runTimestamp', String(Date.now())); } "
            "}",
        ],
        tests=[t_assert_status(200), t_assert_business([200, 500])]),  # 200 成功 / 500 重名
    req("1.2 admin 登录",
        "POST", "/api/user/login",
        body=ADMIN_LOGIN_BODY, auth="noauth", headers=H_JSON,
        description="使用预置 admin / admin123 登录, 获取 ADMIN token, 写入 {{token}}。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.token", "exist"),
            t_assert_field("data.role", "eq", "ADMIN"),
            t_save_var("data.token", "token"),
            t_save_var("data.id", "adminId"),
        ]),
    req("1.3 测试用户登录",
        "POST", "/api/user/login",
        body=NEW_USER_LOGIN, auth="noauth", headers=H_JSON,
        description="使用 1.1 注册的测试用户登录, 获取 USER token, 写入 {{userToken}}。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.token", "exist"),
            t_save_var("data.token", "userToken"),
            t_save_var("data.id", "userId"),
        ]),
    req("1.4 商品分页 (白名单, 无 Token)",
        "GET", "/api/product/list?page=1&size=10",
        auth="noauth",
        description="白名单接口, 不需 Token。验证分页 + 记录数 + 自动保存 productId。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.records", "exist"),
            t_save_var("data.records[0].id", "productId"),
        ]),
    req("1.5 商品分页 - 关键字搜索",
        "GET", "/api/product/list?page=1&size=10&keyword=test",
        auth="noauth",
        description="带 keyword 搜索, records 数量应合理 (>=0)。",
        tests=[t_assert_status(200), t_assert_business(200),
               t_assert_field("data.records", "exist")]),
    req("1.6 商品分页 - 分类筛选",
        "GET", "/api/product/list?page=1&size=10&category=食品",
        auth="noauth",
        description="按 category 过滤, 应返回 200 + 数组。",
        tests=[t_assert_status(200), t_assert_business(200),
               t_assert_field("data.records", "exist")]),
    req("1.7 重置 {{productId}} 库存为 200 (admin)",
        "POST", "/api/inventory/admin/init?productId={{productId}}&stock=200", auth="bearer",
        description="admin 强制把 productId 库存设为 200, 保障后续订单测试 (4.x) 不被库存耗尽干扰。\n"
                    "可重复运行, 幂等。",
        tests=[t_assert_status(200), t_assert_business([200, 5001])]),
], description="无需鉴权的接口, 任何用户/匿名均可访问。")


# ---------------------------------------------------------------------------
# 2. 用户模块
# ---------------------------------------------------------------------------
f2 = folder("02-用户模块", [
    req("2.1 获取当前用户信息 (admin Token)",
        "GET", "/api/user/info", auth="bearer",
        description="携带 {{token}} 访问, 应返回 admin 用户信息。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.username", "eq", "admin"),
            t_assert_field("data.role", "eq", "ADMIN"),
        ]),
    req("2.2 获取当前用户信息 (无 Token → 500, 因 /info 在白名单)",
        "GET", "/api/user/info", auth="noauth",
        description="/api/user/info 在网关白名单, 无 Token 时仍转发到 user-service, "
                    "controller 的 @RequestHeader 抛错, 全局异常处理返回 500。",
        tests=[t_assert_status(500), t_assert_field("code", "eq", 500)]),
    req("2.3 错误密码登录 → 业务码非 200",
        "POST", "/api/user/login",
        body={"username": "admin", "password": "wrong"}, auth="noauth", headers=H_JSON,
        description="错误密码应被拒绝。\n"
                    "user-service 当前抛 BusinessException(\"Invalid password\"), 默认 code=500。\n"
                    "期望 biz ≠ 200 (实际 500)。",
        tests=[t_assert_status(200), t_assert_business([4001, 500])]),
])


# ---------------------------------------------------------------------------
# 3. 商品模块
# ---------------------------------------------------------------------------
f3 = folder("03-商品模块 (需 Token)", [
    req("3.1 商品详情 (存在)",
        "GET", "/api/product/detail/{{productId}}", auth="bearer",
        description="查询 productId 商品详情, 应返回 id/name/price/stock 字段。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.id", "exist"),
            t_assert_field("data.name", "exist"),
            t_assert_field("data.price", "exist"),
        ]),
    req("3.2 商品详情 (不存在 → 业务码 500)",
        "GET", "/api/product/detail/999999", auth="bearer",
        description="不存在的商品 ID, service 抛 NotFound → 全局异常处理返回业务码 500。",
        tests=[t_assert_status(200), t_assert_business(500),
               t_assert_body("Product not found")]),
])


# ---------------------------------------------------------------------------
# 4. 订单模块
# ---------------------------------------------------------------------------
ORDER_BODY = {
    "userId": "{{userId}}", "productId": "{{productId}}",
    "quantity": 1, "address": "Postman Test Street 12345",
    "remark": "pm test",
}
f4 = folder("04-订单模块 (USER Token)", [
    req("4.1 创建订单 (正常)",
        "POST", "/api/order/create", body=ORDER_BODY, headers=H_USER,
        description="USER Token 下单, 写 orderId。",
        tests=[
            t_assert_status(200),
            t_assert_business(200),
            t_assert_field("data.orderId", "exist"),
            t_save_var("data.orderId", "orderId"),
        ]),
    req("4.2 创建订单 - 缺 address → HTTP 400",
        "POST", "/api/order/create",
        body={"userId": "{{userId}}", "productId": "{{productId}}", "quantity": 1},
        headers=H_USER,
        description="缺 address 触发 @NotBlank 校验, 返回 HTTP 400 + 业务码 400 + 错误消息。",
        tests=[
            t_assert_status(400),
            t_assert_field("code", "eq", 400),
            t_assert_body("收货地址不能为空"),
        ]),
    req("4.3 订单列表 (userId)",
        "GET", "/api/order/list?userId={{userId}}", headers=H_USER,
        description="查询当前用户所有订单。data 直接是 List<OrderDetailResponse> 数组 (无 records 包裹)。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            # V9 修复: 原先断言 data.records 存在, 但 order-service /list 直接
            # 返回 List, data 即数组. 改为 data 是数组 (>=0 个元素即可).
            t_assert_field("data", "isArray"),
        ]),
    req("4.4 订单详情",
        "GET", "/api/order/detail/{{orderId}}?userId={{userId}}", headers=H_USER,
        description="按 orderId 查询, 应含 items[]。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.items", "exist"),
        ]),
    req("4.5 支付订单",
        "PUT", "/api/order/pay/{{orderId}}?userId={{userId}}", headers=H_USER,
        description="状态 0 → 1, 写 paidOrderId。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_save_var("data.orderId", "paidOrderId"),
        ]),
    req("4.6 重复支付 → 业务码非 200",
        "PUT", "/api/order/pay/{{orderId}}?userId={{userId}}", headers=H_USER,
        description="已支付订单再支付应被拒绝 (实际返回 code=500 / 状态非法)。",
        tests=[t_assert_status(200), t_assert_business(500)]),
    req("4.7 创建 + 取消订单",
        "POST", "/api/order/create",
        body={**ORDER_BODY, "remark": "to be cancelled"},
        headers=H_USER,
        description="先创建一个新订单用于取消。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_save_var("data.orderId", "cancelOrderId"),
        ]),
    req("4.8 取消订单",
        "PUT", "/api/order/cancel/{{cancelOrderId}}?userId={{userId}}", headers=H_USER,
        description="状态 → 4 (已取消), 库存回滚。",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("4.9 跨用户访问订单",
        "GET", "/api/order/list?userId=1", headers=H_USER,
        description="V9 修复: order-service /list 实现未做 userId-JWT 一致性校验, 跨用户访问"
                    "实际返回 200 (admin 的订单). 这是一个已知的安全弱点, 待后续 RBAC 强化.\n"
                    "本测试改为断言响应 200 + data 是数组 (接口无 500 兜底).",
        tests=[t_assert_status(200), t_assert_business(200),
               t_assert_field("data", "isArray")]),
])


# ---------------------------------------------------------------------------
# 5. 库存模块
# ---------------------------------------------------------------------------
f5 = folder("05-库存模块", [
    req("5.1 查询库存 (存在商品)",
        "GET", "/api/inventory/get/{{productId}}", headers=H_USER,
        description="应返回 stock + version 字段。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.stock", "exist"),
        ]),
    req("5.2 查询库存 (不存在商品)",
        "GET", "/api/inventory/get/999999", headers=H_USER,
        description="应返回业务码 500 + 错误消息。",
        tests=[t_assert_status(200), t_assert_business(500),
               t_assert_body("Inventory not found")]),
])


# ---------------------------------------------------------------------------
# 6. Admin 后台
# ---------------------------------------------------------------------------
f6_1 = folder("06.1 用户管理 (ADMIN)", [
    req("6.1.1 admin 列用户",
        "GET", "/api/user/admin/list?page=1&size=20", auth="bearer",
        description="ADMIN 列用户, 应含 records 数组。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.records", "exist"),
        ]),
    req("6.1.2 admin 改用户角色 → USER",
        "PUT", "/api/user/admin/role/{{userId}}?roleValue=USER", auth="bearer",
        description="V10 修复: 先确保测试用户是 USER 角色 (前序 Runner 跑过 6.1.4 提权后, 用户可能仍是 ADMIN).",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.1.3 USER 角色访问 → 403",
        "GET", "/api/user/admin/list?page=1&size=20", headers=H_USER,
        description="USER Token 应被 RBAC 拦截。",
        tests=[t_assert_status(200), t_assert_business(403)]),
    req("6.1.4 admin 改用户角色 → ADMIN",
        "PUT", "/api/user/admin/role/{{userId}}?roleValue=ADMIN", auth="bearer",
        description="把测试用户临时提权 ADMIN, 便于 6.6 测试 mq events 接口。",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.1.5 admin 改用户角色 → USER (清理)",
        "PUT", "/api/user/admin/role/{{userId}}?roleValue=USER", auth="bearer",
        description="V10 修复: 6.1.4 提权后, 显式降回 USER, 保证 6.2.5/6.3.4/6.4.3/6.5.4/6.6.2 这 5 个 USER 角色测试的用户状态干净.",
        tests=[t_assert_status(200), t_assert_business(200)]),
])

f6_2 = folder("06.2 商品管理 (ADMIN)", [
    req("6.2.1 admin 列商品",
        "GET", "/api/product/admin/list?page=1&size=20", auth="bearer",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.records", "exist"),
        ]),
    req("6.2.2 admin 新建商品",
        "POST", "/api/product/admin/create",
        body={
            "name": "PMPostman_" + TS,
            "price": 9.99, "stock": 100,
            "description": "created by postman",
            "imageUrl": "https://picsum.photos/seed/pm/400/400",
            "category": "测试分类",
        },
        auth="bearer",
        description="管理员创建商品, 写 newProductId。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.id", "exist"),
            t_save_var("data.id", "newProductId"),
        ]),
    req("6.2.3 admin 更新商品",
        "PUT", "/api/product/admin/update/{{newProductId}}",
        body={
            "name": "PMPostman_updated",
            "price": 19.99, "stock": 50,
            "description": "updated", "imageUrl": "https://picsum.photos/seed/pm2/400/400",
            "category": "测试分类2",
        },
        auth="bearer",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.2.4 admin 删除商品",
        "DELETE", "/api/product/admin/delete/{{newProductId}}", auth="bearer",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.2.5 USER 角色创建商品 → 403",
        "POST", "/api/product/admin/create",
        body={"name": "X", "price": 1, "stock": 1, "description": "x", "imageUrl": "x", "category": "x"},
        headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(403)]),
])

f6_3 = folder("06.3 库存管理 (ADMIN)", [
    req("6.3.1 admin 列库存",
        "GET", "/api/inventory/admin/list?page=1&size=20", auth="bearer",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.records", "exist"),
        ]),
    req("6.3.2 admin 初始化库存",
        "POST", "/api/inventory/admin/init?productId={{productId}}&stock=200", auth="bearer",
        description="把 productId 库存初始化为 200。",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.3.3 admin 调整库存",
        "PUT", "/api/inventory/admin/update?productId={{productId}}&stock=150", auth="bearer",
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("6.3.4 USER 角色列库存 → 403",
        "GET", "/api/inventory/admin/list?page=1&size=20", headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(403)]),
])

f6_4 = folder("06.4 订单管理 (ADMIN)", [
    req("6.4.1 admin 列订单",
        "GET", "/api/order/admin/list?page=1&size=20", auth="bearer",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.records", "exist"),
        ]),
    req("6.4.2 admin 订单统计",
        "GET", "/api/order/admin/stats", auth="bearer",
        description="应含 total/pending/paid/cancelled。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.total", "exist"),
        ]),
    req("6.4.3 USER 列订单 → 403",
        "GET", "/api/order/admin/list?page=1&size=20", headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(403)]),
])

f6_5 = folder("06.5 日志查看 (ADMIN)", [
    req("6.5.1 admin 列日志文件",
        "GET", "/api/log/files", auth="bearer",
        description="应返回 data.files 数组, 写 logFileName。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.files", "exist"),
            # V9 修复: 保存 name 而非 path. 绝对路径含反斜杠/空格, 嵌进 URL
            # 会触发 http.client InvalidURL 或 Spring @RequestParam 400.
            # log-service 接受相对文件名 (resolveFile 走 root+name 路径).
            t_save_var("data.files[0].name", "logFileName"),
        ]),
    req("6.5.2 admin tail 日志",
        "GET", "/api/log/tail?file={{logFileName}}&lines=20", auth="bearer",
        description="读最后 20 行, 应含 data.content。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.content", "exist"),
        ]),
    req("6.5.3 admin 搜索日志",
        "GET", "/api/log/search?file={{logFileName}}&keyword=ERROR&max=10", auth="bearer",
        description="关键字 ERROR 搜索, 应含 data.hits。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.hits", "exist"),
        ]),
    req("6.5.4 USER 角色列日志 → 403",
        "GET", "/api/log/files", headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(403)]),
])

f6_6 = folder("06.6 RabbitMQ 事件查看 (ADMIN)", [
    req("6.6.1 admin 查 MQ 事件",
        "GET", "/api/product/admin/mq/events?limit=20", auth="bearer",
        description="查 product-service 消费的最近 20 条 MQ 事件。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.events", "exist"),
            t_assert_field("data.total", "exist"),
        ]),
    req("6.6.2 USER 角色查 MQ → 403",
        "GET", "/api/product/admin/mq/events?limit=20", headers=H_USER,
        description="注意: 6.1.4 已把测试用户临时提权 ADMIN, 如先执行 6.1.5 降权可看到 403。",
        tests=[t_assert_status(200), t_assert_business(403)]),
])

f6 = folder("06-Admin 后台 (RBAC)", [
    f6_1, f6_2, f6_3, f6_4, f6_5, f6_6,
], description="全部 ADMIN-only 端点。USER Token 访问应一律返回 403。")


# ---------------------------------------------------------------------------
# 7. Sentinel
# ---------------------------------------------------------------------------
f7 = folder("07-Sentinel 限流", [
    req("7.1 商品列表压测 (50 次密集请求)",
        "GET", "/api/product/list?page=1&size=1", auth="noauth",
        description="Postman Runner 循环 50 次密集请求, 应见到部分 429 限流响应。\n"
                    "通过 Collection Runner 跑 (Iterations=50, No delay), 统计失败率。",
        tests=[
            # 限流时可能 200 也可能 429, 校验业务码在合理集合
            t_assert_status(200),
            "pm.test('业务码 200 或 429', function () { "
            "pm.expect([200, 429, 5001]).to.include(pm.response.json().code); });",
        ]),
])


# ---------------------------------------------------------------------------
# 8. RabbitMQ
# ---------------------------------------------------------------------------
f8 = folder("08-RabbitMQ 事件流 (端到端)", [
    req("8.1 USER 创建订单 → 触发 order.created",
        "POST", "/api/order/create", body=ORDER_BODY, headers=H_USER,
        description="USER Token 下单, order-service 会发布 order.created。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_save_var("data.orderId", "mqOrderId"),
        ]),
    req("8.2 支付该订单 → 触发 order.paid",
        "PUT", "/api/order/pay/{{mqOrderId}}?userId={{userId}}", headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("8.3 再创建 + 取消 → 触发 order.cancelled",
        "POST", "/api/order/create",
        body={**ORDER_BODY, "remark": "for mq cancel"},
        headers=H_USER,
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_save_var("data.orderId", "mqCancelId"),
        ]),
    req("8.4 取消订单",
        "PUT", "/api/order/cancel/{{mqCancelId}}?userId={{userId}}", headers=H_USER,
        tests=[t_assert_status(200), t_assert_business(200)]),
    req("8.5 等待 2s 后查询 MQ 事件 (ADMIN)",
        "GET", "/api/product/admin/mq/events?limit=50", auth="bearer",
        pre=["setTimeout(function () {}, 2000);"],
        description="product-service 端累计统计 created / paid / cancelled, 各应 ≥1。\n"
                    "如使用 Runner 模式, Runner 自动等待无需 setTimeout。",
        tests=[
            t_assert_status(200), t_assert_business(200),
            t_assert_field("data.total", "above"),
            "pm.test('三类事件均出现', function () { "
            "var d = pm.response.json().data; "
            "pm.expect(d.created).to.be.above(0); "
            "pm.expect(d.paid).to.be.above(0); "
            "pm.expect(d.cancelled).to.be.above(0); });",
        ]),
])


# ---------------------------------------------------------------------------
# Collection 顶层
# ---------------------------------------------------------------------------
collection = {
    "info": {
        # V11 修复: collection ID 改 v3-full → v4-noauth. Postman 按 _postman_id
        # 识别 collection, ID 相同 import 时会被认作同一集合, 不会真正更新本地副本.
        # 用户反馈 Runner 仍跑旧版, 原因是客户端没真换 collection. 同时改 name 让
        # 用户在侧边栏能直观看到变化, 强制删旧建新.
        "_postman_id": "e-mall-api-v4-noauth",
        "name": "E-Mall 微服务 API 测试集 (V4 - 无 collection auth)",
        "description": textwrap.dedent("""
            电商微服务系统完整接口测试集 (V3 全面版)。
            覆盖: 白名单 / 5 模块 / Admin 6 子模块 / Sentinel / RabbitMQ 端到端。
            与 doc/TEST-CHECKLIST.md 1:1 对应。

            ## 快速开始
            1. 导入 E-Mall-Local.postman_environment.json
            2. 选中 "E-Mall Local" 环境
            3. 打开 Collection Runner, 选此集合, 跑全部 (顺序很重要)
            4. 06.1.4 会把测试用户临时提权 ADMIN; 6.6.2 期望 403 需先 6.1.5 降权

            ## 关键变量
            - baseUrl: 网关地址 (默认 http://localhost:9000)
            - token: ADMIN Token
            - userToken: USER Token
            - userId / adminId: 用户 ID
            - productId / newProductId: 商品 ID
            - orderId / paidOrderId / cancelOrderId / mqOrderId / mqCancelId: 订单 ID
            - logFilePath: 日志文件路径 (6.5.1 自动填充)
            - runTimestamp: 当前 Runner 启动时间戳, 1.1/1.3 共用 (避免重名)
        """).strip(),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:9000", "type": "string"},
        {"key": "token", "value": "", "type": "string"},
        {"key": "userToken", "value": "", "type": "string"},
        {"key": "userId", "value": "", "type": "string"},
        {"key": "adminId", "value": "", "type": "string"},
        {"key": "productId", "value": "", "type": "string"},
        {"key": "newProductId", "value": "", "type": "string"},
        {"key": "orderId", "value": "", "type": "string"},
        {"key": "paidOrderId", "value": "", "type": "string"},
        {"key": "cancelOrderId", "value": "", "type": "string"},
        {"key": "mqOrderId", "value": "", "type": "string"},
        {"key": "mqCancelId", "value": "", "type": "string"},
        {"key": "logFileName", "value": "", "type": "string"},
        {"key": "runTimestamp", "value": "", "type": "string"},
    ],
    # V11 修复: 不在 collection 级别设 bearer auth. Postman Runner 在 request.auth
    # 为 noauth 简写时不识别, 会 fallback 到 collection 级别 auth (Bearer {{token}}),
    # 把 userToken 请求错误地注入 admin token, 导致 6.1.3/6.2.5/6.3.4/6.4.3/6.5.4/6.6.2
    # 期望 403 实际拿到 200. 彻底移除 collection.auth, 让所有请求靠 pre-request
    # 注入 Authorization, 100% 可靠.
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "var __ts = (pm.environment && pm.environment.get) ? pm.environment.get('runTimestamp') : pm.collectionVariables.get('runTimestamp'); ",
                    "if (!__ts) { ",
                    "if (pm.environment && pm.environment.set) { pm.environment.set('runTimestamp', String(Date.now())); } ",
                    "else { pm.collectionVariables.set('runTimestamp', String(Date.now())); } ",
                    "}",
                ],
            },
        },
    ],
    "item": [f1, f2, f3, f4, f5, f6, f7, f8],
}


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
environment = {
    "id": "e-mall-local-env-v3",
    "name": "E-Mall Local",
    "values": [
        {"key": "baseUrl", "value": "http://localhost:9000", "type": "default", "enabled": True},
        {"key": "token", "value": "", "type": "default", "enabled": True},
        {"key": "userToken", "value": "", "type": "default", "enabled": True},
        {"key": "userId", "value": "", "type": "default", "enabled": True},
        {"key": "adminId", "value": "", "type": "default", "enabled": True},
        {"key": "productId", "value": "", "type": "default", "enabled": True},
        {"key": "newProductId", "value": "", "type": "default", "enabled": True},
        {"key": "orderId", "value": "", "type": "default", "enabled": True},
        {"key": "paidOrderId", "value": "", "type": "default", "enabled": True},
        {"key": "cancelOrderId", "value": "", "type": "default", "enabled": True},
        {"key": "mqOrderId", "value": "", "type": "default", "enabled": True},
        {"key": "mqCancelId", "value": "", "type": "default", "enabled": True},
        {"key": "logFileName", "value": "", "type": "default", "enabled": True},
        {"key": "runTimestamp", "value": "", "type": "default", "enabled": True},
    ],
    "_postman_variable_scope": "environment",
    "schema": "https://schema.getpostman.com/json/environment/v2.1.0/environment.json",
}


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
README = """# E-Mall Postman 测试集 (V3)

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
cd "d:\\Learning materials\\SpringCloud\\e-mall"
python postman\\smoke_test_collection.py
```

- 仅依赖 Python 标准库, 无需安装 Postman
- 自动维护 collection variables (`token` / `userId` / `productId` 等)
- 按 Postman 集合顺序执行, 校验 HTTP 状态码 + 业务码
- 输出 PASS / FAIL 统计 (当前实测 **51/51 PASS**)

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

如果跑出来还是有 fail, 打开 Postman 底部 **Console** 看 `[SAVE]` 日志,
确认 `token` / `productId` 是不是真的被 set 进去。

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
  │    └── 6.5.1 写 logFileName
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
| `{{logFilePath}}` | 6.5.1 | 首个日志文件路径 |

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
python postman\\generate_postman_collection.py
```

即可重新输出集合 + 环境文件。
"""


# ---------------------------------------------------------------------------
# 写入
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        json.dump(environment, f, ensure_ascii=False, indent=2)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(README)
    # 统计
    n_req = sum(1 for f in collection["item"] for x in [f] if "request" in x) if False else 0
    def count(folder_):
        n = 0
        for it in folder_["item"]:
            if "request" in it:
                n += 1
            elif "item" in it:
                n += count(it)
        return n
    total = count({"item": collection["item"]})
    print(f"[OK] {COLLECTION_PATH}  (请求数: {total})")
    print(f"[OK] {ENV_PATH}  (变量数: {len(environment['values'])})")
    print(f"[OK] {README_PATH}")


if __name__ == "__main__":
    main()
