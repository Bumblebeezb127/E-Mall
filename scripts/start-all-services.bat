@echo off
REM ====================================================================
REM  E-Mall Microservices Startup Script (portable)
REM  - 脚本所在目录的父目录即为项目根 (即包含 pom.xml 的目录)
REM  - java.exe 自动从 JAVA_HOME / PATH / 注册表按顺序查找
REM  - 不再硬编码任何绝对路径
REM ====================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM ---- 1. 解析项目根目录 (脚本所在目录的父目录) ----
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
if not exist "%BASE_DIR%\pom.xml" (
    echo [ERROR] pom.xml not found at "%BASE_DIR%". Please run this script from scripts\ inside the project.
    exit /b 1
)

REM ---- 2. 解析日志目录 ----
set "LOG_DIR=%BASE_DIR%\logs"
set "SENTINEL_LOG_DIR=%LOG_DIR%\csp"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%SENTINEL_LOG_DIR%" mkdir "%SENTINEL_LOG_DIR%"

REM ---- 3. 解析 java.exe ----
call :resolve_java
if not defined JAVA_EXE (
    echo [ERROR] java.exe not found. Please install JDK 8+ or set JAVA_HOME.
    echo         Tried: JAVA_HOME, PATH, registry HKLM\SOFTWARE\JavaSoft\JDK
    exit /b 1
)
for %%I in ("%JAVA_EXE%") do set "JAVA_BIN_DIR=%%~dpI"
set "JAVA_HOME=%JAVA_BIN_DIR%.."

REM ---- 4. 端口定义 ----
set "PORTS=8081 8082 8083 8084 8085 9000"
set "SERVICES=user-service product-service order-service inventory-service log-service gateway"

echo ========================================
echo   E-Mall Microservices Startup
echo   Project : %BASE_DIR%
echo   Java    : %JAVA_EXE%
echo   Logs    : %LOG_DIR%
echo ========================================

REM ---- 5. 杀掉旧进程 ----
echo.
echo [1/3] Killing any existing services on ports %PORTS% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $ports='%PORTS%'.Split(); foreach ($p in $ports) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction Stop; Write-Host ('   killed PID ' + $_.OwningProcess + ' on port ' + $_.LocalPort) } catch {} } }; Start-Sleep -Seconds 2"

REM ---- 6. 启动服务 (每个服务通过独立 helper .bat 启动) ----
echo.
echo [2/3] Starting services in background ...
set "HELPER_DIR=%TEMP%\emall_start_helpers"
if not exist "%HELPER_DIR%" mkdir "%HELPER_DIR%"

for %%S in (%SERVICES%) do (
    set "JAR=%BASE_DIR%\%%S\target\%%S-1.0.0-SNAPSHOT.jar"
    set "LOG=%LOG_DIR%\%%S.log"
    set "HLP=%HELPER_DIR%\start_%%S.bat"

    if exist "!JAR!" (
        REM 写入独立 helper .bat (CRLF)
        >  "!HLP!" echo @echo off
        >> "!HLP!" echo set "JAVA_HOME=%JAVA_HOME%"
        >> "!HLP!" echo set "PATH=%%JAVA_HOME%%\bin;%%PATH%%"
        >> "!HLP!" echo set "EMALL_LOG_ROOT=%LOG_DIR%"
        >> "!HLP!" echo cd /d "%BASE_DIR%\%%S"
        >> "!HLP!" echo "%JAVA_EXE%" -Dcsp.sentinel.log.dir="%SENTINEL_LOG_DIR%" -Demall.log.root="%LOG_DIR%" -jar "!JAR!" ^> "!LOG!" 2^>^&1

        echo    Starting %%S
        start "%%S" /B "!HLP!"
        timeout /t 3 /nobreak >nul
    ) else (
        echo    [SKIP] %%S - jar not found: !JAR!
    )
)

echo.
echo [3/3] Waiting 35s for services to register with Nacos ...
timeout /t 35 /nobreak >nul

echo.
echo ========================================
echo   Service Status Check
echo ========================================
for %%P in (%PORTS%) do (
    netstat -ano | findstr ":%%P " | findstr LISTENING >nul
    if !ERRORLEVEL!==0 (
        echo    [OK]   Port %%P LISTENING
    ) else (
        echo    [FAIL] Port %%P NOT LISTENING
    )
)

echo.
echo ========================================
echo   Tail of each service log
echo ========================================
for %%S in (%SERVICES%) do (
    echo.
    echo ----- %%S -----
    if exist "%LOG_DIR%\%%S.log" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -LiteralPath '%LOG_DIR%\%%S.log' -Tail 8 -ErrorAction SilentlyContinue"
    ) else (
        echo    [no log]
    )
)

echo.
echo Done. Tail logs: %LOG_DIR%\
endlocal
exit /b 0

REM ====================================================================
REM  Helper: 解析 java.exe 位置
REM  1) 环境变量 JAVA_HOME
REM  2) PATH
REM  3) 注册表 HKLM\SOFTWARE\JavaSoft\JDK
REM  4) 注册表 HKLM\SOFTWARE\JavaSoft\Java Development Kit
REM ====================================================================
:resolve_java
if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\java.exe" (
        set "JAVA_EXE=%JAVA_HOME%\bin\java.exe"
        exit /b 0
    )
)

for %%I in (java.exe) do (
    if not defined JAVA_EXE (
        set "PATH_CMD=%%~$PATH:I"
        if defined PATH_CMD (
            if exist "%%~$PATH:I" set "JAVA_EXE=%%~$PATH:I"
        )
    )
)
if defined JAVA_EXE exit /b 0

REM 注册表查询 JDK 安装路径
for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\JavaSoft\JDK" /v JavaHome 2^>nul') do (
    if exist "%%B\bin\java.exe" set "JAVA_EXE=%%B\bin\java.exe"
)
if defined JAVA_EXE exit /b 0

for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\JavaSoft\Java Development Kit" /v JavaHome 2^>nul') do (
    if exist "%%B\bin\java.exe" set "JAVA_EXE=%%B\bin\java.exe"
)
if defined JAVA_EXE exit /b 0

for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\WOW6432Node\JavaSoft\JDK" /v JavaHome 2^>nul') do (
    if exist "%%B\bin\java.exe" set "JAVA_EXE=%%B\bin\java.exe"
)
if defined JAVA_EXE exit /b 0

exit /b 1
