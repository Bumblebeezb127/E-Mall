@echo off
REM ====================================================================
REM  E-Mall Test Suite Runner (portable)
REM  - 项目根从脚本所在目录自动解析
REM  - 实时输出到终端, 同时落到 test\results\*.log
REM ====================================================================
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
if not exist "%BASE_DIR%\pom.xml" (
    echo [ERROR] pom.xml not found at "%BASE_DIR%".
    exit /b 1
)

set "TEST_DIR=%BASE_DIR%\test"
set "RESULT_DIR=%TEST_DIR%\results"
set "GATEWAY=http://localhost:9000"
if not exist "%RESULT_DIR%" mkdir "%RESULT_DIR%"

echo ================================================
echo   E-Mall Test Suite Runner
echo   Project : %BASE_DIR%
echo   Gateway : %GATEWAY%
echo   Time    : %DATE% %TIME%
echo ================================================

echo.
echo [Pre-check] Gateway health ...
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; try { (Invoke-WebRequest -Uri '%GATEWAY%/api/product/list' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { 'DOWN' }"
echo.

set "SCRIPTS=api_test.py integration_test.py sentinel_test.py test_cancel_restore_stock.py test_product_stock_sync.py admin_test.py"
set "TOTAL_PASS=0"
set "TOTAL_FAIL=0"

for %%F in (%SCRIPTS%) do (
    set "PY=%TEST_DIR%\%%F"
    if exist "!PY!" (
        echo -----------------------------------------------
        echo [RUN] %%F
        echo -----------------------------------------------
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; & python '!PY!' 2>&1 | ForEach-Object { $_ | Tee-Object -FilePath '%RESULT_DIR%\%%~nF.log' -Append | Out-Host }"
        if !ERRORLEVEL!==0 (
            echo    [PASS] %%F
            set /a TOTAL_PASS+=1
        ) else (
            echo    [FAIL] %%F (exit !ERRORLEVEL!, log: %RESULT_DIR%\%%~nF.log)
            set /a TOTAL_FAIL+=1
        )
        echo.
    ) else (
        echo    [SKIP] %%F - file not found
    )
)

echo ================================================
echo   FINAL SUMMARY
echo   PASS: !TOTAL_PASS!
echo   FAIL: !TOTAL_FAIL!
echo   Detailed logs: %RESULT_DIR%\
echo ================================================

echo.
pause
endlocal
exit /b 0
