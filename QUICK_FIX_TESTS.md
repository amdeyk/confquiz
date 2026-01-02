# Quick Fix for Test Failures

## Issues Found:
1. ❌ Admin Login Failed - "Not Found" error
2. ❌ Admin Settings Table - Migration not run
3. ❌ Authorization tests failing

---

## Fix Steps (Run on VPS)

### Step 1: Run Database Migration
```bash
cd /opt/apps/confquiz
source venv/bin/activate
python migrations/001_add_admin_settings.py
```

Expected output:
```
Running migration: 001_add_admin_settings
Creating tables...
Inserting default admin settings...
Inserted 3 default admin settings:
  - display_mode = png_slides
  - screen_share_fps = 10
  - screen_share_quality = 0.7
Migration completed successfully!
```

### Step 2: Check Server Startup
```bash
# Check if server is actually running
ps aux | grep main.py

# Check server logs
tail -f logs/app.log  # or wherever logs are

# Or restart server with visible output
python main.py
```

Look for startup errors in the logs.

### Step 3: Verify API Endpoints
```bash
# Test if API is responding
curl http://localhost:8000/
curl http://localhost:8000/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Should return a token, not "Not Found".

### Step 4: Check Admin User Exists
```bash
# Check database for admin user
sqlite3 quiz.db "SELECT * FROM users WHERE role='admin';"
```

If no admin user exists, create one:
```bash
python -c "
from database import AsyncSessionLocal
from models import User
from auth import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            username='admin',
            password_hash=get_password_hash('admin123'),
            role='admin'
        )
        db.add(admin)
        await db.commit()
        print('Admin user created!')

asyncio.run(create_admin())
"
```

### Step 5: Re-run Tests
```bash
python test_all_endpoints.py
```

---

## Common Issues

### Issue 1: Server Not Starting
**Symptom**: "Connection refused" or "Not Found"

**Solution**:
```bash
# Check what's on port 8000
lsof -i :8000
netstat -tulpn | grep 8000

# Kill old process if stuck
kill -9 <PID>

# Start fresh
python main.py
```

### Issue 2: Import Errors on Startup
**Symptom**: ModuleNotFoundError

**Solution**:
```bash
# Install missing dependencies
pip install -r requirements.txt
```

### Issue 3: Database Locked
**Symptom**: "database is locked"

**Solution**:
```bash
# Stop all processes using the database
fuser quiz.db
kill <PID>

# Or restart server
```

### Issue 4: Routes Not Registered
**Symptom**: All endpoints return 404

**Solution**: Check main.py has all router imports:
```python
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
# ... etc
```

---

## Quick Verification Script

Save as `verify_setup.sh`:
```bash
#!/bin/bash

echo "=== Checking Quiz App Setup ==="

# 1. Check server process
echo -n "Server running: "
if pgrep -f "python main.py" > /dev/null; then
    echo "✓ Yes"
else
    echo "✗ No - Start with: python main.py"
fi

# 2. Check database
echo -n "Database exists: "
if [ -f "quiz.db" ]; then
    echo "✓ Yes"
else
    echo "✗ No - Run: python main.py (will create it)"
fi

# 3. Check admin_settings table
echo -n "admin_settings table: "
if sqlite3 quiz.db "SELECT name FROM sqlite_master WHERE type='table' AND name='admin_settings';" | grep -q admin_settings; then
    echo "✓ Exists"
else
    echo "✗ Missing - Run: python migrations/001_add_admin_settings.py"
fi

# 4. Check admin user
echo -n "Admin user exists: "
if sqlite3 quiz.db "SELECT COUNT(*) FROM users WHERE role='admin';" | grep -q "^[1-9]"; then
    echo "✓ Yes"
else
    echo "✗ No - Create admin user"
fi

# 5. Check API endpoint
echo -n "API responding: "
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Yes"
else
    echo "✗ No - Server may not be running"
fi

echo ""
echo "=== Setup Check Complete ==="
```

Run it:
```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

---

## Expected Test Results After Fixes

After running all fixes, you should see:

```
================================================================================
TEST SUMMARY
================================================================================
Total Tests:   50
Passed:        48-50
Failed:        0-2
Skipped:       0

Pass Rate: 96-100%

RECOMMENDATIONS:
✓ All tests passed! System is ready for deployment
```

---

## Still Having Issues?

### Check Server Logs
```bash
# If using systemd
journalctl -u confquiz -f

# If running manually
python main.py  # Look for startup errors
```

### Manual API Test
```bash
# Test each endpoint manually
curl http://localhost:8000/
curl http://localhost:8000/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Debug Mode
Add to test file for more info:
```python
VERBOSE = True
```

---

**After fixing, run tests again:**
```bash
python test_all_endpoints.py
```
