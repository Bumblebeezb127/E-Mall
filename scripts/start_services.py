"""
E-Mall Microservices Starter
Directly starts Java services in background.
"""
import os
import sys
import time
import socket
import subprocess
from pathlib import Path

BASE_DIR = Path(r"d:\Learning materials\SpringCloud\e-mall")
LOG_DIR = BASE_DIR / "logs"
SENTINEL_LOG_DIR = LOG_DIR / "csp"
JDK17 = r"D:\JAVA\JAVA_JDK\JDK_17.0.12"

SERVICES = [
    ("user-service", 8081),
    ("product-service", 8082),
    ("order-service", 8083),
    ("inventory-service", 8084),
    ("gateway", 9000),
]

LOG_DIR.mkdir(parents=True, exist_ok=True)

def is_listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False

def find_pid_by_port(port):
    """Find PID listening on port (Windows)."""
    try:
        out = subprocess.check_output(
            f'netstat -ano | findstr ":{port} " | findstr LISTENING',
            shell=True, text=True, encoding="gbk", errors="ignore"
        )
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[-1].isdigit():
                return int(parts[-1])
    except subprocess.CalledProcessError:
        pass
    return None

print("=" * 70)
print("  E-Mall Microservices Startup")
print(f"  JDK: {JDK17}")
print(f"  Logs: {LOG_DIR}")
print("=" * 70)

# 1) stop existing
print("\n[1/3] Stopping existing services on target ports...")
for name, port in SERVICES:
    pid = find_pid_by_port(port)
    if pid:
        try:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=False)
            print(f"  Killed PID {pid} on port {port} ({name})")
        except Exception as e:
            print(f"  Error killing PID {pid}: {e}")
    else:
        print(f"  Port {port} free ({name})")
time.sleep(2)

# 2) start
print("\n[2/3] Starting services in background...")
procs = []
for name, port in SERVICES:
    jar = BASE_DIR / name / "target" / f"{name}-1.0.0-SNAPSHOT.jar"
    if not jar.exists():
        print(f"  [FAIL] Jar not found: {jar}")
        continue
    log = LOG_DIR / f"{name}.log"
    cmd = [
        str(Path(JDK17) / "bin" / "java.exe"),
        "-jar",
        str(jar),
    ]
    print(f"  Starting {name} (port {port}) -> {log}")
    with open(log, "wb") as f:
        p = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR / name),
            stdout=f,
            stderr=subprocess.STDOUT,
            env={**os.environ, "JAVA_HOME": JDK17, "PATH": str(Path(JDK17)/"bin") + ";" + os.environ.get("PATH","")},
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
    procs.append((name, port, p))
    time.sleep(3)

# 3) wait and check
print("\n[3/3] Waiting 30s for services to register with Nacos...")
for remaining in (30, 20, 10, 0):
    print(f"  ...waiting {remaining}s")
    time.sleep(10)

print("\n" + "=" * 70)
print("  Service Status Check")
print("=" * 70)
all_ok = True
for name, port, p in procs:
    listening = is_listening(port)
    status = "OK  " if listening else "FAIL"
    if not listening:
        all_ok = False
    print(f"  [{status}] {name:<22} port {port}")
    if not listening:
        log = LOG_DIR / f"{name}.log"
        if log.exists():
            tail = log.read_text(encoding="gbk", errors="ignore").splitlines()[-15:]
            print(f"           tail: {' | '.join(tail)[:300]}")

print("\n" + "=" * 70)
print(f"  Result: {'All services started successfully' if all_ok else 'Some services failed to start'}")
print("=" * 70)
sys.exit(0 if all_ok else 1)
