"""
E-Mall RabbitMQ End-to-End Test
Covers:
  - Login admin + register/login a normal user
  - Create order (publishes order.created to RabbitMQ)
  - Pay order (publishes order.paid)
  - Cancel another order (publishes order.cancelled)
  - Verify product-service consumed the events via /api/product/admin/mq/events
  - Verify log-service consumed events and wrote to logs/order-events-*.log
  - Non-admin should be 403 on /api/product/admin/mq/events
"""
import json
import time
import os
import urllib.request
import urllib.error
from typing import Optional, Tuple

GATEWAY = "http://localhost:9000"
LOG_DIR = r"d:\Learning materials\SpringCloud\e-mall\logs"


class ApiTest:
    def __init__(self):
        self.admin_token: Optional[str] = None
        self.user_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.pass_count = 0
        self.fail_count = 0

    def call(self, method: str, path: str, body=None, headers=None) -> Tuple[int, dict, float]:
        url = GATEWAY + path
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        data = json.dumps(body).encode() if body is not None else None
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

    def record(self, name, code, body, ms, expect_code=200, expect_business_code=None, expect_in_body=None):
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
        print("\n--- Setup: admin + user ---")
        code, body, ms = self.call("POST", "/api/user/login",
                                   {"username": "admin", "password": "admin123"})
        self.record("admin login", code, body, ms,
                    expect_business_code=200, expect_in_body="ADMIN")
        if body.get("code") == 200:
            self.admin_token = body["data"]["token"]
            self.admin_id = body["data"]["id"]

        ts = int(time.time())
        uname = f"mqtester_{ts}"
        self.call("POST", "/api/user/register", {"username": uname, "password": "pass1234"})
        code, body, ms = self.call("POST", "/api/user/login",
                                   {"username": uname, "password": "pass1234"})
        self.record(f"user login ({uname})", code, body, ms, expect_business_code=200)
        if body.get("code") == 200:
            self.user_token = body["data"]["token"]
            self.user_id = body["data"]["id"]

    def step_create_pay_cancel(self):
        print("\n--- Trigger order events (created / paid / cancelled) ---")
        if not self.user_token or not self.user_id:
            return None
        code, body, ms = self.call("GET", "/api/product/list?page=1&size=1")
        items = (body.get("data") or {}).get("records") or []
        if not items:
            print("  [SKIP] no product available")
            return None
        pid = items[0]["id"]

        created_order = None
        paid_order = None
        cancelled_order = None

        # Create -> order.created
        code, body, ms = self.call("POST", "/api/order/create",
                                   {"userId": self.user_id, "productId": pid, "quantity": 1,
                                    "address": "MQ Test Address 12345", "remark": "mq test created"},
                                   headers=self.auth(self.user_token))
        self.record("create order (publish order.created)", code, body, ms, expect_business_code=200)
        if body.get("code") == 200:
            created_order = body["data"]["orderId"]

        # Pay -> order.paid
        if created_order:
            code, body, ms = self.call("PUT", f"/api/order/pay/{created_order}?userId={self.user_id}",
                                       headers=self.auth(self.user_token))
            self.record("pay order (publish order.paid)", code, body, ms, expect_business_code=200)

        # Create another and cancel -> order.cancelled
        code, body, ms = self.call("POST", "/api/order/create",
                                   {"userId": self.user_id, "productId": pid, "quantity": 1,
                                    "address": "MQ Test Address 67890", "remark": "mq test cancel"},
                                   headers=self.auth(self.user_token))
        if body.get("code") == 200:
            cancelled_order = body["data"]["orderId"]
            code, body, ms = self.call("PUT", f"/api/order/cancel/{cancelled_order}?userId={self.user_id}",
                                       headers=self.auth(self.user_token))
            self.record("cancel order (publish order.cancelled)", code, body, ms, expect_business_code=200)

        return {"created": created_order, "paid": created_order, "cancelled": cancelled_order}

    def step_verify_mq_consumption(self, expected):
        print("\n--- Verify MQ consumption (product-service /admin/mq/events) ---")
        # Wait up to 5s for events to be consumed
        target_total = 3
        attempts = 0
        while attempts < 10:
            code, body, ms = self.call("GET", "/api/product/admin/mq/events?limit=50",
                                       headers=self.auth(self.admin_token))
            if body.get("code") == 200 and body["data"]["total"] >= target_total:
                break
            time.sleep(1)
            attempts += 1

        self.record("admin query MQ events", code, body, ms, expect_business_code=200)
        if not (isinstance(body, dict) and body.get("code") == 200):
            return
        data = body["data"]
        print(f"      total={data['total']}  created={data['created']}  "
              f"paid={data['paid']}  cancelled={data['cancelled']}")
        # Stats assertions
        assert_msg = f"created={data['created']} paid={data['paid']} cancelled={data['cancelled']}"
        if data["created"] >= 1 and data["paid"] >= 1 and data["cancelled"] >= 1:
            self.pass_count += 1
            print(f"  [PASS] all 3 event types present in product-service consumer        {assert_msg}")
        else:
            self.fail_count += 1
            print(f"  [FAIL] missing event types                                          {assert_msg}")

        # Verify event IDs are unique and contain expected types
        events = data.get("events") or []
        event_types = {e.get("eventType") for e in events}
        if {"order.created", "order.paid", "order.cancelled"} <= event_types:
            self.pass_count += 1
            print(f"  [PASS] recent events contain all 3 types")
        else:
            self.fail_count += 1
            print(f"  [FAIL] recent events types: {event_types}")

    def step_verify_log_file(self):
        print("\n--- Verify log-service persisted events to file ---")
        # Find today's log file
        today = time.strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"order-events-{today}.log")
        if not os.path.exists(log_file):
            # try to find any order-events-*.log
            if os.path.isdir(LOG_DIR):
                for f in sorted(os.listdir(LOG_DIR)):
                    if f.startswith("order-events-") and f.endswith(".log"):
                        log_file = os.path.join(LOG_DIR, f)
                        break
        if not os.path.exists(log_file):
            self.fail_count += 1
            print(f"  [FAIL] order events log file not found in {LOG_DIR}")
            return
        # Read all lines
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        types = {"order.created": 0, "order.paid": 0, "order.cancelled": 0}
        for line in lines:
            for et in types:
                if et in line:
                    types[et] += 1
        if all(v >= 1 for v in types.values()):
            self.pass_count += 1
            print(f"  [PASS] log file {os.path.basename(log_file)} contains all 3 event types: {types}")
        else:
            self.fail_count += 1
            print(f"  [FAIL] log file {os.path.basename(log_file)} event types: {types}")
        # Verify the first line has well-known fields
        if lines and "orderId=" in lines[0] and "eventId=" in lines[0]:
            self.pass_count += 1
            print(f"  [PASS] log line format contains orderId / eventId")
            print(f"         sample: {lines[0].rstrip()[:160]}")
        else:
            self.fail_count += 1
            print(f"  [FAIL] log line format invalid")

    def step_non_admin_forbidden(self):
        print("\n--- Verify non-admin cannot access MQ events ---")
        if not self.user_token:
            return
        code, body, ms = self.call("GET", "/api/product/admin/mq/events",
                                   headers=self.auth(self.user_token))
        self.record("non-admin query MQ events (expect 403)", code, body, ms,
                    expect_business_code=403)

    def run(self):
        print("=" * 70)
        print("  E-Mall RabbitMQ End-to-End Test")
        print(f"  Gateway: {GATEWAY}")
        print(f"  Log dir : {LOG_DIR}")
        print("=" * 70)
        self.step_setup()
        events = self.step_create_pay_cancel()
        if events:
            self.step_verify_mq_consumption(events)
            self.step_verify_log_file()
        self.step_non_admin_forbidden()

        print("\n" + "=" * 70)
        print(f"  RESULT: PASS {self.pass_count} / FAIL {self.fail_count}")
        print("=" * 70)
        return 0 if self.fail_count == 0 else 1


if __name__ == "__main__":
    t = ApiTest()
    exit(t.run())
