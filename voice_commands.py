"""
Voice Command Parser — семантический парсер русских команд
Понимает тысячи вариантов естественных фраз, не требует запоминать команды
Использует: ключевые слова, синонимы, контекст, части речи
"""

import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# === Actions ===
ACTION_ADD_TASK = "add_task"
ACTION_ADD_SCHEDULE = "add_schedule"
ACTION_DELETE_TASK = "delete_task"
ACTION_LIST_TASKS = "list_tasks"
ACTION_ADD_GOAL = "add_goal"
ACTION_GOAL_PROGRESS = "goal_progress"
ACTION_LIST_GOALS = "list_goals"
ACTION_COMPLETE = "complete"
ACTION_MOVE = "move"
ACTION_QUERY = "query"
ACTION_HELP = "help"
ACTION_UNKNOWN = "unknown"
ACTION_THANKS = "thanks"
ACTION_GOODBYE = "goodbye"

# === Многовариантные семантические карты ===

# 1. СЛОВА-ДЕЙСТВИЯ (глаголы)
CREATE_VERBS = [
    "добавь", "добавить", "добавляю", "создай", "создать", "запиши", "записать",
    "напиши", "написать", "внеси", "внести", "занеси", "занести",
    "поставь", "поставить", "запланируй", "запланировать", "спланируй",
    "назначь", "назначить", "наметь", "наметить", "организуй",
    "зафиксируй", "зафиксировать", "сделай пометку", "сделать пометку",
    "запомни", "сохрани", "сохранить", "включи", "включить",
]

DELETE_VERBS = [
    "удали", "удалить", "убери", "убрать", "отмени", "отменить",
    "сними", "снять", "аннулируй", "аннулировать", "сбрось",
    "избавься", "избавиться", "вычеркни", "вычеркнуть",
    "сотри", "стереть", "очисти", "очистить", "пропусти",
]

LIST_VERBS = [
    "покажи", "показать", "выведи", "вывести", "открой", "открыть",
    "прочитай", "прочитать", "озвучь", "озвучить",
    "скажи", "расскажи", "рассказать", "доложи", "доложить",
    "что у меня", "что я должен", "что запланировано", "что стоит",
    "мои задачи", "мой план", "какие дела", "что делать",
    "список", "перечень", "план", "расписание",
]

UPDATE_VERBS = [
    "обнови", "обновить", "измени", "изменить", "поменяй", "поменять",
    "отредактируй", "отредактировать", "скорректируй", "скорректировать",
    "перенеси", "передвинь", "перемести", "сдвинь",
]

COMPLETE_VERBS = [
    "отметь", "отметить", "заверши", "завершить", "закрой", "закрыть",
    "сделано", "готово", "выполнено", "закончил", "закончила",
    "отмечаю", "выполняю", "справился", "сделал", "выполнил",
]

GOAL_VERBS = [
    "добавь цель", "новая цель", "создай цель", "поставь цель",
    "хочу достичь", "моя цель", "план на год", "целевая задача",
    "цель", "задача на будущее", "долгосрочная задача",
]

PROGRESS_VERBS = [
    "прогресс", "сколько процентов", "какой прогресс",
    "отметь прогресс", "обнови прогресс", "измени прогресс",
    "процент выполнения", "на сколько", "статус",
]

QUERY_VERBS = [
    "спросить", "узнать", "интересно", "хочу знать",
    "почему", "зачем", "откуда", "куда", "отчего",
]

HELP_PHRASES = [
    "что ты умеешь", "помощь", "помоги", "команды",
    "как работать", "что делать", "инструкция", "help",
    "как пользоваться", "возможности", "твои функции",
]

GREETING_PHRASES = [
    "привет", "здравствуй", "здравствуйте", "доброе утро",
    "добрый день", "добрый вечер", "салют", "хай", "хеллоу",
    "hello", "hi", "hey", "ку", "здарова", "приветствую",
    "рад тебя видеть", "снова здесь", "я вернулся",
]

THANKS_PHRASES = [
    "спасибо", "благодарю", "сенкс", "thanks", "thx",
    "ты лучший", "отлично", "супер", "класс", "круто",
    "молодец", "умница", "ты крут", "хорошая работа",
]

GOODBYE_PHRASES = [
    "пока", "до свидания", "до встречи", "увидимся",
    "чао", "бай", "bye", "goodbye", "я ушёл",
    "спокойной ночи", "доброй ночи", "отключаюсь",
]

