"""
E-Mall RabbitMQ 事件持续生成器
- 持续创建/支付/取消订单, 让 order-service 不断向 RabbitMQ 发布事件
- 同步消费端 product-service / log-service 落盘
- 用于在 RabbitMQ Management UI (http://localhost:15672) 中肉眼观察消息流
- 按 Ctrl+C 优雅退出
"""
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple

GATEWAY = "http://localhost:9000"
LOG_DIR = r"d:\Learning materials\SpringCloud\e-mall\logs"
INTERVAL_SECONDS = float(os.environ.get("EMALL_OBSERVE_INTERVAL", "3"))


class Observer:
    def __init__(self):
        self.user_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.created = 0
        self.paid = 0
        self.cancelled = 0
        self.cycles = 0
        self.running = True
        self.product_id: Optional[int] = None

    def call(self, method: str, path: str, body=None, headers=None) -> Tuple[int, dict]:
        h = {"Content-Type": "application/json"}
        if headers:
            h.update(headers)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(GATEWAY + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return resp.getcode(), json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode("utf-8"))
            except Exception:
                return e.code, {"raw_error": str(e)}
        except Exception as e:
            return -1, {"error": str(e)}

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def setup(self):
        # 1. 注册并登录一个观察用户 (避免污染生产账号)
        ts = int(time.time())
        uname = f"observer_{ts}"
        self.call("POST", "/api/user/register",
                  {"username": uname, "password": "pass1234"})
        code, body = self.call("POST", "/api/user/login",
                               {"username": uname, "password": "pass1234"})
        if code != 200 or body.get("code") != 200:
            print(f"[FATAL] user login failed: HTTP {code}  {body}")
            sys.exit(1)
        self.user_token = body["data"]["token"]
        self.user_id = body["data"]["id"]
        print(f"[OK] login as {uname} (id={self.user_id})")

        # 2. 选一个商品作为下单目标
        code, body = self.call("GET", "/api/product/list?page=1&size=1")
        items = (body.get("data") or {}).get("records") or []
        if not items:
            print("[FATAL] no product available for ordering")
            sys.exit(1)
        self.product_id = items[0]["id"]
        print(f"[OK] pick product id={self.product_id} for ordering")

    def one_cycle(self):
        # 创建 -> 发布 order.created
        code, body = self.call("POST", "/api/order/create",
                               {"userId": self.user_id, "productId": self.product_id,
                                "quantity": 1, "address": "RabbitMQ Observer Street 12345",
                                "remark": f"observer cycle {self.cycles + 1}"},
                               headers=self.auth(self.user_token))
        if body.get("code") != 200:
            print(f"  [WARN] create order failed: {body}")
            return
        order_id = body["data"]["orderId"]
        self.created += 1
        print(f"  [PUB] order.created     orderId={order_id}")

        # 支付 -> 发布 order.paid
        code, body = self.call("PUT", f"/api/order/pay/{order_id}?userId={self.user_id}",
                               headers=self.auth(self.user_token))
        if body.get("code") == 200:
            self.paid += 1
            print(f"  [PUB] order.paid        orderId={order_id}")

        # 创建另一个 -> 取消 -> 发布 order.cancelled
        code, body = self.call("POST", "/api/order/create",
                               {"userId": self.user_id, "productId": self.product_id,
                                "quantity": 1, "address": "RabbitMQ Observer Street 67890",
                                "remark": f"observer cycle {self.cycles + 1} cancel"},
                               headers=self.auth(self.user_token))
        if body.get("code") == 200:
            cancel_id = body["data"]["orderId"]
            self.created += 1
            print(f"  [PUB] order.created     orderId={cancel_id}")
            code, body = self.call("PUT", f"/api/order/cancel/{cancel_id}?userId={self.user_id}",
                                   headers=self.auth(self.user_token))
            if body.get("code") == 200:
                self.cancelled += 1
                print(f"  [PUB] order.cancelled   orderId={cancel_id}")

    def stop(self, *_):
        self.running = False
        print("\n[STOP] Ctrl+C detected, finishing current cycle...")

    def run(self):
        signal.signal(signal.SIGINT, self.stop)
        self.setup()
        print("=" * 60)
        print("  RabbitMQ 事件持续生成器已启动")
        print("  Management UI: http://localhost:15672  (guest/guest)")
        print(f"  Exchange: emall.order.exchange")
        print(f"  Interval: {INTERVAL_SECONDS}s per cycle")
        print("  Press Ctrl+C to stop and exit")
        print("=" * 60)
        try:
            while self.running:
                self.cycles += 1
                t0 = time.time()
                self.one_cycle()
                print(f"  [STATS] cycle={self.cycles}  "
                      f"created={self.created} paid={self.paid} cancelled={self.cancelled}")
                # 间隔
                elapsed = time.time() - t0
                sleep_left = max(0, INTERVAL_SECONDS - elapsed)
                # 用短步长 sleep, 便于响应 Ctrl+C
                slept = 0.0
                while slept < sleep_left and self.running:
                    time.sleep(0.2)
                    slept += 0.2
        finally:
            print()
            print("=" * 60)
            print("  FINAL STATS")
            print(f"  cycles run    : {self.cycles}")
            print(f"  order.created : {self.created}")
            print(f"  order.paid    : {self.paid}")
            print(f"  order.cancelled: {self.cancelled}")
            print(f"  total events  : {self.created + self.paid + self.cancelled}")
            # 检查落盘文件
            today = time.strftime("%Y-%m-%d")
            log_file = os.path.join(LOG_DIR, f"order-events-{today}.log")
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                print(f"  log file      : {log_file} ({len(lines)} lines)")
            else:
                print(f"  log file      : {log_file} (NOT FOUND - log-service may be down)")
            print("=" * 60)


if __name__ == "__main__":
    Observer().run()
