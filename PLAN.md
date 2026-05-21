# Daily Schedule Reminder — Implementation Plan

> **Goal:** Desktop app with daily schedule, PC notifications + Telegram reminders

**Architecture:**
- Python + PyQt6 (GUI desktop)
- SQLite (local schedule storage)
- `schedule` lib + QThread (background reminder timer)
- `python-telegram-bot` (Telegram notifications, async)
- JSON config file (Telegram token, schedule)

**Tech Stack:** Python 3, PyQt6, SQLite3, python-telegram-bot, schedule, plyer (desktop notifications)

---

### Task 1: Project scaffold + virtual environment

**Objective:** Create project structure and install dependencies

**Files:**
- Create: `C:\Users\sribn\Desktop\daily_reminder\`
- Create: `C:\Users\sribn\Desktop\daily_reminder\requirements.txt`
- Create: `C:\Users\sribn\Desktop\daily_reminder\main.py` (entry point stub)

**Dependencies:**
```
PyQt6
python-telegram-bot==20.7
plyer==2.1
schedule==1.2.0
```

---

### Task 2: Database layer (SQLite)

**Objective:** Create database schema for daily schedule items

**Files:**
- Create: `daily_reminder/database.py`

**Schema:**
- `schedule_items` table: id, time (HH:MM), text, days_of_week (bitmask 0-127), enabled (bool), created_at
- `settings` table: key, value (telegram_token, chat_id, notify_pc, notify_telegram)

**Functions:**
- `init_db()` — create tables
- `add_item(time, text, days, enabled=True)`
- `get_all_items()`
- `update_item(id, **kwargs)`
- `delete_item(id)`
- `get_setting(key)` / `set_setting(key, value)`

---

### Task 3: GUI main window (PyQt6)

**Objective:** Create main window with schedule table + add/edit/delete buttons

**Files:**
- Create: `daily_reminder/gui.py`
- Modify: `main.py` (entry point)

**Layout:**
- Top: day-of-week checkboxes (Mon-Sun)
- Middle: QTableWidget (time column, text column, enabled checkbox)
- Bottom: Add button, Edit button, Delete button
- Menu / toolbar: Settings (Telegram config)

---

### Task 4: Add/Edit schedule item dialog

**Objective:** Dialog to create or modify a schedule item

**Files:**
- Create: `daily_reminder/dialogs.py`

**Dialog fields:**
- Time QTimeEdit
- Task text QLineEdit
- Days checkboxes (Mon-Sun) — default all
- Enabled checkbox
- OK / Cancel buttons

---

### Task 5: Background reminder engine

**Objective:** Background thread that checks schedule every 30s and fires reminders

**Files:**
- Create: `daily_reminder/reminder_engine.py`

**Logic:**
- Run in QThread (non-blocking GUI)
- Every 30 seconds check current time + day against schedule
- If match found:
  1. Show PC notification (plyer)
  2. Send Telegram message (async)
  3. Mark item as "fired" for this minute (prevent repeat)

---

### Task 6: Telegram notification system

**Objective:** Send Telegram notifications via bot

**Files:**
- Create: `daily_reminder/telegram_notifier.py`

**Functions:**
- `send_telegram(message, token, chat_id)` — async send
- `test_connection(token, chat_id)` — verify bot works
- Error handling + logging

---

### Task 7: Settings dialog

**Objective:** Configure Telegram bot token + chat ID

**Files:**
- Modify: `daily_reminder/dialogs.py`

**Fields:**
- Telegram Bot Token (QLineEdit, password mode)
- Chat ID (QLineEdit)
- Enable PC notifications (checkbox)
- Enable Telegram notifications (checkbox)
- Test Telegram button
- Save button

---

### Task 8: System tray + auto-start

**Objective:** Minimize to tray, run at Windows startup

**Files:**
- Modify: `main.py`

**Features:**
- System tray icon (minimize on close)
- Tray menu: Show, Settings, Exit
- Optional: add to Windows startup (shortcut in shell:startup)

---

### Task 9: Packaging as .exe

**Objective:** Package into standalone Windows executable

**Command:** `pyinstaller --noconsole --onefile --icon=icon.ico main.py`