# 2. СЛОВА-ОБЪЕКТЫ (существительные)
TASK_NOUNS = [
    "задачу", "задачи", "задача", "дело", "дела", "напоминание",
    "напоминания", "пункт", "пункты", "встречу", "встреча",
    "созвон", "колл", "митинг", "планёрку", "планерку",
    "совещание", "звонок", "перезвон", "дел",
]

GOAL_NOUNS = [
    "цель", "цели", "задачу", "задачи", "миссия",
    "направление", "стратегия", "амбиция",
]

SCHEDULE_NOUNS = [
    "расписание", "план", "график", "таймлайн", "календарь",
    "режим", "распорядок", "порядок",
]

TIME_NOUNS = [
    "время", "часов", "часа", "час", "часиков",
    "минут", "минуты", "минута",
]

# 3. СЛОВА-ВРЕМЕНА
DAY_WORDS = {
    "понедельник": 0, "пн": 0, "понедельника": 0, "понедельник": 0,
    "вторник": 1, "вт": 1, "вторника": 1,
    "среда": 2, "ср": 2, "среду": 2, "среды": 2,
    "четверг": 3, "чт": 3, "четверга": 3, "четверг": 3,
    "пятница": 4, "пт": 4, "пятницу": 4, "пятницы": 4,
    "суббота": 5, "сб": 5, "субботу": 5, "субботы": 5,
    "воскресенье": 6, "вс": 6, "воскресенья": 6, "воскресенье": 6,
}

MONTH_WORDS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}

TIME_RELATIVE = {
    "через час": 60, "через полчаса": 30, "через 30 минут": 30,
    "через 15 минут": 15, "через 10 минут": 10, "через 5 минут": 5,
    "через 2 часа": 120, "через 3 часа": 180,
    "через полтора часа": 90,
}

DATE_RELATIVE = {
    "сегодня": "today", "сегодняшний": "today",
    "завтра": "tomorrow", "завтрашний": "tomorrow",
    "послезавтра": "day_after",
    "через неделю": 7, "через 2 дня": 2, "через 3 дня": 3,
    "через 4 дня": 4, "через 5 дней": 5, "через 6 дней": 6,
    "через пару дней": 2, "через несколько дней": 3,
    "на следующей неделе": "next_week", "на той неделе": "next_week",
    "в следующем месяце": "next_month",
}

# 4. ВСПОМОГАТЕЛЬНЫЕ
FILLER_WORDS = [
    "пожалуйста", "будь добр", "будьте добры", "плиз", "плииз",
    "ок", "окей", "оукей", "лады", "ладно", "добро", "ага",
    "ну", "типа", "как бы", "в общем", "короче", "значит",
    "так", "ещё", "тогда", "просто", "такой", "такая",
    "сейчас", "прямо", "немедленно", "срочно",
]

PREFIXES = [
    "запиши мне", "добавь мне", "напомни мне", "создай мне",
    "можешь", "сможешь", "не мог бы ты", "не мог бы",
    "я хочу", "хотел бы", "нужно", "надо", "необходимо",
    "просмотри", "давай", "давайте",
]


def _normalize(text: str) -> str:
    """Normalize text: lowercase, remove filler words."""
    if not text:
        return ""
    text = text.lower().strip()
    # Remove filler words
    pattern = r'\b(' + '|'.join(FILLER_WORDS) + r')\b'
    text = re.sub(pattern, '', text)
    # Remove prefixes
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    # Clean up
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\w\s\-\d:]', '', text)
    
    return text if text else ""


