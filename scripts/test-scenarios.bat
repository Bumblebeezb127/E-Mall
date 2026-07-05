@echo off
REM ====================================================================
REM  E-Mall Test Scenarios (portable)
REM  - 启动 MySQL + Nacos + 各服务 (后台)
REM  - 跑测试
REM  - 测试完成后停掉除 MySQL/Nacos 外的所有服务
REM ====================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"

if exist "%BASE_DIR%\scripts\start-all-services.bat" (
    call "%BASE_DIR%\scripts\start-all-services.bat"
) else (
    echo [ERROR] start-all-services.bat not found
    exit /b 1
)

if exist "%BASE_DIR%\scripts\run-all-tests.bat" (
    call "%BASE_DIR%\scripts\run-all-tests.bat"
) else (
    echo [WARN] run-all-tests.bat not found
)

echo.
echo [Post] Stopping business services (keep MySQL & Nacos) ...
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; $ports=8081,8082,8083,8084,8085,9000; foreach ($p in $ports) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} } }"

echo Done.
endlocal
exit /b 0
