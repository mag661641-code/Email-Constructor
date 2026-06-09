import streamlit as st
import os
import requests
import random
import streamlit.components.v1 as components
import re

# ==========================================
# 0. УМНАЯ ФУНКЦИЯ ОБРАБОТКИ ТЕКСТА
# ==========================================
def process_text_to_html(text):
    if not text: return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        item = line.strip()
        if not item:
            processed_lines.append("")
            continue
        if item.startswith(('-', '*', '•')):
            content = item[1:].strip()
            processed_lines.append(f"&bull; {content}")
        else:
            processed_lines.append(item)
    return "<br>".join(processed_lines)

# ---- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ЗНАЧКОВ ----
def make_badges(items, font_size="11px", padding="3px 8px"):
    span_style = (
        f"display:inline-block;"
        f"background:#F6F7FC;"
        f"border:1px solid #d0dff5;"
        f"color:#3D4858;"
        f"font-size:{font_size};"
        f"font-weight:400;"
        f"padding:{padding};"
        f"border-radius:4px;"
        f"margin:0 4px 6px 0;"
        f"white-space:nowrap;"
        f"font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;"
    )
    return "".join(f'<span style="{span_style}">{item.strip()}</span>' for item in items if item.strip())
 
# ---- ПРЕДНАСТРОЕННЫЕ НАБОРЫ ГОСТОВ ----
GOST_PRESETS = {
    "Труба профильная": ["ГОСТ 8639-82", "ГОСТ 8645-82", "ГОСТ 30245-2003", "ГОСТ 13663-86", "ГОСТ 25577-83", "EN 10219", "СТО 00186217"],
    "Труба круглая": ["ГОСТ 8734-75", "ГОСТ 8732-78", "ГОСТ 10704-91", "ГОСТ 10705-80", "ГОСТ 3262-75"],
    "Лист стальной": ["ГОСТ 19903-90", "ГОСТ 14637-89", "ГОСТ 16523-97", "ГОСТ 1577-93"],
    "Уголок": ["ГОСТ 8509-93", "ГОСТ 8510-86", "ТУ 14-2-686"],
    "Двутавр": ["ГОСТ 8239-89", "ГОСТ 26020-83", "СТО АСЧМ 20-93"],
    "Швеллер": ["ГОСТ 8240-97", "ГОСТ 6526-68"],
    "Арматура": ["ГОСТ 5781-82", "ГОСТ 10884-94", "ГОСТ Р 52544-2006"],
    "Своя настройка": []
}
 
# ---- ПРЕДНАСТРОЕННЫЕ НАБОРЫ РАЗМЕРОВ ----
SIZE_PRESETS = {
    "Труба профильная": ["15×15", "20×20", "40×40", "60×40", "60×60", "80×80", "100×100", "120×120", "140×140", "150×150", "160×160", "180×180", "200×200", "300×300", "и другие"],
    "Труба круглая": ["Ø 15", "Ø 20", "Ø 25", "Ø 32", "Ø 40", "Ø 50", "Ø 57", "Ø 76", "Ø 89", "Ø 108", "Ø 159", "Ø 219", "и другие"],
    "Лист стальной": ["1×1000", "1,5×1250", "2×1500", "3×1500", "4×1500", "5×1500", "6×1500", "8×1500", "10×1500", "12×1500", "16×1500", "20×1500", "и другие"],
    "Уголок": ["25×25", "32×32", "40×40", "45×45", "50×50", "63×63", "70×70", "75×75", "80×80", "100×100", "125×125", "150×150", "и другие"],
    "Двутавр": ["10", "12", "14", "16", "18", "20", "24", "27", "30", "36", "40", "45", "50", "55", "60", "и другие"],
    "Швеллер": ["5П", "6,5П", "8П", "10П", "12П", "14П", "16П", "18П", "20П", "22П", "24П", "27П", "30П", "и другие"],
    "Арматура": ["6", "8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36", "40", "и другие"],
    "Своя настройка": []
}

# ==========================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
# ==========================================
st.set_page_config(layout="wide", page_title="Стальметурал | Конструктор", initial_sidebar_state="expanded")

if 'mode' not in st.session_state: st.session_state.mode = None
if 'cute_img' not in st.session_state: st.session_state.cute_img = None
if 'theme' not in st.session_state: st.session_state.theme = "dark"
if 'gost_tags' not in st.session_state: st.session_state.gost_tags = []
if 'size_tags' not in st.session_state: st.session_state.size_tags = []

# ==========================================
# 2. УМНЫЙ CSS
# ==========================================
base_styles = """
<style>
    #MainMenu {visibility: hidden;} 
    header {visibility: hidden; height: 0px !important;} 
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stButton > button {
        height: 90px !important; border-radius: 12px !important;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: center !important;
        gap: 5px !important; white-space: pre-wrap !important;
        text-align: center !important; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .stButton > button:hover { transform: translateY(-5px) !important; border-color: #1e69da !important; box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1) !important; }
    .stButton > button div p { font-size: 14px !important; font-weight: 700 !important; }
    [data-testid="column"]:last-child button { height: 25px !important; line-height: 1 !important; padding: 0 !important; }
    div.stButton > button[kind="primary"] { background-color: #1e69da !important; color: white !important; height: 55px !important; border: none !important; font-weight: 700 !important; text-transform: uppercase; transform: none !important; }
</style>
"""

