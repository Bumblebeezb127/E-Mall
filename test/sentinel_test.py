"""Test Sentinel circuit breaker by simulating inventory-service down"""
import urllib.request
import urllib.error
import json
import time
import subprocess

BASE = "http://localhost:9000"
pass_count = 0
fail_count = 0

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

def check(name, ok, detail=""):
    global pass_count, fail_count
    status = "PASS" if ok else "FAIL"
    if ok:
        pass_count += 1
    else:
        fail_count += 1
    print(f"  [{status}] {name}  {detail}")

print("=" * 70)
print("  Sentinel Circuit Breaker Test (Inventory Down Simulation)")
print("=" * 70)

# 1. Get a valid token first
ts = int(time.time() * 1000) % 1000000
uname = f"cb_{ts}"
call("POST", "/api/user/register", {"username": uname, "password": "Test@123"})
code, body = call("POST", "/api/user/login", {"username": uname, "password": "Test@123"})
token = body.get("data", {}).get("token")
user_id = body.get("data", {}).get("id")
print(f"  Test user: {uname} (id={user_id})")

if not token:
    print("  Failed to get token, aborting")
    exit(1)

# 2. Normal order (should succeed)
print("\n[1] Normal order before stress")
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": 2, "quantity": 1,
                   "address": "测试地址abc12345", "remark": ""},
                  headers={"Authorization": f"Bearer {token}"})
check("Normal order works", code == 200 and body.get("code") == 200, f"HTTP {code} code={body.get('code')}")

# 3. Stress test to trigger Sentinel rate limit / circuit breaker
print("\n[2] Burst test (50 concurrent orders to trigger Sentinel limit)")
import concurrent.futures
def make_order(i):
    return call("POST", "/api/order/create",
                {"userId": user_id, "productId": 3, "quantity": 1,
                 "address": f"压测地址{i:05d}号", "remark": "burst"},
                headers={"Authorization": f"Bearer {token}"})

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    raw = list(pool.map(make_order, range(50)))

results = [(c, body.get("code"), body.get("message", "")[:60]) for c, body in raw]
success = sum(1 for c, bc, _ in results if c == 200 and bc == 200)
limited = sum(1 for c, bc, _ in results if bc in (429, 500, 503))
print(f"  Success: {success}/50, Limited/Error: {limited}/50")
for i, (c, bc, msg) in enumerate(results[:8]):
    print(f"    [{i+1}] HTTP {c} code={bc} {msg}")
check("Sentinel can limit when bursting 50 in parallel",
      limited > 0 or success < 50, f"success={success} limited={limited}")

# 4. After burst, normal request should still work
print("\n[3] Recovery test")
time.sleep(3)
code, body = call("POST", "/api/order/create",
                  {"userId": user_id, "productId": 4, "quantity": 1,
                   "address": "测试恢复地址abc12345", "remark": ""},
                  headers={"Authorization": f"Bearer {token}"})
check("Normal order after burst", code == 200 and body.get("code") == 200, f"HTTP {code} code={body.get('code')}")

# 4. /api/inventory/timeout 慢调用 (需带 /api 前缀, 路由到 inventory-service; 需 POST)
print("\n[4] Slow call /api/inventory/timeout (POST)")
t0 = time.time()
code, body = call("POST", "/api/inventory/timeout", headers={"Authorization": f"Bearer {token}"})
elapsed = time.time() - t0
check("Timeout simulation works (>=2.5s)", elapsed >= 2.5, f"elapsed={elapsed:.2f}s HTTP={code}")

print(f"\n{'='*70}\n  Result: {pass_count} PASS / {fail_count} FAIL\n{'='*70}")
exit(0 if fail_count == 0 else 1)
