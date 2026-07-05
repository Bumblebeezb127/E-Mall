@echo off
setlocal enabledelayedexpansion

set "BASE_DIR=d:\Learning materials\SpringCloud\e-mall"
set "TEST_DIR=%BASE_DIR%\test"
set "RESULT_DIR=%TEST_DIR%\results"
set "GATEWAY_URL=http://localhost:9000"

if not exist "%RESULT_DIR%" mkdir "%RESULT_DIR%"

echo ================================================
echo   E-Mall Test Suite Runner
echo   Time: %date% %time%
echo   Gateway: %GATEWAY_URL%
echo ================================================

REM Pre-check: gateway reachable?
echo.
echo [Pre-check] Gateway health ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%GATEWAY_URL%/api/product/list?page=1&size=1' -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo   [FAIL] Gateway not reachable at %GATEWAY_URL%
    echo   Please start services first: scripts\start-all-services.bat
    exit /b 1
)
echo   [OK] Gateway is up

set PASS=0
set FAIL=0
set "SUMMARY="

call :run_test "api_test.py"                  "16" "End-to-end API flow"
call :run_test "integration_test.py"          "12" "Auth + Order integration"
call :run_test "sentinel_test.py"             "4"  "Sentinel circuit breaker"
call :run_test "test_cancel_restore_stock.py" "3"  "Cancel order restores stock"
call :run_test "test_product_stock_sync.py"   "1"  "Product stock sync (V3)"

echo.
echo ================================================
echo   FINAL SUMMARY
echo ================================================
echo   PASS: !PASS!
echo   FAIL: !FAIL!
echo.
echo   Details:
echo !SUMMARY!
echo.
echo   Detailed logs: %RESULT_DIR%\
echo ================================================

if !FAIL! gtr 0 ( exit /b 1 ) else ( exit /b 0 )


REM ============================================================
REM Run a single test, capture exit code + output, classify result
REM Args: %1=script  %2=cases  %3=description
REM ============================================================
:run_test
set "NAME=%~1"
set "CASES=%~2"
set "DESC=%~3"
set "BASE=%~n1"
set "LOG=%RESULT_DIR%\%BASE%.log"

echo.
echo ------------------------------------------------
echo [%CASES% cases] %NAME%
echo   %DESC%
echo ------------------------------------------------

python "%TEST_DIR%\%NAME%" > "%LOG%" 2>&1
set "EC=!ERRORLEVEL!"

findstr /C:"[FAIL]" /C:"[BUG CONFIRMED]" "%LOG%" >nul 2>&1
set "HAS_FAIL=!ERRORLEVEL!"
findstr /C:"[PASS]" /C:"  [OK]" "%LOG%" >nul 2>&1
set "HAS_PASS=!ERRORLEVEL!"

REM --- Classification (avoid compound if/else ambiguity) ---
set "RESULT=FAIL"
set "REASON=exit !EC!"

if !EC! equ 0 (
    if !HAS_FAIL! neq 0 (
        set "RESULT=PASS"
        set "REASON=exit 0"
    ) else (
        set "REASON=exit 0 but FAIL marker in output"
    )
) else (
    if !HAS_PASS! equ 0 (
        if !HAS_FAIL! neq 0 (
            set "RESULT=PASS"
            set "REASON=exit !EC! but PASS marker in output"
        ) else (
            set "REASON=exit !EC! and FAIL marker in output"
        )
    ) else (
        set "REASON=exit !EC!"
    )
)

REM --- Print result + accumulate summary ---
if "!RESULT!"=="PASS" (
    echo   [PASS] %NAME%  ^(!REASON!^)
    set /a PASS+=1
    set "SUMMARY=!SUMMARY!  [PASS] %NAME% (%CASES% cases) - !REASON!; "
) else (
    echo   [FAIL] %NAME%  ^(!REASON!^, log: %LOG%^)
    set /a FAIL+=1
    set "SUMMARY=!SUMMARY!  [FAIL] %NAME% (%CASES% cases) - !REASON!; "
)
goto :eof
