@echo off
setlocal enabledelayedexpansion

set "JAVA_HOME=D:\JAVA\JAVA_JDK\JDK_17.0.12"
set "BASE_DIR=d:\Learning materials\SpringCloud\e-mall"
set "LOG_DIR=%BASE_DIR%\logs"
set "SENTINEL_LOG_DIR=%LOG_DIR%\csp"
set "HELPER_DIR=%TEMP%\emall_start_helpers"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%SENTINEL_LOG_DIR%" mkdir "%SENTINEL_LOG_DIR%"
if not exist "%HELPER_DIR%" mkdir "%HELPER_DIR%"

echo ========================================
echo    E-Mall Microservices Startup
echo    JDK: %JAVA_HOME%
echo    Logs: %LOG_DIR%
echo ========================================

echo.
echo [1/3] Killing any existing services on ports 8081 8082 8083 8084 9000 ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; Get-NetTCPConnection -LocalPort 8081,8082,8083,8084,9000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction Stop; Write-Host ('   killed PID ' + $_.OwningProcess + ' on port ' + $_.LocalPort) } catch {} }; Start-Sleep -Seconds 2"

echo.
echo [2/3] Starting services in background ...
for %%S in (user-service product-service order-service inventory-service gateway) do (
    set "JAR=%BASE_DIR%\%%S\target\%%S-1.0.0-SNAPSHOT.jar"
    set "LOG=%LOG_DIR%\%%S.log"
    set "HLP=%HELPER_DIR%\start_%%S.bat"

    if exist "!JAR!" (
        rem Generate isolated helper .bat to avoid quoting/escaping issues in start command
        >  "!HLP!" echo @echo off
        >> "!HLP!" echo set "JAVA_HOME=%JAVA_HOME%"
        >> "!HLP!" echo set "PATH=%%JAVA_HOME%%\bin;%%PATH%%"
        >> "!HLP!" echo cd /d "%BASE_DIR%\%%S"
        >> "!HLP!" echo "%JAVA_HOME%\bin\java.exe" -Dcsp.sentinel.log.dir="%SENTINEL_LOG_DIR%" -jar "!JAR!" ^> "!LOG!" 2^>^&1

        echo    Starting %%S
        start "%%S" /B "!HLP!"
        timeout /t 3 /nobreak >nul
    ) else (
        echo    [SKIP] %%S - jar not found: !JAR!
    )
)

echo.
echo [3/3] Waiting 30s for services to register with Nacos ...
timeout /t 30 /nobreak >nul

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
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -LiteralPath '%LOG_DIR%\%%S.log' -Tail 8 -ErrorAction SilentlyContinue"
    ) else (
        echo    [no log]
    )
)

echo.
echo Done.
endlocal
