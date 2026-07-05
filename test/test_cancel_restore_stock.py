"""
Test if cancelling an order restores inventory.
Expected BUG: cancel order does NOT restore stock (current code).
Expected FIX: cancel order DOES restore stock.
"""
import urllib.request
import urllib.error
import json
import time
import random
import pymysql

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


def get_stock_via_api(product_id, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    code, body = call("GET", f"/api/inventory/get/{product_id}", headers=h)
    if code == 200 and body.get("code") == 200:
        d = body.get("data", {})
        return d.get("stock"), d.get("version")
    print(f"    [API stock query fail] HTTP {code}, body={json.dumps(body)[:150]}")
    return None, None


def get_db_stock(product_id):
    """Try DB, fallback to API."""
    try:
        import pymysql
        conn = pymysql.connect(
            host="127.0.0.1", port=3306, user="root", password="123456",
            database="db_inventory", charset="utf8mb4"
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT stock, version FROM inventory WHERE product_id=%s", (product_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
    except Exception as e:
        return None, None  # fallback to API


print("=" * 70)
print("  Test: Cancel Order Should Restore Inventory")
print("=" * 70)

# 1. 选一个 productId, 查初始库存 (需要 token)
PRODUCT_ID = 50
print(f"\n[1] Initial inventory for product {PRODUCT_ID}:")

# 1.0 先登录一个管理员用户拿 token 用于查库存
admin_ts = int(time.time() * 1000) % 1000000
admin_uname = f"admin_view_{admin_ts}_{random.randint(100,999)}"
call("POST", "/api/user/register", {"username": admin_uname, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": admin_uname, "password": "Test@123"})
admin_token = body.get("data", {}).get("token")
init_stock, init_version = get_stock_via_api(PRODUCT_ID, token=admin_token)
print(f"    stock={init_stock}, version={init_version}")
if init_stock is None:
    print("    ABORT: cannot read stock")
    exit(1)

# 2. 注册并登录一个新用户
ts = int(time.time() * 1000) % 1000000
uname = f"restore_test_{ts}_{random.randint(100,999)}"
print(f"\n[2] Register & login: {uname}")
call("POST", "/api/user/register", {"username": uname, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": uname, "password": "Test@123"})
token = body.get("data", {}).get("token")
user_id = body.get("data", {}).get("id")
print(f"    userId={user_id}, token={'YES' if token else 'NO'}")

if not token:
    print("    ABORT: login failed")
    exit(1)

# 3. 创建订单
print(f"\n[3] Create order (productId={PRODUCT_ID}, quantity=1)")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": PRODUCT_ID, "quantity": 1,
                   "address": "库存回滚测试地址abc12345", "remark": "库存测试"},
                  headers={"Authorization": f"Bearer {token}"})
print(f"    HTTP {code}, response: {json.dumps(body, ensure_ascii=False)[:200]}")
order_id = body.get("data", {}).get("orderId")
print(f"    orderId={order_id}")

# 4. 创建订单后查库存
print(f"\n[4] Inventory AFTER create order:")
after_create_stock, after_create_ver = get_stock_via_api(PRODUCT_ID, token=admin_token)
print(f"    stock={after_create_stock}, version={after_create_ver}")
print(f"    diff: stock {init_stock} -> {after_create_stock} (delta={after_create_stock - init_stock})")

# 5. 取消订单
print(f"\n[5] Cancel order (PUT /api/order/cancel/{order_id}?userId={user_id})")
code, body = call("PUT", f"/api/order/cancel/{order_id}?userId={user_id}",
                  headers={"Authorization": f"Bearer {token}"})
print(f"    HTTP {code}, response: {json.dumps(body, ensure_ascii=False)[:200]}")

# 6. 取消订单后查库存
print(f"\n[6] Inventory AFTER cancel order:")
after_cancel_stock, after_cancel_ver = get_stock_via_api(PRODUCT_ID, token=admin_token)
print(f"    stock={after_cancel_stock}, version={after_cancel_ver}")
print(f"    diff vs after_create: {after_cancel_stock - after_create_stock}")
print(f"    diff vs initial:      {after_cancel_stock - init_stock}")

# 7. 结论
print("\n" + "=" * 70)
print("  RESULT")
print("=" * 70)
if after_cancel_stock == after_create_stock:
    print(f"  [BUG CONFIRMED] Stock NOT restored after cancel.")
    print(f"    Initial: {init_stock}, After create: {after_create_stock}, After cancel: {after_cancel_stock}")
    print(f"    Expected: stock should return to {init_stock} after cancel")
else:
    print(f"  [OK] Stock restored after cancel: {after_create_stock} -> {after_cancel_stock}")

# ============================================================
# 8. 边界场景: 多件商品 (quantity=3) 取消
# ============================================================
print("\n" + "=" * 70)
print("  Edge Case 2: Multi-quantity cancel (quantity=3)")
print("=" * 70)
PRODUCT_ID2 = 49  # 用另一个商品
init2_stock, init2_ver = get_stock_via_api(PRODUCT_ID2, token=admin_token)
print(f"\n[2.1] Initial stock of product {PRODUCT_ID2}: {init2_stock}, v={init2_ver}")

# 新用户
ts2 = int(time.time() * 1000) % 1000000
uname2 = f"multi_{ts2}_{random.randint(100,999)}"
call("POST", "/api/user/register", {"username": uname2, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": uname2, "password": "Test@123"})
token2 = body.get("data", {}).get("token")
user_id2 = body.get("data", {}).get("id")

QTY = 3
print(f"\n[2.2] Create order qty={QTY}")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id2, "productId": PRODUCT_ID2, "quantity": QTY,
                   "address": "多件测试地址abc12345", "remark": ""},
                  headers={"Authorization": f"Bearer {token2}"})
order_id2 = body.get("data", {}).get("orderId")
print(f"    orderId={order_id2}, response code={body.get('code')}")

mid2_stock, mid2_ver = get_stock_via_api(PRODUCT_ID2, token=admin_token)
print(f"\n[2.3] After create: stock={mid2_stock} (delta={mid2_stock - init2_stock}, expected -{QTY})")
assert mid2_stock == init2_stock - QTY, f"  [FAIL] create stock not match: {init2_stock}->{mid2_stock}"

print(f"\n[2.4] Cancel order {order_id2}")
code, body = call("PUT", f"/api/order/cancel/{order_id2}?userId={user_id2}",
                  headers={"Authorization": f"Bearer {token2}"})
print(f"    HTTP {code}, code={body.get('code')}, msg={body.get('message')}")

final2_stock, final2_ver = get_stock_via_api(PRODUCT_ID2, token=admin_token)
print(f"\n[2.5] After cancel: stock={final2_stock} (delta vs mid={final2_stock - mid2_stock}, expected +{QTY})")
print(f"    delta vs initial: {final2_stock - init2_stock} (expected 0)")

if final2_stock == init2_stock:
    print(f"  [OK] Multi-quantity cancel correctly restored {QTY} units")
else:
    print(f"  [FAIL] Multi-quantity cancel: expected {init2_stock}, got {final2_stock}")

# ============================================================
# 9. 边界场景: 取消已支付的订单 (应失败, 库存不变)
# ============================================================
print("\n" + "=" * 70)
print("  Edge Case 3: Cancel a paid order (should fail, no stock change)")
print("=" * 70)
PRODUCT_ID3 = 48
init3_stock, _ = get_stock_via_api(PRODUCT_ID3, token=admin_token)
ts3 = int(time.time() * 1000) % 1000000
uname3 = f"paid_{ts3}_{random.randint(100,999)}"
call("POST", "/api/user/register", {"username": uname3, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": uname3, "password": "Test@123"})
token3 = body.get("data", {}).get("token")
user_id3 = body.get("data", {}).get("id")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id3, "productId": PRODUCT_ID3, "quantity": 1,
                   "address": "已支付测试地址abc12345", "remark": ""},
                  headers={"Authorization": f"Bearer {token3}"})
order_id3 = body.get("data", {}).get("orderId")
code, body = call("PUT", f"/api/order/pay/{order_id3}?userId={user_id3}",
                  headers={"Authorization": f"Bearer {token3}"})
print(f"  Order {order_id3} created and paid: code={body.get('code')}")
mid3_stock, _ = get_stock_via_api(PRODUCT_ID3, token=admin_token)
# Try cancel paid order - should fail
code, body = call("PUT", f"/api/order/cancel/{order_id3}?userId={user_id3}",
                  headers={"Authorization": f"Bearer {token3}"})
print(f"  Cancel paid order: HTTP {code}, code={body.get('code')}, msg={body.get('message')}")
final3_stock, _ = get_stock_via_api(PRODUCT_ID3, token=admin_token)
print(f"  Stock: {init3_stock} -> {mid3_stock} (paid) -> {final3_stock} (cancel attempted)")
if final3_stock == mid3_stock and body.get('code') != 200:
    print(f"  [OK] Paid order cancel rejected, stock unchanged")
else:
    print(f"  [WARN] unexpected: code={body.get('code')}, stock change {final3_stock - mid3_stock}")

# ============================================================
# 10. 总结
# ============================================================
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
print(f"  Case 1 (qty=1):       {init_stock} -> {after_create_stock} -> {after_cancel_stock}  {'OK' if after_cancel_stock == init_stock else 'FAIL'}")
print(f"  Case 2 (qty=3):       {init2_stock} -> {mid2_stock} -> {final2_stock}  {'OK' if final2_stock == init2_stock else 'FAIL'}")
print(f"  Case 3 (paid, qty=1): {init3_stock} -> {mid3_stock} -> {final3_stock}  (paid order cancel rejected)")
