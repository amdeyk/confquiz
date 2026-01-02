#!/bin/bash
# Run these commands on your VPS to fix test failures
# Location: /opt/apps/confquiz

echo "========================================="
echo "Fixing Quiz App for Tests"
echo "========================================="
echo ""

# Step 1: Navigate to app directory
cd /opt/apps/confquiz
source venv/bin/activate

# Step 2: Run the database migration
echo "Step 1: Running database migration..."
python migrations/001_add_admin_settings.py

if [ $? -eq 0 ]; then
    echo "✓ Migration completed successfully"
else
    echo "✗ Migration failed - check output above"
    exit 1
fi
echo ""

# Step 3: Verify admin_settings table exists
echo "Step 2: Verifying admin_settings table..."
ADMIN_SETTINGS_COUNT=$(sqlite3 quiz.db "SELECT COUNT(*) FROM admin_settings;" 2>/dev/null)

if [ "$ADMIN_SETTINGS_COUNT" -ge 3 ]; then
    echo "✓ admin_settings table exists with $ADMIN_SETTINGS_COUNT settings"
else
    echo "✗ admin_settings table verification failed"
    exit 1
fi
echo ""

# Step 4: Check admin user exists
echo "Step 3: Checking admin user..."
ADMIN_COUNT=$(sqlite3 quiz.db "SELECT COUNT(*) FROM users WHERE role='admin';" 2>/dev/null)

if [ "$ADMIN_COUNT" -ge 1 ]; then
    echo "✓ Admin user exists"
else
    echo "⚠ No admin user found - creating one..."
    python -c "
import asyncio
from database import AsyncSessionLocal
from models import User
from auth import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            username='admin',
            password_hash=get_password_hash('admin123'),
            role='admin'
        )
        db.add(admin)
        await db.commit()
        print('✓ Admin user created (username: admin, password: admin123)')

asyncio.run(create_admin())
"
fi
echo ""

# Step 5: Check if server is running
echo "Step 4: Checking server status..."
if pgrep -f "python main.py" > /dev/null; then
    echo "✓ Server is running"
    echo "  Restarting server to load new routes..."
    pkill -f "python main.py"
    sleep 2
    nohup python main.py > logs/app.log 2>&1 &
    sleep 3
    echo "✓ Server restarted"
else
    echo "⚠ Server not running - starting it..."
    nohup python main.py > logs/app.log 2>&1 &
    sleep 3
    echo "✓ Server started"
fi
echo ""

# Step 6: Quick API test
echo "Step 5: Testing API endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    echo "✓ API is responding (HTTP 200)"
else
    echo "✗ API test failed (HTTP $RESPONSE)"
    echo "  Check logs: tail -f logs/app.log"
    exit 1
fi
echo ""

# Step 7: Test admin login
echo "Step 6: Testing admin login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✓ Admin login successful"
else
    echo "✗ Admin login failed"
    echo "  Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

echo "========================================="
echo "✓ All checks passed!"
echo "========================================="
echo ""
echo "Now run the tests:"
echo "  python test_all_endpoints.py"
echo ""
