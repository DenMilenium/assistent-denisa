"""Find MainWindow class boundaries"""
import sys, os
os.chdir(r"C:\Users\sribn\Desktop\daily_reminder")

with open("gui.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

in_main = False
for i, line in enumerate(lines, 1):
    if line.startswith("class MainWindow"):
        in_main = True
        print(f"MainWindow starts at line {i}")
    elif in_main and line.startswith("class ") and "MainWindow" not in line:
        print(f"MainWindow ends at line {i-1} (next class: {line.strip()[:40]})")
        in_main = False
    elif in_main and "def on_mic_click" in line:
        print(f"  ✅ def on_mic_click FOUND at line {i}")
    
# Also check indentation of on_mic_click
for i, line in enumerate(lines, 1):
    if "def on_mic_click" in line:
        print(f"Line {i}: '{line.rstrip()}'")
        print(f"  Indent: {len(line) - len(line.lstrip())} spaces")
        
# Find def main()
for i, line in enumerate(lines, 1):
    if line.startswith("def main()"):
        print(f"\ndef main() at line {i}")
        print(f"  Previous line {i-1}: '{lines[i-2].rstrip()}'" if i > 1 else "")
        break