if st.session_state.theme == "light":
    theme_css = """<style>
    [data-testid="stAppViewContainer"] { background-color: #F8F9FA; color: #111827; } 
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; } 
    .stButton > button { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; color: #111827 !important; } 
    .stButton > button:hover { color: #1e69da !important; background-color: #F3F4F6 !important; } 
    h1, h2, h3, label, p, .stMarkdown { color: #111827 !important; } 
    
    /* --- ИСПРАВЛЕНИЕ ДЛЯ ПОЛЕЙ И ВЫПАДАЮЩИХ СПИСКОВ (SELECTBOX) --- */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div { 
        background-color: #FFFFFF !important; 
        color: #111827 !important; 
        border: 1px solid #D1D5DB !important; 
    }
    /* Убираем черный фон у selectbox при наведении/убирании курсора */
    div[data-baseweb="select"] > div:hover { background-color: #F8F9FA !important; border-color: #1e69da !important; }
    
    /* Фиксим выпадающее меню списка */
    ul[data-baseweb="menu"] { background-color: #FFFFFF !important; }
    ul[data-baseweb="menu"] li { color: #111827 !important; }
    ul[data-baseweb="menu"] li:hover { background-color: #F3F4F6 !important; }

    button[data-baseweb="tab"] p { color: #6B7280 !important; font-weight: 600 !important; } 
    button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    </style>"""
else:
    theme_css = """<style>
    [data-testid="stAppViewContainer"] { background-color: #0F1117; color: #F3F4F6; } 
    [data-testid="stSidebar"] { background-color: #161922; } 
    .stButton > button { background-color: #1A1C24 !important; border: 1px solid #3e4452 !important; color: #F3F4F6 !important; } 
    h1, h2, h3, label, p { color: #F3F4F6 !important; } 
    
    /* --- ИСПРАВЛЕНИЕ ДЛЯ ПОЛЕЙ И ВЫПАДАЮЩИХ СПИСКОВ (SELECTBOX) --- */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div { 
        background-color: #1F2937 !important; 
        color: #F3F4F6 !important; 
        border: 1px solid #374151 !important; 
    }
    div[data-baseweb="select"] > div:hover { background-color: #374151 !important; }

    ul[data-baseweb="menu"] { background-color: #1F2937 !important; }
    ul[data-baseweb="menu"] li { color: #F3F4F6 !important; }
    ul[data-baseweb="menu"] li:hover { background-color: #374151 !important; }

    button[data-baseweb="tab"] p { color: #9CA3AF !important; font-weight: 600 !important; } 
    button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    </style>"""
    
st.markdown(base_styles, unsafe_allow_html=True)
st.markdown(theme_css, unsafe_allow_html=True)

# ==========================================
# 3. ЛОГИКА
# ==========================================
def get_cute_gif():
    try:
        animal = random.choice(["cat", "dog"])
        res = requests.get(f"https://api.the{animal}api.com/v1/images/search?mime_types=gif,jpg", timeout=5).json()
        return res[0]['url']
    except: return "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"

def set_mode(name):
    st.session_state.mode = name
    if name: st.session_state.cute_img = get_cute_gif()

menu_items = {
    "stock": {"title": "ПОСТУПЛЕНИЕ", "desc": "Наличие, ГОСТы"},
    "promo": {"title": "СПЕЦПРЕДЛОЖЕНИЕ", "desc": "Товары, таймер"},
    "services": {"title": "УСЛУГИ", "desc": "Обработка, резка"},
    "cases": {"title": "ОТГРУЗКИ", "desc": "Фото, статистика"},
    "expert": {"title": "ЭКСПЕРТНОЕ", "desc": "Статьи и советы"}
}

# ==========================================
# 4. ВЕРХНЯЯ ПАНЕЛЬ
# ==========================================
t_col1, t_col2 = st.columns([12, 1])
with t_col2:
    label = "☀️" if st.session_state.theme == "dark" else "🌙"
    if st.button(label):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ==========================================
