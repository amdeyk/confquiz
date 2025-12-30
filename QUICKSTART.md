# Quick Start Guide - Quiz System

## Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Redis Server** - [Windows](https://github.com/microsoftarchive/redis/releases) | [Linux/Mac](https://redis.io/download)

## Installation (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start Redis

Open a separate terminal:

```bash
redis-server
```

### Step 3: Verify Setup (Optional)

```bash
python verify_setup.py
```

### Step 4: Start the Server

**Option A - Direct (recommended):**
```bash
uvicorn main:app --reload
```

**Option B - With custom host/port:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Option C - Using startup script:**
- Windows: Double-click `start_server.bat`
- Linux/Mac: `./start_server.sh`

## First Time Setup (10 minutes)

### 1. Login as Admin

1. Open browser: `http://localhost:8000`
2. Click "Admin Login"
3. Login with:
   - Username: `admin`
   - Password: `admin123`

### 2. Create Teams

1. Click "Manage Teams"
2. Click "+ Add New Team"
3. Enter:
   - Team Name: "Team Alpha"
   - Team Code: "ALPHA1"
   - Seat Order: 1
4. Repeat for more teams (e.g., BETA2, GAMMA3)

### 3. Create a Session

1. Click "Manage Sessions"
2. Click "+ Create New Session"
3. Enter:
   - Session Name: "Quiz Night 2024"
   - Banner Text: "Welcome to Quiz Night"

### 4. Assign Teams to Session

*Note: This feature will be available in the session detail page*

## Running a Quiz (Basic Flow)

### Quiz Master Setup

1. Login at: `http://localhost:8000/qm/login`
   - Use admin credentials or create Quiz Master account
2. Select your session
3. Familiarize yourself with controls:
   - Slide navigation
   - Timer control
   - Buzzer management
   - Score adjustment

### Team Participation

1. Teams go to: `http://localhost:8000/team/login`
2. Enter team code (e.g., "ALPHA1")
3. Optional: Enter nickname
4. Teams can now:
   - See their score
   - Watch the timer
   - Press the big red BUZZ button

### Main Display Setup

1. Open on projector/TV: `http://localhost:8000/display?session=1`
2. Display shows:
   - Current slide
   - Live scoreboard
   - Timer
   - Buzzer queue

## Common Tasks

### Adding Points to a Team

1. Quiz Master dashboard
2. Scroll to "Score Management"
3. Find team and click "+10" or custom amount

### Starting a Timer

1. Quiz Master dashboard
2. Enter duration (seconds)
3. Click "Start Timer"

### Handling Fastest Finger Round

1. Quiz Master: Click "Unlock Buzzers"
2. Display the question
3. Start timer
4. Teams press their BUZZ button
5. Quiz Master sees buzz order
6. Award points to fastest team
7. Click "Clear Queue" for next question

### Navigating Slides

*Note: You need to upload PPT decks first*

1. Quiz Master dashboard
2. Use "Next" / "Previous" buttons
3. Use "Reveal Answer" to show answer slide

## Accessing from Multiple Devices (Same Wi-Fi)

### Find Your IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```

### Connect Other Devices

Replace `localhost` with your IP address:

- Teams: `http://192.168.1.100:8000/team/login`
- Display: `http://192.168.1.100:8000/display`
- Quiz Master: `http://192.168.1.100:8000/qm/login`

## Troubleshooting

### "Connection Refused" Error

**Cause:** Redis not running

**Fix:**
```bash
redis-server
```

### Teams Can't Login

**Cause:** Team codes not created or incorrect

**Fix:**
1. Login as admin
2. Go to "Manage Teams"
3. Verify team codes match what teams are entering
4. Codes are case-sensitive

### Display Shows "No Session"

**Fix:**
Add session ID to URL: `http://localhost:8000/display?session=1`

### Timer Doesn't Start

**Cause:** WebSocket connection issue

**Fix:**
1. Refresh the page
2. Check browser console for errors
3. Ensure Redis is running

### Buzzer Not Working

**Check:**
1. Are buzzers unlocked? (Quiz Master: "Unlock Buzzers")
2. Is timer running? (Buzzers disabled when timer stopped)
3. Has team already buzzed? (Can only buzz once per question)

## Default Credentials

- **Admin Username:** admin
- **Admin Password:** admin123

⚠️ **Change these in production!**

Edit `.env` file:
```env
ADMIN_USERNAME=yourusername
ADMIN_PASSWORD=yourstrongpassword
```

## Next Steps

1. **Read full documentation:** `README.md`
2. **Check API docs:** `http://localhost:8000/docs`
3. **Review system plan:** `PLAN_AND_API.md`
4. **Customize settings:** Edit `.env` file

## Support

For detailed information, see:
- `README.md` - Complete documentation
- `PLAN_AND_API.md` - API reference and architecture
- `http://localhost:8000/docs` - Interactive API documentation

---

**Ready to Quiz!** 🎯
