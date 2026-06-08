# Скрипт показывает какие alt нужно заменить в template_expert.html
# Запусти его рядом с файлом шаблона

replacements = {
    'alt="Сравнение бесшовных и электросварных труб от Стальметурал" title="Сравнение бесшовных и электросварных труб от Стальметурал"':
        'alt="{{HERO_IMG_ALT}}" title="{{HERO_IMG_ALT}}"',
    
    'alt="{{SHIP_2_TITLE}}" title="{{SHIP_2_TITLE}}"':          # баг на PIPE_1
        'alt="{{PIPE_1_ALT}}" title="{{PIPE_1_ALT}}"',
    
    'alt="Труба электросварная" title="Труба электросварная"':
        'alt="{{PIPE_2_ALT}}" title="{{PIPE_2_ALT}}"',
    
    'alt="Лист горячекатаный" \ntitle="Лист горячекатаный"':
        'alt="{{STOCK_1_ALT}}" \ntitle="{{STOCK_1_ALT}}"',
    
    'alt="Швеллер гнутый" title="Швеллер гнутый"':
        'alt="{{STOCK_2_ALT}}" title="{{STOCK_2_ALT}}"',
    
    'alt="Отвод стальной" \ntitle="Отвод стальной"':
        'alt="{{STOCK_3_ALT}}" \ntitle="{{STOCK_3_ALT}}"',
    
    # SHIP блоки уже используют {{SHIP_1_TITLE}} и {{SHIP_2_TITLE}} — это нормально,
    # но лучше разделить alt и title на отдельные переменные:
    'alt="{{SHIP_1_TITLE}}" title="{{SHIP_1_TITLE}}"':
        'alt="{{SHIP_1_ALT}}" title="{{SHIP_1_ALT}}"',
    
    'alt="Трубы ВГП" title="Трубы ВГП"':
        'alt="{{SHIP_2_ALT}}" title="{{SHIP_2_ALT}}"',
}

import sys
if len(sys.argv) < 2:
    print("Использование: python fix_html.py template_expert.html")
    sys.exit(1)

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

count = 0
for old, new in replacements.items():
    if old in html:
        html = html.replace(old, new)
        count += 1
        print(f"✅ Заменено: {old[:60]}...")
    else:
        print(f"⚠️  Не найдено: {old[:60]}...")

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nГотово. Применено замен: {count}")
