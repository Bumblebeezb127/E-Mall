"""
Test product.stock 冗余字段同步 (V3 fix).
确认:
  - 创建订单后, product.stock 减少
  - 取消订单后, product.stock 恢复
"""
import urllib.request
import urllib.error
import json
import time
import random

BASE = "http://localhost:9000"

def call(method, path, body=None, headers=None, timeout=15):
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


def get_product_stock(product_id):
    code, body = call("GET", f"/api/product/detail/{product_id}")
    if code == 200 and body.get("code") == 200:
        return body.get("data", {}).get("stock")
    return None


print("=" * 70)
print("  Test: product.stock sync with inventory (V3)")
print("=" * 70)

PRODUCT_ID = 50
QTY = 2

# 1. Initial product.stock
print(f"\n[1] Initial product.stock for product {PRODUCT_ID}:")
init_prod_stock = get_product_stock(PRODUCT_ID)
print(f"    product.stock = {init_prod_stock}")
if init_prod_stock is None:
    print("    ABORT")
    exit(1)

# 2. Register/login user
ts = int(time.time() * 1000) % 1000000
uname = f"prod_sync_{ts}_{random.randint(100,999)}"
call("POST", "/api/user/register", {"username": uname, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": uname, "password": "Test@123"})
token = body.get("data", {}).get("token")
user_id = body.get("data", {}).get("id")
print(f"\n[2] User registered: id={user_id}")

# 3. Create order qty=2
print(f"\n[3] Create order qty={QTY}")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": PRODUCT_ID, "quantity": QTY,
                   "address": "库存同步测试地址abc12345", "remark": ""},
                  headers={"Authorization": f"Bearer {token}"})
print(f"    HTTP {code}, code={body.get('code')}, msg={body.get('message')[:100]}")
order_id = body.get("data", {}).get("orderId")
print(f"    orderId = {order_id}")

# 4. product.stock after create
print(f"\n[4] product.stock AFTER create order qty={QTY}:")
after_create_prod = get_product_stock(PRODUCT_ID)
print(f"    product.stock = {after_create_prod} (delta={after_create_prod - init_prod_stock}, expected -{QTY})")

# 5. Cancel order
print(f"\n[5] Cancel order {order_id}")
code, body = call("PUT", f"/api/order/cancel/{order_id}?userId={user_id}",
                  headers={"Authorization": f"Bearer {token}"})
print(f"    HTTP {code}, code={body.get('code')}, msg={body.get('message')[:100]}")

# 6. product.stock after cancel
print(f"\n[6] product.stock AFTER cancel order:")
after_cancel_prod = get_product_stock(PRODUCT_ID)
print(f"    product.stock = {after_cancel_prod} (delta={after_cancel_prod - init_prod_stock}, expected 0)")

# 7. RESULT
print("\n" + "=" * 70)
print("  RESULT")
print("=" * 70)
expected_create = init_prod_stock - QTY
expected_cancel = init_prod_stock
print(f"  Case: create qty={QTY} then cancel")
print(f"  Initial:   {init_prod_stock}")
print(f"  After -:   {after_create_prod}  (expected {expected_create}, {'OK' if after_create_prod == expected_create else 'FAIL'})")
print(f"  After +:   {after_cancel_prod}  (expected {expected_cancel}, {'OK' if after_cancel_prod == expected_cancel else 'FAIL'})")

if after_create_prod == expected_create and after_cancel_prod == expected_cancel:
    print("\n  [PASS] product.stock 冗余字段同步工作正常")
else:
    print("\n  [FAIL] product.stock 未正确同步")
