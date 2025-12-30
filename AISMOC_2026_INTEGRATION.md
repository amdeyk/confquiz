# AISMOC 2026 Conference Integration

## Overview

This quiz system is now fully integrated with the **45th AISMOC 2026** (All India Steel Medical Officers' Conference) branding and design system.

## Conference Details

**Event Information:**
- **Conference Name**: 45th AISMOC 2026
- **Full Name**: All India Steel Medical Officers' Conference
- **Dates**: 12th-15th February
- **Venue**: Steel Club, A-zone, Durgapur

**Leadership:**
- **Chairperson**: Dr. Raj Ranjan Kumar
- **Organizing Secretary**: Dr. Rajeev Kumar
- **Scientific Chair**: Dr. Ajit Karmakar

**Parent Portal**: https://login.aismoc2026dgp.com

---

## Design System Alignment

### ✅ Color Scheme (Matching Parent System)

**Primary Gradient:**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Accent Colors:**
- Purple: `#764ba2` (conference branding)
- Green: `#4CAF50` (success states)
- Blue: `#2196F3` (information)
- Red: `#e74c3c` (timer, buzzer)

### ✅ Typography (Matching Parent System)

**Font Family:**
```css
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
```

**Design Elements:**
- Rounded buttons (border-radius: 50px for circular, 10px for cards)
- White backgrounds with subtle shadows
- Modern, clean interface
- Responsive breakpoints at 768px and 480px

---

## Updated Components

### 1. **Landing Page** (`templates/index.html`)

**Changes:**
- ✅ Conference name and branding header
- ✅ Event dates and venue display
- ✅ Leadership information in footer
- ✅ "45th AISMOC 2026" prominently displayed

**Preview:**
```
🎯 Quiz Competition
45th AISMOC 2026
All India Steel Medical Officers' Conference
12th-15th February | Steel Club, A-zone, Durgapur
```

### 2. **Login Pages**

**Admin Login (`admin_login.html`):**
- ✅ Conference branding header
- ✅ "45th AISMOC 2026 - Quiz Competition System"

**Team Login (`team_login.html`):**
- ✅ Conference branding header
- ✅ "45th AISMOC 2026 - Quiz Competition"

### 3. **Configuration** (`config.py` & `.env`)

**New Conference Settings:**
```python
CONFERENCE_NAME=45th AISMOC 2026
CONFERENCE_FULL_NAME=All India Steel Medical Officers' Conference
CONFERENCE_DATES=12th-15th February
CONFERENCE_VENUE=Steel Club, A-zone, Durgapur
CONFERENCE_CHAIRPERSON=Dr. Raj Ranjan Kumar
CONFERENCE_ORGANIZER=Dr. Rajeev Kumar
CONFERENCE_SCIENTIFIC_CHAIR=Dr. Ajit Karmakar
```

These settings are now available throughout the application via:
```python
from config import settings
print(settings.conference_name)  # "45th AISMOC 2026"
```

### 4. **Database Models** (`models.py`)

**Default Banner Text:**
```python
banner_text = Column(String, default="45th AISMOC 2026 - Quiz Competition")
```

All new sessions will automatically use the conference branding.

### 5. **Test Data** (`create_test_data.py`)

**Session Name:**
```python
Session(
    name="45th AISMOC 2026 - Quiz Competition",
    banner_text="45th AISMOC 2026 - Quiz Competition",
    status="live"
)
```

---

## Integration Features

### 🔗 Link to Parent Portal

A reusable header component has been created (`templates/components/header.html`) that includes:
- Conference logo and name
- Link back to main portal: https://login.aismoc2026dgp.com

**Usage in templates:**
```html
{% include 'components/header.html' %}
```

### 📱 Consistent Branding Across All Interfaces

**All user interfaces now display:**
1. Conference name and branding
2. Event dates and venue
3. Leadership information
4. Unified color scheme
5. Matching typography

---

## Visual Hierarchy

### Landing Page
```
┌─────────────────────────────────────────┐
│     🎯 Quiz Competition                 │
│     45th AISMOC 2026                    │
│     All India Steel Medical Officers'   │
│     Conference                          │
│     12th-15th Feb | Steel Club, Durgapur│
├─────────────────────────────────────────┤
│  [Admin/QM] [Team Login] [Display]     │
├─────────────────────────────────────────┤
│  Chairperson: Dr. Raj Ranjan Kumar      │
│  Org. Sec: Dr. Rajeev Kumar             │
│  Sci. Chair: Dr. Ajit Karmakar          │
└─────────────────────────────────────────┘
```

### Login Pages
```
┌─────────────────────────────────────────┐
│        45th AISMOC 2026                 │
│        Quiz Competition System          │
├─────────────────────────────────────────┤
│         [Login Form]                    │
└─────────────────────────────────────────┘
```

### Main Display
```
┌─────────────────────────────────────────┐
│  45th AISMOC 2026 - Quiz Competition   │
├──────────────────────┬──────────────────┤
│                      │  Timer: 00:30    │
│    [Slide Area]      │  ───────────────  │
│                      │  Scoreboard      │
│                      │  Buzzer Queue    │
└──────────────────────┴──────────────────┘
```

---

## How to Use Conference Settings

### In Templates (Jinja2)

While the settings are in Python config, you can pass them to templates:

```python
# In route handler
from config import settings

@app.get("/custom-page")
async def custom_page(request: Request):
    return templates.TemplateResponse("custom.html", {
        "request": request,
        "conference_name": settings.conference_name,
        "conference_dates": settings.conference_dates
    })
```

### In Python Code

```python
from config import settings

# Access conference details
conference_name = settings.conference_name
# "45th AISMOC 2026"

banner = settings.conference_full_name
# "All India Steel Medical Officers' Conference"
```

### In Database

```python
# Create session with default branding
session = Session(
    name="Morning Quiz Session"
    # banner_text automatically set to "45th AISMOC 2026 - Quiz Competition"
)
```

---

## Customization for Future Conferences

To adapt this system for future AISMOC conferences, simply update `.env`:

```env
# For AISMOC 2027
CONFERENCE_NAME=46th AISMOC 2027
CONFERENCE_DATES=10th-13th March
CONFERENCE_VENUE=Your Venue
# ... etc
```

All branding will automatically update throughout the application!

---

## Checklist: Integration Complete ✅

- ✅ Conference name in all headers
- ✅ Event dates and venue displayed
- ✅ Leadership information shown
- ✅ Color scheme matches parent portal
- ✅ Typography matches parent portal
- ✅ Default session banners use conference name
- ✅ Test data includes conference branding
- ✅ Link to parent portal available
- ✅ Responsive design maintained
- ✅ All login pages branded
- ✅ Configuration centralized in .env

---

## Next Steps

1. **Test the Integration:**
   ```bash
   uvicorn main:app --reload
   ```
   Visit http://localhost:8000 to see the updated branding

2. **Create Test Data:**
   ```bash
   python create_test_data.py
   ```

3. **Customize if Needed:**
   - Edit `.env` for different conference details
   - Modify templates for additional branding elements
   - Add conference logo image if available

---

## Parent System Integration

**Current Link:** https://login.aismoc2026dgp.com

**Potential Future Integrations:**
- SSO (Single Sign-On) with parent portal
- Shared user database
- Guest list import from main system
- Unified authentication
- Conference badge integration

---

**Last Updated:** 2024
**Conference:** 45th AISMOC 2026
**System:** Quiz Competition Platform
