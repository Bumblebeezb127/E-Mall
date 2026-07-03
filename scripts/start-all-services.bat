@echo off
setlocal enabledelayedexpansion

set JAVA_HOME=D:\JAVA\JAVA_JDK\JDK_17.0.12
set PATH=%JAVA_HOME%\bin;%PATH%

set BASE_DIR=d:\Learning materials\SpringCloud\e-mall
set LOG_DIR=%BASE_DIR%\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ========================================
echo    E-Mall Microservices Startup
echo    JDK: %JAVA_HOME%
echo    Logs: %LOG_DIR%
echo ========================================

echo.
echo [1/3] Stopping any existing service processes on ports 8081 8082 8083 8084 9000
for %%P in (8081 8082 8083 8084 9000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr LISTENING') do (
        echo    Stopping PID %%A on port %%P
        taskkill /F /PID %%A >nul 2>&1
    )
)
timeout /t 2 /nobreak >nul

echo.
echo [2/3] Starting services in background...
set PORT_INDEX=0
for %%S in (user-service product-service order-service inventory-service gateway) do (
    set /a PORT_INDEX+=1
    echo    Starting %%S
    start "%%S" /MIN cmd /c "set JAVA_HOME=%JAVA_HOME%&&set PATH=%JAVA_HOME%\bin;%PATH%&&java -jar %BASE_DIR%\%%S\target\%%S-1.0.0-SNAPSHOT.jar > %LOG_DIR%\%%S.log 2>&1"
    timeout /t 3 /nobreak >nul
)

echo.
echo [3/3] Waiting for services to register with Nacos (30s)...
timeout /t 30 /nobreak

echo.
echo ========================================
echo    Service Status Check
echo ========================================
for %%P in (8081 8082 8083 8084 9000) do (
    netstat -ano | findstr ":%%P " | findstr LISTENING >nul
    if !ERRORLEVEL!==0 (
        echo    [OK]   Port %%P LISTENING
    ) else (
        echo    [FAIL] Port %%P NOT LISTENING
    )
)

echo.
echo ========================================
echo    Tail of each service log
echo ========================================
for %%S in (user-service product-service order-service inventory-service gateway) do (
    echo.
    echo ----- %%S -----
    if exist "%LOG_DIR%\%%S.log" (
        powershell -NoProfile -Command "Get-Content '%LOG_DIR%\%%S.log' -Tail 8 -ErrorAction SilentlyContinue"
    ) else (
        echo    [no log]
    )
)

echo.
echo Done.
endlocal
