# Complete User Guide - Screen Sharing & Slides

## CRITICAL: Fix Admin Settings FIRST ⚠️

Before anything else, run this on your VPS:

```bash
cd /opt/apps/confquiz
sqlite3 quiz.db << 'EOF'
INSERT INTO admin_settings (setting_key, setting_value) VALUES
  ('display_mode', 'png_slides'),
  ('screen_share_fps', '10'),
  ('screen_share_quality', '0.7');
SELECT '✓ Inserted:', setting_key, '=', setting_value FROM admin_settings;
EOF
```

**This will fix the "Setting not found" error immediately.**

---

## Part 1: How to Upload Slides (PNG/Traditional Method)

### Step 1: Login to Admin Dashboard

Go to: `http://your-vps-ip:8000/admin/login`
- Username: `admin`
- Password: `admin123` (or your admin password)

### Step 2: Create a Session (if you haven't)

1. Click **"Create Session"** button
2. Enter session name (e.g., "Quiz Night 1")
3. Click Create

### Step 3: Upload PowerPoint Files

1. Click **"Upload Slides"** in the quick actions
2. **Select your session** from the dropdown
3. Upload your PowerPoint files:
   - **Question Deck**: Upload your questions .pptx file
   - **Answer Deck**: Upload your answers .pptx file (optional)

**What happens:**
- Server converts .pptx to PNG images automatically
- Creates thumbnails
- Stores in `media/slides/` folder

### Step 4: Verify Upload

After upload, you should see:
```
✓ Question deck uploaded successfully! 10 slides converted.
```

**Troubleshooting Slide Upload:**

If upload fails, check:

```bash
# On VPS - Check permissions
ls -la /opt/apps/confquiz/media/
# Should show: drwxr-xr-x

# Check if LibreOffice is installed (needed for conversion)
which soffice
# If not found, install:
sudo apt install libreoffice-core libreoffice-impress
```

**Check conversion logs:**
```bash
tail -f /opt/apps/confquiz/logs/app.log
# Upload a file and watch for conversion errors
```

---

## Part 2: How to Use Screen Sharing (WebRTC Method)

This allows you to share your actual PowerPoint presentation directly from your laptop.

### A. Setup (One-time)

#### 1. Create a Presenter User

**In Admin Dashboard:**
1. Scroll down to **"Create Presenter User"** section
2. Fill in:
   - Username: `presenter` (or any name)
   - Password: `presenter123` (or any password)
3. Click **"Create Presenter"**

#### 2. Enable Screen Share Mode

**In Admin Dashboard:**
1. Click **"Display Settings"** button
2. Change **Display Mode** to: `Screen Share (WebRTC)`
3. Set Frame Rate: `10 FPS` (recommended)
4. Click **"Save Display Settings"**

**Now this will work because we fixed the admin_settings data!**

---

### B. Using Screen Sharing

#### 1. Open PowerPoint on Your Laptop

- Open your .pptx file in PowerPoint
- Go to Slideshow mode (press F5)

#### 2. Login as Presenter

Open a new browser tab:
```
http://your-vps-ip:8000/presenter/login
```

Login with:
- Username: `presenter`
- Password: `presenter123`

#### 3. Start Sharing

On the Presenter Dashboard:

1. **Select Session** from dropdown (e.g., "Quiz Night 1")
2. Click **"Start Screen Share"**
3. Browser will ask: "Share your screen?"
4. Select your **PowerPoint window** (not entire screen)
5. Click **"Share"**

#### 4. Display Screens Receive Feed

All display screens connected to the session will now show:
- ✅ Your live PowerPoint presentation
- ✅ Updates when you change slides
- ✅ Animations and transitions

#### 5. Stop Sharing

When done:
- Click **"Stop Sharing"** in presenter dashboard
- Or close the PowerPoint window
- Display screens automatically revert to PNG slides

---

## Part 3: Which Method Should I Use?

### Use PNG Slides (Upload) When:
- ✅ You want automatic slide navigation
- ✅ You want timer control from quiz master dashboard
- ✅ Network is unreliable
- ✅ You don't need animations

### Use Screen Share (WebRTC) When:
- ✅ You have complex PowerPoint animations
- ✅ You want to control slides manually
- ✅ You have embedded videos in slides
- ✅ You want to use PowerPoint's native features

---

## Part 4: Complete Workflow Example

### Scenario: Quiz Night with Screen Sharing

**Preparation (Admin - 30 mins before):**

1. Login to admin dashboard
2. Create session: "Friday Quiz Night"
3. Create teams (Team A, Team B, etc.)
4. Assign teams to session
5. Upload backup PNG slides (in case screen share fails)
6. Enable "Screen Share" mode in Display Settings

**5 Minutes Before Quiz (Presenter):**

1. Open PowerPoint on laptop
2. Login to presenter dashboard: `http://vps:8000/presenter/login`
3. Select session: "Friday Quiz Night"
4. Click "Start Screen Share"
5. Select PowerPoint window
6. Open display screens: `http://vps:8000/display`

**During Quiz (Quiz Master):**

1. Login to quiz master dashboard: `http://vps:8000/qm/dashboard`
2. Start session (status → Live)
3. Unlock buzzers when needed
4. Adjust scores
5. Monitor timer

**If Screen Share Fails:**

1. Admin changes Display Settings → "PNG Slides"
2. Display screens automatically switch to uploaded slides
3. Quiz master uses slide navigation buttons
4. Quiz continues without interruption

---

## Part 5: Troubleshooting

### "Failed to save settings: Setting not found"
**Fix:** Run the SQL command at the top of this guide

### "No presenter login page"
**Check:**
```bash
curl http://localhost:8000/presenter/login
# Should return HTML, not 404
```

If 404, your code may not be deployed. Check `main.py` has:
```python
@app.get("/presenter/login")
```

### Slides not uploading
**Check:**
```bash
# LibreOffice installed?
soffice --version

# Permissions?
ls -la media/

# Logs?
tail -f logs/app.log
```

### Screen share not connecting
**Check:**
- Browser is Chrome/Firefox/Edge (Safari has issues)
- HTTPS or localhost (WebRTC requires secure context)
- No firewall blocking WebSocket connections

---

## Part 6: URLs Reference

| Purpose | URL | Who Uses It |
|---------|-----|-------------|
| Admin Dashboard | `http://vps:8000/admin/login` | Admin |
| Quiz Master Dashboard | `http://vps:8000/qm/login` | Quiz Master |
| **Presenter Login** | `http://vps:8000/presenter/login` | **Presenter** |
| Display Screen | `http://vps:8000/display` | Display (auto-loads) |
| Team Buzzer | `http://vps:8000/team/YOUR-TEAM-CODE` | Teams |

---

## Part 7: Quick Checklist

**Before Your Quiz:**

- [ ] Run SQL fix for admin_settings (top of this guide)
- [ ] Create session in admin dashboard
- [ ] Upload PowerPoint files (PNG backup)
- [ ] Create presenter user
- [ ] Test screen sharing on laptop
- [ ] Open display screens
- [ ] Test buzzer system with teams

**You're ready!** 🎉

---

## Need Help?

**Check server logs:**
```bash
tail -f /opt/apps/confquiz/logs/app.log
```

**Test API endpoints:**
```bash
# Check admin settings
curl http://localhost:8000/api/admin/settings

# Should return:
# {"display_mode": "png_slides", ...}
```

**Restart server if needed:**
```bash
pkill -f "python main.py"
python main.py &
```

---

**Last Updated:** 2026-01-03
