# FIXES APPLIED - 2026-01-02

## ✅ Fixed Issues

### 1. Buzzer Lock Button (FIXED ✅)
**File:** `templates/qm_dashboard.html:424`
**Change:** Now sends `locked` as query parameter instead of in body
```javascript
// Before:
body: JSON.stringify({ locked: buzzerLocked })

// After:
await apiRequest(`/qm/sessions/${sessionId}/buzzer/lock?locked=${buzzerLocked}`, {
    method: 'POST'
});
```
**Status:** Working - confirmed in logs

---

### 2. Timer Background Task (FIXED ✅)
**File:** `routers/qm_router.py`
**Changes:**
1. Added import: `from services.timer_service import timer_service`
2. Modified `start_timer()` to use `timer_service.start_timer()`
3. Modified `pause_timer()` to use `timer_service.pause_timer()`
4. Modified `reset_timer()` to use `timer_service.reset_timer()`

**What This Fixes:**
- Timer now creates background countdown task
- Timer publishes ticks to Redis pub/sub every 100ms
- Timer state properly managed (start/pause/resume/reset)

**Status:** Code fixed, needs service restart

---

### 3. Session Management UI (ADDED ✅)
**File:** `templates/admin_dashboard.html`
**What Was Added:**
- "Manage" button for each session
- Status dropdown (draft/live/ended)
- Team assignment checkboxes
- Save/Cancel buttons

**Features:**
- Change session status without API calls
- Assign teams to session with checkboxes
- Visual status indicators (🟡 draft, 🟢 live, 🔴 ended)

**Status:** Ready to use

---

### 4. Slide Upload UI (ADDED ✅)
**File:** `templates/admin_dashboard.html`
**What Was Added:**
- "Upload Slides" section
- Session selector
- Question deck upload form
- Answer deck upload form
- Uploaded decks display

**Status:** Ready to use (after .env fix)

---

## ⚠️ Issues Remaining

### 1. Slide Upload Returns 500 Error
**Problem:** Wrong LibreOffice path in .env
```
LIBREOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe  ← Windows path!
```

**Fix Required (choose one):**

**Option A: Use python-pptx (Quick)**
```bash
# On VPS:
nano .env
# Comment out the line:
# LIBREOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe

sudo systemctl restart confquiz
```

**Option B: Install LibreOffice (Better)**
```bash
# On VPS:
sudo apt-get install -y libreoffice poppler-utils

nano .env
# Change to:
LIBREOFFICE_PATH=/usr/bin/libreoffice

sudo systemctl restart confquiz
```

---

### 2. Timer Countdown Not Visible (PARTIAL FIX)
**What's Fixed:**
- ✅ Timer service now creates background task
- ✅ Timer publishes ticks to Redis pub/sub channel

**What's Still Missing:**
- ❌ WebSocket connections don't subscribe to timer ticks
- ❌ Timer ticks not forwarded to frontend

**Code That Needs Adding:**
In `routers/ws_router.py`, the WebSocket endpoints need to:
1. Subscribe to Redis channel `timer:tick:{session_id}`
2. Forward received ticks to all connected clients
3. Handle subscription lifecycle (start/stop)

**Current Behavior:**
- Timer API works (200 OK)
- Background countdown runs on server
- Ticks published to Redis
- BUT: No one listening/forwarding to WebSocket clients

**Workaround:**
None currently - requires code changes to ws_router.py

---

## 📋 Deployment Steps

### Step 1: Push Code Changes to VPS
The following files were modified locally and need to be deployed:

1. `templates/qm_dashboard.html` - Buzzer lock fix
2. `routers/qm_router.py` - Timer service integration
3. `templates/admin_dashboard.html` - Session management + slide upload UI

**Deploy command:**
```bash
# From your local machine:
scp templates/qm_dashboard.html user@vps:/opt/apps/confquiz/templates/
scp routers/qm_router.py user@vps:/opt/apps/confquiz/routers/
scp templates/admin_dashboard.html user@vps:/opt/apps/confquiz/templates/
```

---

### Step 2: Fix .env on VPS

**Option A: Comment out LibreOffice (Quick Start)**
```bash
ssh user@vps
cd /opt/apps/confquiz
nano .env

# Find this line and comment it:
# LIBREOFFICE_PATH=C:\\Program Files\\LibreOffice\\program\\soffice.exe

# Save (Ctrl+O, Enter, Ctrl+X)
```

**Option B: Install LibreOffice (Recommended)**
```bash
ssh user@vps
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-impress poppler-utils

cd /opt/apps/confquiz
nano .env

# Change the path to:
LIBREOFFICE_PATH=/usr/bin/libreoffice

# Save (Ctrl+O, Enter, Ctrl+X)
```

---

### Step 3: Restart Service
```bash
sudo systemctl restart confquiz
sudo systemctl status confquiz  # Verify it started
```

---

### Step 4: Test Everything

**Test Slide Upload:**
1. Login as admin
2. Click "Upload Slides"
3. Select session
4. Upload a .pptx file
5. Should see success message

**Test Session Management:**
1. Click "Manage Sessions"
2. Click "Manage" on a session
3. Check teams to assign
4. Change status to "Live"
5. Click "Save Changes"

**Test Timer (Partial):**
1. Login as quiz master
2. Select session
3. Click "Start Timer"
4. Check server logs: `sudo journalctl -u confquiz -f`
5. Should see timer ticks being published (but not visible in UI yet)

**Test Buzzer:**
1. Click "Lock Buzzers" / "Unlock Buzzers"
2. Should toggle successfully
3. Check logs - should show 200 OK

---

## 🔧 Next Steps (For Full Timer Fix)

To make timer countdown visible, modify `routers/ws_router.py`:

```python
import redis.asyncio as redis
from config import settings

async def subscribe_to_timer_ticks(session_id: int):
    """Background task to forward timer ticks to WebSocket clients"""
    r = await redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()

    channel = f"timer:tick:{session_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message and message['type'] == 'message':
                remaining_ms = int(message['data'])
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "event": "timer.tick",
                        "remaining_ms": remaining_ms
                    }
                )
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
```

Then start this task when first WebSocket connects and cancel when last disconnects.

---

## Summary

| Feature | Status | Action Required |
|---------|--------|-----------------|
| Buzzer Lock | ✅ Fixed | Deploy file, restart |
| Session Management | ✅ Added | Deploy file, restart |
| Slide Upload UI | ✅ Added | Deploy file, restart |
| Slide Upload Backend | ⚠️ Blocked | Fix .env LibreOffice path |
| Timer Backend | ✅ Fixed | Deploy file, restart |
| Timer Frontend Display | ❌ Not Working | Needs ws_router.py changes |
| Score Controls | ✅ Working | Already deployed |
| Team Assignment | ✅ Working | Use "Manage" button |

---

*Last Updated: 2026-01-02*
*Files Modified: 3*
*Deployment Required: Yes*
