# SLIDE UPLOAD SYSTEM - SETUP GUIDE

## Overview

The quiz system can convert PowerPoint files to PNG images for display during quizzes. There are TWO conversion methods:

1. **LibreOffice (Recommended)** - High quality, accurate rendering
2. **python-pptx (Fallback)** - Basic rendering, may lose formatting

---

## Required Dependencies

### Python Packages (Already in requirements.txt)

```bash
pip install python-pptx  # For reading PPT files
pip install Pillow       # For image processing
pip install pdf2image    # For PDF to image conversion
```

### System Dependencies for LibreOffice Method

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-impress
sudo apt-get install -y poppler-utils  # For pdf2image
```

#### CentOS/RHEL:
```bash
sudo yum install -y libreoffice-core libreoffice-impress
sudo yum install -y poppler-utils
```

#### Windows:
1. Download LibreOffice: https://www.libreoffice.org/download/
2. Install to default location: `C:\Program Files\LibreOffice\program\soffice.exe`
3. Download poppler: https://github.com/oschwartz10612/poppler-windows/releases/
4. Add poppler bin directory to PATH

---

## Configuration

### 1. Check Your .env File

The system needs to know where LibreOffice is installed:

```env
# Add this to your .env file:
LIBREOFFICE_PATH=/usr/bin/libreoffice

# Windows users:
# LIBREOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe

# If not set, system falls back to python-pptx
```

### 2. Verify LibreOffice Installation

**Linux:**
```bash
which libreoffice
# Should output: /usr/bin/libreoffice

# Test conversion:
libreoffice --headless --convert-to pdf test.pptx
```

**Windows:**
```cmd
"C:\Program Files\LibreOffice\program\soffice.exe" --version
```

### 3. Test PDF to Image Conversion

```bash
python -c "from pdf2image import convert_from_path; print('pdf2image works!')"
```

If this fails, install poppler-utils (see above).

---

## How the Conversion Works

### With LibreOffice (High Quality):

```
1. Upload .pptx file
   ↓
2. Save to media/ppt/ directory
   ↓
3. LibreOffice converts PPT → PDF
   ↓
4. pdf2image converts PDF → PNG images (one per slide)
   ↓
5. Pillow creates thumbnails
   ↓
6. Store paths in database
```

**Advantages:**
- ✅ Accurate rendering of slides
- ✅ Preserves fonts, animations, layouts
- ✅ Handles complex PowerPoint features
- ✅ Professional quality output

**Requirements:**
- LibreOffice installed on server
- poppler-utils for PDF conversion
- ~60 seconds for 20-slide deck

---

### Fallback: python-pptx (Basic Quality):

```
1. Upload .pptx file
   ↓
2. Save to media/ppt/ directory
   ↓
3. python-pptx reads slide layout
   ↓
4. Pillow renders basic version
   ↓
5. Create thumbnails
   ↓
6. Store paths in database
```

**Advantages:**
- ✅ No system dependencies needed
- ✅ Works out of the box
- ✅ Faster processing

**Limitations:**
- ⚠️ Limited rendering capabilities
- ⚠️ May lose formatting
- ⚠️ Complex slides may not render correctly
- ⚠️ Animations/transitions ignored

---

## Installation Commands (Full Setup)

### For Ubuntu/Debian Server:

```bash
# 1. Install Python packages
pip install python-pptx Pillow pdf2image

# 2. Install system dependencies
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-impress poppler-utils

# 3. Verify installation
which libreoffice
libreoffice --version

# 4. Update .env file
echo "LIBREOFFICE_PATH=/usr/bin/libreoffice" >> .env

# 5. Restart application
# (If using systemd, supervisor, etc.)
```

---

## Troubleshooting

### Error: "libreoffice: command not found"

**Cause:** LibreOffice not installed or not in PATH
**Fix:**
```bash
# Ubuntu/Debian:
sudo apt-get install libreoffice

# Check installation:
which libreoffice
```

---

### Error: "pdf2image.exceptions.PDFInfoNotInstalledError"

**Cause:** poppler-utils not installed
**Fix:**
```bash
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# CentOS/RHEL:
sudo yum install poppler-utils
```

---

### Error: "Timeout waiting for LibreOffice conversion"

**Cause:** Very large PPT file or slow server
**Fix:** Increase timeout in `media_service.py` line 74:
```python
subprocess.run(cmd, check=True, timeout=120)  # Increase from 60 to 120 seconds
```

---

### Error: "Permission denied writing to media/slides"

**Cause:** Web server doesn't have write permissions
**Fix:**
```bash
# Check current permissions:
ls -la media/