def _extract_time(text: str) -> tuple[str | None, str]:
    """Extract time from text. Returns (time_str, remaining_text)."""
    patterns = [
        # "в 15:00", "в 15.00", "на 15:00"
        r'(?:в|на|к|до)\s*(\d{1,2})[.:](\d{2})',
        # "в 3 часа 30 минут", "в 3 часа", "в 18 часов"
        r'(?:в|на|к)\s*(\d{1,2})\s*(?:час|часа|часов|ч)\s*(?:(\d{1,2})\s*(?:мин|минут|минуты))?',
        # "в 6 вечера", "в 9 утра"
        r'(?:в|на|к|до)\s*(\d{1,2})\s*(?:утра|дня|вечера|ночи)',
        # "в 7" (одинокая цифра в контексте времени)
        r'(?:в|на|к|до)\s*(\d{1,2})(?:\s|$|\.)',
        # "через час", "через полчаса" etc.
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            hour = int(groups[0])
            minute = int(groups[1]) if len(groups) > 1 and groups[1] is not None else 0
            
            # Context-based hour adjustment
            if "вечера" in text or "ночи" in text:
                if hour < 6:
                    hour += 12
            elif "утра" in text and hour > 12:
                hour -= 12
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_str = f"{hour:02d}:{minute:02d}"
                # Remove matched text
                text = text[:match.start()] + text[match.end():]
                return time_str, text
    
    # Check relative time expressions
    for phrase, minutes in TIME_RELATIVE.items():
        if phrase in text:
            now = datetime.now()
            target = now + timedelta(minutes=minutes)
            time_str = target.strftime("%H:%M")
            text = text.replace(phrase, "")
            return time_str, text
    
    return None, text


def _extract_date(text: str) -> tuple[str | None, str]:
    """Extract date from text. Returns (date_str, remaining_text)."""
    # Direct relative dates
    for phrase, value in DATE_RELATIVE.items():
        if phrase in text and isinstance(value, str):
            text = text.replace(phrase, "")
            return value, text
        elif phrase in text and isinstance(value, int):
            target = datetime.now() + timedelta(days=value)
            text = text.replace(phrase, "")
            return target.strftime("%d.%m.%Y"), text
    
    # Day of week: "в пятницу", "в среду", etc.
    for day_name, day_num in sorted(DAY_WORDS.items(), key=lambda x: -len(x[0])):
        pattern = r'(?:в|на|к|до|со|ко)\s*' + re.escape(day_name) + r'\b'
        match = re.search(pattern, text)
        if match:
            today = datetime.now()
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target = today + timedelta(days=days_ahead)
            text = text[:match.start()] + text[match.end():]
            return target.strftime("%d.%m.%Y"), text
    
    # "25 марта", "3 мая", "1 января"
    date_match = re.search(r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)', text)
    if date_match:
        day = int(date_match.group(1))
        month = MONTH_WORDS[date_match.group(2)]
        year = datetime.now().year
        # If month already passed, next year
        if month < datetime.now().month:
            year += 1
        text = text[:date_match.start()] + text[date_match.end():]
        return f"{day:02d}.{month:02d}.{year}", text
    
    # "01.05.2026", "01.05", "01/05"
    date_match = re.search(r'(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?', text)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
        if year < 100:
            year += 2000
        text = text[:date_match.start()] + text[date_match.end():]
        return f"{day:02d}.{month:02d}.{year}", text
    
    return None, text


def extract_task_text(original: str, normalized: str) -> str:
    """Extract meaningful task text from the command."""
    if not normalized:
        return original.capitalize() if original else ""
    
    # Remove action words
    for word_list in [CREATE_VERBS, DELETE_VERBS, LIST_VERBS, UPDATE_VERBS, 
                      COMPLETE_VERBS, GOAL_VERBS, PROGRESS_VERBS, HELP_PHRASES,
                      GREETING_PHRASES, THANKS_PHRASES, GOODBYE_PHRASES]:
        for phrase in sorted(word_list, key=len, reverse=True):
            if normalized.startswith(phrase):
                normalized = normalized[len(phrase):].strip()
                break
    
    # Remove time/date patterns
    normalized, _ = _extract_time(normalized)
    normalized, _ = _extract_date(normalized)
    if not normalized:
        return original.capitalize() if original else ""
    
    # Remove remaining prefixes
    remaining_fillers = [
        "задачу", "задачи", "дело", "дела", "напоминание", "встречу",
        "на", "в", "на", "мне", "для меня", "пожалуйста", "срочно",
        "немедленно", "сегодня", "завтра", "на сегодня", "на завтра",
    ]
    for word in sorted(remaining_fillers, key=len, reverse=True):
        if normalized.startswith(word):
            normalized = normalized[len(word):].strip()
    
    # Clean up
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized.capitalize() if normalized else original


def parse_command(text: str) -> dict:
    """
    Parse natural Russian text into structured command.
    Понимает тысячи вариантов фраз, не требует точных формулировок.
    
    Returns: {"action": ACTION_*, "params": {...}, "confidence": 0.0-1.0}
    """
    original = text.strip()
    normalized = _normalize(text)
    params = {"text": "", "time": None, "date": None, "goal": None, "progress": None}
    
    if not normalized:
        return {"action": ACTION_UNKNOWN, "params": params, "confidence": 0}
    
    score = _semantic_match(normalized)
    
    best_action = score["action"]
    params = score["params"]
    
    # If we got ADD_SCHEDULE, extract the actual task text
    if best_action == ACTION_ADD_SCHEDULE:
        task_text = extract_task_text(original, normalized)
        if task_text:
            params["text"] = task_text
    
    logger.info(f"NLU: '{original}' → action={best_action}, params={params}, confidence={score['confidence']}")
    
    return {
        "action": best_action,
        "params": params,
        "confidence": score.get("confidence", 0.5),
    }


def _semantic_match(text: str) -> dict:
    if not text:
        return {"action": "unknown", "params": {}, "confidence": 0}
    text_lower = text.lower()
    
    categories = {
        ACTION_HELP: {
            "score": 0,
            "patterns": HELP_PHRASES,
            "weight": 3.0,
        },
        ACTION_THANKS: {
            "score": 0,
            "patterns": THANKS_PHRASES,
            "weight": 2.0,
        },
        ACTION_GOODBYE: {
            "score": 0,
            "patterns": GOODBYE_PHRASES,
            "weight": 2.0,
        },
        ACTION_QUERY: {
            "score": 0,
            "patterns": GREETING_PHRASES + QUERY_VERBS,
            "weight": 2.0,
        },
        ACTION_DELETE_TASK: {
            "score": 0,
            "patterns": DELETE_VERBS,
            "weight": 3.0,
        },
        ACTION_LIST_TASKS: {
            "score": 0,
            "patterns": LIST_VERBS,
            "weight": 3.0,
        },
        ACTION_LIST_GOALS: {
            "score": 0,
            "patterns": [p for p in LIST_VERBS + GOAL_VERBS if "цел" in p],
            "weight": 3.0,
        },
        ACTION_ADD_GOAL: {
            "score": 0,
            "patterns": GOAL_VERBS,
            "weight": 3.0,
        },
        ACTION_GOAL_PROGRESS: {
            "score": 0,
            "patterns": PROGRESS_VERBS,
            "weight": 3.0,
        },
        ACTION_COMPLETE: {
            "score": 0,
            "patterns": COMPLETE_VERBS,
            "weight": 2.5,
        },
        ACTION_ADD_SCHEDULE: {
            "score": 0,
            "patterns": CREATE_VERBS,
            "weight": 2.5,
        },
    }
    
    # Score each category
    for action, cat in categories.items():
        for pattern in cat["patterns"]:
            if pattern in text_lower:
                boost = cat["weight"]
                # Boost for exact phrase matches
                if text_lower.startswith(pattern):
                    boost *= 1.5
                cat["score"] += boost
    
    # Time detection = bonus for ADD_SCHEDULE
    time_val, _ = _extract_time(text)
    if time_val:
        categories[ACTION_ADD_SCHEDULE]["score"] += 2.0
    
    date_val, _ = _extract_date(text)
    if date_val:
        categories[ACTION_ADD_SCHEDULE]["score"] += 1.5
    
    # Progress % detection = bonus for ACTION_GOAL_PROGRESS
    if re.search(r'\d+\s*%', text) or re.search(r'\d+\s*(процент|процентов|процента)', text):
        categories[ACTION_GOAL_PROGRESS]["score"] += 3.0
    
    # Goal word = bonus for goal actions
    if any(w in text_lower for w in ["цел", "миссия", "стратеги"]):
        categories[ACTION_ADD_GOAL]["score"] += 2.0
        categories[ACTION_LIST_GOALS]["score"] += 1.5
        categories[ACTION_GOAL_PROGRESS]["score"] += 1.5
    
    # Task words = bonus for task actions
    if any(w in text_lower for w in TASK_NOUNS):
        categories[ACTION_ADD_SCHEDULE]["score"] += 1.0
        categories[ACTION_LIST_TASKS]["score"] += 0.5
    
    # Find best category
    best_action = ACTION_UNKNOWN
    best_score = 0
    
    for action, cat in categories.items():
        if cat["score"] > best_score:
            best_score = cat["score"]
            best_action = action
    
    # Build params
    params = {"text": "", "time": None, "date": None, "goal": None, "progress": None}
    
    if best_action == ACTION_ADD_SCHEDULE or best_action == ACTION_ADD_TASK:
        params["time"] = time_val if time_val else "09:00"
        params["date"] = date_val if date_val else "today"
    
    if best_action == ACTION_GOAL_PROGRESS:
        prog_match = re.search(r'(\d+)\s*%', text) or re.search(r'(\d+)\s*(?:процент|процентов|процента)', text)
        if prog_match:
            params["progress"] = int(prog_match.group(1))
        # Try to find goal name
        remaining = text
        for pat in PROGRESS_VERBS:
            remaining = remaining.replace(pat, "")
        remaining = re.sub(r'\d+\s*%', '', remaining)
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        params["text"] = remaining.capitalize()
    
    if best_action == ACTION_ADD_GOAL:
        remaining = text
        for pat in GOAL_VERBS:
            remaining = remaining.replace(pat, "")
        remaining = re.sub(r'\b(до|к|на|в)\s*\w+', '', remaining)
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        if remaining:
            params["text"] = remaining.capitalize()
    
    if best_action == ACTION_DELETE_TASK:
        remaining = text
        for pat in DELETE_VERBS:
            remaining = remaining.replace(pat, "")
        remaining = re.sub(r'\b(задачу|задачи|дело|напоминание|встречу)\b', '', remaining)
        remaining = re.sub(r'\s+', ' ', remaining).strip()
        if remaining:
            params["text"] = remaining
    
    confidence = min(best_score / 5.0, 0.99)
    confidence = max(confidence, 0.2)
    
    return {"action": best_action, "params": params, "confidence": confidence}


# ---- Response formatters ----

def format_tasks_response(items: list) -> str:
    """Format list of schedule items for voice response."""
    if not items:
        return "У тебя нет запланированных задач на это время."
    
    enabled_items = [i for i in items if i["enabled"]]
    
    if not enabled_items:
        return "У тебя нет активных задач."
    
    response = f"У тебя {len(enabled_items)} задач{'а' if len(enabled_items) == 1 else 'и'}:\n\n"
    for item in enabled_items:
        response += f"⏰ {item['time']} — {item['text']}\n"
    
    return response


def format_goals_response(goals: list) -> str:
    """Format goals for voice response."""
    if not goals:
        return "У тебя нет целей. Скажи: «добавь цель...» чтобы создать."
    
    response = f"У тебя {len(goals)} целей:\n\n"
    for g in goals:
        progress = int(g.get("progress", 0))
        bar = "━" * (progress // 10) + "─" * ((100 - progress) // 10)
        if progress >= 70:
            marker = "🟢"
        elif progress >= 30:
            marker = "🟡"
        else:
            marker = "🔴"
        response += f"{marker} {g['name']} — {progress}%\n{bar}\n"
    
    return response


def get_greeting() -> str:
    """Get appropriate greeting based on time of day."""
    hour = datetime.now().hour
    if hour < 6:
        return "Доброй ночи, Денис!"
    elif hour < 12:
        return "Доброе утро, Денис! Чем займёмся сегодня?"
    elif hour < 18:
        return "Добрый день, Денис! Как твои успехи?"
    else:
        return "Добрый вечер, Денис! Как прошёл день?"


def get_help_text() -> str:
    """Get full help text."""
    return (
        "🗣️ *Голосовой ассистент — понимает любые формулировки!*\n\n"
        "📅 *Задачи:*\n"
        "• «Запиши встречу с Сергеем в пятницу в 3 часа»\n"
        "• «Напомни про звонок завтра в 10 утра»\n"
        "• «Добавь дело купить продукты на сегодня»\n"
        "• «Поставь напоминание на 18:00 позвонить маме»\n"
        "• «Назначь планерку на четверг в 11»\n\n"
        "📋 *Список:*\n"
        "• «Что у меня сегодня?»\n"
        "• «Какие дела на завтра?»\n"
        "• «Покажи всё расписание»\n"
        "• «Что я должен сделать?»\n"
        "• «Мой план на неделю»\n\n"
        "🗑️ *Удалить:*\n"
        "• «Удали задачу про звонок»\n"
        "• «Отмени встречу в пятницу»\n"
        "• «Убери напоминание»\n\n"
        "🎯 *Цели:*\n"
        "• «Добавь цель выучить Python»\n"
        "• «Хочу достичь уровня C1 в английском»\n"
        "• «Моя цель — заработать 5 млн»\n"
        "• «Какие у меня цели?»\n\n"
        "📊 *Прогресс:*\n"
        "• «Отметь прогресс по книге 50 процентов»\n"
        "• «Статус по финансовой цели»\n"
        "• «На сколько выполнил бизнес-план?»\n\n"
        "✅ *Выполнено:*\n"
        "• «Отметь задачу как сделанную»\n"
        "• «Я закончил проект»\n"
        "• «Готово, выполнил»\n\n"
        "🎤 *Говори как удобно!* Я понимаю любые фразы."
    )
