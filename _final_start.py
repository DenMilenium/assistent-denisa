"""FINAL: download all, fix avatar, add photo, start program"""
import os, subprocess, sys

PROJECT = r"C:\Users\sribn\Desktop\daily_reminder"
PHOTO_SRC = r"C:\Users\sribn\Desktop\photo_2025-06-30_03-24-53.jpg"

os.chdir(PROJECT)

# 1. Create venv if needed
if not os.path.exists(os.path.join(PROJECT, "venv")):
    print("Creating venv...")
    subprocess.run("python -m venv venv", shell=True, check=True)

# 2. Install deps
print("Installing deps...")
subprocess.run(
    "venv\\Scripts\\activate && pip install PyQt6 edge-tts openpyxl speechrecognition sounddevice numpy python-vlc",
    shell=True, capture_output=True
)

# 3. Download files from GitHub via git
print("Downloading from GitHub...")
subprocess.run("git clone https://github.com/DenMilenium/assistent-denisa.git .", shell=True)

# 4. Copy photo
if os.path.exists(PHOTO_SRC):
    import shutil
    shutil.copy2(PHOTO_SRC, os.path.join(PROJECT, "assistent_photo.jpg"))
    print("Photo copied!")

# 5. Start
print("Starting program...")
subprocess.Popen(
    f'start cmd /k "cd /d {PROJECT} && venv\\Scripts\\activate && python -B main.py"',
    shell=True
)
print("Done!")
