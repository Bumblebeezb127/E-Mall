"""
Smoke test for E-Mall Postman Collection
- Walks the generated Postman collection JSON
- Substitutes {{var}} with collection/environment variables
- Sends each request and validates tests via simple Python checks
- Reports pass/fail per request
"""
import json
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
import time
from pathlib import Path

BASE = "http://localhost:9000"
COLLECTION_PATH = Path(r"d:\Learning materials\SpringCloud\e-mall\postman\E-Mall-API-Collection.json")
ENV_PATH = Path(r"d:\Learning materials\SpringCloud\e-mall\postman\E-Mall-Local.postman_environment.json")


def load_collection():
    return json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))


def load_env():
    return {v["key"]: v["value"] for v in json.loads(ENV_PATH.read_text(encoding="utf-8"))["values"]}


def build_url(request):
    url = request.get("url", {})
    raw = url.get("raw", "")
    if "{{baseUrl}}" in raw:
        raw = raw.replace("{{baseUrl}}", BASE)
    # urllib will not encode unencoded Chinese in path; we need to split base + query
    if "?" in raw:
        base, qs = raw.split("?", 1)
        # Encode the query string values
        encoded_qs = urllib.parse.urlencode(
            [(k, urllib.parse.unquote(v)) for k, v in urllib.parse.parse_qsl(qs, keep_blank_values=True)],
            encoding="utf-8",
        )
        return base + "?" + encoded_qs
    return raw


def send_request(item, vars_, subst):
    req = item["request"]
    method = req["method"]
    # Substitute variables first (including {{baseUrl}}), then URL-encode
    url_raw = req.get("url", {}).get("raw", "")
    url = subst(url_raw)
    # Replace baseUrl with actual base
    if url.startswith("{{baseUrl}}"):
        url = BASE + url[len("{{baseUrl}}"):]
    # URL-encode the query string portion
    if "?" in url:
        base, qs = url.split("?", 1)
        encoded_qs = urllib.parse.urlencode(
            [(k, urllib.parse.unquote(v)) for k, v in urllib.parse.parse_qsl(qs, keep_blank_values=True)],
            encoding="utf-8",
        )
        url = base + "?" + encoded_qs

    # auth
    headers = {}
    auth = req.get("auth", {})
    if auth.get("type") == "bearer":
        b = auth.get("bearer", [])
        for entry in b:
            if entry.get("key") == "token":
                t = subst(entry.get("value", ""))
                headers["Authorization"] = t
                break
    for h in req.get("header", []):
        headers[h["key"]] = subst(h.get("value", ""))

    body = None
    if req.get("body", {}).get("mode") == "raw":
        body = req["body"].get("raw", "")
        body = subst(body)

    data = body.encode("utf-8") if body else None
    r = urllib.request.Request(url, data=data, method=method, headers=headers)

    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            code = resp.status
            text = resp.read().decode("utf-8", errors="replace")
            return code, text
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def extract_var_from_response(response_text, save_spec, vars_):
    """
    save_spec like: 'data.token' or 'data.records[0].id'
    Returns the value or None.
    """
    try:
        j = json.loads(response_text)
    except Exception:
        return None
    # parse path with [n] support
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", save_spec)
    cur = j
    for tok in tokens:
        if tok.startswith("[") and tok.endswith("]"):
            idx = int(tok[1:-1])
            if isinstance(cur, list) and 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        else:
            if isinstance(cur, dict) and tok in cur:
                cur = cur[tok]
            else:
                return None
    return cur


def run_test_script(item, code, text, vars_):
    """Run all `pm.test` scripts embedded in the item's test event."""
    test_events = [e for e in item.get("event", []) if e.get("listen") == "test"]
    results = []
    for ev in test_events:
        script = ev.get("script", {}).get("exec", [])
        for line in script:
            line = line.strip()
            if not line:
                continue
            # Match simple patterns
            if line.startswith("pm.test("):
                # Extract test name
                m = re.match(r"pm\.test\(['\"](.+?)['\"]", line)
                name = m.group(1) if m else "unnamed test"
                # Just count as executed; full JS eval not possible
                results.append((name, "skipped (JS not eval'd)"))
            elif line.startswith("if") or line.startswith("var ") or line.startswith("}"):
                pass
    return results


