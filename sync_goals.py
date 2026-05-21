"""
Auto-sync daily schedule from цели_2026_трекер.xlsx
Creates reminders for each time block in the schedule
"""

from datetime import datetime
import database
from goals import load_all_goals

DAY_BIT = {
    "понедельник": 1, "пн": 1,
    "вторник": 2, "вт": 2,
    "среда": 4, "ср": 4,
    "четверг": 8, "чт": 8,
    "пятница": 16, "пт": 16,
    "суббота": 32, "сб": 32,
    "воскресенье": 64, "вс": 64,
}

ALL_DAYS = 127  # Mon-Sun
WEEKDAYS = 31   # Mon-Fri
WEEKEND = 96    # Sat-Sun


def get_days_mask(day_name: str) -> int:
    """Convert Russian day name to bitmask."""
    name = day_name.lower().strip()
    if name in DAY_BIT:
        return DAY_BIT[name]

    # Check for ranges
    day_names = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    day_names_short = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    for i, dlist in enumerate([day_names, day_names_short]):
        for j, d in enumerate(dlist):
            if d in name:
                return 1 << j

    return ALL_DAYS


def synced_once() -> bool:
    """Check if auto-sync has been done."""
    return database.get_setting("auto_schedule_synced") == "1"


def mark_synced():
    database.set_setting("auto_schedule_synced", "1")


def auto_sync():
    """Create schedule items from goals file."""
    if synced_once():
        return False

    data = load_all_goals()
    if not data.get("schedule"):
        return False

    # Get all unique tasks from schedule
    seen_tasks = set()
    tasks_to_add = []

    for day in data["schedule"]:
        blocks = [
            ("06:00", day.get("morning", "")),
            ("07:00", day.get("sport", "")),
            ("08:30", day.get("breakfast", "")),
            ("09:00", day.get("work_morning", "")),
            ("13:00", "🍽️ Обед"),
            ("14:00", day.get("work_evening", "")),
            ("18:00", "🍽️ Ужин"),
            ("19:00", day.get("development", "")),
            ("21:30", day.get("review", "")),
        ]

        day_name = day.get("day", "").lower()
        mask = get_days_mask(day_name)

        for time_str, task_text in blocks:
            if not task_text or task_text in ("—", "-", "", "—"):
                continue

            key = f"{time_str}|{task_text[:50]}"
            if key not in seen_tasks:
                seen_tasks.add(key)
                tasks_to_add.append((time_str, task_text, mask))
            else:
                # Add days to existing task
                for i, (t, txt, m) in enumerate(tasks_to_add):
                    if t == time_str and txt[:50] == task_text[:50]:
                        tasks_to_add[i] = (t, txt, m | mask)
                        break

    # Now create items grouped by time
    for time_str, task_text, mask in tasks_to_add:
        database.add_item(time_str, task_text, mask, enabled=True, from_goals=True)

    mark_synced()
    return True


def check_and_resync():
    """Check if goals file changed and resync if needed."""
    # For now, just return synced status
    return synced_once()
