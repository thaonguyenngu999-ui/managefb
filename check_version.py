"""Debug script to check if code is up to date"""
import os
import sys

print("=" * 50)
print("DEBUG: Checking code version")
print("=" * 50)

# Check main.py nav_items
with open("main.py", "r") as f:
    content = f.read()
    if '"content"' in content and '"Soạn tin"' in content:
        print("✅ main.py: Has 'Soạn tin' tab")
    else:
        print("❌ main.py: MISSING 'Soạn tin' tab!")

# Check if content_tab.py exists
if os.path.exists("tabs/content_tab.py"):
    print("✅ tabs/content_tab.py: EXISTS")
else:
    print("❌ tabs/content_tab.py: NOT FOUND!")

# Check __init__.py
with open("tabs/__init__.py", "r") as f:
    content = f.read()
    if "ContentTab" in content:
        print("✅ tabs/__init__.py: Has ContentTab import")
    else:
        print("❌ tabs/__init__.py: MISSING ContentTab!")

# Check __pycache__
pycache_path = "tabs/__pycache__"
if os.path.exists(pycache_path):
    print(f"⚠️  __pycache__ exists - may have old cache")
    print(f"   Run: rm -rf tabs/__pycache__")
else:
    print("✅ No __pycache__ found")

# Try import
print("\n" + "=" * 50)
print("Testing imports...")
print("=" * 50)

try:
    from tabs import ContentTab
    print("✅ ContentTab import: SUCCESS")
except Exception as e:
    print(f"❌ ContentTab import FAILED: {e}")

print("\n" + "=" * 50)
print("If all checks pass, restart app with:")
print("  python main.py")
print("=" * 50)
