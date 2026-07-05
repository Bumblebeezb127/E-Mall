@echo off
REM ====================================================================
REM  E-Mall RabbitMQ 观察脚本
REM  - 持续创建 / 支付 / 取消订单, 让 order-service 不断向 RabbitMQ
REM    发布 order.* 事件
REM  - 用于在 RabbitMQ Management UI (http://localhost:15672) 中
REM    肉眼观察 Exchange / Queue / Message Rate
REM  - 按 Ctrl+C 退出 (不要直接关闭 cmd 窗口)
REM ====================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
set "PY=%SCRIPT_DIR%rabbitmq_observe.py"
set "GATEWAY=http://localhost:9000"

echo ================================================
echo   E-Mall RabbitMQ Observer
echo   Project : %BASE_DIR%
echo   Gateway : %GATEWAY%
echo   Time    : %DATE% %TIME%
echo ================================================
echo.

REM --- Pre-check : gateway ---
echo [Pre-check] Gateway health ...
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; try { (Invoke-WebRequest -Uri '%GATEWAY%/api/product/list' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { 'DOWN' }"
echo.

REM --- 探测 python ---
set "PY_EXE="
for /f "delims=" %%I in ('where python 2^>nul') do (
    if not defined PY_EXE set "PY_EXE=%%I"
)
if not defined PY_EXE (
    echo [ERROR] python not found in PATH. Install Python 3.8+ first.
    pause
    exit /b 1
)
echo [INFO] Using python: %PY_EXE%
echo.

echo ================================================
echo   Starting RabbitMQ event generator ...
echo   - Cycle interval: 3s (override with EMALL_OBSERVE_INTERVAL)
echo   - Press Ctrl+C in this window to stop
echo ================================================
echo.

REM -u 强制 unbuffered, 实时回显
"%PY_EXE%" -u "%PY%"
set "RC=%ERRORLEVEL%"

echo.
echo ================================================
echo   Observer exited with code %RC%
echo ================================================
pause
endlocal
exit /b %RC%
