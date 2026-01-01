# QUIZ MASTER WORKFLOW GUIDE

**Date:** 2026-01-01
**Status:** ✅ Critical fixes applied

---

## RECENT FIXES APPLIED

### 1. ✅ Buzzer Lock Button Fixed
**Problem:** Buzzer lock/unlock button was returning 422 validation error
**Root Cause:** Frontend was sending `locked` parameter in JSON body, but backend expected it as a query parameter
**Fix Applied:** Changed line 424 in `qm_dashboard.html`:
```javascript
// Before (incorrect):
body: JSON.stringify({ locked: buzzerLocked })

// After (correct):
await apiRequest(`/qm/sessions/${sessionId}/buzzer/lock?locked=${buzzerLocked}`, {
    method: 'POST'
});
```
**Status:** ✅ Fixed - buzzer lock now works correctly

---

### 2. ✅ Slide Upload UI Created
**Problem:** No UI existed for uploading PowerPoint slides
**What Was Added:**
- New "Upload Slides" section in Admin Dashboard
- Session selector dropdown
- Separate upload forms for Question and Answer decks
- Display of uploaded decks with slide count
- Full integration with backend `/api/admin/sessions/{id}/decks` endpoint

**How to Use:**
1. Login as admin
2. Click "Upload Slides" button
3. Select a session from dropdown
4. Upload Question deck (.ppt or .pptx file)
5. Upload Answer deck (.ppt or .pptx file)
6. System automatically converts PowerPoint to PNG images

**Files Modified:**
- `templates/admin_dashboard.html` - Added slide upload UI
- Lines 98-138: HTML structure
- Lines 191-243: CSS styling
- Lines 403-524: JavaScript upload logic

---

## UNDERSTANDING QUIZ CONTROLS

### What Does Each Button Do?

#### **TIMER CONTROLS**
- **Start Timer** - Starts countdown from specified duration (in seconds)
  - The timer DOES work - it's running on the server
  - You won't see it count down on QM dashboard (only shows on display screen)
  - To verify it's working: Open `/display` page in another browser tab
- **Pause Timer** - Pauses the countdown
- **Reset Timer** - Stops timer and resets to 00:00

**Why you can't see the timer on QM dashboard:**
The QM dashboard doesn't have a live timer display - it only has control buttons. The actual countdown appears on the **Display Screen** (`/display` page) which is meant to be shown to the audience.

#### **BUZZER CONTROLS**
- **Lock/Unlock Buzzers** - Controls whether teams can press their buzzers
  - 🔒 **LOCKED** (red button) = Teams CANNOT buzz in
  - 🔓 **UNLOCKED** (green button) = Teams CAN buzz in
  - When locked, the buzzer queue is also cleared
- **Clear Queue** - Removes all teams from buzzer queue (also locks buzzers)

**How Buzzer System Works:**
1. Quiz master unlocks buzzers
2. Teams press their buzz button on team interface
3. System records EXACT timestamp (milliseconds)
4. Buzzer queue shows teams in order from fastest to slowest
5. Quiz master can see who buzzed first
6. After answering, quiz master locks buzzers again

#### **SLIDE CONTROLS**
- **Previous Slide** - Go to previous slide
- **Next Slide** - Advance to next slide
- **Reveal Answer** - Show answer for current question slide

**Why slide controls return 400 error:**
❌ You haven't uploaded any slides yet! The quiz master can't navigate slides that don't exist.

---

## PROPER QUIZ SETUP WORKFLOW

### ⚠️ IMPORTANT: You MUST Complete Setup BEFORE Using QM Controls

Here's the correct sequence to set up a quiz:

### STEP 1: Create Teams (Admin)
1. Login as admin
2. Click "Manage Teams"
3. Create all teams participating in quiz
4. Assign seat order (optional)

✅ You've completed this step

---

### STEP 2: Create Session (Admin or QM)
1. Click "Manage Sessions"
2. Create new session with name and banner text
3. Session created in "draft" status

