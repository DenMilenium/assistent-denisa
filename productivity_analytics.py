"""
Productivity Analytics — анализирует выполнение задач и даёт рекомендации
"""

from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
import database


def analyze_performance(days: int = 30) -> dict:
    """Analyze task completion performance over last N days."""
    stats = database.get_completion_stats(days)
    items = database.get_all_items()
    total_tasks = len([i for i in items if i["enabled"]])
    
    # Daily breakdown
    daily_counts = {}
    total_completed = 0
    for day in stats:
        daily_counts[day["date"]] = day["done_count"]
        total_completed += day["done_count"]
    
    max_daily = max(daily_counts.values()) if daily_counts else 0
    best_day = max(daily_counts, key=daily_counts.get) if daily_counts else None
    
    # Day of week analysis
    weekday_counts = Counter()
    weekday_total = Counter()
    for day_str, count in daily_counts.items():
        try:
            dt = datetime.strptime(day_str, "%Y-%m-%d")
            weekday_counts[dt.weekday()] += count
            weekday_total[dt.weekday()] += total_tasks
        except:
            pass
    
    best_weekday = max(weekday_counts, key=weekday_counts.get) if weekday_counts else None
    
    # Streak calculation
    streak = 0
    current_streak = 0
    today = date.today()
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        if d in daily_counts and daily_counts[d] >= 1:
            current_streak += 1
            streak = max(streak, current_streak)
        else:
            current_streak = 0
    
    # Average completion rate
    avg_daily = total_completed / max(days, 1)
    
    # Weekly comparison
    this_week = sum(daily_counts.get(
        (today - timedelta(days=i)).isoformat(), 0
    ) for i in range(7))
    last_week = sum(daily_counts.get(
        (today - timedelta(days=i+7)).isoformat(), 0
    ) for i in range(7))
    
    week_change = ((this_week - last_week) / max(last_week, 1)) * 100
    
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    return {
        "total_days": len(daily_counts),
        "total_completed": total_completed,
        "avg_daily": round(avg_daily, 1),
        "max_daily": max_daily,
        "best_day": best_day,
        "best_weekday": day_names[best_weekday] if best_weekday is not None else None,
        "streak": streak,
        "current_streak": current_streak,
        "this_week": this_week,
        "last_week": last_week,
        "week_change": round(week_change, 0),
        "daily_counts": daily_counts,
    }


def get_ai_recommendation(analytics: dict = None) -> str:
    """Get smart recommendation based on analytics."""
    if analytics is None:
        analytics = analyze_performance(7)
    
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    day_names = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    
    # Weekday check
    is_weekend = weekday >= 5
    
    # Time of day
    if 6 <= hour < 10:
        time_label = "утро"
    elif 10 <= hour < 13:
        time_label = "предобеденное время"
    elif 13 <= hour < 15:
        time_label = "после обеда"
    elif 15 <= hour < 18:
        time_label = "вторая половина дня"
    elif 18 <= hour < 22:
        time_label = "вечер"
    else:
        time_label = "ночь"
    
    # Build recommendation
    parts = []
    
    # Streak motivation
    if analytics["streak"] >= 5:
        parts.append(f"🔥 У тебя серия из {analytics['streak']} дней! Не останавливайся!")
    elif analytics["streak"] >= 3:
        parts.append(f"💪 Хорошая серия — {analytics['streak']} дня подряд!")
    elif analytics["current_streak"] > 0:
        parts.append(f"📈 Сегодня уже {analytics['current_streak']}-й день подряд с выполненными задачами!")
    
    # Weekly performance
    if analytics["week_change"] > 20:
        parts.append(f"📊 На этой неделе ты сделал на {analytics['week_change']:.0f}% больше, чем на прошлой! 🔥")
    elif analytics["week_change"] < -20:
        parts.append(f"📊 На этой неделе задач меньше, чем на прошлой. Наверстаем? 💪")
    elif analytics["this_week"] > 0:
        parts.append(f"📊 Стабильно — {analytics['this_week']} задач за неделю!")
    
    # Best time recommendation
    if analytics["best_weekday"]:
        best = analytics["best_weekday"].lower()
        if day_names[weekday] == best:
            parts.append(f"⏰ Сегодня {best} — твой самый продуктивный день! Используй это!")
    
    # Time-based tips
    if is_weekend:
        parts.append("🌴 Выходной — хорошо бы совместить отдых с полезными делами")
    elif 6 <= hour < 10:
        parts.append("☀️ Утро — лучшее время для сложных задач, пока свежая голова")
    elif 13 <= hour < 15:
        parts.append("🍽️ После обеда — хорошее время для креативных задач")
    elif 18 <= hour < 20 and not is_weekend:
        parts.append("🏁 Вечер — отлично доделать то, что не успел днём")
    
    # Average recommendation
    if analytics["avg_daily"] < 1:
        parts.append("💡 Попробуй ставить 3 небольшие задачи на день — это легко и мотивирует")
    elif analytics["avg_daily"] < 3:
        parts.append(f"💡 Твоя норма — {analytics['avg_daily']:.0f} задач в день. Попробуй добавить ещё одну!")
    elif analytics["avg_daily"] >= 5:
        parts.append(f"💪 {analytics['avg_daily']:.0f} задач в день — отличный темп! Так держать!")
    
    return " ".join(parts)


def get_motivation(done_count: int = 0, streak: int = 0) -> str:
    """Get motivational message."""
    if done_count == 0 and streak == 0:
        return None
    
    messages = []
    
    if done_count >= 5:
        messages.append("🔥 Ты машина! 5 задач уже сделано!")
    elif done_count >= 3:
        messages.append("💪 Отличный темп! Уже 3 задачи!")
    elif done_count >= 1:
        messages.append("✅ Первая задача готова! Двигаем дальше!")
    
    if streak >= 7:
        messages.append(f"🏆 {streak} дней подряд! Ты легенда!")
    elif streak >= 5:
        messages.append(f"🔥 {streak} дней подряд! Не останавливайся!")
    elif streak >= 3:
        messages.append(f"💪 Уже {streak} дня подряд с выполнением!")
    
    if not messages:
        messages.append("✅ Готово! Отличная работа!")
    
    return " ".join(messages)


def get_day_status() -> dict:
    """Get today's productivity status."""
    today_str = date.today().isoformat()
    stats = database.get_completion_stats(1)
    
    done_today = 0
    for s in stats:
        if s["date"] == today_str:
            done_today = s["done_count"]
    
    items = database.get_all_items()
    total_today = len([i for i in items if i["enabled"]])
    
    analytics = analyze_performance(7)
    
    if done_today == 0:
        status = "😴 Ещё ничего не сделано"
        emoji = "🌅"
    elif done_today <= total_today * 0.3:
        status = "🌅 Хорошее начало!"
        emoji = "👶"
    elif done_today <= total_today * 0.6:
        status = "💪 В процессе! Так держать"
        emoji = "💪"
    elif done_today <= total_today * 0.9:
        status = "🔥 Почти всё сделано!"
        emoji = "🔥"
    else:
        status = "🎉 Все задачи выполнены! Ты красавчик!"
        emoji = "🏆"
    
    return {
        "done": done_today,
        "total": total_today,
        "percent": round(done_today / max(total_today, 1) * 100),
        "status": status,
        "emoji": emoji,
        "streak": analytics["streak"],
    }
