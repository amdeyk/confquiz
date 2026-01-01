# ADMIN DASHBOARD - COMPLETE GUIDE

**Date:** 2026-01-01
**Status:** ✅ All critical features now have UI

---

## ✅ NEW FEATURES ADDED

### 1. Session Management UI
- Change session status (draft → live → ended)
- Assign teams to session with checkboxes
- All done through admin dashboard - NO MORE API CALLS NEEDED!

### 2. Slide Upload UI
- Upload PowerPoint question and answer decks
- Automatic conversion to PNG images
- View uploaded decks and slide counts

---

## COMPLETE ADMIN WORKFLOW

### STEP 1: Create Teams

1. Login as admin
2. Click **"Manage Teams"** button
3. Click **"+ Add New Team"**
4. Fill in:
   - Team Name (e.g., "Alpha Team")
   - Team Code (e.g., "TEAM01" - must be unique, auto-uppercase)
   - Seat Order (optional, for display ordering)
5. Click **"Create Team"**
6. Repeat for all teams

**Result:** Teams appear in the teams list with their codes

---

### STEP 2: Create Session

1. Click **"Manage Sessions"** button
2. Click **"+ Create New Session"**
3. Fill in:
   - Session Name (e.g., "AISMOC 2026 Quiz Round 1")
   - Banner Text (appears on display screen, e.g., "AISMOC 2026 QUIZ")
4. Click **"Create Session"**

**Result:** Session created with status "draft" (yellow 🟡)

---

### STEP 3: Manage Session (NEW!)

1. In the sessions list, find your session
2. Click **"Manage"** button (next to "View")
3. A panel opens showing:

#### **Session Status Dropdown:**
- 🟡 **Draft** (Preparing) - Session is being set up
- 🟢 **Live** (Active) - Quiz is running, teams can join
- 🔴 **Ended** (Finished) - Quiz completed

Select the status you want.

#### **Team Assignment Checkboxes:**
You'll see a list of all your teams with checkboxes:
```
☑ Alpha Team (TEAM01)
☑ Beta Team (TEAM02)
☑ Gamma Team (TEAM03)
☐ Delta Team (TEAM04)
```

- **Check** the teams that should participate in this session
- **Uncheck** teams that won't participate
- Already assigned teams are pre-checked

4. Click **"Save Changes"**

**Result:**
- Session status updated (color badge changes)
- Teams assigned to session (can now login and participate)
- Score entries created for each team (starting at 0)

---

### STEP 4: Upload Slides (NEW!)

1. Click **"Upload Slides"** button
2. Select your session from the dropdown
3. Upload forms appear for:

#### **Question Deck:**
- Click "Choose File"
- Select your .ppt or .pptx file with questions
- Click **"Upload Question Deck"**
- Wait 30-60 seconds for conversion
- Success message shows: "Question deck uploaded! X slides converted"

#### **Answer Deck:**
- Click "Choose File"
- Select your .ppt or .pptx file with answers
- Click **"Upload Answer Deck"**
- Wait for conversion
- Success message shows: "Answer deck uploaded! X slides converted"

**Result:**
- Uploaded decks appear in "Uploaded Decks" section
- Shows deck type, filename, and slide count
- Slides are ready for quiz master to use

---

### STEP 5: Create Quiz Master (If Needed)

1. Click **"Create Quiz Master"** button
2. Fill in:
   - Username (e.g., "quizmaster1")
   - Password (secure password)
3. Click **"Create Quiz Master"**

**Result:** Quiz master can now login at `/qm/login`

---

## HOW TO USE THE MANAGE SESSION PANEL

### Typical Workflow:

#### **Before the Quiz:**
```
1. Create session (auto-status: draft 🟡)
2. Click "Manage"
3. Assign all participating teams ✓
4. Keep status as "draft"
5. Save changes
6. Upload slides using "Upload Slides" section
```

#### **When Ready to Start:**
```
1. Go back to sessions list
2. Click "Manage" on your session
3. Change status dropdown to "Live" 🟢
4. Save changes
```

**This allows:**
- Teams to login at `/team/login`
- Quiz master to select session in `/qm/dashboard`
- Display screen to show session at `/display`

#### **After Quiz Ends:**
```
1. Click "Manage"
2. Change status to "Ended" 🔴
3. Save changes
```

**This:**
- Prevents new teams from joining
- Marks session as complete
- Preserves scores for review

---

## COMPLETE CHECKLIST FOR QUIZ SETUP

Use this checklist before your quiz:

- [ ] **1. Teams Created**
  - All teams have names and unique codes
  - Seat order set (optional)

- [ ] **2. Session Created**
  - Session has meaningful name
  - Banner text set for display

- [ ] **3. Session Managed**
  - Click "Manage" button
  - All participating teams checked ✓
  - Status set to "draft" for now
  - Save changes clicked

- [ ] **4. Slides Uploaded**
  - Click "Upload Slides"
  - Select the session
  - Question deck uploaded and converted
  - Answer deck uploaded and converted
  - Uploaded decks section shows both decks

- [ ] **5. Quiz Master Created**
  - Username and password set
  - Quiz master can login successfully

- [ ] **6. Test Setup**
  - Open `/display` - should show session
  - Quiz master login and select session
  - Try slide controls (next/prev should work)
  - One team login test at `/team/login`

