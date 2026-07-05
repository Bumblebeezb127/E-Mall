@echo off
REM ====================================================================
REM  E-Mall Test Suite Runner (interactive, portable)
REM  - 默认交互模式: 每按一次回车, 执行一个测试, 输出对应结果
REM  - 一次性模式:  --all 参数, 串行执行全部测试 (旧行为)
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
set "MODE=interactive"
if /i "%~1"=="--all" set "MODE=batch"
if not exist "%RESULT_DIR%" mkdir "%RESULT_DIR%"

REM 测试清单 (短测试在前, 利于交互体验)
set "SCRIPTS=test_product_stock_sync.py test_cancel_restore_stock.py sentinel_test.py rabbitmq_test.py admin_test.py integration_test.py api_test.py"

echo ================================================
echo   E-Mall Test Suite Runner
echo   Project : %BASE_DIR%
echo   Gateway : %GATEWAY%
echo   Mode    : %MODE%
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
    echo [ERROR] python not found in PATH.
    pause
    exit /b 1
)

set "TOTAL_PASS=0"
set "TOTAL_FAIL=0"
set "TOTAL_SKIP=0"

REM ============== 一次性模式 ==============
if /i "%MODE%"=="batch" goto :batch_loop

REM ============== 交互模式 ==============
REM - 不用 goto 跳出 for 循环, 用 RUNNING=0 标志
REM - BATCH_REQUESTED=1 表示用户已选 [a], 跑剩余全部
set "RUNNING=1"
set "BATCH_REQUESTED=0"
set "IDX=0"
echo ================================================
echo   交互模式 - 每按一次回车, 执行一个测试
echo   [Enter] 执行当前   [s] 跳过当前
echo   [a] 跑完剩余全部   [q] 退出 (已跑结果保留)
echo ================================================
echo.
for %%F in (%SCRIPTS%) do (
    if !RUNNING!==1 (
        set "PY=%TEST_DIR%\%%F"
        if not exist "!PY!" (
            echo [SKIP] %%F - file not found
            set /a TOTAL_SKIP+=1
        ) else (
            if !BATCH_REQUESTED!==1 (
                call :run_test %%F "!PY!"
            ) else (
                set /a IDX+=1
                echo -----------------------------------------------
                echo   [ 待执行 !IDX!/7 ]  %%F
                echo -----------------------------------------------
                set "CMD=x"
                set /p "CMD=  按 [Enter] 执行 / [s] 跳过 / [a] 跑完剩余 / [q] 退出: "
                if /i "!CMD!"=="q" (
                    set "RUNNING=0"
                ) else if /i "!CMD!"=="a" (
                    set "BATCH_REQUESTED=1"
                    call :run_test %%F "!PY!"
                ) else if /i "!CMD!"=="s" (
                    echo   [SKIP] %%F
                    set /a TOTAL_SKIP+=1
                ) else (
                    call :run_test %%F "!PY!"
                )
                echo.
            )
        )
    )
)
goto :summary

:batch_loop
echo [INFO] batch mode: 串行执行全部测试 ...
for %%F in (%SCRIPTS%) do (
    set "PY=%TEST_DIR%\%%F"
    if exist "!PY!" (
        echo -----------------------------------------------
        echo [RUN] %%F
        echo -----------------------------------------------
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; & '%PY_EXE%' '!PY!' 2>&1 | ForEach-Object { $_ | Tee-Object -FilePath '%RESULT_DIR%\%%~nF.log' -Append | Out-Host }"
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
        set /a TOTAL_SKIP+=1
    )
)
goto :summary

REM ============== 执行单个测试 (子例程) ==============
:run_test
set "FNAME=%~1"
set "FPATH=%~2"
echo   [RUN] %FNAME% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Continue'; & '%PY_EXE%' '%FPATH%' 2>&1 | ForEach-Object { $_ | Tee-Object -FilePath '%RESULT_DIR%\%FNAME:~0,-3%.log' -Append | Out-Host }"
if !ERRORLEVEL!==0 (
    echo   [PASS] %FNAME%
    set /a TOTAL_PASS+=1
) else (
    echo   [FAIL] %FNAME% (exit !ERRORLEVEL!, log: %RESULT_DIR%\%FNAME:~0,-3%.log)
    set /a TOTAL_FAIL+=1
)
exit /b 0

:summary
echo ================================================
echo   FINAL SUMMARY
echo   PASS: !TOTAL_PASS!
echo   FAIL: !TOTAL_FAIL!
echo   SKIP: !TOTAL_SKIP!
echo   Detailed logs: %RESULT_DIR%\
echo ================================================
echo.
pause
endlocal
exit /b 0
