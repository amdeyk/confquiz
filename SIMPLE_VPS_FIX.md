# Simple VPS Fix - Missing Admin Settings Data

## Problem Identified

Your server logs show:
- ✅ `admin_settings` table EXISTS
- ✅ Migration was run
- ❌ But the default settings data is MISSING

This is why you're getting:
```
GET /api/admin/settings/display_mode HTTP/1.1" 404 Not Found
```

## Solution (2 Simple Steps)

### Step 1: Check Current Data

SSH into your VPS and run:

```bash
cd /opt/apps/confquiz
source venv/bin/activate

# Check if settings exist
sqlite3 quiz.db "SELECT * FROM admin_settings;"
```

**Expected Output:**
- If EMPTY: You'll see nothing (need to insert data)
- If HAS DATA: You'll see rows with settings

---

### Step 2: Insert Missing Settings

Run the fix script:

```bash
# Upload fix_admin_settings_data.py to your VPS first
# Then run:
python fix_admin_settings_data.py
```

**Expected Output:**
```
============================================================
Fixing Admin Settings Data
============================================================

Current admin_settings count: 0

Missing settings: display_mode, screen_share_fps, screen_share_quality

✓ Inserting: display_mode = png_slides
✓ Inserting: screen_share_fps = 10
✓ Inserting: screen_share_quality = 0.7

============================================================
✓ Successfully inserted 3 settings!
============================================================

Final admin_settings:
  - display_mode = png_slides
  - screen_share_fps = 10
  - screen_share_quality = 0.7

Done!
```

---

### Step 3: Verify API Works

Test the endpoint:

```bash
curl http://localhost:8000/api/admin/settings/display_mode \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Expected Output:**
```json
{
  "setting_key": "display_mode",
  "setting_value": "png_slides"
}
```

---

## Alternative: Manual SQL Insert

If you prefer, insert directly with SQL:

```bash
sqlite3 quiz.db << 'EOF'
INSERT OR IGNORE INTO admin_settings (setting_key, setting_value) VALUES
  ('display_mode', 'png_slides'),
  ('screen_share_fps', '10'),
  ('screen_share_quality', '0.7');
SELECT * FROM admin_settings;
EOF
```

---

## After Fix: Re-run Tests

Once settings are inserted:

```bash
python test_all_endpoints.py
```

You should see:
- ✅ Admin Settings Table test passes
- ✅ Get All Settings test passes
- ✅ Get Specific Setting test passes
- ✅ Update Settings tests pass

---

## Files to Upload to VPS

Upload these files to `/opt/apps/confquiz`:

1. **fix_admin_settings_data.py** - The fix script (easiest method)

Or just use manual SQL insert (no upload needed).

---

## Quick Summary

**Problem**: Migration created table but didn't insert default data
**Solution**: Run `python fix_admin_settings_data.py` or manual SQL insert
**Result**: All settings endpoints will work, tests will pass

---

**Next**: Once this is fixed, all your admin settings features will work correctly!