# 5. ГЛАВНОЕ МЕНЮ
# ==========================================
if st.session_state.mode is None:
    st.markdown("<h1 style='text-align:center;'>Конструктор рассылок</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; opacity: 0.7;'>Выберите шаблон</p><br>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    for i, (m_id, info) in enumerate(menu_items.items()):
        with cols[i]:
            btn_label = f"{info['title']}\n{info['desc']}"
            if st.button(btn_label, key=m_id, use_container_width=True):
                set_mode(m_id)
                st.rerun()
else:
    # ==========================================
    # 6. РЕДАКТОР
    # ==========================================
    mode = st.session_state.mode
    data = {}
    
    with st.sidebar:
        st.button("« В ГЛАВНОЕ МЕНЮ", on_click=set_mode, args=(None,), use_container_width=True)
        st.write("---")
        if st.session_state.cute_img:
            st.image(st.session_state.cute_img, use_container_width=True)
            st.caption("Ваша психологическая поддержка")

    st.title(f"Шаблон: {menu_items[mode]['title']}")
    tabs = st.tabs(["Контакты", "Баннер", "Тексты", "Блоки", "Эксперт"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        data['EMAIL'] = c1.text_input("Email филиала", "msk@stalmetural.ru")
        data['PHONE'] = c1.text_input("Телефон филиала", "+7 (499) 130-60-28")
        
        data['PHONE_DIGITS'] = "".join(filter(str.isdigit, data['PHONE']))
        if not data['PHONE_DIGITS'].startswith('+'):
            data['PHONE_DIGITS'] = "+" + data['PHONE_DIGITS']
        data['PHONE_LINK'] = f"tel:{data['PHONE_DIGITS']}"

        data['CITY_IN'] = c2.text_input("Город (в чем? где?)", "в Москве")
        data['LINK_LOGO'] = c2.text_input("Ссылка при клике на логотип", "https://stalmetural.ru/")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        data['LINK_CATALOG'] = col_m1.text_input("Ссылка 'Каталог'", "https://stalmetural.ru/catalog/")
        data['LINK_COMPANY'] = col_m2.text_input("Ссылка 'О компании/Кейсы'", "https://stalmetural.ru/about/")
        data['LINK_DELIVERY'] = col_m3.text_input("Ссылка 'Доставка'", "https://stalmetural.ru/delivery/")
        
        data['FOOTER_ADDRESS'] = st.text_input("Адрес в футере", "ООО \"СМУ\", г. Екатеринбург, ул. Машиностроителей 10")
        data['UnsubscribeUrl'], data['webversion'], data['email'] = "{{UnsubscribeUrl}}", "{{webversion}}", "{{email}}"

    with tabs[1]:
        data['PREHEADER_TEXT'] = st.text_input("Прехедер (текст в почтовике перед открытием)", "Узнайте подробности в письме...")
        st.markdown("---")
        
        if mode == "promo":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере (начинать с "НА")', "НА КВАДРАТ ЧУГУННЫЙ")
            data['DISCOUNT_LABEL'] = st.text_input("Метка скидки", "СКИДКА 10%")
        elif mode == "stock":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', "ТРУБА ПРОФИЛЬНАЯ")
        elif mode == "cases":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', "НУЖЕН МЕТАЛЛ ТОЧНО В СРОК И ПО ГОСТУ?")
            data['HERO_BG_IMG'] = st.text_input("Фоновая картинка всей шапки", "https://cp.unisender.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=6onoffr9spwg3rauf9n3p3mtxkb98nhpzugtp36yr4smm1mnuid9xzaqh6qaw8wyyxn6ircwydoatz4yhkeno9cb5u3mum5c3c8j5f9pxcd4q95izr51ecpifdwzh6n19h4rnygkteo34fcmjp5hwypi1hh")
            data['HERO_IMG'] = st.text_input("Картинка отгрузки (справа)", "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=633kxjmua5h3e6auf9n3p3mtxkbqyuz5g9t4bxmiwacn4se1m7mm8f3xb9kfj4sdqs7u6wy3p67hniwanz5qzpz6e3oafgod1gfpiyt35tefhp8sjg7t3fqc9p5i93btrk54ju1mbjtetk")
            data['HERO_BTN_LINK'] = st.text_input("Ссылка кнопки 'Рассчитать проект'", data.get('LINK_CATALOG', ''))        
        elif mode == "expert":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', "БЕСШОВНАЯ ИЛИ ЭЛЕКТРОСВАРНАЯ")
            data['HERO_IMG'] = st.text_input("Картинка справа", "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=6uyisxkcb9z7eaauf9n3p3mtxknbsdqxp466f8gerep3qqo3qg9gbanpmbuqopttjmnzyzspdqyqxfm55dgtdc1xhua6ni8nrnmqq1qo538z6idf768zyjwfpoohe8gbci4z3phict9wqfg496t8gqbqy5r6b3tjcs34m6na")
            data['HERO_BTN_LINK'] = st.text_input("Ссылка кнопки 'Читать подробнее'", data.get('LINK_CATALOG', ''))
        else:
            data['HERO_TITLE'] = st.text_input('Заголовок баннера', "МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ")

    with tabs[2]:
        st.markdown("""
        <div style="background-color: #1e69da33; padding: 10px; border-radius: 5px; border: 1px solid #1e69da; margin-bottom: 15px;">
            <strong>Как оформлять текст:</strong><br>
            • <b>**текст**</b> — жирный | <b>- пункт</b> — список | <b>Enter</b> — новая строка
        </div>
        """, unsafe_allow_html=True)

        if mode == "promo":
            st.subheader("📝 Главная статья")
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", "Снижаем стоимость на партию")
            t_pre_raw = st.text_area("Текст ДО ссылки", "Мы открываем **спецпредложение**...")
            col_a1, col_a2 = st.columns(2)
            a_word = col_a1.text_input("Слово-ссылка", "партию квадрата")
            a_link = col_a2.text_input("Куда ведет", "https://stalmetural.ru/catalog/")
            t_post_raw = st.text_area("Текст ПОСЛЕ ссылки", "из наличия.")
            data['TEXT_BODY'] = f'{process_text_to_html(t_pre_raw)} <a href="{a_link}" style="text-decoration:none; color:#1e69da; font-weight:bold;">{a_word}</a> {process_text_to_html(t_post_raw)}'
            
            st.markdown("---")
            st.subheader("📎 Блок P.S.")
            ps_c = st.columns(3)
            with ps_c[0]: n1 = st.text_input("Товар 1", "чугунные круги")
            with ps_c[1]: n2 = st.text_input("Товар 2", "втулки")
            with ps_c[2]: n3 = st.text_input("Товар 3", "услуги")
            data['PS_BLOCK'] = f'P.S. Также в наличии <a href="{data["LINK_CATALOG"]}">{n1}</a>, <a href="{data["LINK_CATALOG"]}">{n2}</a> и <a href="{data["LINK_CATALOG"]}">{n3}</a>. Напишите нам.'
       
        elif mode == "expert":
            st.subheader("📝 Основная статья блога")
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", "Выбираем трубу без переплат")
            text_body_raw = st.text_area(
                "Текст статьи (используйте ** для жирного и - для списков)", 
                height=250, 
                value="Часто в смету закладывают дорогую бесшовную трубу там, где можно безопасно использовать электросварную.\n\n**Где можно сэкономить до 40%?**\nЭлектросварная труба (ЭСВ) идеально подходит для легких металлоконструкций, заборов и систем ЖКХ с низким давлением.\n\n**Где рисковать нельзя?**\nВ нефтегазовой промышленности необходима только бесшовная труба (БШ)."
            )
            data['TEXT_BODY'] = process_text_to_html(text_body_raw)
            data['TEXT_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Связаться с нами'", "https://stalmetural.ru/contacts/")

        elif mode == "stock":
            st.subheader("Текст для статьи 'Поступление'")
            data['STOCK_MAIN_TITLE'] = st.text_input("Заголовок статьи", "Склад пополнен: Профильная труба всех типоразмеров")
            stock_intro_raw = st.text_area("Вводный абзац", "Обновили складской запас профильного проката. В наличии все позиции...")
            data['STOCK_INTRO'] = process_text_to_html(stock_intro_raw)

        elif mode == "cases":
            st.subheader("Текст кейса (История успеха)")
            data['CASE_MAIN_TITLE'] = st.text_input("Главный заголовок статьи", "Металл с гарантией: проверка по ГОСТ и полный пакет документов при отгрузке")
            
            task_raw = st.text_area("Задача / Вводный текст", "Недостаточная толщина стенки, отсутствие сертификатов или дефекты поверхности могут остановить стройку на недели. В «Стальметурал» мы внедрили трехступенчатый контроль отгрузки, чтобы вы спали спокойно.", height=100)
            data['CASE_TASK'] = process_text_to_html(task_raw)
            
            steps_raw = st.text_area("Что мы сделали (Список / Буллиты)", 
                "- **Замеры перед погрузкой:** Проверяем толщину стенки и параметры металла на соответствие ГОСТу.\n"
                "- **Полная документация:** Пакет оригинальных сертификатов передается водителю сразу – никаких «дошлем почтой».\n"
                "- **Точность до миллиметра:** Собственный цех резки на ЧПУ гарантирует, что детали встанут как влитые.", height=150)
            data['CASE_STEPS'] = process_text_to_html(steps_raw)
            
            data['CASE_RESULT'] = st.text_input("Результат (выводится в рамке снизу)", "Ваш объект не будет простаивать из-за брака.")

        elif mode == "services":
            st.subheader("📝 Основной текстовый блок")
            data['TEXT_TITLE'] = st.text_input("Заголовок раздела", "Больше, чем просто продажа металла")

            text_body_raw = st.text_area(
                "Основной текст письма",
                height=300,
                value=(
                    "Закупка металла «с запасом» и ручная подрезка на объекте — это **скрытые убытки вашего проекта**. "
                    "Вы переплачиваете за лишний вес при доставке и тратите оплачиваемое время рабочих на подгонку деталей.\n\n"
                    "Мы предлагаем перейти на **готовую компонентную базу**. Вы получаете детали, нарезанные точно в размер.\n\n"
                    "**Как изменится ваша смета и процесс:**\n\n"
                    "- **Оплата за результат:** вы платите только за готовые детали, а не за обрезки и стружку.\n"
                    "- **Оптимизация логистики:** машина везет только готовые к монтажу изделия.\n"
                    "- **Монтаж с колес:** никакой ручной работы — сборка начинается сразу после разгрузки.\n"
                    "- **Заводская точность:** лазерная и плазменная резка исключают брак.\n\n"
                    "Из-за высокого спроса производственные мощности цеха **ограничены**. Свяжитесь с нами сегодня."
                )
            )
            data['TEXT_BODY'] = process_text_to_html(text_body_raw)

        
        else:
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", "Заголовок")
            t_raw = st.text_area("Текст", "Текст...")
            data['TEXT_BODY'] = process_text_to_html(t_raw)
            data['TEXT_BTN_LINK'] = st.text_input("Ссылка для кнопки", "https://stalmetural.ru/contacts/")

    with tabs[3]:
                # --- ВСЕ НАСТРОЙКИ БЛОКОВ ---
        if mode == "cases":
            st.subheader("Настройка блоков (Товары, Услуги, Статистика)")
            with st.expander("1. Участвовали в отгрузке (4 товара)"):
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'PROD_{i}_TITLE'] = col1.text_input("Название", key=f"pr_t{i}")
                    data[f'PROD_{i}_PRICE'] = col2.text_input("Цена (Например: 39 500₽/т)", key=f"pr_p{i}")
                    data[f'PROD_{i}_DESC'] = st.text_area("Описание (ГОСТ, марка)", key=f"pr_d{i}", height=70)
                    col3, col4 = st.columns(2)
                    data[f'PROD_{i}_IMG'] = col3.text_input("URL картинки товара", key=f"pr_i{i}")
                    data[f'PROD_{i}_LINK'] = col4.text_input("Ссылка на каталог", data.get('LINK_CATALOG', ''), key=f"pr_l{i}")
                    st.markdown("---")
                
                data['PROD_EXTRA_TEXT'] = st.text_input("Текст под товарами", "+ еще 8 позиций сопутствующего проката и метизов укомплектованы в эту же машину")
                data['ALL_PROD_LINK'] = st.text_input("Ссылка кнопки 'Посмотреть весь сортамент'", data.get('LINK_CATALOG', ''))

            with st.expander("2. Не тратьте время на подгонку (3 Услуги)"):
                data['SERVICES_TITLE'] = st.text_input("Главный заголовок услуг", "Не тратьте время на подгонку на объекте")
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'SERV_{i}_TITLE'] = col1.text_input("Название услуги", key=f"srv_t{i}")
                    data[f'SERV_{i}_DESC'] = col2.text_input("Краткое описание", key=f"srv_d{i}")
                    col3, col4 = st.columns(2)
                    data[f'SERV_{i}_IMG'] = col3.text_input("URL картинки услуги", key=f"srv_i{i}")
                    data[f'SERV_{i}_LINK'] = col4.text_input("Ссылка 'Заказать'", data.get('LINK_CATALOG', ''), key=f"srv_l{i}")
                    st.markdown("---")

        elif mode == "expert":
            st.subheader("Настройка блоков (Трубы, Наличие, Отгрузки)")
            
            with st.expander("1. Какой товар подходит под ваши задачи? (2 колонки)", expanded=True):
                data['PIPE_SECTION_TITLE'] = st.text_input("Заголовок", "Какой товар подходит под ваши задачи?")
                for i in range(1, 3):
                    st.markdown(f"**Труба №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'PIPE_{i}_TITLE'] = col1.text_input("Название", key=f"expt_t{i}")
                    data[f'PIPE_{i}_PRICE'] = col2.text_input("Цена (Например: 100 000₽/т)", key=f"expt_p{i}")
                    pipe_desc_raw = st.text_area("Описания и ГОСТы (используйте - для списков)", key=f"expt_d{i}", height=100)
                    data[f'PIPE_{i}_DESC'] = process_text_to_html(pipe_desc_raw)
                    col3, col4 = st.columns(2)
                    data[f'PIPE_{i}_IMG'] = col3.text_input("URL картинки", key=f"expt_i{i}")
                    data[f'PIPE_{i}_LINK'] = col4.text_input("Ссылка на каталог", data.get('LINK_CATALOG', ''), key=f"expt_l{i}")
                    st.markdown("---")

            with st.expander("2. Также в наличии на складе (3 товара)"):
                data['STOCK_SECTION_TITLE'] = st.text_input("Заголовок блока наличия", "Также в наличии на складе")
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'STOCK_{i}_TITLE'] = col1.text_input("Название", key=f"exst_t{i}")
                    data[f'STOCK_{i}_PRICE'] = col2.text_input("Цена", key=f"exst_p{i}")
                    data[f'STOCK_{i}_DESC'] = st.text_input("Краткое описание", key=f"exst_d{i}")
                    col3, col4 = st.columns(2)
                    data[f'STOCK_{i}_IMG'] = col3.text_input("URL картинки товара", key=f"exst_i{i}")
                    data[f'STOCK_{i}_LINK'] = col4.text_input("Ссылка", data.get('LINK_CATALOG', ''), key=f"exst_l{i}")
                    st.markdown("---")

            with st.expander("3. Наши отгрузки (2 кейса)"):
                data['SHIP_SECTION_TITLE'] = st.text_input("Заголовок блока отгрузок", "Наши отгрузки")
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'SHIP_{i}_TITLE'] = col1.text_input("Что отгрузили", key=f"exsh_t{i}")
                    data[f'SHIP_{i}_DATE'] = col2.text_input("Дата", key=f"exsh_dt{i}")
                    data[f'SHIP_{i}_DESC'] = st.text_input("Описание", key=f"exsh_d{i}")
                    col3, col4 = st.columns(2)
                    data[f'SHIP_{i}_IMG'] = col3.text_input("URL картинки отгрузки", key=f"exsh_i{i}")
                    data[f'SHIP_{i}_LINK'] = col4.text_input("Ссылка", data.get('LINK_CATALOG', ''), key=f"exsh_l{i}")
                    st.markdown("---")

        elif mode == "stock":
            st.subheader("Настройка контента Поступления")
 
            with st.expander("1. Описание и Буллиты"):
                data['TEXT_TITLE'] = st.text_input("Заголовок текста", "Труба всех типоразмеров")
                data['TEXT_BODY'] = st.text_area("Вводный текст", "Обновили складской запас...")
                for i in range(1, 4):
                    data[f'BULLET_{i}'] = st.text_input(f"Пункт списка {i}", key=f"st_blt{i}")

           # ===================================================
            # БЛОК 2: ГОСТЫ И РАЗМЕРЫ
            # ===================================================
            with st.expander("2. Технический блок (ГОСТы и Размеры)"):
 
                # ========== БЛОК ГОСТОВ ==========
                st.markdown("##### Стандарты производства (ГОСТ / ТУ)")
 
                gost_preset = st.selectbox(
                    "Быстрый выбор по типу металла",
                    options=list(GOST_PRESETS.keys()),
                    key="gost_preset_select"
                )
 
                if gost_preset != "Своя настройка":
                    if st.button("↺ Загрузить стандарты для выбранного типа", key="load_gost"):
                        st.session_state.gost_tags = GOST_PRESETS[gost_preset].copy()
                        st.rerun()
 
                if st.session_state.gost_tags:
                    st.markdown("**Текущие стандарты** (кликните на ячейку, чтобы удалить):")
                    cols_g = st.columns(4)
                    tags_to_remove_g = []
                    for idx, tag in enumerate(st.session_state.gost_tags):
                        with cols_g[idx % 4]:
                            if st.button(f"{tag} ✕", key=f"del_gost_{idx}", use_container_width=True):
                                tags_to_remove_g.append(tag)
                    for t in tags_to_remove_g:
                        st.session_state.gost_tags.remove(t)
                        st.rerun()
                else:
                    st.info("Список стандартов пуст. Добавьте вручную ниже.")
 
                col_g1, col_g2 = st.columns([3, 1])
                new_gost = col_g1.text_input("Добавить стандарт вручную", placeholder="Например: ГОСТ 8639-82 или EN 10219", key="new_gost_input")
                if col_g2.button("＋ Добавить", key="add_gost_btn", use_container_width=True):
                    if new_gost.strip() and new_gost.strip() not in st.session_state.gost_tags:
                        st.session_state.gost_tags.append(new_gost.strip())
                        st.rerun()
 
                data['GOST_BLOCK'] = make_badges(st.session_state.gost_tags, font_size="11px", padding="3px 8px")
 
                st.markdown("---")
 
                # ========== БЛОК РАЗМЕРОВ ==========
                st.markdown("##### Ходовые размеры в наличии (мм)")
 
                size_preset = st.selectbox(
                    "Быстрый выбор размеров по типу",
                    options=list(SIZE_PRESETS.keys()),
                    key="size_preset_select"
                )
 
                if size_preset != "Своя настройка":
                    if st.button("↺ Загрузить размеры для выбранного типа", key="load_size"):
                        st.session_state.size_tags = SIZE_PRESETS[size_preset].copy()
                        st.rerun()
 
                if st.session_state.size_tags:
                    st.markdown("**Текущие размеры** (кликните на ячейку, чтобы удалить):")
                    cols_s = st.columns(5)
                    tags_to_remove_s = []
                    for idx, tag in enumerate(st.session_state.size_tags):
                        with cols_s[idx % 5]:
                            if st.button(f"{tag} ✕", key=f"del_size_{idx}", use_container_width=True):
                                tags_to_remove_s.append(tag)
                    for t in tags_to_remove_s:
                        st.session_state.size_tags.remove(t)
                        st.rerun()
                else:
                    st.info("Список размеров пуст. Добавьте вручную ниже.")
 
                col_s1, col_s2 = st.columns([3, 1])
                new_size = col_s1.text_input("Добавить размер вручную", placeholder="Например: 80×80 или Ø 57", key="new_size_input")
                if col_s2.button("＋ Добавить", key="add_size_btn", use_container_width=True):
                    if new_size.strip() and new_size.strip() not in st.session_state.size_tags:
                        st.session_state.size_tags.append(new_size.strip())
                        st.rerun()
 
                data['SIZE_BLOCK'] = make_badges(st.session_state.size_tags, font_size="12px", padding="4px 10px")
 
                # Предпросмотр
                st.markdown("---")
                st.markdown("**Предпросмотр блока в письме:**")
                preview_html = f"""
                <div style="border:1px solid #d0dff5;border-radius:8px;padding:20px;background:#fff;font-family:Arial,sans-serif;">
                    <div style="font-size:11px;font-weight:700;color:#282824;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;">Стандарты производства (ГОСТ / ТУ)</div>
                    <div style="line-height:2;margin-bottom:20px;">{data['GOST_BLOCK']}</div>
                    <div style="height:1px;background:#d0dff5;margin-bottom:20px;"></div>
                    <div style="font-size:11px;font-weight:700;color:#282824;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;">Ходовые размеры в наличии (мм)</div>
                    <div style="line-height:2;">{data['SIZE_BLOCK']}</div>
                </div>
                """
                components.html(preview_html, height=280)

            with st.expander("3. Также в наличии (3 товара)"):
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    data[f'T_{i}'] = st.text_input("Название", key=f"st_t{i}")
                    data[f'D_{i}'] = st.text_input("Описание", key=f"st_d{i}")
                    data[f'P_{i}'] = st.text_input("Цена", key=f"st_p{i}")
                    data[f'OLD_P_{i}'] = st.text_input("Старая цена (для зачеркивания)", key=f"st_op{i}")
                    data[f'I_{i}'] = st.text_input("URL картинки", key=f"st_i{i}")
                    data[f'L_{i}'] = st.text_input("Ссылка", data['LINK_CATALOG'], key=f"st_l{i}")

            with st.expander("4. Наши отгрузки (2 кейса)"):
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    data[f'CASE_TITLE_{i}'] = st.text_input("Заголовок кейса", key=f"st_ct{i}")
                    data[f'CASE_DESC_{i}'] = st.text_input("Описание кейса", key=f"st_cd{i}")
                    data[f'CASE_DATE_{i}'] = st.text_input("Дата", key=f"st_cdt{i}")
                    data[f'CASE_IMG_{i}'] = st.text_input("URL картинки кейса", key=f"st_ci{i}")

        elif mode == "promo":
            st.subheader("Товарные и структурные блоки")
            
            # --- 1. ПЕРСОНАЛЬНЫЕ ЦЕНЫ (Сетка 2х2) ---
            with st.expander("1. Ваши персональные цены (Сетка 2x2)", expanded=True):
                
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    data[f'T_{i}'] = col1.text_input("Название", key=f"p_t{i}")
                    data[f'P_{i}'] = col2.text_input("Цена (со скидкой)", key=f"p_p{i}")
                    data[f'OLD_P_{i}'] = col3.text_input("Старая цена", key=f"p_op{i}")
                    
                    col_d1, col_d2 = st.columns(2)
                    data[f'D_{i}'] = col_d1.text_input("Описание (кратко)", key=f"p_d{i}")
                    data[f'I_{i}'] = col_d2.text_input("URL картинки", key=f"p_i{i}")
                    data[f'L_{i}'] = st.text_input("Ссылка", data['LINK_CATALOG'], key=f"p_l{i}")
                    st.markdown("---")

            # --- 2. ФИКСИРОВАННЫЕ ЦЕНЫ (Сетка 1х3 - малые) ---
            with st.expander("2. Также зафиксировали цены (Малые блоки 1x3)"):
                
                for i in range(1, 4):
                    st.markdown(f"**Малый товар №{i}**")
                    col1, col2 = st.columns([2, 1])
                    data[f'SMALL_T_{i}'] = col1.text_input("Название", key=f"sm_t{i}")
                    data[f'SMALL_P_{i}'] = col2.text_input("Цена", key=f"sm_p{i}")
                    data[f'SMALL_D_{i}'] = st.text_input("Описание (ГОСТ, сталь)", key=f"sm_d{i}")
                    
                    col_i1, col_i2 = st.columns(2)
                    data[f'SMALL_I_{i}'] = col_i1.text_input("URL картинки", key=f"sm_img{i}")
                    data[f'SMALL_L_{i}'] = col_i2.text_input("Ссылка", data['LINK_CATALOG'], key=f"sm_link{i}")
                    st.markdown("---")

            # --- 3. КАТЕГОРИИ (1х2) ---
            with st.expander("3. Категории товаров"):
                data['CAT_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Категории товаров")
                for i in range(1, 3):
                    st.markdown(f"**Категория №{i}**")
                    data[f'CAT_TITLE_{i}'] = st.text_input("Заголовок категории", key=f"ct_t{i}")
                    data[f'CAT_DESC_{i}'] = st.text_area("Описание категории", key=f"ct_d{i}")
                    
                    col_c1, col_c2 = st.columns(2)
                    data[f'CAT_IMG_{i}'] = col_c1.text_input("URL картинки категории", key=f"ct_i{i}")
                    data[f'CAT_LINK_{i}'] = col_c2.text_input("Ссылка категории", data['LINK_CATALOG'], key=f"ct_l{i}")
                    st.markdown("---")

            # --- 4. ОТГРУЗКИ (1х2) ---
            with st.expander("4. Наши отгрузки за неделю"):
                data['CASE_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Наши отгрузки")
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    col_k1, col_k2 = st.columns([2, 1])
                    data[f'CASE_TITLE_{i}'] = col_k1.text_input("Заголовок отгрузки", key=f"cs_t{i}")
                    data[f'CASE_DATE_{i}'] = col_k2.text_input("Дата", key=f"cs_dt{i}")
                    
                    data[f'CASE_DESC_{i}'] = st.text_input("Описание (что отгрузили)", key=f"cs_d{i}")
                    data[f'CASE_IMG_{i}'] = st.text_input("URL фото отгрузки", key=f"cs_i{i}")
                    st.markdown("---")

        elif mode == "services":
            st.subheader("⚙️ Настройка блоков шаблона Услуги")

            # --- БЛОК 1: ТЕХНОЛОГИИ (3 карточки) ---
            with st.expander("1. Технологии, которые сэкономят ваше время", expanded=True):
                data['TECH_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Технологии, которые сэкономят ваше время")
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'T_{i}'] = col1.text_input("Название", key=f"sv_t{i}")
                    data[f'I_{i}'] = col2.text_input("URL картинки", key=f"sv_i{i}")
                    data[f'D_{i}'] = st.text_input("Описание", key=f"sv_d{i}")
                    data[f'L_{i}'] = st.text_input("Ссылка кнопки 'Заказать'", data.get('LINK_CATALOG', ''), key=f"sv_l{i}")
                    st.markdown("---")

# --- БЛОК 2: СОРТАМЕНТ (2 товара) ---
            with st.expander("2. Сортамент под ваши чертежи"):
                data['SORT_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Сортамент под ваши чертежи")
                sort_intro_raw = st.text_area(
                    "Вводный текст",
                    "Поставляем прокат напрямую с заводов и сразу передаём в заготовительный цех. "
                    "Выбирайте качественную основу, которую наши мастера превратят в идеальные детали по вашим размерам"
                )
                data['SORT_INTRO'] = process_text_to_html(sort_intro_raw)
                data['SORT_BTN_LINK'] = st.text_input("Ссылка кнопки 'Смотреть все категории'", data.get('LINK_CATALOG', ''))

                for i in range(1, 3):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'SORT_T_{i}'] = col1.text_input("Название", key=f"sr_t{i}")
                    data[f'SORT_I_{i}'] = col2.text_input("URL картинки", key=f"sr_i{i}")
                    
                    # === ДОБАВИЛИ УМНЫЙ ТЕКСТ СЮДА ===
                    desc_raw = st.text_area("Описание (можно списком через - )", key=f"sr_d{i}", height=120)
                    data[f'SORT_D_{i}'] = process_text_to_html(desc_raw)
                    # ==================================
                    
                    col3, col4 = st.columns(2)
                    data[f'SORT_SPEC_{i}'] = col3.text_input("Характеристика (Размер / Сечение)", key=f"sr_sp{i}")
                    data[f'SORT_L_{i}'] = col4.text_input("Ссылка кнопки 'Узнать цену'", data.get('LINK_CATALOG', ''), key=f"sr_l{i}")
                    st.markdown("---")

            # --- БЛОК 3: ОТГРУЗКИ (2 кейса) ---
            with st.expander("3. Монтаж без задержек: отгружаем точно в срок"):
                data['SHIP_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Монтаж без задержек: отгружаем точно в срок")
                for i in range(1, 3):
                    st.markdown(f"**Отгрузка №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'SHIP_T_{i}'] = col1.text_input("Название товара", key=f"sh_t{i}")
                    data[f'SHIP_DATE_{i}'] = col2.text_input("Дата", key=f"sh_dt{i}")
                    data[f'SHIP_D_{i}'] = st.text_input("Описание", key=f"sh_d{i}")
                    data[f'SHIP_I_{i}'] = st.text_input("URL фото отгрузки", key=f"sh_i{i}")
                    st.markdown("---")



        else:
            st.info("Блоки для данного шаблона настраиваются индивидуально. Перейдите в другой шаблон.")

    with tabs[4]:
        st.info("Блок Алины зафиксирован в дизайне. Здесь меняется только ссылка кнопки.")
        data['ALINA_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Рассчитать смету'", "https://stalmetural.ru/contacts/")

    st.write("---")
    if st.button("СОБРАТЬ ФИНАЛЬНЫЙ HTML", type="primary", use_container_width=True):
        file_name = f"template_{mode}.html"
        file_path = os.path.join("templates", file_name)
        if not os.path.exists(file_path): file_path = file_name
        
        try:
            with open(file_path, "r", encoding="utf-8") as f: 
                html = f.read()
            
            # ЗАМЕНА ПЕРЕМЕННЫХ (Исправлен баг "if val", теперь заменяет даже пустые)
            for key, val in data.items():
                replacement = str(val) if val else ""
                html = html.replace(f"{{{{{key}}}}}", replacement)
            
            st.success("Готово!")
            components.html(html, height=800, scrolling=True)
            with st.expander("Скопировать код"): 
                st.code(html, language="html")
        except Exception as e: 
            st.error(f"Файл шаблона `{file_name}` не найден или произошла ошибка! {e}")
