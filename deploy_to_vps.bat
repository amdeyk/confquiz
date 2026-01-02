@echo off
REM Deploy screen sharing updates to VPS (Windows version)
REM Usage: deploy_to_vps.bat your-vps-ip
REM Requires: PuTTY's pscp.exe and plink.exe in PATH (or install WinSCP)

set VPS_IP=%1
set VPS_USER=root
set APP_DIR=/opt/apps/confquiz

if "%VPS_IP%"=="" (
    echo Usage: deploy_to_vps.bat ^<vps-ip^>
    echo Example: deploy_to_vps.bat 192.168.1.100
    exit /b 1
)

echo =========================================
echo Deploying Screen Sharing Updates to VPS
echo =========================================
echo.
echo Target: %VPS_USER%@%VPS_IP%:%APP_DIR%
echo.
echo NOTE: This script uses SCP for file transfer.
echo       If you don't have pscp/plink, use WinSCP or manual upload.
echo.

REM Check if pscp is available
where pscp >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pscp not found in PATH
    echo.
    echo Please install PuTTY or use manual deployment:
    echo.
    echo 1. Open WinSCP
    echo 2. Connect to %VPS_IP%
    echo 3. Upload these files to %APP_DIR%:
    echo    - templates\admin_dashboard.html
    echo    - templates\presenter_login.html
    echo    - templates\presenter_dashboard.html
    echo    - templates\display.html
    echo    - routers\admin_router.py
    echo    - routers\ws_router.py
    echo    - main.py
    echo    - auth.py
    echo    - schemas.py
    echo    - models.py
    echo    - database.py
    echo    - migrations\001_add_admin_settings.py
    echo.
    echo 4. SSH to VPS and run:
    echo    cd %APP_DIR%
    echo    python migrations/001_add_admin_settings.py
    echo    python fix_admin_settings_data.py
    echo    pkill -f "python main.py"
    echo    nohup python main.py ^> logs/app.log 2^>^&1 ^&
    echo.
    pause
    exit /b 1
)

echo Step 1: Deploying templates...
pscp templates\admin_dashboard.html %VPS_USER%@%VPS_IP%:%APP_DIR%/templates/
pscp templates\presenter_login.html %VPS_USER%@%VPS_IP%:%APP_DIR%/templates/
pscp templates\presenter_dashboard.html %VPS_USER%@%VPS_IP%:%APP_DIR%/templates/
pscp templates\display.html %VPS_USER%@%VPS_IP%:%APP_DIR%/templates/

echo Step 2: Deploying routers...
pscp routers\admin_router.py %VPS_USER%@%VPS_IP%:%APP_DIR%/routers/
pscp routers\ws_router.py %VPS_USER%@%VPS_IP%:%APP_DIR%/routers/

echo Step 3: Deploying main files...
pscp main.py %VPS_USER%@%VPS_IP%:%APP_DIR%/
pscp auth.py %VPS_USER%@%VPS_IP%:%APP_DIR%/
pscp schemas.py %VPS_USER%@%VPS_IP%:%APP_DIR%/
pscp models.py %VPS_USER%@%VPS_IP%:%APP_DIR%/
pscp database.py %VPS_USER%@%VPS_IP%:%APP_DIR%/

echo Step 4: Deploying migration...
plink %VPS_USER%@%VPS_IP% "mkdir -p %APP_DIR%/migrations"
pscp migrations\001_add_admin_settings.py %VPS_USER%@%VPS_IP%:%APP_DIR%/migrations/

echo Step 5: Deploying helper scripts...
pscp fix_admin_settings_data.py %VPS_USER%@%VPS_IP%:%APP_DIR%/
pscp quick_fix.sh %VPS_USER%@%VPS_IP%:%APP_DIR%/

echo.
echo Step 6: Restarting server on VPS...
plink %VPS_USER%@%VPS_IP% "cd %APP_DIR% && source venv/bin/activate && python migrations/001_add_admin_settings.py && python fix_admin_settings_data.py && pkill -f 'python main.py' && sleep 2 && nohup python main.py > logs/app.log 2>&1 &"

echo.
echo =========================================
echo Deployment Complete!
echo =========================================
echo.
echo Your VPS should now have:
echo   - Screen sharing feature
echo   - Presenter dashboard
echo   - Display settings UI
echo   - Admin settings configured
echo.
echo Test at:
echo   Admin: https://aisquiz.qubixvirtual.in/admin/dashboard
echo   Presenter: https://aisquiz.qubixvirtual.in/presenter/login
echo.
pause
