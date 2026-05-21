"""Check if gui.py has on_mic_click from Windows perspective"""
import sys, os
os.chdir(r"C:\Users\sribn\Desktop\daily_reminder")
sys.path.insert(0, ".")

# Read gui.py directly
with open("gui.py", "r", encoding="utf-8") as f:
    content = f.read()

# Check for on_mic_click
count = content.count("on_mic_click")
print(f"on_mic_click found: {count} times")

# Check for def on_mic_click
def_count = content.count("def on_mic_click")
print(f"def on_mic_click: {def_count} times")

# Try to import
try:
    from gui import MainWindow
    print("✅ MainWindow imported OK")
    # Check if on_mic_click exists
    if hasattr(MainWindow, 'on_mic_click'):
        print("✅ MainWindow.on_mic_click EXISTS")
    else:
        print("❌ MainWindow.on_mic_click MISSING")
except Exception as e:
    print(f"❌ Import failed: {e}")

# File size
size = os.path.getsize("gui.py")
print(f"gui.py size: {size} bytes")
