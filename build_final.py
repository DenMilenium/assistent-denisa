"""
FINAL FIX — единый скрипт.
Запускается из WSL в чистом репозитории.
Делает всё правильно и пушит на GitHub.
"""
import os, sys, json, urllib.request, base64

REPO_DIR = "/mnt/c/Users/sribn/Desktop/daily_reminder"
os.chdir(REPO_DIR)

def gh_download(filename):
    """Download file from GitHub"""
    url = f"https://api.github.com/repos/DenMilenium/assistent-denisa/contents/{filename}"
    try:
        data = json.loads(urllib.request.urlopen(url).read())
        content = base64.b64decode(data["content"]).decode("utf-8")
        with open(f"{REPO_DIR}/{filename}", "w", encoding="utf-8") as f:
            f.write(content)
        return content
    except:
        return None

# Step 1: Download ALL fresh files from GitHub
print("📥 Downloading clean files from GitHub...")
files = [
    "main.py", "gui.py", "live_avatar.py", "greeting_screen.py",
    "voice_assistant.py", "voice_commands.py", "command_actions.py",
    "stt_engine.py", "neon_theme.py", "theme.py", "goals.py",
    "database.py", "dialogs.py", "reminder_engine.py", "focus_timer.py",
    "productivity_analytics.py", "sync_goals.py", "telegram_bot.py",
    "telegram_notifier.py", "create_icon.py", "test_all.py"
]
for f in files:
    if gh_download(f):
        print(f"  ✅ {f}")

# Step 2: Fix gui.py — add continuous voice loop, remove all old trash
print("\n🔧 Fixing gui.py...")
with open(f"{REPO_DIR}/gui.py", "r") as f:
    gui = f.read()

# Clean the file from any line numbers and corruption
lines = gui.split("\n")
clean_lines = []
for line in lines:
    # Remove line number prefix if present (e.g. "   123|")
    import re
    clean = re.sub(r'^\s*\d+\|', '', line)
    clean_lines.append(clean)
gui = "\n".join(clean_lines)

# Remove dupes: keep only the LAST occurrence of key imports
gui_lines = gui.split("\n")
seen = {}
result = []
# Backwards: keep first occurrence = last in file
for line in reversed(gui_lines):
    key = line.strip()
    if key.startswith("from ") or key.startswith("import "):
        if key in seen:
            continue
        seen[key] = True
    result.append(line)
gui = "\n".join(reversed(result))

# Remove duplicate voice method blocks — find all on_mic_click
import re
on_mic_count = len(re.findall(r'def on_mic_click', gui))
print(f"  Found {on_mic_count} on_mic_click definitions")

if on_mic_count > 1:
    # Remove all old voice methods (everything between the voice section comment
    # and "class FocusWidget")
    voice_section_pattern = r'    # ============================================================\n    # ГОЛОСОВОЙ АССИСТЕНТ.*?(?=\nclass FocusWidget)'
    gui = re.sub(voice_section_pattern, '', gui, flags=re.DOTALL)
    print("  Removed old voice section")

# Inject NEW clean voice loop
voice_code = '''
    # ============================================================
    # ГОЛОСОВОЙ АССИСТЕНТ — непрерывный диалог
    # ============================================================
    
    def on_mic_click(self):
        """Toggle continuous voice dialog on/off."""
        if hasattr(self, '_voice_active') and self._voice_active:
            self._voice_active = False
            self._safe_status("⏹️ Стоп")
            self._safe_mic_reset()
            return
        
        self._voice_active = True
        self.mic_btn.setEnabled(False)
        self.mic_btn.setText("⏹️ Стоп")
        self.voice_status.setText("🎙️ Слушаю...")
        self.transcript_label.hide()
        self.avatar_widget.set_mood("thinking")
        
        import threading
        thread = threading.Thread(target=self._voice_loop, daemon=True)
        thread.start()
    
    def _voice_loop(self):
        """Continuous loop: listen → STT → NLU → action → TTS → repeat."""
        import time
        
        try:
            while self._voice_active:
                self._safe_status("🎙️ Говори команду...")
                
                audio_path = None
                for attempt in range(3):
                    audio_path = record_from_mic(duration=10)
                    if audio_path:
                        break
                    if attempt < 2:
                        time.sleep(0.3)
                
                if not audio_path:
                    self._safe_status("❌ Микрофон недоступен")
                    self._safe_speak("Микрофон не работает. Проверь подключение.")
                    break
                
                self._safe_status("🧠 Распознаю...")
                text = None
                if 'SR_AVAILABLE' in dir():
                    from stt_engine import transcribe_with_google
                    text = transcribe_with_google(audio_path)
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                if not text:
                    self._safe_status("🤷 Не расслышал. Повтори...")
                    time.sleep(1)
                    continue
                
                text = text.strip().lower()
                self._safe_transcript(text)
                logger.info(f"STT: '{text}'")
                
                if text in ("стоп","хватит","замолчи","отстань","выйти","exit","stop","quit","закончить","завершить","прекрати","остановись"):
                    self._safe_speak("Хорошо, замолкаю.")
                    break
                
                self._safe_status("🤔 Думаю...")
                command = parse_command(text)
                action = command.get("action", "unknown")
                confidence = command.get("confidence", 0)
                
                if confidence < 0.2:
                    self._safe_speak("Я не понял. Скажи ещё раз.")
                    time.sleep(0.5)
                    continue
                
                response = process_command(command)
                result_text = response.get("text", "Готово!")
                success = response.get("success", True)
                
                if success:
                    self._safe_speak(result_text)
                    self._safe_status(f"✅ {result_text[:60]}")
                    self._safe_avatar_mood("happy")
                else:
                    self._safe_speak(f"Не смог: {result_text[:80]}")
                    self._safe_status(f"❌ {result_text[:60]}")
                
                self._safe_refresh()
                time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Voice loop: {e}")
        finally:
            self._voice_active = False
            self._safe_mic_reset()
            self._safe_avatar_stop()
'''

