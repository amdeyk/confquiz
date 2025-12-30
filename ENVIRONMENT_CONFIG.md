# Environment Configuration Guide

## Overview

This quiz system is **conference-agnostic** and configured entirely through environment variables. The same codebase can be used for any conference or event by simply changing the `.env` file.

## 🔒 **Critical Rules**

### ✅ DO:
- ✅ Copy `.env.example` to `.env` and customize
- ✅ Keep `.env` in `.gitignore` (already configured)
- ✅ Create separate `.env` files for different environments (dev, staging, prod)
- ✅ Store production `.env` securely (not in git)
- ✅ Read all branding from environment variables

### ❌ DON'T:
- ❌ **NEVER commit `.env` to git**
- ❌ **NEVER hardcode conference/event details in code**
- ❌ **NEVER put defaults with real data in `config.py`**
- ❌ **NEVER modify `.env` in pull requests**
- ❌ **NEVER hardcode branding in templates**

---

## Setup Process

### 1. **Initial Setup (First Time)**

```bash
# Copy the example file
cp .env.example .env

# Edit with your conference details
nano .env  # or use any editor
```

### 2. **Configure Your Conference**

Edit `.env` with your event details:

```env
# Conference/Event Details (Required)
CONFERENCE_NAME=45th AISMOC 2026
CONFERENCE_FULL_NAME=All India Steel Medical Officers' Conference
CONFERENCE_DATES=12th-15th February
CONFERENCE_VENUE=Steel Club, A-zone, Durgapur
CONFERENCE_CHAIRPERSON=Dr. Raj Ranjan Kumar
CONFERENCE_ORGANIZER=Dr. Rajeev Kumar
CONFERENCE_SCIENTIFIC_CHAIR=Dr. Ajit Karmakar
```

### 3. **Customize Other Settings**

```env
# Admin credentials (change these!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here

# Security
SECRET_KEY=generate-a-random-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000
```

---

## Configuration Reference

### Required Settings

#### **CONFERENCE_NAME** (Required)
- Short name of your conference/event
- Displayed prominently throughout the app
- Example: `45th AISMOC 2026`

#### **ADMIN_USERNAME** & **ADMIN_PASSWORD** (Required)
- Admin account credentials
- **Change from defaults in production!**

#### **SECRET_KEY** (Required)
- Used for JWT token encryption
- Generate: `openssl rand -hex 32`
- Must be kept secret!

### Optional Settings

All other conference fields are optional:
- `CONFERENCE_FULL_NAME` - Full descriptive name
- `CONFERENCE_DATES` - Event dates (displayed on landing page)
- `CONFERENCE_VENUE` - Event location
- `CONFERENCE_CHAIRPERSON` - Leadership name
- `CONFERENCE_ORGANIZER` - Organizing secretary name
- `CONFERENCE_SCIENTIFIC_CHAIR` - Scientific chair name

If not set, these fields won't be displayed (graceful degradation).

---

## How It Works

### 1. **Settings are Loaded**

`config.py` reads from `.env`:
```python
from config import settings

# Access anywhere in code
conference_name = settings.conference_name
```

### 2. **Templates Receive Settings**

All route handlers pass settings to templates:
```python
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "settings": settings  # ← Conference data available
    })
```

### 3. **Templates Display Conditionally**

Templates use Jinja2 to show data only if present:
```html
{% if settings.conference_name %}
    <h2>{{ settings.conference_name }}</h2>
{% endif %}
```

No data? No display. The app degrades gracefully.

---

## Multiple Environment Setup

### Development Environment

`.env.dev`:
```env
CONFERENCE_NAME=Test Conference
ADMIN_PASSWORD=dev123
DATABASE_URL=sqlite+aiosqlite:///./dev.db
```

### Production Environment

`.env.prod`:
```env
CONFERENCE_NAME=45th AISMOC 2026
ADMIN_PASSWORD=VerySecurePassword123!
DATABASE_URL=postgresql://...
```

### Usage

```bash
# Development
cp .env.dev .env
uvicorn main:app --reload

# Production
cp .env.prod .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Git Workflow

### ✅ What Gets Committed

```
quiz/
├── .env.example          ✅ Template with placeholder values
├── .gitignore            ✅ Contains .env
├── config.py             ✅ Reads from env, no hardcoded defaults
├── templates/            ✅ Use Jinja2 variables, no hardcoded text
└── ...
```

### ❌ What NEVER Gets Committed

```
quiz/
├── .env                  ❌ NEVER commit (contains secrets)
├── .env.prod             ❌ NEVER commit (production config)
└── .env.dev              ❌ NEVER commit (may contain secrets)
```

### .gitignore Already Configured

```gitignore
# Secrets & Keys
.env
.env.*
!.env.example
```

The `!.env.example` ensures the example file IS committed.

---

## Security Best Practices

### 1. **Generate Secure Keys**

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Strong password
python -c "import secrets; print(secrets.token_urlsafe(20))"
```

