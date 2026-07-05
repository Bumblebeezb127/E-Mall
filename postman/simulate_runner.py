"""Simulate Postman Runner end-to-end: 1.1-1.3, 6.1.1-6.1.5, 6.2.5, 6.3.4, 6.4.3, 6.5.4, 6.6.2."""
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:9000"
RUN_TS = str(int(time.time() * 1000))


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers=h)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "body": e.read().decode()}


def get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "body": e.read().decode()}


def put(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {}, method="PUT")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "body": e.read().decode()}


def show(label, r, expect_business=None):
    code = r.get("code", r.get("_http", "?"))
    msg = r.get("message", "")[:40]
    mark = "OK" if code == expect_business else "!!"
    print(f"  [{mark}] {label} → code={code} {msg}")


print(f"=== Simulating Runner (runTimestamp={RUN_TS}) ===\n")

# 1.1 注册
new_user = f"pmuser_{RUN_TS}"
r = post("/api/user/register", {"username": new_user, "password": "pass1234"})
show("1.1 register", r, expect_business=200)

# 1.2 admin 登录
r = post("/api/user/login", {"username": "admin", "password": "admin123"})
admin_token = r["data"]["token"]
admin_role = r["data"].get("role")
show("1.2 admin login", r, expect_business=200)
print(f"     admin role in JWT = {admin_role}")

# 1.3 user 登录
r = post("/api/user/login", {"username": new_user, "password": "pass1234"})
user_token = r["data"]["token"]
user_id = r["data"]["id"]
user_role = r["data"].get("role")
show("1.3 user login", r, expect_business=200)
print(f"     user role in JWT = {user_role}, id = {user_id}")

h_admin = {"Authorization": "Bearer " + admin_token}
h_user = {"Authorization": "Bearer " + user_token}

# 6.1.1 admin 列用户
print()
r = get("/api/user/admin/list?page=1&size=20", headers=h_admin)
show("6.1.1 admin list", r, expect_business=200)

# 6.1.2 admin 改 userId → USER
r = put(f"/api/user/admin/role/{user_id}?roleValue=USER", headers=h_admin)
show("6.1.2 admin → USER", r, expect_business=200)

# 6.1.3 USER 访问 /admin/list
r = get("/api/user/admin/list?page=1&size=20", headers=h_user)
show("6.1.3 USER list (期望 403)", r, expect_business=403)

# 6.1.4 admin 改 → ADMIN
r = put(f"/api/user/admin/role/{user_id}?roleValue=ADMIN", headers=h_admin)
show("6.1.4 admin → ADMIN", r, expect_business=200)

# 6.1.5 admin 改 → USER (清理)
r = put(f"/api/user/admin/role/{user_id}?roleValue=USER", headers=h_admin)
show("6.1.5 admin → USER (清理)", r, expect_business=200)

# 6.2.5 USER 创建商品
print()
r = post("/api/product/admin/create",
         {"name": "X", "price": 1, "stock": 1, "description": "x", "imageUrl": "x", "category": "x"},
         headers=h_user)
show("6.2.5 USER create (期望 403)", r, expect_business=403)

# 6.3.4 USER 列库存
r = get("/api/inventory/admin/list?page=1&size=20", headers=h_user)
show("6.3.4 USER list inventory (期望 403)", r, expect_business=403)

# 6.4.3 USER 列订单
r = get("/api/order/admin/list?page=1&size=20", headers=h_user)
show("6.4.3 USER list orders (期望 403)", r, expect_business=403)

# 6.5.4 USER 列日志
r = get("/api/log/files", headers=h_user)
show("6.5.4 USER list logs (期望 403)", r, expect_business=403)

# 6.6.2 USER 查 MQ
r = get("/api/product/admin/mq/events?limit=20", headers=h_user)
show("6.6.2 USER mq events (期望 403)", r, expect_business=403)
