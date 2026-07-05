@echo off
REM ====================================================================
REM  E-Mall Frontend Initialization Script (portable)
REM
REM  - 脚本所在目录的父目录即为项目根
REM  - 自动定位 easybuy-frontend 目录
REM  - node / npm 自动从 NODE_HOME / PATH / 常见安装路径查找
REM  - 不再硬编码任何绝对路径
REM
REM  执行步骤:
REM      1. 校验 easybuy-frontend\package.json 存在
REM      2. 校验 / 安装 npm 依赖 (npm install)
REM      3. 推送 Nacos 后端配置
REM      4. 升级 MySQL 数据库 (执行 sql/upgrade.sql)
REM      5. 更新商品图片占位 (执行 scripts/update_product_images.py)
REM      6. 提示后续步骤
REM
REM  Usage:
REM      frontend-init.bat           # 默认执行所有步骤
REM      frontend-init.bat -skip-deps # 跳过 npm install
REM      frontend-init.bat -skip-db  # 跳过数据库升级
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

set "FRONTEND_DIR=%BASE_DIR%\easybuy-frontend"
if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] easybuy-frontend\package.json not found at "%FRONTEND_DIR%".
    exit /b 1
)

REM ---- 2. 解析 node / npm ----
call :resolve_node
if not defined NPM_EXE (
    echo [ERROR] npm not found. Please install Node.js 18+ or set NODE_HOME.
    exit /b 1
)

REM ---- 3. 解析 Python (用于运行 init 脚本) ----
call :resolve_python
if not defined PYTHON_EXE (
    echo [ERROR] python not found. Please install Python 3.8+ or set PYTHON_HOME.
    exit /b 1
)

REM ---- 4. 解析参数 ----
set "SKIP_DEPS=0"
set "SKIP_DB=0"
:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="-skip-deps" set "SKIP_DEPS=1"
if /i "%~1"=="-skip-db"   set "SKIP_DB=1"
shift
goto :parse_args
:args_done

echo ========================================
echo   E-Mall Frontend Initialization
echo   Project  : %BASE_DIR%
echo   Frontend : %FRONTEND_DIR%
echo   Node     : %NODE_EXE%
echo   npm      : %NPM_EXE%
echo   Python   : %PYTHON_EXE%
echo ========================================
echo.

REM ---- 5. 安装依赖 ----
if "%SKIP_DEPS%"=="1" (
    echo [1/5] skipping npm install (use default to install)
) else (
    echo [1/5] Installing npm dependencies (this may take a few minutes) ...
    cd /d "%FRONTEND_DIR%"
    "%NPM_EXE%" install --no-audit --no-fund --loglevel=error
    if not !ERRORLEVEL!==0 (
        echo [ERROR] npm install failed.
        exit /b 1
    )
    cd /d "%BASE_DIR%"
)

REM ---- 6. 推送 Nacos 配置 ----
echo.
echo [2/5] Pushing Nacos configs ...
"%PYTHON_EXE%" "%BASE_DIR%\scripts\push_nacos_configs.py"
if not !ERRORLEVEL!==0 (
    echo [WARN] push_nacos_configs failed, but continuing.
)

REM ---- 7. 升级数据库 ----
if "%SKIP_DB%"=="1" (
    echo.
    echo [3/5] skipping database upgrade (use default to upgrade)
) else (
    echo.
    echo [3/5] Upgrading MySQL database ...
    "%PYTHON_EXE%" "%BASE_DIR%\scripts\upgrade_db.py"
    if not !ERRORLEVEL!==0 (
        echo [WARN] upgrade_db failed, but continuing. You can run it manually later.
    )
)

REM ---- 8. 更新商品图片 ----
echo.
echo [4/5] Updating product images ...
"%PYTHON_EXE%" "%BASE_DIR%\scripts\update_product_images.py"
if not !ERRORLEVEL!==0 (
    echo [WARN] update_product_images failed, but continuing.
)

REM ---- 9. 完成 ----
echo.
echo [5/5] Done. Summary:
echo.
echo   Dependencies installed at : %FRONTEND_DIR%\node_modules
echo   Nacos configs             : pushed (or skipped)
echo   Database                  : upgrade attempted
echo   Product images            : updated
echo.
echo Next steps:
echo   1. Start backend services : scripts\mvn-build.bat  ^&^&  scripts\start-all-services.bat
echo   2. Start frontend dev     : cd %FRONTEND_DIR% ^&^& npm run dev
echo   3. Build frontend prod    : cd %FRONTEND_DIR% ^&^& npm run build
echo.
endlocal
exit /b 0

REM ====================================================================
REM  Helper: 解析 node / npm
REM  1) 环境变量 NODE_HOME
REM  2) PATH
REM  3) 常见安装路径
REM ====================================================================
:resolve_node
if defined NODE_HOME (
    if exist "%NODE_HOME%\node.exe" set "NODE_EXE=%NODE_HOME%\node.exe"
    if exist "%NODE_HOME%\npm.cmd"  set "NPM_EXE=%NODE_HOME%\npm.cmd"
)
if not defined NPM_EXE (
    for /f "delims=" %%I in ('where npm 2^>nul') do (
        if not defined NPM_EXE set "NPM_EXE=%%I"
    )
)
if defined NPM_EXE (
    for %%I in ("%NPM_EXE%") do set "NPM_DIR=%%~dpI"
    if exist "!NPM_DIR!\node.exe" set "NODE_EXE=!NPM_DIR!\node.exe"
)
if defined NODE_EXE exit /b 0

for %%P in ("%ProgramFiles%\nodejs\node.exe" "%ProgramFiles(x86)%\nodejs\node.exe" "%LOCALAPPDATA%\Programs\nodejs\node.exe") do (
    if exist "%%~P" (
        set "NODE_EXE=%%~P"
        set "NPM_EXE=%%~dpnode.exe"
    )
)
if defined NODE_EXE exit /b 0

exit /b 1

REM ====================================================================
REM  Helper: 解析 python
REM  1) 环境变量 PYTHON_HOME
REM  2) PATH
REM ====================================================================
:resolve_python
if defined PYTHON_HOME (
    if exist "%PYTHON_HOME%\python.exe" set "PYTHON_EXE=%PYTHON_HOME%\python.exe"
    if exist "%PYTHON_HOME%\python"     set "PYTHON_EXE=%PYTHON_HOME%\python"
)
if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
    )
)
if not defined PYTHON_EXE (
    for /f "delims=" %%I in ('where py 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
    )
)
if defined PYTHON_EXE exit /b 0
exit /b 1
