"""Test Suite — Assistent denisa self-diagnostics (FIXED)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

tests_passed = 0
tests_failed = 0

def test(name, condition, detail=""):
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"  ✅ {name}")
    else:
        tests_failed += 1
        print(f"  ❌ {name} — {detail}")

print("=" * 60)
print("🧪 ASSISTENT DENISA — SELF DIAGNOSTICS")
print("=" * 60)

# === TEST 1: Database ===
print("\n📦 DATABASE")
try:
    import database
    database.init_db()
    
    database.add_item("09:00", "Тестовая задача", 127, True)
    items = database.get_all_items()
    test("Create item", len(items) > 0)
    
    if items:
        test_id = items[0]["id"]
        database.mark_completed(test_id)
        test("Mark completed", database.is_completed_today(test_id))
        database.unmark_completed(test_id)
        test("Unmark completed", not database.is_completed_today(test_id))
        database.delete_item(test_id)
    
    database.set_setting("test_key", "test_value")
    val = database.get_setting("test_key")
    test("Settings save/load", val == "test_value")
    
except Exception as e:
    test("Database module", False, str(e)[:100])

# === TEST 2: TTS ===
print("\n🎤 VOICE (TTS)")
try:
    from voice_assistant import text_to_speech, text_to_speech_sync, speak, EDGE_AVAILABLE
    test("Edge TTS import", EDGE_AVAILABLE)
    
    if EDGE_AVAILABLE:
        # Use speak() instead of text_to_speech(play_now=...)
        path = text_to_speech("Привет Денис! Это тестовое сообщение.")
        test("TTS file generation", path is not None and os.path.exists(path),
             f"path={path}" if not path else "")
        
        if path:
            size = os.path.getsize(path)
            test("TTS file size > 1KB", size > 1000, f"Got {size} bytes")
        
        data = text_to_speech_sync("Тест для Telegram голоса.")
        test("TTS bytes generation", data is not None and len(data) > 1000,
             f"Got {len(data) if data else 0} bytes")
        
        # Test speak (generates + plays)
        result_path = speak("Тест", play_now=False)
        test("Speak function", result_path is not None)
        
        from voice_assistant import _init_player, PLAY_METHOD
        _init_player()
        test("Audio playback method", PLAY_METHOD is not None,
             f"Method: {PLAY_METHOD}")
        
except Exception as e:
    import traceback
    test("TTS module", False, f"{type(e).__name__}: {str(e)[:80]}")

# === TEST 3: Voice Commands ===
print("\n🧠 VOICE COMMANDS (NLU)")
try:
    from voice_commands import parse_command, _normalize
    from command_actions import process_command
    
    # First test simple functions
    normalized = _normalize("добавь встречу в пятницу в 15:00")
    test("Normalize function", bool(normalized), normalized)
    
    test_cases = [
        ("добавь встречу в пятницу в 15:00", "add_schedule"),
        ("что у меня на сегодня", "list_tasks"),
        ("удали задачу купить молоко", "delete_task"),
        ("добавь цель выучить Python", "add_goal"),
        ("отметь прогресс по книге 50%", "goal_progress"),
        ("привет", "query"),
        ("спасибо", "thanks"),
        ("пока", "goodbye"),
        ("что ты умеешь", "help"),
        ("запиши позвонить маме завтра в 10 утра", "add_schedule"),
        ("какие у меня цели", "list_goals"),
        ("я закончил проект", "complete"),
    ]
    
    for phrase, expected in test_cases:
        result = parse_command(phrase)
        if result is None:
            test(f"NLU: \"{phrase[:20]}...\"", False, "parse_command returned None")
            continue
        action = result["action"]
        passed = action == expected
        test(f"NLU: \"{phrase[:25]}...\"", passed, f"Got: {action}, expected: {expected}")
    
    # Test process_command
    cmd = parse_command("привет")
    if cmd:
        result = process_command(cmd)
        test("Process greeting", result["success"], result.get("text", "")[:50])
    
    cmd = parse_command("что ты умеешь")
    if cmd:
        result = process_command(cmd)
        test("Process help", result["success"], result.get("text", "")[:50])
    
    cmd = parse_command("добавь встречу завтра в 15:00")
    if cmd:
        result = process_command(cmd)
        test("Process add schedule", result["success"], result.get("text", "")[:60])
    
except Exception as e:
    import traceback
    test("Voice Commands module", False, f"{type(e).__name__}: {str(e)[:80]}")

# === TEST 4: Goals ===
print("\n🎯 GOALS (Excel)")
try:
    from goals import load_all_goals, get_today_schedule, get_urgent_tasks
    
    data = load_all_goals()
    test("Load goals file", data is not None)
    
    goals = data.get("goals", [])
    test("Goals loaded", len(goals) >= 3, f"Got {len(goals)} goals")
    
    for i, g in enumerate(goals):
        name = g.get("name", g.get("id", f"unknown_{i}"))
        test(f"  Goal {i+1}: {str(name)[:30]}", bool(name), str(name)[:40])
    
    subtasks = data.get("subtasks", [])
    test("Subtasks loaded", len(subtasks) > 5, f"Got {len(subtasks)} subtasks")
    
    schedule = data.get("schedule", [])
    test("Schedule entries", len(schedule) > 20, f"Got {len(schedule)} days")
    
    total = data.get("total_progress", -1)
    test("Total progress", total >= 0, f"Got {total}%")
    
except Exception as e:
    import traceback
    test("Goals module", False, f"{type(e).__name__}: {str(e)[:80]}")

# === TEST 5: Focus Timer ===
print("\n⏱️ FOCUS TIMER")
try:
    from focus_timer import FocusTimer, FocusMode
    
    timer = FocusTimer()
    test("Focus timer init", timer is not None)
    
    timer.start_focus()
    test("Focus started", timer.current_mode == FocusMode.FOCUS)
    test("Focus seconds", timer.seconds_left > 0, f"Got {timer.seconds_left}s")
    
    timer.stop()
    test("Focus stopped", timer.current_mode == FocusMode.STOPPED)
    
except Exception as e:
    test("Focus timer", False, str(e)[:80])

# === TEST 6: Productivity Analytics ===
print("\n📊 PRODUCTIVITY ANALYTICS")
try:
    from productivity_analytics import analyze_performance, get_motivation, get_ai_recommendation, get_day_status
    
    analytics = analyze_performance(7)
    test("Analytics - days", analytics is not None)
    test("Analytics - streak", "streak" in analytics)
    
    mot = get_motivation(3, 5)
    test("Motivation message", mot is not None, mot or "")
    
    status = get_day_status()
    test("Day status", status is not None)
    
except Exception as e:
    test("Productivity Analytics", False, str(e)[:80])

# === TEST 7: Neon Theme ===
print("\n🎨 NEON THEME")
try:
    from neon_theme import (
        TEXT_NEON_CYAN, TEXT_NEON_WHITE, TEXT_NEON_PINK, TEXT_NEON_GREEN,
        TEXT_NEON_BLUE, TEXT_NEON_PURPLE, TEXT_MUTED, FONT_MONO,
        BORDER_NEON, MASTER_STYLE
    )
    test("Neon theme import", bool(TEXT_NEON_CYAN))
    test("Font mono", bool(FONT_MONO))
    test("Master style length", len(MASTER_STYLE) > 1000, f"Got {len(MASTER_STYLE)} chars")
    
    from neon_theme import get_button_style
    primary = get_button_style("primary")
    test("Button style - primary", "gradient" in primary)
    danger = get_button_style("danger")
    test("Button style - danger", "255, 107, 157" in danger)
    
except Exception as e:
    test("Neon theme", False, str(e)[:80])

# === TEST 8: GUI Import (without QApp) ===
print("\n🖥️ GUI MODULES")
try:
    # Only test imports that don't need QApplication
    from live_avatar import LiveAvatar, AnimatedAvatarWidget
    test("LiveAvatar import", True)
    
    from greeting_screen import GreetingOverlay, GreetingManager
    test("GreetingScreen import", True)
    
    from focus_timer import FocusTimer
    test("FocusTimer import", True)
    
except Exception as e:
    test("GUI modules", False, str(e)[:80])

# === SUMMARY ===
print("\n" + "=" * 60)
total = tests_passed + tests_failed
print(f"📋 RESULTS: {tests_passed}/{total} passed, {tests_failed} failed")
if tests_failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"⚠️ {tests_failed} tests FAILED need fixing")
print("=" * 60)