# Grant permissions:
sudo chown -R www-data:www-data media/
# (Replace www-data with your web server user)

# Or make writable:
chmod -R 755 media/
```

---

## Testing Your Setup

### 1. Create Test PowerPoint File

Create a simple test.pptx with 2-3 slides

### 2. Test Upload via UI

1. Login to admin dashboard
2. Click "Upload Slides"
3. Select a session
4. Upload test.pptx as "Question Deck"
5. Wait for conversion
6. Check "Uploaded Decks" section

**Expected Result:**
```
📊 QUESTION Deck
File: test.pptx
Slides: 3 slides converted
```

### 3. Verify Files Created

```bash
ls -la media/slides/deck_1/
# Should show: slide_000.png, slide_001.png, slide_002.png

ls -la media/thumbs/
# Should show: deck_1_thumb_000.png, etc.
```

---

## File Structure

After successful upload:

```
media/
├── ppt/
│   └── deck_1_uuid.pptx          # Original uploaded file
├── slides/
│   └── deck_1/
│       ├── slide_000.png         # Full-size slide 1
│       ├── slide_001.png         # Full-size slide 2
│       └── slide_002.png         # Full-size slide 3
└── thumbs/
    ├── deck_1_thumb_000.png      # Thumbnail slide 1
    ├── deck_1_thumb_001.png      # Thumbnail slide 2
    └── deck_1_thumb_002.png      # Thumbnail slide 3
```

---

## Performance Notes

### Conversion Times (approximate):

| Slides | LibreOffice | python-pptx |
|--------|-------------|-------------|
| 10 slides | ~30 seconds | ~10 seconds |
| 20 slides | ~60 seconds | ~20 seconds |
| 50 slides | ~150 seconds | ~50 seconds |

**Factors affecting speed:**
- Slide complexity (images, animations)
- Server CPU/RAM
- Disk I/O speed
- Network speed (for large uploads)

---

## Recommendations

### For Production Use:

1. ✅ **Install LibreOffice** - Better quality is worth the setup
2. ✅ **Use SSD storage** - Faster conversion and file serving
3. ✅ **Limit file size** - Max 50MB per upload recommended
4. ✅ **Test before quiz** - Upload and verify slides hours before event
5. ✅ **Keep originals** - Don't delete source .pptx files

### For Development/Testing:

1. ✅ **python-pptx is fine** - Good enough for testing
2. ✅ **Small test decks** - Use 5-10 slide decks for faster iteration
3. ℹ️ **Mock data** - Use simple slides without complex formatting

---

## Security Considerations

### Upload Validation:

The system already validates:
- ✅ File extension (.ppt, .pptx only)
- ✅ Admin authentication required
- ✅ Files stored outside web root
- ✅ Unique filenames (UUID) prevent collisions

### Additional Recommendations:

1. **File size limits** - Configure max upload in nginx/apache:
   ```nginx
   client_max_body_size 50M;
   ```

2. **Virus scanning** - Consider adding ClamAV for production:
   ```bash
   sudo apt-get install clamav
   clamscan uploaded_file.pptx
   ```

3. **Disk space monitoring** - Slides can consume significant space

---

## Alternative: Manual Upload

If LibreOffice conversion fails, you can manually convert slides:

### 1. Export slides from PowerPoint:
- File → Export → PNG
- Save each slide as PNG
- Name as: slide_000.png, slide_001.png, etc.

### 2. Upload to server:
```bash
scp slide_*.png user@server:/path/to/media/slides/deck_1/
```

### 3. Create thumbnails:
```bash
for file in slide_*.png; do
  convert "$file" -resize 200x150 "thumb_${file}"
done
```

### 4. Update database:
Insert Deck and Slide records manually via SQL

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Upload UI | ✅ Complete | Added in admin dashboard |
| Backend API | ✅ Complete | `/api/admin/sessions/{id}/decks` |
| LibreOffice Conversion | ⚠️ Optional | Requires system install |
| python-pptx Fallback | ✅ Built-in | Works without dependencies |
| File Validation | ✅ Complete | .ppt/.pptx only |
| Thumbnail Generation | ✅ Complete | Automatic |
| Database Storage | ✅ Complete | Deck and Slide models |

---

**Quick Start Command (Ubuntu):**
```bash
sudo apt-get install -y libreoffice poppler-utils && \
pip install python-pptx Pillow pdf2image && \
echo "LIBREOFFICE_PATH=/usr/bin/libreoffice" >> .env && \
echo "✅ Ready for slide uploads!"
```

---

*Last Updated: 2026-01-01*
*Slide upload UI: ✅ Ready*
*Dependencies: ⚠️ Check your server*
