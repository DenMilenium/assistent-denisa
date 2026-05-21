"""Fix all test failures automatically"""
import sys
sys.path.insert(0, '.')

from datetime import datetime

# Fix 1: NLU _semantic_match None safety
with open('voice_commands.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'def _semantic_match(text: str) -> dict:\n    """\n    Semantic scoring'
new = 'def _semantic_match(text: str) -> dict:\n    if not text:\n        return {"action": "unknown", "params": {}, "confidence": 0}\n    text_lower = text.lower()'

if old in content:
    content = content.replace(old, new)
    with open('voice_commands.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fix 1 applied: NLU NoneType safety')
else:
    print('Fix 1: already applied or pattern different')
    # Alternative: add check at start
    alt_old = 'text_lower = text.lower()'
    alt_new = 'if not text:\n        return {"action": "unknown", "params": {}, "confidence": 0}\n    text_lower = text.lower()'
    if 'def _semantic_match' in content and alt_old in content.split('def _semantic_match')[-1].split(':')[0]:
        # Find the first occurrence inside the function
        idx = content.find('def _semantic_match')
        func_body = content[idx:]
        first_line_end = func_body.find('\n')
        after_def = func_body[first_line_end:]
        if alt_old in after_def:
            pos = after_def.find(alt_old)
            content = content[:idx + first_line_end + 1] + after_def[:pos] + '    if not text:\n        return {"action": "unknown", "params": {}, "confidence": 0}\n' + after_def[pos:]
            with open('voice_commands.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print('Fix 1 applied (alt method)')

# Fix 2: Schedule date parsing in goals.py
with open('goals.py', 'r', encoding='utf-8') as f:
    content = f.read()

old2 = 'if row[0] and isinstance(row[0], datetime):'
new2 = '''if not row[0]:
            continue
        date_val = row[0]
        if isinstance(date_val, str):
            try:
                date_val = datetime.strptime(date_val, "%d.%m.%Y")
            except ValueError:
                continue
        if isinstance(date_val, datetime):'''

if old2 in content:
    content = content.replace(old2, new2)
    with open('goals.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fix 2 applied: Schedule date parsing')
else:
    print('Fix 2: pattern not found, trying alternative')
    # Check if already fixed
    if 'date_val = row[0]' in content:
        print('Fix 2: already applied')
    else:
        print('Fix 2: could not apply')

print()
print('All fixes processed!')
print('Run: python test_all.py to verify')
