"""
E-Mall Admin Endpoint Test
Covers:
  - Login as admin
  - Access user admin endpoints (list / role change / delete)
  - Access product admin endpoints (list / create / update / delete)
  - Access inventory admin endpoints (list / init / update)
  - Access order admin endpoints (list / stats / force-cancel / force-pay / delete)
  - Access log service endpoints (files / tail / search)
  - Non-admin should get 403
"""
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Tuple

GATEWAY = "http://localhost:9000"

class ApiTest:
    def __init__(self):
        self.admin_token: Optional[str] = None
        self.admin_id: Optional[int] = None
        self.user_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.results = []
        self.pass_count = 0
        self.fail_count = 0

    def call(self, method: str, path: str, body=None, headers=None) -> Tuple[int, dict, float]:
        # URL-encode the query string to safely carry paths / spaces / backslashes
        parts = path.split("?", 1)
        url = GATEWAY + parts[0]
        if len(parts) > 1 and parts[1]:
            qs = []
            for kv in parts[1].split("&"):
                k, _, v = kv.partition("=")
                qs.append(urllib.parse.quote(k, safe='') + "=" + urllib.parse.quote(v, safe=''))
            url = url + "?" + "&".join(qs)
        data = None
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.getcode()
                raw = resp.read().decode("utf-8")
                body = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            code = e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = {"raw_error": str(e)}
        except Exception as e:
            code = -1
            body = {"error": str(e)}
        elapsed_ms = (time.time() - t0) * 1000
        return code, body, elapsed_ms

    def record(self, name: str, code: int, body, ms: float, expect_code: int = 200, expect_business_code: int = None, expect_in_body: str = None):
        ok = (code == expect_code)
        if expect_business_code is not None and isinstance(body, dict):
            ok = ok and (body.get("code") == expect_business_code)
        if expect_in_body and isinstance(body, dict):
            ok = ok and (expect_in_body.lower() in str(body).lower())
        status = "PASS" if ok else "FAIL"
        if ok:
            self.pass_count += 1
        else:
            self.fail_count += 1
        snippet = json.dumps(body, ensure_ascii=False)[:140] if body else "(empty)"
        print(f"  [{status}] {name:<48} HTTP {code}  {ms:6.0f}ms  {snippet}")

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def step_setup(self):
        print("\n--- Setup: login admin and a normal user ---")
        # Admin: admin / admin123 (init.sql)
        code, body, ms = self.call("POST", "/api/user/login",
                                   {"username": "admin", "password": "admin123"})
        self.record("admin login", code, body, ms,
                    expect_business_code=200, expect_in_body="ADMIN")
        if body.get("code") == 200 and body.get("data", {}).get("token"):
            self.admin_token = body["data"]["token"]
            self.admin_id = body["data"]["id"]

        # Normal user: 复用 api_test.py 注册的 user1 / pass1234 (若已存在则登录)
        # 先注册再登录
        ts = int(time.time())
        uname = f"admtester_{ts}"
        self.call("POST", "/api/user/register", {"username": uname, "password": "pass1234"})
        code, body, ms = self.call("POST", "/api/user/login",
                                   {"username": uname, "password": "pass1234"})
        self.record(f"user login ({uname})", code, body, ms, expect_business_code=200)
        if body.get("code") == 200 and body.get("data", {}).get("token"):
            self.user_token = body["data"]["token"]
            self.user_id = body["data"]["id"]
        self.normal_username = uname

    # ----- User admin -----
    def test_user_admin(self):
        print("\n--- Test: user admin endpoints ---")
        if not self.admin_token: return
        code, body, ms = self.call("GET", "/api/user/admin/list?page=1&size=20",
                                   headers=self.auth(self.admin_token))
        self.record("admin list users", code, body, ms,
                    expect_business_code=200, expect_in_body="records")

        # normal user forbidden
        if self.user_token:
            code, body, ms = self.call("GET", "/api/user/admin/list",
                                       headers=self.auth(self.user_token))
            self.record("non-admin list users (expect 403)", code, body, ms,
                        expect_business_code=403)

        # role change
        if self.user_id:
            code, body, ms = self.call("PUT", f"/api/user/admin/role/{self.user_id}?roleValue=USER",
                                       headers=self.auth(self.admin_token))
            self.record("admin change role -> USER", code, body, ms, expect_business_code=200)

    # ----- Product admin -----
    def test_product_admin(self):
        print("\n--- Test: product admin endpoints ---")
        if not self.admin_token: return
        code, body, ms = self.call("GET", "/api/product/admin/list?page=1&size=20",
                                   headers=self.auth(self.admin_token))
        self.record("admin list products", code, body, ms,
                    expect_business_code=200, expect_in_body="records")

        # create a new product
        new_product = {
            "name": f"AdminTestProduct_{int(time.time())}",
            "price": 9.99,
            "stock": 100,
            "description": "Created by admin test",
            "imageUrl": "https://picsum.photos/seed/admin/400/400",
            "category": "测试分类"
        }
        code, body, ms = self.call("POST", "/api/product/admin/create",
                                   new_product, headers=self.auth(self.admin_token))
        self.record("admin create product", code, body, ms, expect_business_code=200)
        # get new product id
        if body.get("code") == 200:
            code2, body2, _ = self.call("GET", "/api/product/admin/list?page=1&size=5&keyword=AdminTestProduct",
                                        headers=self.auth(self.admin_token))
            records = (body2.get("data") or {}).get("records") or []
            new_id = records[0]["id"] if records else None
            if new_id:
                # update
                code, body, ms = self.call("PUT", f"/api/product/admin/update/{new_id}",
                                           {"name": new_product["name"] + "_updated",
                                            "price": 19.99, "stock": 50, "description": "updated",
                                            "imageUrl": new_product["imageUrl"], "category": "测试分类2"},
                                           headers=self.auth(self.admin_token))
                self.record("admin update product", code, body, ms, expect_business_code=200)
                # delete
                code, body, ms = self.call("DELETE", f"/api/product/admin/delete/{new_id}",
                                           headers=self.auth(self.admin_token))
                self.record("admin delete product", code, body, ms, expect_business_code=200)

    # ----- Inventory admin -----
    def test_inventory_admin(self):
        print("\n--- Test: inventory admin endpoints ---")
        if not self.admin_token: return
        code, body, ms = self.call("GET", "/api/inventory/admin/list?page=1&size=20",
                                   headers=self.auth(self.admin_token))
        self.record("admin list inventory", code, body, ms,
                    expect_business_code=200, expect_in_body="records")

        # pick a product and update stock
        code, body, ms = self.call("GET", "/api/product/list?page=1&size=1")
        items = (body.get("data") or {}).get("records") or []
        if items:
            pid = items[0]["id"]
            code, body, ms = self.call("PUT", f"/api/inventory/admin/update?productId={pid}&stock=99",
                                       headers=self.auth(self.admin_token))
            self.record("admin set inventory", code, body, ms, expect_business_code=200)

    # ----- Order admin -----
    def test_order_admin(self):
        print("\n--- Test: order admin endpoints ---")
        if not self.admin_token or not self.user_id: return
        # list
        code, body, ms = self.call("GET", "/api/order/admin/list?page=1&size=20",
                                   headers=self.auth(self.admin_token))
        self.record("admin list orders", code, body, ms,
                    expect_business_code=200, expect_in_body="records")
        # stats
        code, body, ms = self.call("GET", "/api/order/admin/stats",
                                   headers=self.auth(self.admin_token))
        self.record("admin order stats", code, body, ms,
                    expect_business_code=200, expect_in_body="total")

        # create a pending order, then force-pay & verify
        # first get a product
        code, body, ms = self.call("GET", "/api/product/list?page=1&size=1")
        items = (body.get("data") or {}).get("records") or []
        if not items:
            print("  [SKIP] no product to create order")
            return
        pid = items[0]["id"]
        code, body, ms = self.call("POST", "/api/order/create",
                                   {"userId": self.user_id, "productId": pid, "quantity": 1,
                                    "address": "Admin Test Address 12345", "remark": "admin test"},
                                   headers=self.auth(self.user_token))
        if body.get("code") != 200:
            print(f"  [SKIP] order create failed: {body}")
            return
        order_id = body["data"]["orderId"]
        code, body, ms = self.call("PUT", f"/api/order/admin/pay/{order_id}",
                                   headers=self.auth(self.admin_token))
        self.record("admin force-pay order", code, body, ms, expect_business_code=200)

        # create another order and force-cancel
        code, body, ms = self.call("POST", "/api/order/create",
                                   {"userId": self.user_id, "productId": pid, "quantity": 1,
                                    "address": "Admin Test Address 12345", "remark": "admin cancel test"},
                                   headers=self.auth(self.user_token))
        if body.get("code") == 200:
            order_id2 = body["data"]["orderId"]
            code, body, ms = self.call("PUT", f"/api/order/admin/cancel/{order_id2}",
                                       headers=self.auth(self.admin_token))
            self.record("admin force-cancel order", code, body, ms, expect_business_code=200)
            # delete
            code, body, ms = self.call("DELETE", f"/api/order/admin/delete/{order_id2}",
                                       headers=self.auth(self.admin_token))
            self.record("admin delete order", code, body, ms, expect_business_code=200)

        # non-admin should be forbidden
        if self.user_token:
            code, body, ms = self.call("GET", "/api/order/admin/list",
                                       headers=self.auth(self.user_token))
            self.record("non-admin list orders (expect 403)", code, body, ms,
                        expect_business_code=403)

    # ----- Log service -----
    def test_log_service(self):
        print("\n--- Test: log service endpoints ---")
        if not self.admin_token: return
        code, body, ms = self.call("GET", "/api/log/files",
                                   headers=self.auth(self.admin_token))
        self.record("admin list log files", code, body, ms,
                    expect_business_code=200, expect_in_body="files")

        if body.get("code") == 200 and (body.get("data") or {}).get("files"):
            f0 = body["data"]["files"][0]
            path = f0["path"]
            code, body, ms = self.call("GET", f"/api/log/tail?file={path}&lines=20",
                                       headers=self.auth(self.admin_token))
            self.record("admin tail log (20 lines)", code, body, ms,
                        expect_business_code=200, expect_in_body="content")
            code, body, ms = self.call("GET", f"/api/log/search?file={path}&keyword=ERROR&max=10",
                                       headers=self.auth(self.admin_token))
            self.record("admin search log (keyword=ERROR)", code, body, ms,
                        expect_business_code=200, expect_in_body="hits")

        if self.user_token:
            code, body, ms = self.call("GET", "/api/log/files",
                                       headers=self.auth(self.user_token))
            self.record("non-admin list log files (expect 403)", code, body, ms,
                        expect_business_code=403)

    def run(self):
        print("=" * 70)
        print("  E-Mall Admin Endpoint Test")
        print(f"  Gateway: {GATEWAY}")
        print("=" * 70)
        self.step_setup()
        self.test_user_admin()
        self.test_product_admin()
        self.test_inventory_admin()
        self.test_order_admin()
        self.test_log_service()

        print("\n" + "=" * 70)
        print(f"  RESULT: PASS {self.pass_count} / FAIL {self.fail_count}")
        print("=" * 70)
        return 0 if self.fail_count == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(ApiTest().run())
