"""Apply all fixes to gui.py safely"""
import os

os.chdir(r"/mnt/c/Users/sribn/Desktop/daily_reminder")

with open("gui.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: Move voice methods into MainWindow class
# Current: voice methods are after FocusWidget, before def main()
# Target: voice methods at end of MainWindow class, before FocusWidget

voice_start = "    # ============================================================\n    # ГОЛОСОВОЙ АССИСТЕНТ"
fw_marker = "\n\nclass FocusWidget(QWidget):"
main_marker = "\n\ndef main():"

idx_voice = content.find(voice_start)
idx_fw = content.find(fw_marker)
idx_main = content.find(main_marker)

if idx_voice > idx_fw:
    # Extract voice block
    voice_block = content[idx_voice:idx_main]
    # Remove from current position
    content = content[:idx_voice] + content[idx_main:]
    # Insert before FocusWidget
    insert_pos = content.find(fw_marker)
    content = content[:insert_pos] + "\n" + voice_block + content[insert_pos:]
    changes += 1
    print(f"✅ Voice methods moved into MainWindow")

# Fix 2: avatar_widget.set_speaking.emit -> avatar_widget.avatar.set_speaking.emit
count_emit = content.count("self.avatar_widget.set_speaking.emit")
if count_emit > 0:
    content = content.replace(
        "self.avatar_widget.set_speaking.emit(True)",
        "self.avatar_widget.avatar.set_speaking.emit(True)"
    )
    content = content.replace(
        "self.avatar_widget.set_speaking.emit(False)",
        "self.avatar_widget.avatar.set_speaking.emit(False)"
    )
    changes += 1
    print(f"✅ Fixed {count_emit}x avatar_widget.set_speaking.emit to avatar. version")

# Fix 3: Check that gui.py doesn't have the "|" line numbers (from previous corruption)
if content.startswith("1|"):
    print("❌ File still corrupted! Need to restore from git")
    exit(1)

with open("gui.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Total changes: {changes}")

# Verify
from gui import MainWindow
if hasattr(MainWindow, 'on_mic_click'):
    print("✅ MainWindow.on_mic_click exists!")
else:
    print("❌ MainWindow.on_mic_click still missing!")
