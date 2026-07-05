@echo off
REM ====================================================================
REM  E-Mall Backend One-Click Build Script (portable)
REM
REM  - 脚本所在目录的父目录即为项目根 (即包含 pom.xml 的目录)
REM  - mvn 自动从 MAVEN_HOME / PATH / 注册表按顺序查找
REM  - 不再硬编码任何绝对路径
REM
REM  Usage:
REM      mvn-build.bat            # 完整构建, 跳过测试
REM      mvn-build.bat -test      # 完整构建, 跑单元测试
REM      mvn-build.bat -clean     # clean + package, 跳过测试
REM ====================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM ---- 1. 解析项目根目录 ----
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
if not exist "%BASE_DIR%\pom.xml" (
    echo [ERROR] pom.xml not found at "%BASE_DIR%".
    exit /b 1
)

REM ---- 2. 解析 maven ----
call :resolve_maven
if not defined MVN_EXE (
    echo [ERROR] mvn not found. Please install Maven 3.6+ or set MAVEN_HOME.
    exit /b 1
)

REM ---- 3. 解析构建参数 ----
set "SKIP_TESTS=-DskipTests"
set "CLEAN=0"
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="-test"      set "SKIP_TESTS="
if /i "%~1"=="-tests"     set "SKIP_TESTS="
if /i "%~1"=="-clean"     set "CLEAN=1"
shift
goto :parse_args
:args_done

echo ========================================
echo   E-Mall Backend Build
echo   Project : %BASE_DIR%
echo   Maven   : %MVN_EXE%
echo   Mode    : %CLEAN% (0=package, 1=clean+package)
echo   Tests   : %SKIP_TESTS%
echo ========================================
echo.

cd /d "%BASE_DIR%"

if "%CLEAN%"=="1" (
    echo [1/3] mvn clean ...
    "%MVN_EXE%" clean
    if not !ERRORLEVEL!==0 (
        echo [ERROR] mvn clean failed.
        exit /b 1
    )
) else (
    echo [1/3] skipping clean (use -clean to enable)
)

echo.
echo [2/3] mvn package %SKIP_TESTS% ...
"%MVN_EXE%" package %SKIP_TESTS%
if not !ERRORLEVEL!==0 (
    echo [ERROR] mvn package failed.
    exit /b 1
)

echo.
echo [3/3] Verifying build outputs ...
set "OK=0"
set "FAIL=0"
for %%S in (user-service product-service order-service inventory-service log-service gateway) do (
    set "JAR=%BASE_DIR%\%%S\target\%%S-1.0.0-SNAPSHOT.jar"
    if exist "!JAR!" (
        echo    [OK]   %%S-1.0.0-SNAPSHOT.jar
        set /a OK=OK+1
    ) else (
        echo    [FAIL] %%S-1.0.0-SNAPSHOT.jar NOT FOUND
        set /a FAIL=FAIL+1
    )
)

echo.
echo ========================================
echo   Build Summary: %OK% OK, %FAIL% FAIL
echo ========================================
if not "%FAIL%"=="0" exit /b 1
echo.
echo Next step: scripts\start-all-services.bat
endlocal
exit /b 0

REM ====================================================================
REM  Helper: 解析 mvn 位置
REM  1) 环境变量 MAVEN_HOME / M2_HOME
REM  2) PATH
REM  3) 注册表 HKLM\SOFTWARE\Apache Software Foundation\Maven
REM ====================================================================
:resolve_maven
if defined MAVEN_HOME (
    if exist "%MAVEN_HOME%\bin\mvn.cmd" set "MVN_EXE=%MAVEN_HOME%\bin\mvn.cmd"
    if exist "%MAVEN_HOME%\bin\mvn"     set "MVN_EXE=%MAVEN_HOME%\bin\mvn"
)
if defined M2_HOME if not defined MVN_EXE (
    if exist "%M2_HOME%\bin\mvn.cmd" set "MVN_EXE=%M2_HOME%\bin\mvn.cmd"
    if exist "%M2_HOME%\bin\mvn"     set "MVN_EXE=%M2_HOME%\bin\mvn"
)
if defined MVN_EXE exit /b 0

for /f "delims=" %%I in ('where mvn 2^>nul') do (
    if not defined MVN_EXE set "MVN_EXE=%%I"
)
if defined MVN_EXE exit /b 0

for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\Apache Software Foundation\Maven" /v MAVEN_HOME 2^>nul') do (
    if exist "%%B\bin\mvn.cmd" set "MVN_EXE=%%B\bin\mvn.cmd"
)
if defined MVN_EXE exit /b 0

exit /b 1
