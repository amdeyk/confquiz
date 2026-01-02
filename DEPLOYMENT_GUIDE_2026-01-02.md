# Deployment Guide - 2026-01-02

## Overview
This deployment includes:
1. **Critical Fixes**: Slide navigation and buzzer broadcasting
2. **Phase 1**: Database foundation for screen sharing feature

---

## Part 1: Critical Fixes (Deploy First)

### Files to Deploy

1. **`routers/qm_router.py`** - Slide navigation fixes
2. **`routers/ws_router.py`** - Buzzer broadcasting fixes
3. **`database.py`** - Added get_async_session_maker function

### What's Fixed

#### Fix 1: Slide Navigation & Display
- ✅ Auto-starts quiz with first slide when clicking "Next Slide"
- ✅ Broadcasts slide changes to display screen with correct event name
- ✅ Includes full slide object with png_path in broadcast
- ✅ All navigation endpoints now broadcast properly (next/prev/reveal/jump)

#### Fix 2: Buzzer System
- ✅ Team buzzer presses now appear on display
- ✅ Respects buzzer lock/unlock state
- ✅ Prevents duplicate buzzes from same team
- ✅ Broadcasts to all connected clients (QM, display, teams)

### Deployment Commands

```bash
# From your Windows machine (D:\quiz directory):
scp routers/qm_router.py user@vps:/opt/apps/confquiz/routers/
scp routers/ws_router.py user@vps:/opt/apps/confquiz/routers/
scp database.py user@vps:/opt/apps/confquiz/

# SSH into VPS and restart service
ssh user@vps
sudo systemctl restart confquiz
sudo systemctl status confquiz

# Check logs for startup success
sudo journalctl -u confquiz -f
```

### Testing Critical Fixes

**Test Slide Navigation:**
1. Login as quiz master
2. Select a session
3. Click "Next Slide" - Should start quiz with first slide
4. **Open display page in another tab/window**
5. Click "Next Slide" again - Display should update immediately
6. Try "Previous Slide" and "Reveal Answer" - All should update display

**Test Buzzer:**
1. Team opens `/team/interface` and logs in
2. QM clicks "Unlock Buzzers"
3. Team clicks "BUZZ"
4. **Check display screen** - Should show team buzzed in
5. **Check QM screen** - Should show buzzer notification
6. QM clicks "Lock Buzzers"
7. Team clicks "BUZZ" again - Should be rejected

---

## Part 2: Phase 1 Database Changes (Deploy After Testing Fixes)

### Files to Deploy

1. **`models.py`** - Added AdminSettings model, updated User role comment
2. **`migrations/001_add_admin_settings.py`** - Migration script for default settings

### What's Added

#### Database Changes
- ✅ New `AdminSettings` model with settings for screen sharing
- ✅ Updated User model to support 'presenter' role (preparation for Phase 2)

#### Default Settings
- `display_mode` = `"png_slides"` (current mode)
- `screen_share_fps` = `"10"` (future screen share frame rate)
- `screen_share_quality` = `"0.7"` (future screen share quality)

### Deployment Commands

```bash
# From your Windows machine:
scp models.py user@vps:/opt/apps/confquiz/
scp -r migrations user@vps:/opt/apps/confquiz/

# SSH into VPS
ssh user@vps
cd /opt/apps/confquiz

# Run migration to create admin_settings table and insert defaults
python migrations/001_add_admin_settings.py

# Expected output:
# Running migration: 001_add_admin_settings
# Creating tables...
# Inserting default admin settings...
# Inserted 3 default admin settings:
#   - display_mode = png_slides
#   - screen_share_fps = 10
#   - screen_share_quality = 0.7
# Migration completed successfully!

# Restart service to load new model
sudo systemctl restart confquiz
sudo systemctl status confquiz
```

### Verifying Phase 1 Deployment

```bash
# SSH into VPS
ssh user@vps
cd /opt/apps/confquiz

# Check if admin_settings table exists
sqlite3 quiz.db "SELECT * FROM admin_settings;"

# Expected output:
# 1|display_mode|png_slides|2026-01-02 XX:XX:XX
# 2|screen_share_fps|10|2026-01-02 XX:XX:XX
# 3|screen_share_quality|0.7|2026-01-02 XX:XX:XX
```

---

## Complete Deployment Sequence

### Step 1: Deploy Critical Fixes
```bash
# Deploy files
scp routers/qm_router.py user@vps:/opt/apps/confquiz/routers/
scp routers/ws_router.py user@vps:/opt/apps/confquiz/routers/
scp database.py user@vps:/opt/apps/confquiz/

# Restart service
ssh user@vps
sudo systemctl restart confquiz
```

### Step 2: Test Critical Fixes
- Test slide navigation on display
- Test buzzer on display
- Verify timer still works

### Step 3: Deploy Phase 1 (Database)
```bash
# Deploy files
scp models.py user@vps:/opt/apps/confquiz/
scp -r migrations user@vps:/opt/apps/confquiz/

# Run migration
ssh user@vps
cd /opt/apps/confquiz
python migrations/001_add_admin_settings.py

# Restart service
sudo systemctl restart confquiz
```

### Step 4: Verify Phase 1
```bash
# Check database
sqlite3 quiz.db "SELECT * FROM admin_settings;"
```

---

## Status Summary

| Component | Status | Ready to Deploy |
|-----------|--------|-----------------|
| Slide Navigation Fix | ✅ Complete | Yes |
| Buzzer Broadcasting Fix | ✅ Complete | Yes |
| AdminSettings Model | ✅ Complete | Yes |
| Migration Script | ✅ Complete | Yes |
| get_async_session_maker | ✅ Complete | Yes |

**All components tested locally and ready for deployment.**

---

## Next Steps After Deployment

Once both parts are successfully deployed and tested:

1. **Verify all fixes work in production**:
   - Slides update on display
   - Buzzer appears on display
   - Timer still works

2. **Begin Phase 2** (Authentication & Authorization):
   - Add presenter auth decorator to auth.py
   - Add presenter creation endpoint to admin_router.py
   - Add settings CRUD endpoints to admin_router.py

---

## Rollback Plan

If issues occur after deployment:

### Rollback Critical Fixes:
```bash
# Restore from git (assumes previous commit was working)
ssh user@vps
cd /opt/apps/confquiz
git checkout HEAD~1 routers/qm_router.py routers/ws_router.py database.py
sudo systemctl restart confquiz
```

### Rollback Phase 1:
```bash
# Remove admin_settings table
sqlite3 quiz.db "DROP TABLE IF EXISTS admin_settings;"

# Restore old models.py
git checkout HEAD~1 models.py
sudo systemctl restart confquiz
```

---

## Questions or Issues?

If deployment fails, check:
1. Service logs: `sudo journalctl -u confquiz -f`
2. Database file permissions: `ls -la quiz.db`
3. Python environment activated
4. All dependencies installed

---

*Created: 2026-01-02*
*Ready for Production Deployment*
