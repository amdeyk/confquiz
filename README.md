# Quiz System - Real-time Interactive Quiz Platform

A comprehensive FastAPI-based quiz system with real-time buzzer functionality, WebSocket communication, and multi-device support.

## Features

- 🎯 **Multi-Role Support**: Admin, Quiz Master, Teams, and Main Display
- 📱 **Responsive Design**: Optimized for both desktop and mobile devices
- ⚡ **Real-time Updates**: WebSocket-based live updates for all clients
- 🔴 **Buzzer System**: Concurrent buzz handling with millisecond precision
- ⏱️ **Timer Management**: Flexible timer system with presets
- 📊 **Score Management**: Real-time scoring with undo functionality
- 📽️ **PPT Support**: Upload and display PowerPoint presentations
- 🌐 **Offline Operation**: Works over local Wi-Fi network

## System Requirements

- Python 3.10 or higher
- Redis server (for real-time features)
- LibreOffice (optional, for better PPT conversion)
- Modern web browser

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Redis

**Windows:**
- Download Redis from https://github.com/microsoftarchive/redis/releases
- Or use WSL2 with Ubuntu and install via apt

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac with Homebrew
brew install redis
```

### 3. Start Redis Server

**Windows:**
```bash
redis-server
```

**Linux/Mac:**
```bash
sudo service redis-server start
# or
redis-server
```

## Quick Start

### 1. Start the Application

```bash
uvicorn main:app --reload
```

Or with custom host/port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### 2. Access Different Interfaces

- **Landing Page**: http://localhost:8000
- **Admin Dashboard**: http://localhost:8000/admin/login
  - Default credentials: `admin` / `admin123`
- **Quiz Master**: http://localhost:8000/qm/login
- **Team Login**: http://localhost:8000/team/login
- **Main Display**: http://localhost:8000/display

## Setup Workflow

### Step 1: Admin Setup

1. Login as admin (`admin` / `admin123`)
2. Create teams with unique codes:
   - Go to "Manage Teams"
   - Add team name, code, and optional seat order
3. Create Quiz Master users (optional):
   - Go to "Create Quiz Master"
   - Set username and password
4. Create a quiz session:
   - Go to "Manage Sessions"
   - Enter session name and banner text

### Step 2: Configure Session (Admin)

1. Upload question and answer decks (PPT files)
2. Create rounds with scoring presets
3. Assign teams to the session
4. Set session status to "live"

### Step 3: Quiz Master Control

1. Login as Quiz Master
2. Select the active session
3. Control panel features:
   - **Slide Navigation**: Next/Previous/Reveal Answer
   - **Timer Control**: Start/Pause/Reset with custom durations
   - **Buzzer Control**: Lock/Unlock buzzers, view buzz queue
   - **Score Management**: Award/deduct points, undo actions

### Step 4: Team Participation

1. Teams login using their unique code
2. Team interface shows:
   - Current score
   - Timer countdown
   - Large red BUZZ button
   - Placement indicator
3. Teams press buzzer during fastest finger rounds
4. Buzzer is automatically locked after use

### Step 5: Main Display

1. Open display on a laptop/projector
2. Shows:
   - Current slide/question
   - Live scoreboard
   - Timer countdown
   - Buzzer queue
   - Session banner

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Edit `.env` file to customize (or set `ENV_FILE` to use another file, such as `.env2` for this update):

```env
# Server Settings
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./quiz.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Network Setup for Offline Use

### 1. Find Your Local IP

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

**Linux/Mac:**
```bash
ifconfig
```

### 2. Update Configuration

In `.env`, set:
```env
HOST=0.0.0.0
PORT=8000
```

### 3. Start Server

```bash
python main.py
```

### 4. Access from Other Devices

On the same Wi-Fi network:
- Admin: `http://192.168.1.100:8000/admin/login`
- Teams: `http://192.168.1.100:8000/team/login`
- Display: `http://192.168.1.100:8000/display`

Replace `192.168.1.100` with your actual local IP.

## Project Structure

```
quiz/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── database.py            # Database setup
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── auth.py                # Authentication logic
├── routers/               # API route handlers
│   ├── auth_router.py
│   ├── admin_router.py
│   ├── qm_router.py
│   ├── team_router.py
│   ├── display_router.py
│   ├── media_router.py
│   └── ws_router.py       # WebSocket handlers
├── services/              # Business logic
│   ├── media_service.py   # PPT processing
│   ├── timer_service.py   # Timer management
│   └── buzzer_service.py  # Buzzer logic
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── team_login.html
│   ├── admin_dashboard.html
│   ├── qm_dashboard.html
│   ├── team_interface.html
│   └── display.html
├── static/                # CSS, JS, images
│   ├── css/
│   └── js/
└── media/                 # Uploaded files and slides
    ├── uploads/
    ├── slides/
    └── thumbs/
```

## Troubleshooting

### Redis Connection Error

**Problem**: "Connection refused" when starting the app

**Solution**: Make sure Redis is running
```bash
redis-server
```

### Database Not Found

**Problem**: SQLite database errors

**Solution**: Database is created automatically on first run. Check file permissions.

### WebSocket Connection Failed

**Problem**: Teams can't connect via WebSocket

**Solution**:
- Check firewall settings
- Ensure WebSocket support in reverse proxy (if used)
- Try accessing via IP instead of localhost

### PPT Conversion Issues

**Problem**: Slides not converting properly

**Solution**:
- Install LibreOffice and set path in `.env`
- Or use python-pptx (limited rendering)

### Port Already in Use

**Problem**: "Address already in use" error

**Solution**: Change port in `.env` or kill the process using port 8000

## Advanced Features

### Buzzer Concurrency

The system uses Redis sorted sets with timestamps for accurate buzz ordering:
- Sub-millisecond precision
- Handles simultaneous button presses
- First buzz detection using Redis SETNX
- Lua scripts for atomic operations

### Timer System

- Background asyncio tasks for countdown
- Redis-based state management
- Pub/Sub for real-time updates
- Pause/Resume functionality
- Per-slide and per-round defaults

### Score Management

- Event sourcing for score changes
- Undo functionality
- Audit logs for all actions
- Configurable scoring presets per round

## Security Notes

⚠️ **Important for Production**:

1. Change default admin password
2. Use strong SECRET_KEY
3. Enable HTTPS
4. Configure CORS properly
5. Use environment variables for secrets
6. Implement rate limiting

## Future Enhancements

- [ ] Audio cues for timer and buzzer
- [ ] Video support for questions
- [ ] Export quiz results to Excel
- [ ] Mobile app for teams
- [ ] Multiple quiz masters
- [ ] Team statistics and analytics
- [ ] QR code generation for team login
- [ ] Backup/Restore functionality

## License

This project is provided as-is for educational and event purposes.

## Support

For issues or questions, refer to the PLAN_AND_API.md file for detailed API documentation and system architecture.

---

**Made with ❤️ for interactive quiz events**
