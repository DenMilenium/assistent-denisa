"""
Voice Command Parser — понимает русские голосовые команды
Превращает естественный язык в структурированные действия
"""

import re
import logging
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

# Типы действий
ACTION_ADD_TASK = "add_task"
ACTION_ADD_SCHEDULE = "add_schedule"
ACTION_DELETE_TASK = "delete_task"
ACTION_LIST_TASKS = "list_tasks"
ACTION_ADD_GOAL = "add_goal"
ACTION_GOAL_PROGRESS = "goal_progress"
ACTION_LIST_GOALS = "list_goals"
ACTION_QUERY = "query"
ACTION_HELP = "help"
ACTION_UNKNOWN = "unknown"


# Дни недели
DAYS_RU = {
    "понедельник": 0, "пн": 0,
    "вторник": 1, "вт": 1,
    "среда": 2, "ср": 2,
    "четверг": 3, "чт": 3,
    "пятница": 4, "пт": 4,
    "суббота": 5, "сб": 5,
    "воскресенье": 6, "вс": 6,
}

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}


def parse_command(text: str) -> dict:
    """
    Parse a Russian text command into structured action.
    
    Returns:
        {
            "action": ACTION_*,
            "params": {
                "text": str,
                "time": str or None,
                "date": str or None,
                "goal": str or None,
                "progress": int or None,
            },
            "confidence": 0.0-1.0
        }
    """
    text = text.lower().strip()
    
    # Remove filler words
    text = re.sub(r'\b(пожалуйста|будь добр|будьте добры|плиз|ок|окей|ладно)\b', '', text).strip()
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Reset params
    params = {"text": "", "time": None, "date": None, "goal": None, "progress": None}
    
    # === HELP ===
    if re.match(r'^(что ты умеешь|помощь|help|команды|что можно)', text):
        return {"action": ACTION_HELP, "params": params, "confidence": 1.0}
    
    # === GREETINGS ===
    if re.match(r'^(привет|здравствуй|доброе утро|добрый день|добрый вечер|хай|hello|hi)', text):
        return {"action": ACTION_QUERY, "params": {"query": "greeting"}, "confidence": 1.0}
    
    # === LIST TASKS ===
    if re.search(r'(что у меня|покажи|список|расписание|план|что делать|какие задачи)', text):
        if re.search(r'(сегодня|на сегодня|сейчас)', text):
            params["date"] = "today"
        elif re.search(r'(завтра|на завтра)', text):
            params["date"] = "tomorrow"
        elif re.search(r'(неделю|на неделю)', text):
            params["date"] = "week"
        return {"action": ACTION_LIST_TASKS, "params": params, "confidence": 0.9}
    
    # === DELETE TASK ===
    if re.search(r'(удали|отмени|убери|удалить|отменить|отмена)', text):
        task_text = re.sub(r'(удали|отмени|убери|удалить|отменить|пожалуйста|задачу|задачи|напоминание)', '', text).strip()
        params["text"] = task_text
        return {"action": ACTION_DELETE_TASK, "params": params, "confidence": 0.8}
    
    # === ADD GOAL ===
    if re.search(r'(добавь цель|новая цель|создай цель|поставь цель)', text):
        goal_text = re.sub(r'(добавь|новая|создай|поставь|цель)', '', text).strip()
        params["text"] = goal_text
        
        # Check for deadline
        deadline_match = re.search(r'(до|к|к концу)\s+(\w+)', text)
        if deadline_match:
            params["date"] = deadline_match.group(2)
        
        return {"action": ACTION_ADD_GOAL, "params": params, "confidence": 0.85}
    
    # === GOAL PROGRESS ===
    if re.search(r'(прогресс|отметь|процент|сколько|статус)', text) and re.search(r'(цель|цели|задача)', text):
        # "Отметь прогресс по книге 30%"
        progress_match = re.search(r'(\d+)\s*%', text)
        if progress_match:
            params["progress"] = int(progress_match.group(1))
        
        # Extract goal name
        goal_text = re.sub(r'(отметь|прогресс|по|процент|сколько|\d+\s*%|цель|цели)', '', text).strip()
        params["text"] = goal_text
        
        return {"action": ACTION_GOAL_PROGRESS, "params": params, "confidence": 0.85}
    
    # === LIST GOALS ===
    if re.search(r'(какие цели|список целей|мои цели|покажи цели)', text):
        return {"action": ACTION_LIST_GOALS, "params": params, "confidence": 0.95}
    
    # === ADD TASK / SCHEDULE (most complex) ===
    if re.search(r'(добавь|запиши|создай|напомни|запланируй|запиши)', text):
        # Extract time
        time_str = None
        time_match = re.search(r'(?:в|на)\s*(\d{1,2})[.:](\d{2})', text)
        if time_match:
            h, m = int(time_match.group(1)), int(time_match.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                time_str = f"{h:02d}:{m:02d}"
        
        # "в 18:00" format
        if not time_str:
            time_match = re.search(r'в\s+(\d{1,2})\s*(?:часов|ч|:)\s*(\d{0,2})', text)
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2)) if time_match.group(2) else 0
                if 0 <= h <= 23:
                    time_str = f"{h:02d}:{m:02d}"
        
        # "в 3 часа" → 15:00 (если не указано утро)
        if not time_str:
            hour_match = re.search(r'в\s+(\d{1,2})\s*(?:часа|часов|час)', text)
            if hour_match:
                h = int(hour_match.group(1))
                if h <= 5:
                    h += 12  # 3 часа → 15:00
                if 0 <= h <= 23:
                    time_str = f"{h:02d}:00"
        
        # Extract date
        date_str = None
        
        # "сегодня"
        if re.search(r'сегодня|сегодня\w*', text):
            date_str = "today"
        # "завтра"
        elif re.search(r'завтра', text):
            date_str = "tomorrow"
        # "послезавтра"
        elif re.search(r'послезавтра', text):
            date_str = "day_after"
        # Day of week
        else:
            for day_name, day_num in DAYS_RU.items():
                if re.search(r'\b' + day_name + r'\b', text):
                    today = datetime.now()
                    days_ahead = day_num - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target = today + timedelta(days=days_ahead)
                    date_str = target.strftime("%d.%m.%Y")
                    break
        
        # Date with number + month
        if not date_str:
            date_match = re.search(r'(\d{1,2})\s+(\w+)', text)
            if date_match:
                day = int(date_match.group(1))
                month_name = date_match.group(2).lower()
                if month_name in MONTHS_RU:
                    month = MONTHS_RU[month_name]
                    year = datetime.now().year
                    date_str = f"{day:02d}.{month:02d}.{year}"
        
        # "через N дней"
        if not date_str:
            days_match = re.search(r'через\s+(\d+)\s*(?:дня|дней|день)', text)
            if days_match:
                days = int(days_match.group(1))
                target = datetime.now() + timedelta(days=days)
                date_str = target.strftime("%d.%m.%Y")
        
        # Extract task text (remove command words)
        task_text = text
        task_text = re.sub(r'(добавь|запиши|создай|напомни|запланируй|запиши)', '', task_text)
        task_text = re.sub(r'(во|в|на|к)\s*\d{1,2}[.:]?\d{0,2}\s*(?:часов|часа|час)?', '', task_text)
        task_text = re.sub(r'(на|к|до)\s+\d{1,2}\s+\w+', '', task_text)  # "на пятницу", "до декабря"
        task_text = re.sub(r'(сегодня|завтра|послезавтра|через\s+\d+\s+дня)', '', task_text)
        task_text = re.sub(r'\b(пожалуйста|будь добр|задачу|задачи|дело|встречу)\b', '', task_text)
        task_text = re.sub(r'\s+', ' ', task_text).strip()
        
        if not task_text:
            task_text = "Напоминание"
        
        params["text"] = task_text.capitalize()
        params["time"] = time_str or "09:00"
        params["date"] = date_str or "today"
        
        return {"action": ACTION_ADD_SCHEDULE, "params": params, "confidence": 0.8}
    
    # === QUERY (general question) ===
    if re.search(r'(что|кто|где|когда|почему|зачем|как|сколько|какой)', text):
        return {"action": ACTION_QUERY, "params": {"query": text}, "confidence": 0.6}
    
    # === THANKS ===
    if re.search(r'(спасибо|благодарю|cпасибо|сенкс|thx|thanks)', text):
        return {"action": ACTION_QUERY, "params": {"query": "thanks"}, "confidence": 1.0}
    
    # Unknown
    return {"action": ACTION_UNKNOWN, "params": params, "confidence": 0.3}


def format_tasks_response(items: list) -> str:
    """Format list of schedule items for voice response."""
    if not items:
        return "У тебя нет запланированных задач на это время."
    
    response = f"У тебя {len(items)} задач:\n"
    for item in items:
        enabled = "✅" if item["enabled"] else "⏸️"
        response += f"\n{enabled} {item['time']} — {item['text']}"
    
    return response


def format_goals_response(goals: list) -> str:
    """Format goals for voice response."""
    if not goals:
        return "У тебя нет целей."
    
    response = f"У тебя {len(goals)} целей:\n"
    for g in goals:
        response += f"\n🎯 {g['name']} — {int(g.get('progress', 0))}%"
    
    return response


def get_greeting() -> str:
    """Get appropriate greeting based on time of day."""
    hour = datetime.now().hour
    if hour < 6:
        return "Доброй ночи, Денис!"
    elif hour < 12:
        return "Доброе утро, Денис!"
    elif hour < 18:
        return "Добрый день, Денис!"
    else:
        return "Добрый вечер, Денис!"
