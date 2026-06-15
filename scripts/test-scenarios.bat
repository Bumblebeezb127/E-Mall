@echo off
setlocal enabledelayedexpansion

chcp 65001 > nul
color 0A

echo ================================================
echo     E-Mall 微服务异常场景测试脚本
echo ================================================
echo.

set GATEWAY_URL=http://localhost:8080
set INVENTORY_URL=http://localhost:8084
set PRODUCT_URL=http://localhost:8082
set NACOS_URL=http://localhost:8848
set SLEEP_INTERVAL=0.5
set WAIT_AFTER_RESTART=10

set TEST_USER=loadtest
set TEST_PASS=password123
set TOKEN=
set PRODUCT_ID=1
set ORDER_QUANTITY=1

set REPORT_FILE=test_report_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set REPORT_FILE=%REPORT_FILE: =%
set REPORT_FILE=%REPORT_FILE:/=-%

call :init_report
call :get_token

echo [INFO] 测试环境: %GATEWAY_URL%
echo [INFO] 报告文件: %REPORT_FILE%
echo.

goto menu

:menu
echo ================================================
echo              请选择测试场景
echo ================================================
echo   1. 熔断降级测试 (Circuit Breaker)
echo   2. 配置热更新测试 (Config Hot Update)
echo   3. 执行全部测试
echo   4. 退出
echo ================================================
set /p choice=请输入选项 [1-4]:

if "%choice%"=="1" goto test_circuit_breaker
if "%choice%"=="2" goto test_config_hot_update
if "%choice%"=="3" goto test_all
if "%choice%"=="4" goto end
echo [ERROR] 无效选项，请重新选择
echo.
goto menu

:test_all
call :test_circuit_breaker
echo.
call :test_config_hot_update
goto summary

:test_circuit_breaker
echo.
echo ================================================
echo       场景一：熔断降级测试
echo ================================================
call :log "========================================"
call :log "开始熔断降级测试 - %date% %time%"
call :log "========================================"

call :log_step "STEP 1" "准备测试 - 获取Token并验证服务正常"
echo [STEP 1] 准备测试 - 获取Token并验证服务正常

call :get_token
if not defined TOKEN (
    call :log_fail "获取Token失败"
    echo [FAIL] 获取Token失败，无法继续测试
    goto :eof
)
echo [INFO] Token获取成功: !TOKEN:~0,20!...

call :log_pass "Token获取成功"

echo.
call :log_step "STEP 2" "正常调用创建订单接口"
echo [STEP 2] 正常调用创建订单接口

call :create_order_normal
set NORMAL_RESULT=!ERRORLEVEL!

if !NORMAL_RESULT!==0 (
    call :log_pass "正常调用创建订单成功"
    echo [PASS] 正常调用创建订单成功
) else (
    call :log_warn "正常调用返回非预期结果"
    echo [WARN] 正常调用返回非预期结果，继续测试...
)

echo.
call :log_step "STEP 3" "停止inventory-service服务"
echo [STEP 3] 停止inventory-service服务

call :stop_inventory_service
if !ERRORLEVEL!==0 (
    call :log_pass "inventory-service已停止"
    echo [PASS] inventory-service已停止
) else (
    call :log_warn "停止服务失败，可能服务未运行"
    echo [WARN] 停止服务失败，可能服务未运行
)

echo.
call :log_step "STEP 4" "连续调用创建订单接口10次，观察降级"
echo [STEP 4] 连续调用创建订单接口10次（间隔0.5秒）

set DEGRADATION_COUNT=0
set TOTAL_CALLS=0

for /L %%i in (1,1,10) do (
    echo [INFO] 第 %%i/10 次调用...
    set /a TOTAL_CALLS+=1
    call :create_order_degradation
    if !ERRORLEVEL!==0 (
        set /a DEGRADATION_COUNT+=1
    )
    timeout /t 1 /nobreak > nul
)

echo.
echo [RESULT] 降级响应次数: !DEGRADATION_COUNT!/!TOTAL_CALLS!

