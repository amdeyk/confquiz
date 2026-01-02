# Manual Deployment Guide - Screen Sharing Feature

## Why Deploy?

Your VPS currently has the **old version** of files without:
- ❌ Presenter creation form in admin dashboard
- ❌ Display settings UI
- ❌ Presenter login/dashboard pages
- ❌ WebRTC screen sharing support

After deployment you'll have:
- ✅ Full screen sharing feature
- ✅ Presenter dashboard
- ✅ Complete admin UI with all controls

---

## Quick Start (For Now)

**To use screen sharing RIGHT NOW without deploying:**

Run this on your VPS to create presenter user:

```bash
cd /opt/apps/confquiz
source venv/bin/activate

python << 'EOF'
import asyncio
from database import AsyncSessionLocal
from models import User
from auth import get_password_hash
from sqlalchemy import select

async def create_presenter():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == 'presenter'))
        if result.scalar_one_or_none():
            print('Presenter user already exists')
            return

        presenter = User(
            username='presenter',
            password_hash=get_password_hash('presenter123'),
            role='presenter'
        )
        db.add(presenter)
        await db.commit()
        print('✅ Presenter created! Username: presenter, Password: presenter123')

asyncio.run(create_presenter())
EOF
```

**Then:**
1. Fix admin_settings: `python fix_admin_settings_data.py`
2. Login at: `https://aisquiz.qubixvirtual.in/presenter/login`

---

## Full Deployment (Recommended)

### Method 1: Using SCP (Linux/Mac)

```bash
# From your local machine where you have the updated files
cd D:\quiz  # or wherever your quiz folder is

# Run the deployment script
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh singapore-datacenter.serverpoint.com
```

---

### Method 2: Using WinSCP (Windows - EASIEST)

#### Step 1: Open WinSCP

1. Download WinSCP: https://winscp.net/
2. New Site:
   - Host: `singapore-datacenter.serverpoint.com`
   - User: `root`
   - Password: (your VPS password)
3. Click Login

#### Step 2: Navigate to App Directory

In WinSCP, go to: `/opt/apps/confquiz`

#### Step 3: Upload These Files

**Upload from your local `D:\quiz` folder:**

| Local File | VPS Destination |
|------------|-----------------|
| `templates\admin_dashboard.html` | `/opt/apps/confquiz/templates/` |
| `templates\presenter_login.html` | `/opt/apps/confquiz/templates/` |
| `templates\presenter_dashboard.html` | `/opt/apps/confquiz/templates/` |
| `templates\display.html` | `/opt/apps/confquiz/templates/` |
| `routers\admin_router.py` | `/opt/apps/confquiz/routers/` |
| `routers\ws_router.py` | `/opt/apps/confquiz/routers/` |
| `main.py` | `/opt/apps/confquiz/` |
| `auth.py` | `/opt/apps/confquiz/` |
| `schemas.py` | `/opt/apps/confquiz/` |
| `models.py` | `/opt/apps/confquiz/` |
| `database.py` | `/opt/apps/confquiz/` |
| `migrations\001_add_admin_settings.py` | `/opt/apps/confquiz/migrations/` |
| `fix_admin_settings_data.py` | `/opt/apps/confquiz/` |

**Just drag and drop each file!**

#### Step 4: SSH to VPS and Restart

In WinSCP, press **Ctrl+P** to open terminal, then run:

```bash
cd /opt/apps/confquiz
source venv/bin/activate

# Run migration and fix
python migrations/001_add_admin_settings.py
python fix_admin_settings_data.py

# Restart server
pkill -f "python main.py"
sleep 2
nohup python main.py > logs/app.log 2>&1 &
sleep 3

# Verify
pgrep -f "python main.py" && echo "✅ Server running" || echo "❌ Server not running"
```

---

### Method 3: Using FileZilla (Windows Alternative)

1. Download FileZilla: https://filezilla-project.org/
2. Connect:
   - Host: `sftp://singapore-datacenter.serverpoint.com`
   - Username: `root`
   - Password: (your password)
   - Port: 22