✅ You've completed this step

---

### STEP 3: Upload Slides (Admin) ⚠️ **YOU SKIPPED THIS**
1. Click "Upload Slides" button
2. Select the session from dropdown
3. Upload **Question Deck** (PowerPoint file with all questions)
4. Upload **Answer Deck** (PowerPoint file with all answers)
5. System converts PPT to images automatically
6. Verify slides appear in "Uploaded Decks" section

❌ **This is why your slide controls don't work!**

**Supported Formats:**
- .ppt (PowerPoint 97-2003)
- .pptx (PowerPoint 2007+)

**Upload Time:**
- Expect 30-60 seconds for a 20-slide deck
- System converts each slide to PNG image
- Creates thumbnail versions for preview

---

### STEP 4: Assign Teams to Session (Admin) ⚠️ **YOU SKIPPED THIS**
**Currently:** No UI exists for this - must use API directly

**API Endpoint:**
```http
POST /api/admin/sessions/{session_id}/teams
Content-Type: application/json

{
  "team_ids": [1, 2, 3, 4]
}
```

**Using curl:**
```bash
curl -X POST "http://your-server/api/admin/sessions/1/teams" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4]'
```

**What this does:**
- Creates TeamSession records linking teams to session
- Initializes score entries for each team (starting at 0)
- Allows teams to login and join the session

❌ **Without this, teams can't participate!**

---

### STEP 5: Change Session Status to "Live" (Admin) ⚠️ **YOU SKIPPED THIS**
**Currently:** No UI exists for this - must use API directly

**API Endpoint:**
```http
PATCH /api/admin/sessions/{session_id}
Content-Type: application/json

{
  "status": "live"
}
```

**Using curl:**
```bash
curl -X PATCH "http://your-server/api/admin/sessions/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "live"}'
```

**Session Status Values:**
- `draft` - Session being prepared (default)
- `live` - Quiz is active
- `ended` - Quiz finished

❌ **Without this, quiz master might not see the session!**

---

### STEP 6: Start Quiz (Quiz Master)
1. Login as quiz master
2. Select session from dropdown
3. Now all controls will work:
   - ✅ Slide navigation (because slides are uploaded)
   - ✅ Timer controls (will show on display screen)
   - ✅ Buzzer controls (teams can buzz in)
   - ✅ Score controls (teams assigned to session)

---

## CURRENT STATUS OF YOUR QUIZ

Based on server logs, here's what you've done:

| Step | Status | Issue |
|------|--------|-------|
| 1. Create Teams | ✅ Done | Teams exist in database |
| 2. Create Session | ✅ Done | Session ID 1 exists |
| 3. Upload Slides | ❌ **NOT DONE** | **No slides uploaded** |
| 4. Assign Teams to Session | ❌ **NOT DONE** | **Teams not linked to session** |
| 5. Set Status to Live | ❌ Unclear | Status might still be "draft" |
| 6. Quiz Master Controls | ⚠️ **Partial** | Controls exist but have no data to work with |

---

## WHY CONTROLS AREN'T WORKING

### Slide Controls (Next/Prev/Reveal)
```
❌ Error: 400 Bad Request
🔍 Reason: No slides uploaded to session
✅ Fix: Upload PowerPoint files using new Slide Upload UI
```

### Timer Controls
```
✅ Timer IS working! (Server logs show 200 OK)
🔍 Reason: You think it's not working because:
   - QM dashboard doesn't display timer countdown
   - You need to open Display Screen (/display) to see timer
✅ Fix: Open display page in another browser window
```

### Buzzer Lock
```
✅ Fixed! Was 422 error, now works correctly
🔍 Reason: Parameter passing mismatch (now fixed)
✅ Fix: Applied - buzzer lock/unlock now functional
```

### Score Controls
```
✅ UI exists and works
⚠️ Warning: Won't show teams if they aren't assigned to session
✅ Fix: Assign teams to session using API (see Step 4 above)
```