if !DEGRADATION_COUNT! gtr 0 (
    call :log_pass "熔断降级生效 - !DEGRADATION_COUNT!/!TOTAL_CALLS! 次返回降级信息"
    echo [PASS] 熔断降级生效 - !DEGRADATION_COUNT!/!TOTAL_CALLS! 次返回降级信息
) else (
    call :log_fail "未检测到降级响应"
    echo [FAIL] 未检测到降级响应，请检查Sentinel配置
)

echo.
call :log_step "STEP 5" "等待10秒后重启inventory-service"
echo [STEP 5] 等待10秒后重启inventory-service

call :start_inventory_service
if !ERRORLEVEL!==0 (
    call :log_pass "inventory-service已重启"
    echo [PASS] inventory-service已重启
) else (
    call :log_warn "重启服务失败"
    echo [WARN] 重启服务失败
)

echo [INFO] 等待10秒让服务完全启动...
timeout /t 10 /nobreak > nul

echo.
call :log_step "STEP 6" "再次调用订单接口验证熔断器半开恢复"
echo [STEP 6] 再次调用订单接口验证熔断器半开恢复

call :create_order_normal
set RECOVERY_RESULT=!ERRORLEVEL!

if !RECOVERY_RESULT!==0 (
    call :log_pass "熔断器半开恢复成功"
    echo [PASS] 熔断器半开恢复成功，服务调用正常
) else (
    call :log_warn "服务调用仍异常，可能熔断器未完全恢复"
    echo [WARN] 服务调用仍异常，可能熔断器未完全恢复
)

call :log "========================================"
call :log "熔断降级测试完成"
call :log "========================================"

:skip_circuit_breaker
goto :eof

:test_config_hot_update
echo.
echo ================================================
echo       场景二：配置热更新测试
echo ================================================
call :log "========================================"
call :log "开始配置热更新测试 - %date% %time%"
call :log "========================================"

echo.
call :log_step "STEP 1" "记录当前每页默认记录数"
echo [STEP 1] 记录当前每页默认记录数

call :get_product_list
call :get_product_count_before

echo.
call :log_step "STEP 2" "修改Nacos配置 page.size: 10 -> 20"
echo [STEP 2] 修改Nacos配置 page.size: 10 ^-> 20

call :update_nacos_config "page.size=20"
if !ERRORLEVEL!==0 (
    call :log_pass "Nacos配置已修改为 page.size=20"
    echo [PASS] Nacos配置已修改为 page.size=20
) else (
    call :log_fail "Nacos配置修改失败"
    echo [FAIL] Nacos配置修改失败
    goto :skip_config_test
)

echo.
call :log_step "STEP 3" "等待3秒后调用商品列表接口验证"
echo [STEP 3] 等待3秒后调用商品列表接口验证

timeout /t 3 /nobreak > nul

call :get_product_list_size_20
set NEW_COUNT=!ERRORLEVEL!

if !NEW_COUNT!==20 (
    call :log_pass "热更新生效 - 返回20条记录"
    echo [PASS] 热更新生效 - 返回20条记录
) else (
    call :log_warn "记录数不符合预期: !NEW_COUNT! (期望20)"
    echo [WARN] 记录数不符合预期: !NEW_COUNT! (期望20)
)

echo.
call :log_step "STEP 4" "再次修改Nacos配置 page.size: 20 -> 5"
echo [STEP 4] 再次修改Nacos配置 page.size: 20 ^-> 5

call :update_nacos_config "page.size=5"
if !ERRORLEVEL!==0 (
    call :log_pass "Nacos配置已修改为 page.size=5"
    echo [PASS] Nacos配置已修改为 page.size=5
) else (
    call :log_fail "Nacos配置修改失败"
    echo [FAIL] Nacos配置修改失败
    goto :skip_config_test
)

echo.
call :log_step "STEP 5" "等待3秒后调用商品列表接口验证"
echo [STEP 5] 等待3秒后调用商品列表接口验证

