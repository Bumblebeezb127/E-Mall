"""Stop all E-Mall services."""
import subprocess
import socket
import os

PORTS = [8081, 8082, 8083, 8084, 9000]
NAMES = {8081: "user-service", 8082: "product-service", 8083: "order-service",
         8084: "inventory-service", 9000: "gateway"}

def find_pid_by_port(port):
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

print("Stopping all E-Mall services...")
for port in PORTS:
    pid = find_pid_by_port(port)
    if pid:
        try:
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=False)
            print(f"  Killed PID {pid} on port {port} ({NAMES.get(port,'?')})")
        except Exception as e:
            print(f"  Error killing PID {pid}: {e}")
    else:
        print(f"  Port {port} free ({NAMES.get(port,'?')})")
print("Done.")
