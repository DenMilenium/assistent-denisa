"""
Daily Schedule Reminder — Database Layer
SQLite database for schedule items and settings
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
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default settings
    defaults = {
        "telegram_token": "",
        "telegram_chat_id": "",
        "notify_pc": "1",
        "notify_telegram": "0",
    }
    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()


# ---- Schedule Items CRUD ----

def add_item(time_str: str, text: str, days_mask: int = 127, enabled: bool = True):
    conn = get_connection()
    conn.execute(
        "INSERT INTO schedule_items (time, text, days_mask, enabled) VALUES (?, ?, ?, ?)",
        (time_str, text, days_mask, 1 if enabled else 0),
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
    conn.commit()
    conn.close()


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