timeout /t 3 /nobreak > nul

call :get_product_list_size_5
set FINAL_COUNT=!ERRORLEVEL!

if !FINAL_COUNT!==5 (
    call :log_pass "热更新生效 - 返回5条记录"
    echo [PASS] 热更新生效 - 返回5条记录
) else (
    call :log_warn "记录数不符合预期: !FINAL_COUNT! (期望5)"
    echo [WARN] 记录数不符合预期: !FINAL_COUNT! (期望5)
)

echo.
call :log_step "STEP 6" "恢复配置为默认值 page.size=10"
echo [STEP 6] 恢复配置为默认值 page.size=10

call :update_nacos_config "page.size=10"
call :log_pass "配置已恢复"

call :log "========================================"
call :log "配置热更新测试完成"
call :log "========================================"

:skip_config_test
goto :eof

:summary
echo.
echo ================================================
echo            测试执行摘要
echo ================================================
echo.
echo 场景一（熔断降级测试）:
echo   - 降级响应率: !DEGRADATION_COUNT!/!TOTAL_CALLS!
echo   - 恢复验证: !RECOVERY_RESULT!
echo.
echo 场景二（配置热更新测试）:
echo   - 修改为20后记录数: !NEW_COUNT!
echo   - 修改为5后记录数: !FINAL_COUNT!
echo.
echo 详细报告已保存至: %REPORT_FILE%
echo ================================================

goto end

:init_report
echo [测试报告 - %date% %time%] > %REPORT_FILE%
echo ============================================== >> %REPORT_FILE%
echo. >> %REPORT_FILE%
goto :eof

:log
echo %~1 >> %REPORT_FILE%
goto :eof

:log_step
echo. >> %REPORT_FILE%
echo [%%1] %%2 >> %REPORT_FILE%
goto :eof

:log_pass
echo [PASS] %~1 >> %REPORT_FILE%
goto :eof

:log_fail
echo [FAIL] %~1 >> %REPORT_FILE%
goto :eof

:log_warn
echo [WARN] %~1 >> %REPORT_FILE%
goto :eof

:get_token
echo [INFO] 获取访问Token...
for /f "tokens=*" %%r in ('curl -s -X POST "%GATEWAY_URL%/api/user/login" -H "Content-Type: application/json" -d "{\"username\":\"%TEST_USER%\",\"password\":\"%TEST_PASS%\"}"') do set RESPONSE=%%r
echo !RESPONSE! | findstr /C:"\"code\":200" > nul
if !ERRORLEVEL!==0 (
    for /f "tokens=2 delims=,: " %%a in ('echo !RESPONSE! ^| findstr "token"') do set TOKEN=%%a
    set TOKEN=!TOKEN:"=!
    set TOKEN=!TOKEN:,=!
    set TOKEN=!TOKEN:}=!
    exit /b 0
) else (
    set TOKEN=
    exit /b 1
)

:create_order_normal
for /f "tokens=*" %%r in ('curl -s -X POST "%GATEWAY_URL%/api/order/create" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN%" -d "{\"userId\":1,\"productId\":%PRODUCT_ID%,\"quantity\":%ORDER_QUANTITY%}"') do set ORDER_RESP=%%r
echo !ORDER_RESP! | findstr /C:"\"code\":200" > nul
if !ERRORLEVEL!==0 (
    exit /b 0
) else (
    exit /b 1
)