# Insert before FocusWidget
fw_idx = gui.find("class FocusWidget(QWidget):")
if fw_idx > 0:
    insert_at = gui.rfind("\n", 0, fw_idx)
    gui = gui[:insert_at] + voice_code + gui[insert_at:]
    print("  ✅ Voice loop injected")
else:
    print("  ❌ FocusWidget not found")

with open(f"{REPO_DIR}/gui.py", "w") as f:
    f.write(gui)
print("  ✅ gui.py saved clean")

# Step 3: Fix voice_assistant.py
print("\n🔧 Fixing voice_assistant.py...")
with open(f"{REPO_DIR}/voice_assistant.py", "r") as f:
    va = f.read()

# Add TTS rate
va = va.replace(
    "DEFAULT_VOICE = VOICE_RU_MALE", 
    "DEFAULT_VOICE = VOICE_RU_MALE\nTTS_RATE = \"+20%\"  # Faster speech"
)

# Fix text_to_speech (first one)
va = va.replace(
    "communicate = edge_tts.Communicate(text, voice)",
    "communicate = edge_tts.Communicate(text, voice, rate=\"+20%\")"
)

# Fix text_to_speech_sync (second one)
va = va.replace(
    "communicate = edge_tts.Communicate(text, voice)\n            audio_bytes",
    "communicate = edge_tts.Communicate(text, voice, rate=\"+20%\")\n            audio_bytes"
)

with open(f"{REPO_DIR}/voice_assistant.py", "w") as f:
    f.write(va)
print("  ✅ TTS rate +20% applied")

# Step 4: Copy цели_2026_трекер.xlsx from original location
print("\n🔧 Checking goals file...")
goals_src = "/mnt/c/Users/sribn/Desktop/цели_2026_трекер.xlsx"
goals_dst = f"{REPO_DIR}/цели_2026_трекер.xlsx"
if os.path.exists(goals_src):
    import shutil
    shutil.copy2(goals_src, goals_dst)
    print(f"  ✅ Goals file copied")
else:
    print(f"  ⚠️ Goals file not found at {goals_src}")

# Step 5: Clean up temp files
print("\n🧹 Cleaning trash files...")
trash = ["build.py", "_fix_all.py", "_test_tts.py", "_test_tts2.py", "_test_mic.py",
         "_fix_methods.py", "_fix_methods2.py", "_apply_fixes.py", "_check_gui.py",
         "_check_bounds.py", "_check_imports.py", "_debug_run.py", "_inspect_schedule.py",
         "fix_qgroupbox.py", "fix_all.py", "_run_test.py", "_crash.log", "update.zip"]
for t in trash:
    path = f"{REPO_DIR}/{t}"
    if os.path.exists(path):
        os.remove(path)
print(f"  ✅ Trash cleaned")

# Step 6: Add .gitignore for pycache
with open(f"{REPO_DIR}/.gitignore", "w") as f:
    f.write("__pycache__/\n*.pyc\n*.pyo\nvenv/\n*.log\nupdate.zip\naudio_cache/\n")

# Step 7: Push to GitHub
print("\n⬆️ Pushing to GitHub...")
os.system("git add -A")
os.system('git commit -m "final: clean build - continuous voice dialog + fast TTS + VLC"')
os.system("git push origin main 2>&1")

print("\n" + "=" * 60)
print("✅ FINAL BUILD COMPLETE!")
print("=" * 60)
print("\nGitHub: https://github.com/DenMilenium/assistent-denisa")
print("Теперь просто сделай git pull и запусти!")
