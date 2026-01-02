#!/bin/bash
# Quick check if screen sharing files exist on VPS

echo "Checking VPS for screen sharing files..."
echo ""

echo "1. Checking templates:"
ls -lh templates/presenter_*.html 2>/dev/null && echo "✓ Presenter templates exist" || echo "✗ Presenter templates missing"
echo ""

echo "2. Checking if admin_dashboard has presenter form:"
grep -q "Create Presenter User" templates/admin_dashboard.html && echo "✓ Admin dashboard has presenter form" || echo "✗ Admin dashboard missing presenter form"
echo ""

echo "3. Checking main.py for presenter routes:"
grep -q "/presenter/login" main.py && echo "✓ Presenter routes exist in main.py" || echo "✗ Presenter routes missing from main.py"
echo ""

echo "4. Checking admin_router for presenter endpoint:"
grep -q "create_presenter" routers/admin_router.py && echo "✓ Presenter creation endpoint exists" || echo "✗ Presenter creation endpoint missing"
echo ""

echo "5. Testing presenter login endpoint:"
curl -s http://localhost:8361/presenter/login | head -5
echo ""
