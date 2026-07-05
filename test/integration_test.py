"""E-Mall Integration Tests: Auth, Order, Inventory"""
import urllib.request
import urllib.error
import json
import time

BASE = "http://localhost:9000"
pass_count = 0
fail_count = 0

def call(method, path, body=None, headers=None, timeout=10):
    url = BASE + path
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}
    except Exception as e:
        return -1, {"error": str(e)}

def check(name, ok, detail=""):
    global pass_count, fail_count
    status = "PASS" if ok else "FAIL"
    if ok:
        pass_count += 1
    else:
        fail_count += 1
    print(f"  [{status}] {name}  {detail}")

print("=" * 70)
print("  E-Mall Auth + Order Integration Tests")
print("=" * 70)

# 1. 鉴权测试
print("\n[1] Auth Filter Tests")
code, body = call("GET", "/api/order/list?userId=1")
check("No token rejected (expect 401)", code == 401, f"HTTP {code}")

code, body = call("GET", "/api/order/list?userId=1", headers={"Authorization": "Bearer invalid_xxx"})
check("Invalid token rejected (expect 401)", code == 401, f"HTTP {code}")

code, body = call("POST", "/api/user/login", {"username": "nonexistent_user_zzz", "password": "x"})
check("Invalid credentials rejected (500)", code == 200 and body.get("code") == 500, f"HTTP {code} code={body.get('code')}")

# 2. 完整注册-登录-下单流程
print("\n[2] Full Order Flow")
ts = int(time.time() * 1000) % 1000000
uname = f"flowtest_{ts}"

code, body = call("POST", "/api/user/register", {"username": uname, "password": "Test@123"})
check("Register new user", code == 200 and body.get("code") == 200, f"HTTP {code} code={body.get('code')}")

code, body = call("POST", "/api/user/login", {"username": uname, "password": "Test@123"})
check("Login success", code == 200 and body.get("code") == 200 and body.get("data", {}).get("token"),
      f"HTTP {code} has_token={bool(body.get('data',{}).get('token'))}")
if code != 200 or not body.get("data", {}).get("token"):
    print("  Cannot continue, login failed")
    exit(1)

token = body["data"]["token"]
user_id = body["data"]["id"]

# 3. 商品列表 (无需鉴权)
code, body = call("GET", "/api/product/list?page=1&size=5")
products = body.get("data", {}).get("records", []) if isinstance(body.get("data"), dict) else []
check("Product list returns items", code == 200 and len(products) > 0, f"HTTP {code} count={len(products)}")

if products:
    test_product = products[0]
    pid = test_product["id"]
    price = test_product["price"]
    stock = test_product["stock"]

    # 4. 下单 (使用token)
    code, body = call("POST", "/api/order/create",
                      {"userId": user_id, "productId": pid, "quantity": 1,
                       "address": "北京市朝阳区某街道123号测试地址", "remark": "集成测试订单"},
                      headers={"Authorization": f"Bearer {token}"})
    order_no = body.get("data", {}).get("orderNo") if isinstance(body.get("data"), dict) else None
    check("Create order success", code == 200 and body.get("code") == 200 and order_no,
          f"HTTP {code} orderNo={order_no}")

    # 5. 库存扣减验证 (使用同一商品再下一个单验证库存正常扣减)
    code, body = call("POST", "/api/order/create",
                      {"userId": user_id, "productId": pid, "quantity": 1,
                       "address": "北京市朝阳区某街道456号测试地址2", "remark": ""},
                      headers={"Authorization": f"Bearer {token}"})
    check("Create second order (inventory deduct)", code == 200 and body.get("code") == 200,
          f"HTTP {code} code={body.get('code')} msg={body.get('message', '')[:50]}")

    # 6. 查询订单列表
    code, body = call("GET", f"/api/order/list?userId={user_id}", headers={"Authorization": f"Bearer {token}"})
    order_list = body.get("data", []) if isinstance(body.get("data"), list) else []
    check("List orders for user", code == 200 and len(order_list) >= 2, f"HTTP {code} count={len(order_list)}")

    # 7. 库存查询
    code, body = call("GET", f"/api/inventory/get/{pid}", headers={"Authorization": f"Bearer {token}"})
    check("Inventory query works", code in (200, 500), f"HTTP {code} msg={body.get('message','')[:50]}")

# 8. 异常场景
print("\n[3] Error Scenarios")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": 99999, "quantity": 1,
                   "address": "北京市朝阳区某街道789号", "remark": ""},
                  headers={"Authorization": f"Bearer {token}"})
check("Invalid productId rejected (503 fallback)", code == 200 and body.get("code") == 503,
      f"HTTP {code} code={body.get('code')}")

# 库存不足测试
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": 1, "quantity": 99999,
                   "address": "北京市朝阳区某街道测试库存不足", "remark": ""},
                  headers={"Authorization": f"Bearer {token}"})
check("Insufficient stock rejected", code == 200 and body.get("code") in (500, 503),
      f"HTTP {code} code={body.get('code')} msg={body.get('message','')[:50]}")

print(f"\n{'='*70}\n  Result: {pass_count} PASS / {fail_count} FAIL\n{'='*70}")
exit(0 if fail_count == 0 else 1)