3. Navigate to `/opt/apps/confquiz`
4. Upload same files as WinSCP method
5. Use PuTTY to SSH and run restart commands

---

## Files You're Deploying

### Templates (4 files)
- `admin_dashboard.html` - **UPDATED** with presenter form + display settings
- `presenter_login.html` - **NEW** login page for presenters
- `presenter_dashboard.html` - **NEW** screen sharing interface
- `display.html` - **UPDATED** with WebRTC receiver

### Python Backend (7 files)
- `main.py` - **UPDATED** with presenter routes
- `auth.py` - **UPDATED** with presenter auth
- `schemas.py` - **UPDATED** with admin settings schemas
- `models.py` - **UPDATED** with AdminSettings model
- `database.py` - **UPDATED** with session maker
- `routers/admin_router.py` - **UPDATED** with presenter + settings endpoints
- `routers/ws_router.py` - **UPDATED** with WebRTC signaling

### Database & Scripts (3 files)
- `migrations/001_add_admin_settings.py` - Creates admin_settings table
- `fix_admin_settings_data.py` - Inserts default data
- `quick_fix.sh` - Helper script

---

## After Deployment

### 1. Verify Admin Dashboard

Go to: `https://aisquiz.qubixvirtual.in/admin/dashboard`

**You should now see:**
- ✅ "Display Settings" button in quick actions
- ✅ "Create Presenter User" section below "Create Quiz Master"

### 2. Create Presenter User

In admin dashboard:
1. Scroll to "Create Presenter User"
2. Username: `presenter`
3. Password: `presenter123`
4. Click "Create Presenter"

### 3. Configure Display Settings

1. Click "Display Settings" button
2. Select "Screen Share (WebRTC)"
3. FPS: 10
4. Click "Save Display Settings"

**This will work now because admin_settings data is fixed!**

### 4. Test Presenter Login

Go to: `https://aisquiz.qubixvirtual.in/presenter/login`

**You should see:**
- Login form with username/password
- After login → Presenter Dashboard
- Options to select session and start screen sharing

---

## Troubleshooting Deployment

### Server won't restart after upload

```bash
# Check for syntax errors
cd /opt/apps/confquiz
python -m py_compile main.py

# Check logs
tail -f logs/app.log
```

### Files uploaded but no changes visible

```bash
# Clear browser cache or use Ctrl+Shift+R
# Verify file timestamp
ls -la templates/admin_dashboard.html

# Should show recent modification time
```

### Import errors after deployment

```bash
# Ensure all dependencies installed
cd /opt/apps/confquiz
source venv/bin/activate
pip install -r requirements.txt
```

---

## Rollback (If Something Breaks)

WinSCP automatically creates backups. To rollback:

```bash
cd /opt/apps/confquiz
ls -la backups/

# Restore from backup (use timestamp folder)
cp backups/20260103_*/templates/*.html templates/
cp backups/20260103_*/routers/*.py routers/
cp backups/20260103_*/*.py .

# Restart
pkill -f "python main.py"
python main.py &
```

---

## Deployment Checklist

Before deployment:
- [ ] Backup current VPS files
- [ ] Verify local files are complete
- [ ] Note current server uptime

During deployment:
- [ ] Upload all 14 files to correct locations
- [ ] Run migration script
- [ ] Run fix_admin_settings_data.py
- [ ] Restart server

After deployment:
- [ ] Check server is running (`pgrep -f "python main.py"`)
- [ ] Test admin dashboard loads
- [ ] Verify presenter login page exists
- [ ] Create test presenter user
- [ ] Test screen sharing

---

## Summary

**Fastest Option:** Use WinSCP (Method 2) - just drag and drop 14 files!

**Current Workaround:** Use the Python script at the top to create presenter user now

**Full Solution:** Deploy all files to get complete UI and features

---

**Estimated Time:**
- WinSCP deployment: 10 minutes
- Testing: 5 minutes
- **Total: 15 minutes**

Let me know when you've deployed and I'll help test everything!
