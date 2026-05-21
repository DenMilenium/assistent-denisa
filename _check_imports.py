"""Quick check: test all imports + audio init"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []

print("=== Import Check ===")

try:
    from live_avatar import LiveAvatar, AnimatedAvatarWidget
    print("✅ Avatar import")
except Exception as e:
    errors.append(f"Avatar: {e}")
    traceback.print_exc()

try:
    from voice_assistant import _init_player, PLAY_METHOD
    _init_player()
    print(f"✅ Audio init: method={PLAY_METHOD}")
except Exception as e:
    errors.append(f"Audio: {e}")
    traceback.print_exc()

try:
    from neon_theme import apply_neon_theme
    print("✅ Neon theme")
except Exception as e:
    errors.append(f"Neon: {e}")
    traceback.print_exc()

try:
    from gui import MainWindow
    print("✅ GUI MainWindow")
except Exception as e:
    errors.append(f"GUI: {e}")
    traceback.print_exc()

try:
    from greeting_screen import GreetingManager
    print("✅ Greeting")
except Exception as e:
    errors.append(f"Greeting: {e}")
    traceback.print_exc()

try:
    import database
    database.init_db()
    print("✅ Database")
except Exception as e:
    errors.append(f"DB: {e}")
    traceback.print_exc()

print()
if errors:
    print("❌ ERRORS:")
    for e in errors:
        print(f"  {e}")
else:
    print("✅ All checks passed!")
