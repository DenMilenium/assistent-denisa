"""
Command Actions — выполняет команды: создаёт задачи, цели, обновляет прогресс
"""

import logging
from datetime import datetime, timedelta
import database
from goals import load_all_goals
from voice_commands import (
    ACTION_ADD_TASK, ACTION_ADD_SCHEDULE, ACTION_DELETE_TASK,
    ACTION_LIST_TASKS, ACTION_ADD_GOAL, ACTION_GOAL_PROGRESS,
    ACTION_LIST_GOALS, ACTION_QUERY, ACTION_HELP, ACTION_UNKNOWN,
    ACTION_COMPLETE, ACTION_THANKS, ACTION_GOODBYE,
    format_tasks_response, format_goals_response, get_greeting,
    get_help_text,
)

logger = logging.getLogger(__name__)

DAY_BITS = {"пн": 1, "вт": 2, "ср": 4, "чт": 8, "пт": 16, "сб": 32, "вс": 64}


def _day_name_to_mask(day_str: str) -> int:
    """Convert day name to bitmask."""
    day_str = day_str.lower().strip()[:2]
    return DAY_BITS.get(day_str, 127)


def _get_day_names(mask: int) -> list:
    """Convert mask to day names."""
    names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return [names[i] for i in range(7) if mask & (1 << i)]


def process_command(command: dict) -> dict:
    """
    Process a parsed command and execute the action.
    Returns response dict with text for voice/message reply.
    """
    action = command.get("action", ACTION_UNKNOWN)
    params = command.get("params", {})
    
    if action == ACTION_HELP:
        return _handle_help()
    
    elif action == ACTION_THANKS:
        return _handle_thanks()
    
    elif action == ACTION_GOODBYE:
        return _handle_goodbye()
    
    elif action == ACTION_QUERY:
        return _handle_query(params)
    
    elif action == ACTION_LIST_TASKS:
        return _handle_list_tasks(params)
    
    elif action == ACTION_ADD_SCHEDULE:
        return _handle_add_schedule(params)
    
    elif action == ACTION_DELETE_TASK:
        return _handle_delete_task(params)
    
    elif action == ACTION_ADD_GOAL:
        return _handle_add_goal(params)
    
    elif action == ACTION_GOAL_PROGRESS:
        return _handle_goal_progress(params)
    
    elif action == ACTION_COMPLETE:
        return _handle_complete(params)
    
    elif action == ACTION_LIST_GOALS:
        return _handle_list_goals(params)
    
    else:
        return {
            "text": "Я не совсем понял команду. Скажи 'помощь', чтобы узнать, что я умею.",
            "success": False
        }


def _handle_help() -> dict:
    return {"text": get_help_text(), "success": True}


def _handle_thanks() -> dict:
    phrase = (
        "Всегда пожалуйста, Денис! 😊\n"
        "Обращайся в любое время — я здесь, чтобы помочь."
    )
    return {"text": phrase, "success": True}


def _handle_goodbye() -> dict:
    hour = datetime.now().hour
    if hour < 6 or hour > 22:
        phrase = "Спокойной ночи, Денис! Сладких снов 🌙"
    elif hour < 12:
        phrase = "Хорошего дня, Денис! Буду ждать твоих команд ☀️"
    else:
        phrase = "Пока, Денис! Если что — я здесь 😊"
    return {"text": phrase, "success": True}


def _handle_help() -> dict:
    return {"text": get_help_text(), "success": True}


def _handle_query(params: dict) -> dict:
    query = params.get("query", "")
    
    if query == "greeting":
        return {"text": get_greeting(), "success": True}
    elif query == "thanks":
        return {"text": "Всегда пожалуйста, Денис! Обращайся ещё 😊", "success": True}
    else:
        return {"text": "Я не знаю ответа на этот вопрос. Скажи 'помощь' для списка команд.", "success": True}


def _handle_list_tasks(params: dict) -> dict:
    items = database.get_all_items()
    date_filter = params.get("date", "")
    
    # Filter by date if needed
    if date_filter == "today":
        today_mask = 1 << datetime.now().weekday()
        items = [i for i in items if i["enabled"] and (i["days_mask"] & today_mask)]
    elif date_filter == "tomorrow":
        tomorrow_mask = 1 << (datetime.now().weekday() + 1) % 7
        items = [i for i in items if i["enabled"] and (i["days_mask"] & tomorrow_mask)]
    
    return {"text": format_tasks_response(items), "success": True}


