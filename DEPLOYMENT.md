# Deployment Guide

## Quick Reference

This system is designed to be deployed for **any conference or event** by simply configuring the `.env` file. No code changes needed.

---

## Pre-Deployment Checklist

### 1. **Environment Configuration**

- [ ] Copy `.env.example` to `.env`
- [ ] Set `CONFERENCE_NAME` (required)
- [ ] Set strong `ADMIN_PASSWORD`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure all conference details
- [ ] Verify `.env` is NOT in git
- [ ] Optional: set `ENV_FILE` to override the default `.env` (use `.env2` for this update if `.env` is protected)

### 2. **Dependencies**

- [ ] Python 3.10+ installed
- [ ] Redis server available
- [ ] LiveKit SFU installed and running (see `LIVEKIT_VPS_SETUP.md`)
- [ ] LibreOffice (optional, for PPT conversion)
- [ ] All Python packages installed

### 3. **Database**

- [ ] Database initialized (auto-created on first run)
- [ ] Admin user created
- [ ] Test teams configured (optional)

---

## Deployment Methods

### LiveKit SFU (VPS)

Screen sharing uses LiveKit as an SFU with systemd on the VPS. Follow the setup guide:

- `LIVEKIT_VPS_SETUP.md`

### Method 1: Local Network (Recommended for Events)

**Best for**: Conference rooms, local events, offline operation

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Set CONFERENCE_NAME and other details

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis
redis-server &

# 4. Start application
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Find your IP
# Windows: ipconfig
# Linux/Mac: ifconfig

# 6. Access from other devices
# http://YOUR-IP:8000
```

**Advantages**:
- ✅ No internet required
- ✅ Low latency
- ✅ Full control
- ✅ Secure (local network only)

---

### Method 2: Cloud Server (VPS)

**Best for**: Remote participation, multi-location events

#### DigitalOcean / AWS / Azure

```bash
# 1. Create server (Ubuntu 22.04)

# 2. SSH into server
ssh root@your-server-ip

# 3. Install dependencies
apt update
apt install -y python3-pip redis-server libreoffice

# 4. Clone repository
git clone <your-repo>
cd quiz

# 5. Install Python packages
pip3 install -r requirements.txt

# 6. Configure environment
cp .env.example .env
nano .env

# Required settings:
CONFERENCE_NAME=Your Conference Name
ADMIN_PASSWORD=strong-password-here
SECRET_KEY=generate-with-openssl-rand
HOST=0.0.0.0
PORT=8000

# 7. Start Redis
systemctl start redis
systemctl enable redis

# 8. Run with production server
pip3 install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Using Systemd (Recommended)

Create `/etc/systemd/system/quiz.service`:

```ini
[Unit]
Description=Quiz System
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/path/to/quiz
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start quiz
systemctl enable quiz
systemctl status quiz
```

---

### Method 3: Docker

**Best for**: Consistent deployments, easy scaling

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Start Redis and app
CMD redis-server --daemonize yes && \
    uvicorn main:app --host 0.0.0.0 --port 8000
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  quiz:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis
    restart: unless-stopped
    volumes:
      - ./media:/app/media
      - ./quiz.db:/app/quiz.db

volumes:
  redis_data:
```

**Deploy**:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

### Method 4: Heroku

**Best for**: Quick deployment, no server management

```bash
# 1. Install Heroku CLI
# https://devcli.heroku.com/

# 2. Login
heroku login

# 3. Create app
heroku create your-quiz-app

# 4. Add Redis
heroku addons:create heroku-redis:mini

# 5. Set environment variables
heroku config:set CONFERENCE_NAME="Your Conference"
heroku config:set ADMIN_PASSWORD="secure-password"
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"

# 6. Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 7. Deploy
git push heroku main

# 8. Open app
heroku open
```

---

## Reverse Proxy Setup (Nginx)

**For production deployments with domain name**

```nginx
# /etc/nginx/sites-available/quiz

server {
    listen 80;
    server_name quiz.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /path/to/quiz/static;
        expires 30d;
    }

    location /media {
        alias /path/to/quiz/media;
        expires 30d;
    }
}
```

Enable and restart:
```bash
ln -s /etc/nginx/sites-available/quiz /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## SSL/HTTPS Setup (Let's Encrypt)

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d quiz.yourdomain.com

