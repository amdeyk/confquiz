#!/bin/bash
# Deploy screen sharing updates to VPS
# Usage: ./deploy_to_vps.sh your-vps-ip

VPS_IP=$1
VPS_USER="root"
APP_DIR="/opt/apps/confquiz"

if [ -z "$VPS_IP" ]; then
    echo "Usage: ./deploy_to_vps.sh <vps-ip>"
    echo "Example: ./deploy_to_vps.sh 192.168.1.100"
    exit 1
fi

echo "========================================="
echo "Deploying Screen Sharing Updates to VPS"
echo "========================================="
echo ""
echo "Target: $VPS_USER@$VPS_IP:$APP_DIR"
echo ""

# Check if files exist locally
echo "Step 1: Checking local files..."
FILES_TO_DEPLOY=(
    "templates/admin_dashboard.html"
    "templates/presenter_login.html"
    "templates/presenter_dashboard.html"
    "templates/display.html"
    "routers/admin_router.py"
    "routers/ws_router.py"
    "main.py"
    "auth.py"
    "schemas.py"
    "models.py"
    "database.py"
    "migrations/001_add_admin_settings.py"
)

MISSING_FILES=0
for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ✗ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "  ✓ Found: $file"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "❌ Error: $MISSING_FILES file(s) missing"
    echo "Please run this script from the quiz project root directory"
    exit 1
fi

echo ""
echo "Step 2: Backing up current files on VPS..."
ssh $VPS_USER@$VPS_IP "cd $APP_DIR && mkdir -p backups/$(date +%Y%m%d_%H%M%S) && cp templates/*.html routers/*.py *.py backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true"

if [ $? -eq 0 ]; then
    echo "  ✓ Backup created"
else
    echo "  ⚠ Backup failed (continuing anyway)"
fi

echo ""
echo "Step 3: Deploying files..."

# Deploy templates
echo "  Deploying templates..."
scp templates/admin_dashboard.html $VPS_USER@$VPS_IP:$APP_DIR/templates/
scp templates/presenter_login.html $VPS_USER@$VPS_IP:$APP_DIR/templates/
scp templates/presenter_dashboard.html $VPS_USER@$VPS_IP:$APP_DIR/templates/
scp templates/display.html $VPS_USER@$VPS_IP:$APP_DIR/templates/

# Deploy routers
echo "  Deploying routers..."
scp routers/admin_router.py $VPS_USER@$VPS_IP:$APP_DIR/routers/
scp routers/ws_router.py $VPS_USER@$VPS_IP:$APP_DIR/routers/

# Deploy main files
echo "  Deploying main files..."
scp main.py $VPS_USER@$VPS_IP:$APP_DIR/
scp auth.py $VPS_USER@$VPS_IP:$APP_DIR/
scp schemas.py $VPS_USER@$VPS_IP:$APP_DIR/
scp models.py $VPS_USER@$VPS_IP:$APP_DIR/
scp database.py $VPS_USER@$VPS_IP:$APP_DIR/

# Deploy migration
echo "  Deploying migration..."
ssh $VPS_USER@$VPS_IP "mkdir -p $APP_DIR/migrations"
scp migrations/001_add_admin_settings.py $VPS_USER@$VPS_IP:$APP_DIR/migrations/

# Deploy fix scripts
echo "  Deploying helper scripts..."
scp fix_admin_settings_data.py $VPS_USER@$VPS_IP:$APP_DIR/
scp quick_fix.sh $VPS_USER@$VPS_IP:$APP_DIR/

echo ""
echo "Step 4: Running post-deployment tasks..."

ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /opt/apps/confquiz
source venv/bin/activate

echo "  Running database migration..."
python migrations/001_add_admin_settings.py

echo "  Fixing admin_settings data..."
python fix_admin_settings_data.py

echo "  Restarting server..."
pkill -f "python main.py"
sleep 2
nohup python main.py > logs/app.log 2>&1 &
sleep 3

echo "  Verifying server started..."
if pgrep -f "python main.py" > /dev/null; then
    echo "  ✓ Server is running"
else
    echo "  ✗ Server failed to start - check logs"
    exit 1
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Deployment Successful!"
    echo "========================================="
    echo ""
    echo "Your VPS is now updated with:"
    echo "  ✓ Screen sharing feature (WebRTC)"
    echo "  ✓ Presenter dashboard"
    echo "  ✓ Display settings UI"
    echo "  ✓ Admin settings configured"
    echo ""
    echo "URLs:"
    echo "  Admin Dashboard:     http://$VPS_IP:8000/admin/dashboard"
    echo "  Presenter Login:     http://$VPS_IP:8000/presenter/login"
    echo "  Display Screen:      http://$VPS_IP:8000/display"
    echo ""
    echo "Next steps:"
    echo "  1. Login to admin dashboard"
    echo "  2. Create presenter user (now available in UI)"
    echo "  3. Test presenter login"
    echo "  4. Test screen sharing"
    echo ""
else
    echo ""
    echo "❌ Deployment failed - check errors above"
    exit 1
fi