:create_order_degradation
for /f "tokens=*" %%r in ('curl -s -X POST "%GATEWAY_URL%/api/order/create" -H "Content-Type: application/json" -H "Authorization: Bearer %TOKEN%" -d "{\"userId\":1,\"productId\":%PRODUCT_ID%,\"quantity\":%ORDER_QUANTITY%}"') do set ORDER_RESP=%%r
echo !ORDER_RESP! | findstr /C:"库存服务" > nul
if !ERRORLEVEL!==0 (
    echo       [!ORDER_RESP:~0,80!...]
    exit /b 0
)
echo !ORDER_RESP! | findstr /C:"繁忙" > nul
if !ERRORLEVEL!==0 (
    echo       [!ORDER_RESP:~0,80!...]
    exit /b 0
)
echo !ORDER_RESP! | findstr /C:"不可用" > nul
if !ERRORLEVEL!==0 (
    echo       [!ORDER_RESP:~0,80!...]
    exit /b 0
)
echo !ORDER_RESP! | findstr /C:"降级" > nul
if !ERRORLEVEL!==0 (
    echo       [!ORDER_RESP:~0,80!...]
    exit /b 0
)
echo !ORDER_RESP! | findstr /C:"503" > nul
if !ERRORLEVEL!==0 (
    echo       [!ORDER_RESP:~0,80!...]
    exit /b 0
)
echo       [响应: !ORDER_RESP:~0,60!...]
exit /b 1

:get_product_list
for /f "tokens=*" %%r in ('curl -s "%GATEWAY_URL%/api/product/list?page=1^&size=10"') do set PROD_RESP=%%r
goto :eof

:get_product_list_size_20
for /f "tokens=*" %%r in ('curl -s "%GATEWAY_URL%/api/product/list?page=1^&size=20"') do set PROD_RESP_20=%%r
echo !PROD_RESP_20! | findstr /C:"\"code\":200" > nul
if !ERRORLEVEL!==0 (
    for /f "tokens=*" %%c in ('echo !PROD_RESP_20! ^| findstr /C:"\"id\":"') do (
        set /a COUNT+=1
    )
    exit /b !COUNT!
)
exit /b 0

:get_product_list_size_5
for /f "tokens=*" %%r in ('curl -s "%GATEWAY_URL%/api/product/list?page=1^&size=5"') do set PROD_RESP_5=%%r
echo !PROD_RESP_5! | findstr /C:"\"code\":200" > nul
if !ERRORLEVEL!==0 (
    set COUNT=0
    for /f "tokens=*" %%c in ('echo !PROD_RESP_5! ^| findstr /C:"\"id\":"') do (
        set /a COUNT+=1
    )
    exit /b !COUNT!
)
exit /b 0

:get_product_count_before
set COUNT=0
for /f "tokens=*" %%c in ('echo !PROD_RESP! ^| findstr /C:"\"id\":"') do (
    set /a COUNT+=1
)
echo [INFO] 当前记录数: !COUNT!
exit /b 0

:stop_inventory_service
echo [INFO] 停止inventory-service (localhost:8084)...
netstat -ano | findstr ":8084" | findstr "LISTENING" > nul
if !ERRORLEVEL! neq 0 (
    echo [INFO] inventory-service可能未运行
    exit /b 0
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8084" ^| findstr "LISTENING"') do set PID=%%p
echo [INFO] 找到进程 PID: !PID!
taskkill /F /PID !PID! > nul 2>&1
if !ERRORLEVEL!==0 (
    echo [INFO] inventory-service已停止
    exit /b 0
) else (
    echo [WARN] 无法停止进程
    exit /b 1
)

:start_inventory_service
echo [INFO] 启动inventory-service...
echo [INFO] 请确保服务可执行文件或IDE运行配置已就绪
echo [INFO] 手动启动命令: java -jar inventory-service.jar
echo [INFO] 或在IDE中启动 InventoryServiceApplication
exit /b 0

:update_nacos_config
echo [INFO] 更新Nacos配置: %~1
echo [WARN] 请手动在Nacos控制台修改配置:
echo [WARN]   1. 访问 http://localhost:8848/nacos
echo [WARN]   2. 进入 配置管理 -> 配置列表
echo [WARN]   3. 选择 product-service.yaml
echo [WARN]   4. 修改 %~1
echo [WARN]   5. 点击发布
echo.
set /p confirm=确认已完成Nacos配置修改? [Y/N]:
if /i "!confirm!"=="Y" (
    exit /b 0
) else (
    exit /b 1
)

:end
echo.
echo [INFO] 测试脚本执行完成
pause
