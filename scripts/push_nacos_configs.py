"""
Push updated Nacos configs (with Sentinel dashboard port 8858) to Nacos.
"""
import urllib.request
import urllib.parse
import json
import os
from pathlib import Path

NACOS_URL = "http://localhost:8848"
BASE_DIR = Path(r"d:\Learning materials\SpringCloud\e-mall")

CONFIGS = [
    ("user-service.yaml", "DEFAULT_GROUP"),
    ("product-service.yaml", "DEFAULT_GROUP"),
    ("order-service.yaml", "DEFAULT_GROUP"),
    ("inventory-service.yaml", "DEFAULT_GROUP"),
    ("gateway.yaml", "DEFAULT_GROUP"),
]

def push_config(data_id, group, content):
    url = f"{NACOS_URL}/nacos/v1/cs/configs"
    data = urllib.parse.urlencode({
        "dataId": data_id,
        "group": group,
        "content": content,
        "type": "yaml",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except Exception as e:
        return -1, str(e)

print("=" * 70)
print("  Pushing Nacos configs (Sentinel dashboard 8080 -> 8858)")
print("=" * 70)

for cfg_name, group in CONFIGS:
    # Look in both module-local and gateway resources
    candidates = [
        BASE_DIR / "user-service" / "src" / "main" / "resources" / cfg_name,
        BASE_DIR / "product-service" / "src" / "main" / "resources" / cfg_name,
        BASE_DIR / "order-service" / "src" / "main" / "resources" / cfg_name,
        BASE_DIR / "inventory-service" / "src" / "main" / "resources" / cfg_name,
        BASE_DIR / "gateway" / "src" / "main" / "resources" / cfg_name,
    ]
    src = next((p for p in candidates if p.exists()), None)
    if not src:
        print(f"  [SKIP] {cfg_name:<30} file not found")
        continue
    content = src.read_text(encoding="utf-8")
    code, body = push_config(cfg_name, group, content)
    if code == 200 and "true" in body.lower():
        print(f"  [OK]   {cfg_name:<30} pushed (dashboard: 8858)")
    else:
        print(f"  [FAIL] {cfg_name:<30} code={code} body={body[:100]}")

print("=" * 70)
print("  Done. Restart services to pick up new config.")
print("=" * 70)