def _handle_add_schedule(params: dict) -> dict:
    text = params.get("text", "")
    time_str = params.get("time", "09:00")
    date_str = params.get("date", "today")
    
    if not text:
        return {"text": "Не могу добавить пустую задачу. Уточни, что нужно сделать.", "success": False}
    
    # Determine days mask from date
    if date_str == "today":
        mask = 1 << datetime.now().weekday()
    elif date_str == "tomorrow":
        mask = 1 << (datetime.now().weekday() + 1) % 7
    elif date_str == "week":
        mask = 127  # All days
    else:
        # Try to parse as date and find day of week
        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            mask = 1 << dt.weekday()
        except:
            mask = 127
    
    try:
        database.add_item(time_str, text, mask, enabled=True)
        day_names = _get_day_names(mask)
        days_str = ", ".join(day_names)
        
        return {
            "text": f"✅ Добавил задачу: «{text}» в {time_str} на {days_str}.",
            "success": True
        }
    except Exception as e:
        logger.error(f"Add schedule failed: {e}")
        return {"text": f"Не удалось добавить задачу: {e}", "success": False}


def _handle_delete_task(params: dict) -> dict:
    task_text = params.get("text", "").lower()
    
    if not task_text:
        return {"text": "Какую задачу удалить? Уточни название.", "success": False}
    
    items = database.get_all_items()
    found = []
    
    for item in items:
        if task_text in item["text"].lower():
            found.append(item)
    
    if not found:
        return {"text": f"Не нашёл задачу «{task_text}» в расписании.", "success": False}
    
    # Delete first match
    item = found[0]
    database.delete_item(item["id"])
    
    return {"text": f"🗑️ Удалил задачу «{item['text']}» на {item['time']}.", "success": True}


def _handle_add_goal(params: dict) -> dict:
    text = params.get("text", "")
    
    if not text:
        return {"text": "Какую цель добавить? Скажи название.", "success": False}
    
    # We can't write to Excel from here easily, so we add as a note
    # For now, add to a special "goals" note field
    database.set_setting(f"goal_note_{datetime.now().timestamp()}", text)
    
    return {
        "text": f"🎯 Записал: «{text}». Для отслеживания добавь цель в Excel-файл.",
        "success": True
    }


def _handle_goal_progress(params: dict) -> dict:
    text = params.get("text", "").lower()
    progress = params.get("progress", 0)
    
    if not text:
        return {"text": "По какой цели отметить прогресс?", "success": False}
    
    # Look up goals from Excel
    data = load_all_goals()
    goals = data.get("goals", [])
    
    matched = []
    for g in goals:
        if text in g["name"].lower() or text in g.get("description", "").lower():
            matched.append(g)
    
    if matched:
        goal = matched[0]
        database.set_setting(f"goal_progress_{goal['id']}", str(progress))
        return {
            "text": f"📊 Отметил прогресс по цели «{goal['name']}» — {progress}%. Для обновления в Excel измени файл.",
            "success": True
        }
    else:
        return {
            "text": f"Цель «{text}» не найдена. Вот твои цели:\n" + 
                    "\n".join(f"• {g['name']}" for g in goals),
            "success": True
        }


def _handle_list_goals(params: dict) -> dict:
    data = load_all_goals()
    goals = data.get("goals", [])
    return {"text": format_goals_response(goals), "success": True}


def _handle_complete(params: dict) -> dict:
    """Mark a task as completed."""
    task_text = params.get("text", "").lower()
    
    if not task_text:
        # Mark most recent task
        items = database.get_all_items()
        today = datetime.now().weekday()
        for item in reversed(items):
            if item["enabled"]:
                from datetime import date
                database.mark_completed(item["id"])
                return {"text": f"✅ Отметил задачу «{item['text']}» как выполненную!", "success": True}
        return {"text": "Нет активных задач для отметки.", "success": True}
    
    items = database.get_all_items()
    for item in items:
        if task_text in item["text"].lower():
            database.mark_completed(item["id"])
            return {"text": f"✅ Отметил задачу «{item['text']}» как выполненную!", "success": True}
    
    return {"text": f"Не нашёл задачу «{task_text}».", "success": False}