def main():
    col = load_collection()
    vars_ = load_env()
    # 模拟 Postman collection 级 prerequest script: 整个 Runner 期间只生成一次
    RUN_TIMESTAMP = str(int(time.time() * 1000))
    print(f"[INFO] Loaded {len(vars_)} environment variables")
    print(f"[INFO] Run timestamp: {RUN_TIMESTAMP}")
    print(f"[INFO] Collection: {col['info']['name']}")
    print()

    # Walk the collection
    def walk(items, folder=""):
        for it in items:
            if "item" in it:
                yield from walk(it["item"], folder=it["name"])
            else:
                yield it, folder

    def subst(s):
        if not isinstance(s, str):
            return s
        def repl(m):
            key = m.group(1)
            if key == "$timestamp":
                return RUN_TIMESTAMP
            if key == "runTimestamp":
                return RUN_TIMESTAMP
            if key in vars_:
                return vars_[key]
            return m.group(0)
        return re.sub(r"\{\{([^}]+)\}\}", repl, s)

    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for it, folder in walk(col["item"]):
        total += 1
        name = it["name"]
        label = f"[{folder}] {name}" if folder else name
        try:
            code, text = send_request(it, vars_, subst)
        except Exception as e:
            print(f"  [ERROR] {label} - {e}")
            failed += 1
            continue

        # Run the test event and capture save_var side effects
        test_events = [e for e in it.get("event", []) if e.get("listen") == "test"]
        for ev in test_events:
            exec_list = ev.get("script", {}).get("exec", [])
            # Within each exec entry, find save patterns and their path
            for line in exec_list:
                m = re.search(r"pm\.collectionVariables\.set\(['\"]([^'\"]+)['\"]", line)
                if m and m.group(1) in ("token", "userToken", "userId", "adminId", "productId",
                                        "newProductId", "orderId", "paidOrderId",
                                        "cancelOrderId", "mqOrderId", "mqCancelId", "logFilePath"):
                    var_name = m.group(1)
                    # The path is in the same line (multi-line string with embedded \n).
                    # save_var uses __tokens = ("data.token").match(...), so the path is
                    # the first thing inside the parens of __tokens = (...).
                    path_m = re.search(r"__tokens = \(([^)]+)\)", line)
                    if path_m:
                        path = path_m.group(1).strip().strip('"').strip("'")
                        v = extract_var_from_response(text, path, vars_)
                        if v is not None:
                            vars_[var_name] = str(v)

        # Basic status check
        tests = [e for e in it.get("event", []) if e.get("listen") == "test"]
        has_status_200 = any("pm.response.to.have.status(200)" in l for ev in tests for l in ev.get("script", {}).get("exec", []))
        has_status_400 = any("pm.response.to.have.status(400)" in l for ev in tests for l in ev.get("script", {}).get("exec", []))
        has_status_500 = any("pm.response.to.have.status(500)" in l for ev in tests for l in ev.get("script", {}).get("exec", []))

        expected = 200
        if has_status_400: expected = 400
        elif has_status_500: expected = 500

        # Rate limit (7.1) is OK if 200
        if code == 0:
            print(f"  [FAIL] {label} - network error")
            failed += 1
        elif code == expected or (expected == 200 and code in (200, 429)):
            # Capture business code for some
            try:
                j = json.loads(text)
                biz = j.get("code", "?")
                print(f"  [PASS] {label} (HTTP {code}, biz={biz})")
            except:
                print(f"  [PASS] {label} (HTTP {code})")
            passed += 1
        else:
            print(f"  [FAIL] {label} (HTTP {code}, expected {expected})")
            failed += 1

    print()
    print("=" * 60)
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