---

## QUICK START CHECKLIST

To get your quiz running RIGHT NOW:

- [ ] **1. Upload Slides**
  - Go to Admin Dashboard
  - Click "Upload Slides"
  - Select your session
  - Upload Question deck PPT
  - Upload Answer deck PPT
  - Wait for conversion to complete

- [ ] **2. Assign Teams to Session** (via API)
  ```bash
  # Get your auth token first by logging in
  # Then assign teams 1, 2, 3, 4 to session 1:
  curl -X POST "http://localhost:8000/api/admin/sessions/1/teams" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '[1, 2, 3, 4]'
  ```

- [ ] **3. Set Session to Live** (via API)
  ```bash
  curl -X PATCH "http://localhost:8000/api/admin/sessions/1" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"status": "live"}'
  ```

- [ ] **4. Open Display Screen**
  - Open browser to `/display`
  - Select your session
  - Leave this open for audience to see

- [ ] **5. Teams Login**
  - Each team goes to `/team/login`
  - Enters their team code
  - Enters a nickname
  - Now they can buzz in

- [ ] **6. Quiz Master Controls Session**
  - Login to `/qm/dashboard`
  - Select session
  - Use slide controls to navigate
  - Use timer for timed questions
  - Lock/unlock buzzers
  - Adjust scores using new score controls

---

## MISSING UI FEATURES

These features exist in the backend but have NO frontend interface yet:

### 1. Team Assignment to Session
**Endpoint exists:** `POST /api/admin/sessions/{id}/teams`
**UI exists:** ❌ NO
**Workaround:** Use curl/Postman to call API directly

### 2. Session Status Management
**Endpoint exists:** `PATCH /api/admin/sessions/{id}`
**UI exists:** ❌ NO
**Workaround:** Use curl/Postman to call API directly

### 3. Round Management
**Endpoint exists:** `POST /api/admin/sessions/{id}/rounds`
**UI exists:** ❌ NO
**Impact:** Not critical for basic quiz operation

### 4. Slide Mapping (Question ↔ Answer)
**Endpoint exists:** `POST /api/admin/sessions/{id}/mappings`
**UI exists:** ❌ NO
**Impact:** Optional - improves reveal answer functionality

---

## TESTING YOUR SETUP

### Verify Slides Uploaded:
```bash
curl -X GET "http://localhost:8000/api/admin/sessions/1/decks" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** List of decks with slide counts

### Verify Teams Assigned:
```bash
curl -X GET "http://localhost:8000/api/display/sessions/1/snapshot"
```
**Expected:** JSON with teams and their scores

### Verify Session Status:
```bash
curl -X GET "http://localhost:8000/api/admin/sessions/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Expected:** `"status": "live"`

---

## COMMON ISSUES

### "No teams appear in score controls"
**Cause:** Teams not assigned to session
**Fix:** Use API to assign teams (see Step 4)

### "Slide controls return 400 error"
**Cause:** No slides uploaded
**Fix:** Upload slides using new UI (see Step 3)

### "Timer doesn't seem to work"
**Cause:** Timer IS working, you're just not seeing it
**Fix:** Open `/display` page to see timer countdown

### "Buzzer lock returns 422 error"
**Cause:** Parameter passing issue
**Status:** ✅ FIXED in this update

---

## NEXT STEPS - RECOMMENDED IMPROVEMENTS

To complete the admin UI and make the system fully self-service:

1. **Add Team Assignment UI** - Checkboxes to assign teams to session
2. **Add Session Status Dropdown** - Change draft → live → ended
3. **Add Round Management UI** - Create rounds with scoring presets
4. **Add Edit Team UI** - Modify team name/code/order
5. **Add Delete Team UI** - Remove teams no longer needed

---

*Last Updated: 2026-01-01*
*All critical bugs fixed ✅*
*Slide upload UI added ✅*
*Ready for quiz operation with API setup ✅*
