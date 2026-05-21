"""
Daily Schedule Reminder — Database Layer
+ completion tracking
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            text TEXT NOT NULL,
            days_mask INTEGER NOT NULL DEFAULT 127,
            enabled INTEGER NOT NULL DEFAULT 1,
            is_from_goals INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            date TEXT NOT NULL,
            completed_at TEXT NOT NULL DEFAULT (datetime('now')),
            note TEXT DEFAULT '',
            FOREIGN KEY (item_id) REFERENCES schedule_items(id)
        )
    """)

    # Default settings
    defaults = {
        "telegram_token": "",
        "telegram_chat_id": "",
        "notify_pc": "1",
    "notify_telegram": "0",
    "notify_voice": "1",
    "voice_telegram": "0",
    "auto_schedule_synced": "0",
    }
    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()


# ---- Schedule Items CRUD ----

def add_item(time_str: str, text: str, days_mask: int = 127, enabled: bool = True, from_goals: bool = False):
    conn = get_connection()
    conn.execute(
        "INSERT INTO schedule_items (time, text, days_mask, enabled, is_from_goals) VALUES (?, ?, ?, ?, ?)",
        (time_str, text, days_mask, 1 if enabled else 0, 1 if from_goals else 0),
    )
    conn.commit()
    conn.close()


def get_all_items():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM schedule_items ORDER BY time"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_item(item_id: int, **kwargs):
    allowed = {"time", "text", "days_mask", "enabled"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    conn = get_connection()
    conn.execute(
        f"UPDATE schedule_items SET {set_clause} WHERE id = ?", values
    )
    conn.commit()
    conn.close()


def delete_item(item_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM schedule_items WHERE id = ?", (item_id,))
    conn.execute("DELETE FROM completions WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_goal_items():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM schedule_items WHERE is_from_goals = 1 ORDER BY time"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_goal_items():
    """Remove all auto-generated goal items (for resync)."""
    conn = get_connection()
    conn.execute("DELETE FROM schedule_items WHERE is_from_goals = 1")
    conn.execute("""
        DELETE FROM completions WHERE item_id IN 
        (SELECT id FROM schedule_items WHERE is_from_goals = 1)
    """)
    conn.commit()
    conn.close()


# ---- Completions ----

def mark_completed(item_id: int, note: str = ""):
    """Mark an item as completed for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    # Check if already completed today
    existing = conn.execute(
        "SELECT id FROM completions WHERE item_id = ? AND date = ?",
        (item_id, today),
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO completions (item_id, date, note) VALUES (?, ?, ?)",
            (item_id, today, note),
        )
        conn.commit()
    conn.close()


def unmark_completed(item_id: int):
    """Remove completion mark for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    conn.execute(
        "DELETE FROM completions WHERE item_id = ? AND date = ?",
        (item_id, today),
    )
    conn.commit()
    conn.close()


def is_completed_today(item_id: int) -> bool:
    """Check if an item is completed today."""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM completions WHERE item_id = ? AND date = ?",
        (item_id, today),
    ).fetchone()
    conn.close()
    return row is not None


def get_completion_stats(days: int = 30):
    """Get completion statistics for last N days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.date, COUNT(c.id) as done_count,
               (SELECT COUNT(*) FROM schedule_items WHERE enabled = 1) as total_items
        FROM completions c
        WHERE c.date >= date('now', ?)
        GROUP BY c.date
        ORDER BY c.date DESC
    """, (f"-{days} days",)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_week_stats():
    """Get current week stats (Mon-Sun)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.date, COUNT(c.id) as done_count
        FROM completions c
        WHERE c.date >= date('now', 'weekday 1', '-7 days')
        GROUP BY c.date
        ORDER BY c.date
    """).fetchall()
    conn.close()

    total_items = len(get_all_items())
    total_done = sum(r["done_count"] for r in rows)
    days_active = len(rows)

    return {
        "days_active": days_active,
        "total_done": total_done,
        "total_items": total_items,
        "daily_data": [dict(r) for r in rows],
    }


# ---- Settings ----

def get_setting(key: str) -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else ""


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()