### 2. **Different Credentials Per Environment**

Never use the same passwords in dev and production!

```env
# Dev
ADMIN_PASSWORD=dev123

# Prod
ADMIN_PASSWORD=Xy9$mK2#pL8@vN4!
```

### 3. **Rotate Secrets Regularly**

Update `SECRET_KEY` and passwords periodically.

### 4. **Secure Storage**

Production `.env` should be:
- Stored in secure password manager
- Or deployed via CI/CD secrets
- Never in version control
- Never in Slack/email

---

## Example Configurations

### Conference Example (AISMOC 2026)

```env
CONFERENCE_NAME=45th AISMOC 2026
CONFERENCE_FULL_NAME=All India Steel Medical Officers' Conference
CONFERENCE_DATES=12th-15th February
CONFERENCE_VENUE=Steel Club, A-zone, Durgapur
CONFERENCE_CHAIRPERSON=Dr. Raj Ranjan Kumar
CONFERENCE_ORGANIZER=Dr. Rajeev Kumar
CONFERENCE_SCIENTIFIC_CHAIR=Dr. Ajit Karmakar
```

### Corporate Event Example

```env
CONFERENCE_NAME=TechCon 2024
CONFERENCE_FULL_NAME=Annual Technology Conference
CONFERENCE_DATES=March 15-17, 2024
CONFERENCE_VENUE=Convention Center, Mumbai
CONFERENCE_CHAIRPERSON=John Doe
CONFERENCE_ORGANIZER=Jane Smith
CONFERENCE_SCIENTIFIC_CHAIR=Dr. Alex Brown
```

### Minimal Example

```env
# Just the essentials
CONFERENCE_NAME=Quiz Night 2024
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure123
SECRET_KEY=your-secret-key-here
```

---

## Verification

### Check Configuration

```bash
# Verify environment is loaded correctly
python -c "from config import settings; print(f'Conference: {settings.conference_name}')"
```

### Test Application

```bash
# Start server
uvicorn main:app --reload

# Visit http://localhost:8000
# You should see your conference name displayed
```

---

## Troubleshooting

### "CONFERENCE_NAME is required"

**Problem**: `CONFERENCE_NAME` not set in `.env`

**Solution**:
```bash
echo "CONFERENCE_NAME=Your Conference" >> .env
```

### Changes Not Reflected

**Problem**: Server not reloading

**Solution**: Restart the server
```bash
# Kill server (Ctrl+C)
uvicorn main:app --reload
```

### Displaying Wrong Conference

**Problem**: Wrong `.env` file loaded

**Solution**: Check which `.env` is being used
```bash
# Show current .env
cat .env | grep CONFERENCE_NAME
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Copy `.env.example` to `.env`
- [ ] Set strong `ADMIN_PASSWORD`
- [ ] Generate new `SECRET_KEY`
- [ ] Set all conference details
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test configuration loads correctly
- [ ] Never commit `.env` to git
- [ ] Document production `.env` location securely

---

## Code Reusability

### Same Code, Different Conferences

```bash
# AISMOC 2026
CONFERENCE_NAME=45th AISMOC 2026
# → Entire app branded as AISMOC 2026

# AISMOC 2027
CONFERENCE_NAME=46th AISMOC 2027
# → Same code, now branded as AISMOC 2027

# Different Event
CONFERENCE_NAME=Medical Quiz League 2024
# → Same code, completely different branding
```

### No Code Changes Required!

The entire application adapts to the `.env` configuration.

---

## Advanced: Environment Variables in Production

### Using Docker

```dockerfile
# Dockerfile
FROM python:3.10
# ... setup ...
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

```bash
# docker-compose.yml
services:
  quiz:
    env_file: .env.prod
```

### Using Kubernetes

```yaml
# ConfigMap for non-sensitive data
apiVersion: v1
kind: ConfigMap
metadata:
  name: quiz-config
data:
  CONFERENCE_NAME: "45th AISMOC 2026"

# Secret for sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: quiz-secrets
data:
  ADMIN_PASSWORD: <base64-encoded>
  SECRET_KEY: <base64-encoded>
```

---

## Summary

✅ **Conference-agnostic code**
✅ **Environment-controlled branding**
✅ **Secure secrets management**
✅ **Multiple environments supported**
✅ **No hardcoded production data**
✅ **Git-safe workflow**

**Remember**: `.env` is production-only, never committed, and controls all branding!