# Auto-renewal (already configured)
certbot renew --dry-run
```

---

## Environment-Specific Configurations

### Development

`.env.dev`:
```env
CONFERENCE_NAME=Test Conference
DATABASE_URL=sqlite+aiosqlite:///./dev.db
ADMIN_PASSWORD=dev123
DEBUG=true
```

### Staging

`.env.staging`:
```env
CONFERENCE_NAME=Staging Conference
DATABASE_URL=postgresql://...
ADMIN_PASSWORD=staging-password
```

### Production

`.env.prod`:
```env
CONFERENCE_NAME=45th AISMOC 2026
DATABASE_URL=postgresql://...
ADMIN_PASSWORD=very-secure-password
SECRET_KEY=production-secret-key
```

**Deploy**:
```bash
# Development
cp .env.dev .env
uvicorn main:app --reload

# Production
cp .env.prod .env
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Post-Deployment Tasks

### 1. **Create Admin User**

Admin user is auto-created on first start using credentials from `.env`.

### 2. **Create Test Data** (Optional)

```bash
python create_test_data.py
```

This creates:
- Quiz Master account
- 5 test teams
- Sample session (uses `CONFERENCE_NAME` from .env)

### 3. **Verify Configuration**

```bash
# Check environment loaded correctly
python -c "from config import settings; print(settings.conference_name)"

# Test server
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"1.0.0"}
```

### 4. **Generate QR Codes** (For team login)

```bash
# Example: Generate QR code for team login URL
qrencode -t PNG -o team_login_qr.png "http://your-ip:8000/team/login"
```

---

## Backup & Restore

### Backup

```bash
# Database
cp quiz.db quiz.db.backup

# Media files
tar -czf media_backup.tar.gz media/

# Environment (NEVER commit)
cp .env .env.backup
```

### Restore

```bash
# Database
cp quiz.db.backup quiz.db

# Media
tar -xzf media_backup.tar.gz

# Environment
cp .env.backup .env
```

---

## Monitoring

### Application Logs

```bash
# Development
# Logs output to console

# Production (systemd)
journalctl -u quiz -f

# Production (Docker)
docker-compose logs -f quiz
```

### Health Check

```bash
# Check if service is running
curl http://localhost:8000/health

# Check Redis
redis-cli ping
```

---

## Scaling

### Horizontal Scaling (Multiple Workers)

```bash
# Gunicorn with 4 workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Each worker handles concurrent requests
# Recommended: 2-4 workers per CPU core
```

### Load Balancing (Nginx)

```nginx
upstream quiz_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://quiz_backend;
    }
}
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Redis Connection Error

```bash
# Check Redis status
systemctl status redis

# Start Redis
systemctl start redis

# Test connection
redis-cli ping
```

### Database Migration Issues

```bash
# Delete database and recreate
rm quiz.db
uvicorn main:app --reload
# Database auto-created on startup
```

---

## Security Hardening

### 1. **Firewall**

```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 2. **Strong Passwords**

```bash
# Generate strong password
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. **Rate Limiting** (Nginx)

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/auth/login {
    limit_req zone=login burst=3;
    proxy_pass http://127.0.0.1:8000;
}
```

---

## Multi-Conference Deployment

### Same Server, Different Conferences

```bash
# Conference 1
cd /opt/quiz-aismoc2026
cp .env.aismoc2026 .env
uvicorn main:app --port 8001

# Conference 2
cd /opt/quiz-techcon2024
cp .env.techcon2024 .env
uvicorn main:app --port 8002
```

Each conference gets its own:
- Port
- Database
- `.env` file
- Media directory

**Same codebase, different configurations!**

---

## Checklist: Ready for Production?

- [ ] `.env` configured with strong credentials
- [ ] `SECRET_KEY` generated securely
- [ ] Redis running and accessible
- [ ] Database initialized
- [ ] HTTPS configured (if public)
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Monitoring setup
- [ ] Health checks working
- [ ] Test quiz session created
- [ ] Teams can login successfully
- [ ] WebSocket connections working
- [ ] Timer functioning correctly
- [ ] Buzzer system tested

---

**Your quiz system is now deployed and ready for your conference!**

For any issues, refer to:
- `README.md` - Complete documentation
- `ENVIRONMENT_CONFIG.md` - Environment setup
- `QUICKSTART.md` - Quick setup guide
