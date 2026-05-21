"""Fix gui.py: move voice methods INTO MainWindow class"""
import os
os.chdir(r"C:\Users\sribn\Desktop\daily_reminder")

with open("gui.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find markers
voice_start = "    # ============================================================\n    # ГОЛОСОВОЙ АССИСТЕНТ"
fw_class = "\n\nclass FocusWidget(QWidget):"
main_def = "\n\ndef main():"

idx_voice = content.find(voice_start)
idx_fw = content.find(fw_class)
idx_main = content.find(main_def)

print(f"Voice: line {content[:idx_voice].count(chr(10)) + 1}")
print(f"FocusWidget: line {content[:idx_fw].count(chr(10)) + 1}")
print(f"def main(): line {content[:idx_main].count(chr(10)) + 1}")

if idx_voice > idx_fw:
    print("Moving voice block INTO MainWindow...")
    voice_block = content[idx_voice:idx_main]
    content = content[:idx_voice] + content[idx_main:]
    insert_pos = content.find(fw_class)
    content = content[:insert_pos] + "\n" + voice_block + content[insert_pos:]
    
    with open("gui.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ DONE")
else:
    print("Already inside MainWindow")

# Verify
with open("gui.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

main_start = None
main_end = None
for i, line in enumerate(lines):
    if line.startswith("class MainWindow"):
        main_start = i
    elif main_start and line.startswith("class FocusWidget"):
        main_end = i
        break

if main_start and main_end:
    inside = any("def on_mic_click" in line for line in lines[main_start:main_end])
    print(f"on_mic_click inside MainWindow: {inside}")
    print(f"MainWindow: lines {main_start+1}-{main_end}")
    
    # Show last few lines before FocusWidget
    for line in lines[main_end-5:main_end]:
        if line.strip():
            print(f"  {main_end-4 + lines[main_end-5:main_end].index(line)}:{line.rstrip()[:80]}")
