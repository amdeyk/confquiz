#!/bin/bash
# Quick one-command fix for missing admin_settings data
# Usage: ./quick_fix.sh

echo ""
echo "========================================"
echo "Quick Fix: Admin Settings Data"
echo "========================================"
echo ""

# Navigate to app directory
cd /opt/apps/confquiz 2>/dev/null || cd "$(dirname "$0")"

echo "Step 1: Checking current admin_settings..."
CURRENT_COUNT=$(sqlite3 quiz.db "SELECT COUNT(*) FROM admin_settings;" 2>/dev/null)

if [ -z "$CURRENT_COUNT" ]; then
    echo "✗ Error: Could not access database"
    exit 1
fi

echo "Current settings count: $CURRENT_COUNT"
echo ""

if [ "$CURRENT_COUNT" -ge 3 ]; then
    echo "✓ Admin settings already exist!"
    echo ""
    sqlite3 quiz.db "SELECT setting_key, setting_value FROM admin_settings;"
    echo ""
    echo "Nothing to fix. Exiting."
    exit 0
fi

echo "Step 2: Inserting missing settings..."
sqlite3 quiz.db << 'EOF'
INSERT OR IGNORE INTO admin_settings (setting_key, setting_value) VALUES
  ('display_mode', 'png_slides'),
  ('screen_share_fps', '10'),
  ('screen_share_quality', '0.7');
EOF

if [ $? -eq 0 ]; then
    echo "✓ Settings inserted successfully!"
else
    echo "✗ Failed to insert settings"
    exit 1
fi
echo ""

echo "Step 3: Verifying..."
FINAL_COUNT=$(sqlite3 quiz.db "SELECT COUNT(*) FROM admin_settings;")
echo "Final settings count: $FINAL_COUNT"
echo ""

echo "Current admin_settings:"
sqlite3 quiz.db "SELECT '  - ' || setting_key || ' = ' || setting_value FROM admin_settings;"
echo ""

echo "========================================"
echo "✓ Fix Complete!"
echo "========================================"
echo ""
echo "Now test with:"
echo "  curl http://localhost:8000/api/admin/settings"
echo ""
