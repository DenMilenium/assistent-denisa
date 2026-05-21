"""
Goals module — reads цели_2026_трекер.xlsx and syncs data
"""

import os
import openpyxl
from datetime import datetime

GOALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "цели_2026_трекер.xlsx")
# Fallback to desktop
if not os.path.exists(GOALS_FILE):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    GOALS_FILE = os.path.join(desktop, "цели_2026_трекер.xlsx")


def _parse_progress(val):
    """Parse progress value to float, handling strings and None."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace("%", "").replace(",", ".").strip())
    except (ValueError, TypeError):
        return 0


def load_all_goals():
    """Load goals data from Excel file."""
    if not os.path.exists(GOALS_FILE):
        return {"goals": [], "subtasks": [], "schedule": [], "monthly": [], "billionaires": [], "total_progress": 0}

    wb = openpyxl.load_workbook(GOALS_FILE, data_only=True)
    data = {}

    # General goals
    ws = wb["Генеральные цели"]
    goals = []
    for row in ws.iter_rows(min_row=7, max_row=12, values_only=True):
        if row[1]:
            goals.append({
                "id": row[0],
                "name": row[1],
                "deadline": str(row[2]) if row[2] else "",
                "status": str(row[3]) if row[3] else "",
                "progress": _parse_progress(row[4]),
                "description": str(row[5]) if row[5] else "",
            })
    data["goals"] = goals

    # Sub-tasks
    ws = wb["Подзадачи"]
    subtasks = []
    for row in ws.iter_rows(min_row=7, max_row=42, values_only=True):
        if row[1]:  # has task name
            subtasks.append({
                "goal_id": row[0] if row[0] else 0,
                "name": str(row[1]) if row[1] else "",
                "category": str(row[2]) if row[2] else "",
                "deadline": str(row[3]) if row[3] else "",
                "progress": _parse_progress(row[4]),
                "status": str(row[5]) if row[5] else "",
                "description": str(row[6]) if row[6] else "",
            })
    data["subtasks"] = subtasks

    # Daily schedule
    ws = wb["Расписание дня"]
    schedule = []
    for row in ws.iter_rows(min_row=6, max_row=70, values_only=True):
        if row[0] and isinstance(row[0], datetime):
            schedule.append({
                "date": row[0],
                "day": str(row[1]) if row[1] else "",
                "morning": str(row[2]) if row[2] else "",
                "sport": str(row[3]) if row[3] else "",
                "breakfast": str(row[4]) if row[4] else "",
                "work_morning": str(row[5]) if row[5] else "",
                "lunch": str(row[6]) if row[6] else "",
                "work_evening": str(row[7]) if row[7] else "",
                "dinner": str(row[8]) if row[8] else "",
                "development": str(row[9]) if row[9] else "",
                "review": str(row[10]) if row[10] else "",
                "priority": str(row[11]) if row[11] else "",
            })
    data["schedule"] = schedule

    # Monthly KPIs
    ws = wb["По месяцам"]
    monthly = []
    for row in ws.iter_rows(min_row=7, max_row=15, values_only=True):
        if row[0]:
            monthly.append({
                "month": str(row[0]) if row[0] else "",
                "books_plan": row[1],
                "books_fact": row[2],
                "neural": str(row[3]) if row[3] else "",
                "weight": row[4],
                "income": row[5] if row[5] else 0,
                "english": str(row[6]) if row[6] else "",
                "contacts": row[7] if row[7] else 0,
                "contracts": str(row[8]) if row[8] else "",
            })
    data["monthly"] = monthly

    # Billionaires
    ws = wb["Миллиардеры"]
    billionaires = []
    for row in ws.iter_rows(min_row=7, max_row=16, values_only=True):
        if row[1]:
            billionaires.append({
                "num": row[0],
                "name": str(row[1]) if row[1] else "",
                "company": str(row[2]) if row[2] else "",
                "country": str(row[3]) if row[3] else "",
                "field": str(row[4]) if row[4] else "",
                "strategy": str(row[5]) if row[5] else "",
                "status": str(row[6]) if row[6] else "",
            })
    data["billionaires"] = billionaires

    # Dashboard metrics
    total_progress = 0
    goal_count = 0
    for g in goals:
        total_progress += g["progress"]
        goal_count += 1
    data["total_progress"] = round(total_progress / goal_count, 1) if goal_count else 0

    wb.close()
    return data


def get_today_schedule():
    """Get today's schedule from goals file."""
    data = load_all_goals()
    today = datetime.now().date()
    for item in data.get("schedule", []):
        if isinstance(item.get("date"), datetime) and item["date"].date() == today:
            return item
    return None


def get_urgent_tasks():
    """Get tasks that are due within 7 days or overdue."""
    data = load_all_goals()
    today = datetime.now()
    urgent = []

    for task in data.get("subtasks", []):
        status = task.get("status", "").strip().lower()
        if status in ("выполнено", "выполнено"):
            continue
        if task.get("progress", 0) >= 100:
            continue

        deadline_str = task.get("deadline", "").strip()
        if not deadline_str:
            continue

        # Parse various date formats
        deadline = None
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y"]:
            try:
                deadline = datetime.strptime(deadline_str, fmt)
                break
            except ValueError:
                continue

        if deadline is None:
            # Try month-year format
            for fmt in ["%B %Y", "%b %Y", "%m.%Y"]:
                try:
                    deadline = datetime.strptime(deadline_str, fmt)
                    break
                except ValueError:
                    continue

        if deadline:
            days_left = (deadline - today).days
            if -30 <= days_left <= 7:
                task["days_left"] = days_left
                urgent.append(task)

    return sorted(urgent, key=lambda x: x.get("days_left", 999))