- [ ] **7. Go Live**
  - Click "Manage" on session
  - Change status to "Live" 🟢
  - Save changes
  - All teams login
  - Quiz master ready at controls

- [ ] **8. Start Quiz!**
  - Quiz master navigates slides
  - Teams buzz in
  - Quiz master adjusts scores
  - Display screen shows everything

---

## WHAT EACH BUTTON DOES

### In Sessions List:

| Button | Action |
|--------|--------|
| **Manage** | Opens panel to change status and assign teams |
| **View** | Redirects to Quiz Master dashboard |

### In Manage Panel:

| Control | Purpose |
|---------|---------|
| **Status Dropdown** | Change draft/live/ended status |
| **Team Checkboxes** | Select which teams participate |
| **Save Changes** | Apply status and team assignments |
| **Cancel** | Close panel without saving |

---

## UNDERSTANDING SESSION STATUS

### 🟡 Draft (Preparing)
**When to use:** While setting up the quiz
- Teams being assigned
- Slides being uploaded
- Testing the setup

**What it means:**
- Session exists but not active
- Teams may not be able to join yet
- Quiz master can select it for testing

---

### 🟢 Live (Active)
**When to use:** When quiz is running
- All setup complete
- Teams ready to join
- Quiz master ready to start

**What it means:**
- Teams can login and participate
- Display screen shows session
- Quiz master has full control
- Buzzer, timer, slides all active

---

### 🔴 Ended (Finished)
**When to use:** After quiz completes
- All questions asked
- Scores finalized
- Winner declared

**What it means:**
- No new teams can join
- Session marked as complete
- Scores preserved for review
- Can still view results

---

## TEAM ASSIGNMENT EXPLAINED

### Why Assign Teams?

When you check teams in the Manage panel:
1. **Creates TeamSession** records linking team to session
2. **Creates Score** entries starting at 0 points
3. **Allows team login** with their team code
4. **Shows teams** in quiz master score controls
5. **Displays teams** on scoreboard

### What If I Don't Assign Teams?

If no teams assigned:
- ❌ Teams can't login to session
- ❌ Score controls won't show teams
- ❌ Scoreboard will be empty
- ❌ Quiz can't function properly

### Can I Add Teams Later?

Yes! You can:
1. Click "Manage" at any time
2. Check additional teams
3. Save changes
4. New teams can now join

### Can I Remove Teams?

Yes:
1. Click "Manage"
2. Uncheck teams you want to remove
3. Save changes
4. **Note:** This doesn't delete their scores, just marks them as inactive

---

## TROUBLESHOOTING

### "No teams appear in checkboxes"
**Solution:** Create teams first using "Manage Teams" section

### "Can't change session status"
**Solution:** Make sure you clicked "Save Changes" button

### "Teams assigned but can't login"
**Possible causes:**
- Session status not set to "Live"
- Team using wrong code
- Team code is case-sensitive (auto-uppercase in system)

### "Quiz master can't see session"
**Solution:**
- Change status to "Live"
- Or check if quiz master endpoint allows "draft" sessions

### "Slides don't appear after upload"
**Solution:**
- Check "Uploaded Decks" section - should show deck with slide count
- If shows 0 slides, conversion failed - check server logs
- May need LibreOffice installed (see SLIDE_UPLOAD_SETUP.md)

---

## COMPARING OLD VS NEW WORKFLOW

### ❌ OLD WAY (Before This Update):

```bash
# Had to use curl commands:
curl -X POST "http://server/api/admin/sessions/1/teams" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1,2,3,4]'

curl -X PATCH "http://server/api/admin/sessions/1" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "live"}'
```
**Problems:**
- Required technical knowledge
- Had to get auth token manually
- Easy to make syntax errors
- No visual feedback

---

### ✅ NEW WAY (Current):

```
1. Click "Manage"
2. Check teams you want
3. Select "Live" from dropdown
4. Click "Save Changes"
```

**Benefits:**
- ✅ No technical knowledge needed
- ✅ Visual interface
- ✅ See current state
- ✅ Immediate feedback
- ✅ Can't make syntax errors
- ✅ Auth token handled automatically

---

## SUMMARY

You now have **complete admin UI** for:

| Feature | Status | How to Access |
|---------|--------|---------------|
| Create Teams | ✅ Complete | "Manage Teams" button |
| Create Sessions | ✅ Complete | "Manage Sessions" button |
| **Assign Teams** | ✅ **NEW!** | "Manage" button → checkboxes |
| **Change Status** | ✅ **NEW!** | "Manage" button → dropdown |
| **Upload Slides** | ✅ **NEW!** | "Upload Slides" button |
| Create Quiz Master | ✅ Complete | "Create Quiz Master" button |

**No more API calls needed!** Everything is in the admin dashboard.

---

## QUICK REFERENCE

### Ready to Run Your Quiz?

1. ✅ Teams created
2. ✅ Session created
3. ✅ Click "Manage" → Check teams → Select "Live" → Save
4. ✅ Click "Upload Slides" → Upload both decks
5. ✅ Quiz master ready
6. ✅ **START!**

---

*Last Updated: 2026-01-01*
*All admin features: ✅ UI Complete*
*No API calls required: ✅*
*Ready for production: ✅*
