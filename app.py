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
    /* Основной фон и боковая панель */
    [data-testid="stAppViewContainer"] { background-color: #F8F9FA; color: #111827; } 
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; } 
    
    /* Тексты */
    h1, h2, h3, label, p, .stMarkdown { color: #111827 !important; } 
    button[data-baseweb="tab"] p { color: #6B7280 !important; font-weight: 600 !important; } 
    button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    
    /* Кнопки */
    .stButton > button { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; color: #111827 !important; } 
    .stButton > button:hover { color: #1e69da !important; background-color: #F3F4F6 !important; } 
    
    /* Обычные инпуты (с видимым курсором) */
    .stTextInput input, .stTextArea textarea { 
        background-color: #FFFFFF !important; 
        color: #111827 !important; 
        caret-color: #111827 !important; 
        border: 1px solid #D1D5DB !important; 
    }
    
    /* --- ФИКС АККОРДЕОНОВ (st.expander) --- */
    [data-testid="stExpander"] { border: 1px solid #D1D5DB !important; border-radius: 8px !important; background-color: #FFFFFF !important; }
    [data-testid="stExpander"] details summary, 
    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary * { 
        background-color: #F3F4F6 !important; 
        color: #111827 !important; 
    }
    [data-testid="stExpander"] details summary p { font-weight: 600 !important; }
    [data-testid="stExpander"] details summary svg { fill: #111827 !important; }

    /* --- ФИКС СЕЛЕКТБОКСОВ (ПОЛЯ) --- */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div > div { 
        background-color: #FFFFFF !important; 
    }
    div[data-baseweb="select"] > div { border: 1px solid #D1D5DB !important; }
    div[data-baseweb="select"] > div:hover { background-color: #F8F9FA !important; border-color: #1e69da !important; }
    div[data-baseweb="select"] * { color: #111827 !important; }
    div[data-baseweb="select"] svg { fill: #111827 !important; }
    
    /* --- ФИКС ВЫПАДАЮЩЕГО СПИСКА (В ИЗОЛИРОВАННОМ СЛОЕ) --- */
    div[data-baseweb="popover"] > div { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;}
    ul[role="listbox"] { background-color: #FFFFFF !important; }
    ul[role="listbox"] li { color: #111827 !important; background-color: transparent !important; }
    ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] { background-color: #F3F4F6 !important; color: #1e69da !important; }
    </style>"""
else:
    theme_css = """<style>
    /* Основной фон и боковая панель */
    [data-testid="stAppViewContainer"] { background-color: #0F1117; color: #F3F4F6; } 
    [data-testid="stSidebar"] { background-color: #161922; border-right: 1px solid #2D3748; } 
    
    /* Тексты */
    h1, h2, h3, label, p { color: #F3F4F6 !important; } 
    button[data-baseweb="tab"] p { color: #9CA3AF !important; font-weight: 600 !important; } 
    button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    
    /* Кнопки */
    .stButton > button { background-color: #1A1C24 !important; border: 1px solid #3e4452 !important; color: #F3F4F6 !important; } 
    
    /* Обычные инпуты (с видимым курсором) */
    .stTextInput input, .stTextArea textarea { 
        background-color: #1F2937 !important; 
        color: #F3F4F6 !important; 
        caret-color: #F3F4F6 !important; 
        border: 1px solid #374151 !important; 
    }
    
    /* --- ФИКС АККОРДЕОНОВ (st.expander) --- */
    [data-testid="stExpander"] { border: 1px solid #374151 !important; border-radius: 8px !important; background-color: #0F1117 !important; }
    [data-testid="stExpander"] details summary, 
    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary * { 
        background-color: #1F2937 !important; 
        color: #F3F4F6 !important; 
    }
    [data-testid="stExpander"] details summary p { font-weight: 600 !important; }
    [data-testid="stExpander"] details summary svg { fill: #F3F4F6 !important; }

    /* --- ФИКС СЕЛЕКТБОКСОВ (ПОЛЯ) --- */
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div > div { 
        background-color: #1F2937 !important; 
    }
    div[data-baseweb="select"] > div { border: 1px solid #374151 !important; }
    div[data-baseweb="select"] > div:hover { background-color: #374151 !important; border-color: #1e69da !important; }
    div[data-baseweb="select"] * { color: #F3F4F6 !important; }
    div[data-baseweb="select"] svg { fill: #F3F4F6 !important; }

    /* --- ФИКС ВЫПАДАЮЩЕГО СПИСКА (В ИЗОЛИРОВАННОМ СЛОЕ) --- */
    div[data-baseweb="popover"] > div { background-color: #1F2937 !important; border: 1px solid #374151 !important; }
    ul[role="listbox"] { background-color: #1F2937 !important; }
    ul[role="listbox"] li { color: #F3F4F6 !important; background-color: transparent !important; }
    ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] { background-color: #374151 !important; color: #60a5fa !important; }
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
        d_email = "msk@stalmetural.ru"
        data['EMAIL'] = c1.text_input("Email филиала", placeholder=d_email) or d_email
        
        d_phone = "+7 (499) 130-60-28"
        data['PHONE'] = c1.text_input("Телефон филиала", placeholder=d_phone) or d_phone
        
        data['PHONE_DIGITS'] = "".join(filter(str.isdigit, data['PHONE']))
        if not data['PHONE_DIGITS'].startswith('+'):
            data['PHONE_DIGITS'] = "+" + data['PHONE_DIGITS']
        data['PHONE_LINK'] = f"tel:{data['PHONE_DIGITS']}"
        
        d_city = "в Москве"
        data['CITY_IN'] = c2.text_input("Город (в чем? где?)", placeholder=d_city) or d_city
        
        d_logo = "https://stalmetural.ru/"
        data['LINK_LOGO'] = c2.text_input("Ссылка при клике на логотип", placeholder=d_logo) or d_logo
        
        col_m1, col_m2, col_m3 = st.columns(3)
        d_cat = "https://stalmetural.ru/catalog/"
        data['LINK_CATALOG'] = col_m1.text_input("Ссылка 'Каталог'", placeholder=d_cat) or d_cat
        
        d_about = "https://stalmetural.ru/about/"
        data['LINK_COMPANY'] = col_m2.text_input("Ссылка 'О компании/Кейсы'", placeholder=d_about) or d_about
        
        d_deliv = "https://stalmetural.ru/delivery/"
        data['LINK_DELIVERY'] = col_m3.text_input("Ссылка 'Доставка'", placeholder=d_deliv) or d_deliv
        
        d_addr = "ООО \"СМУ\", г. Екатеринбург, ул. Машиностроителей 10"
        data['FOOTER_ADDRESS'] = st.text_input("Адрес в футере", placeholder=d_addr) or d_addr
        data['UnsubscribeUrl'], data['webversion'], data['email'] = "{{UnsubscribeUrl}}", "{{webversion}}", "{{email}}"

    with tabs[1]:
        d_pre = "Узнайте подробности в письме..."
        data['PREHEADER_TEXT'] = st.text_input("Прехедер", placeholder=d_pre) or d_pre
        st.markdown("---")
        
        if mode == "promo":
            d_ht = "НА КВАДРАТ ЧУГУННЫЙ"
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', placeholder=d_ht) or d_ht
            d_dl = "СКИДКА 10%"
            data['DISCOUNT_LABEL'] = st.text_input("Метка скидки", placeholder=d_dl) or d_dl
        elif mode == "stock":
            d_ht = "ТРУБА ПРОФИЛЬНАЯ"
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', placeholder=d_ht) or d_ht
        elif mode == "cases":
            d_ht = "НУЖЕН МЕТАЛЛ ТОЧНО В СРОК И ПО ГОСТУ?"
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', placeholder=d_ht) or d_ht
            d_hi = "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=633kxjmua5h3e6auf9n3p3mtxkbqyuz5g9t4bxmiwacn4se1m7mm8f3xb9kfj4sdqs7u6wy3p67hniwanz5qzpz6e3oafgod1gfpiyt35tefhp8sjg7t3fqc9p5i93btrk54ju1mbjtetk"
            data['HERO_IMG'] = st.text_input("Картинка отгрузки", placeholder=d_hi) or d_hi
            data['HERO_BTN_LINK'] = st.text_input("Ссылка кнопки", placeholder=data.get('LINK_CATALOG', '')) or data.get('LINK_CATALOG', '')    
        elif mode == "expert":
            d_ht = "БЕСШОВНАЯ ИЛИ ЭЛЕКТРОСВАРНАЯ"
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере', placeholder=d_ht) or d_ht
            d_hi = "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=6uyisxkcb9z7eaauf9n3p3mtxknbsdqxp466f8gerep3qqo3qg9gbanpmbuqopttjmnzyzspdqyqxfm55dgtdc1xhua6ni8nrnmqq1qo538z6idf768zyjwfpoohe8gbci4z3phict9wqfg496t8gqbqy5r6b3tjcs34m6na"
            data['HERO_IMG'] = st.text_input("Картинка справа", placeholder=d_hi) or d_hi
            data['HERO_BTN_LINK'] = st.text_input("Ссылка кнопки", placeholder=data.get('LINK_CATALOG', '')) or data.get('LINK_CATALOG', '')
        else:
            data['HERO_TITLE'] = st.text_input('Заголовок баннера', placeholder="МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ") or "МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ"

    with tabs[2]:
        st.markdown("""
        <div style="background-color: #1e69da33; padding: 10px; border-radius: 5px; border: 1px solid #1e69da; margin-bottom: 15px;">
            <strong>Как оформлять текст:</strong><br>
            • <b>**текст**</b> — жирный | <b>- пункт</b> — список | <b>Enter</b> — новая строка
        </div>
        """, unsafe_allow_html=True)

        if mode == "promo":
            st.subheader("📝 Главная статья")
            
            # Заголовок
            title_def = "Снижаем стоимость на партию"
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", placeholder=title_def) or title_def
            
            # Текст ДО ссылки
            pre_def = "Мы открываем **спецпредложение**..."
            t_pre_raw = st.text_area("Текст ДО ссылки", placeholder=pre_def) or pre_def
            
            # Ссылка
            col_a1, col_a2 = st.columns(2)
            word_def = "партию квадрата"
            a_word = col_a1.text_input("Слово-ссылка", placeholder=word_def) or word_def
            
            link_def = "https://stalmetural.ru/catalog/"
            a_link = col_a2.text_input("Куда ведет", placeholder=link_def) or link_def
            
            # Текст ПОСЛЕ ссылки
            post_def = "из наличия."
            t_post_raw = st.text_area("Текст ПОСЛЕ ссылки", placeholder=post_def) or post_def
            
            data['TEXT_BODY'] = f'{process_text_to_html(t_pre_raw)} <a href="{a_link}" style="text-decoration:none; color:#1e69da; font-weight:bold;">{a_word}</a> {process_text_to_html(t_post_raw)}'
            
            st.markdown("---")
            st.subheader("📎 Блок P.S.")
            ps_c = st.columns(3)
            
            # Настройка товаров в P.S. с использованием placeholder
            with ps_c[0]: 
                n1_def = "профнастил"
                n1 = st.text_input("Товар 1", placeholder=n1_def) or n1_def
            with ps_c[1]: 
                n2_def = "втулки"
                n2 = st.text_input("Товар 2", placeholder=n2_def) or n2_def
            with ps_c[2]: 
                n3_def = "услуги"
                n3 = st.text_input("Товар 3", placeholder=n3_def) or n3_def
            
            link_style = "color: #1e69da; text-decoration: none; font-weight: bold;"
            data['PS_BLOCK'] = f'P.S. Также в наличии <a href="{data["LINK_CATALOG"]}" style="{link_style}">{n1}</a>, <a href="{data["LINK_CATALOG"]}" style="{link_style}">{n2}</a> и <a href="{data["LINK_CATALOG"]}" style="{link_style}">{n3}</a>. Напишите нам в ответ на это письмо – подберем решение.'
        elif mode == "expert":
            st.subheader("Основная статья блога")
            
            # Заголовок
            d_title = "Выбираем трубу без переплат"
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", placeholder=d_title) or d_title
            
            # Основной текст (выносим пример в переменную, чтобы код был чистым)
            d_body = (
                "Часто в смету закладывают дорогую бесшовную трубу там, где можно безопасно использовать электросварную.\n\n"
                "**Где можно сэкономить до 40%?**\n"
                "Электросварная труба (ЭСВ) идеально подходит для легких металлоконструкций, заборов и систем ЖКХ с низким давлением.\n\n"
                "**Где рисковать нельзя?**\n"
                "В нефтегазовой промышленности необходима только бесшовная труба (БШ)."
            )
            
            # Используем placeholder вместо value
            text_body_raw = st.text_area(
                "Текст статьи (используйте ** для жирного и - для списков)", 
                height=250, 
                placeholder=d_body
            ) or d_body
            
            data['TEXT_BODY'] = process_text_to_html(text_body_raw)
            
            # Ссылка
            d_link = "https://stalmetural.ru/contacts/"
            data['TEXT_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Связаться с нами'", placeholder=d_link) or d_link

        elif mode == "stock":
            st.subheader("Вводная статья и преимущества")
            
            # Убрали "Склад пополнен:" из дефолтного значения, чтобы не было дубля!
            d_tt = "Профильная труба всех типоразмеров"
            data['TEXT_TITLE'] = st.text_input("Главный заголовок", placeholder=d_tt) or d_tt
            
            d_tb = "Обновили складской запас профильного проката. В наличии все позиции..."
            data['TEXT_BODY'] = process_text_to_html(st.text_area("Вводный абзац", placeholder=d_tb) or d_tb)
            
            st.markdown("**Ключевые пункты (Буллиты):**")
            for i in range(1, 4):
                col_b1, col_b2 = st.columns([1, 2])
                d_bt = f"Заголовок {i}"
                d_bd = f"Описание пункта {i}"
                data[f'BULLET_TITLE_{i}'] = col_b1.text_input(f"Заголовок {i}", placeholder=d_bt, key=f"bt{i}") or d_bt
                data[f'BULLET_TEXT_{i}'] = col_b2.text_input(f"Текст {i}", placeholder=d_bd, key=f"bd{i}") or d_bd

        elif mode == "cases":
            st.subheader("Текст кейса (История успеха)")
            d_ct = "Металл с гарантией: проверка по ГОСТ и полный пакет документов"
            data['CASE_MAIN_TITLE'] = st.text_input("Заголовок статьи", placeholder=d_ct) or d_ct
            d_ctask = "Недостаточная толщина стенки может остановить стройку..."
            data['CASE_TASK'] = process_text_to_html(st.text_area("Задача", placeholder=d_ctask) or d_ctask)
            d_csteps = "- **Замеры перед погрузкой**\n- **Полная документация**"
            data['CASE_STEPS'] = process_text_to_html(st.text_area("Что сделали", placeholder=d_csteps) or d_csteps)
            d_cres = "Ваш объект не будет простаивать из-за брака."
            data['CASE_RESULT'] = st.text_input("Результат", placeholder=d_cres) or d_cres

        elif mode == "services":
            st.subheader("Основной текстовый блок")
            
            d_title = "Больше, чем просто продажа металла"
            data['TEXT_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_title) or d_title

            d_body = (
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
            text_body_raw = st.text_area("Основной текст письма", height=300, placeholder=d_body) or d_body
            data['TEXT_BODY'] = process_text_to_html(text_body_raw)

        
        else:
            d_tt = "Заголовок статьи"
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", placeholder=d_tt) or d_tt
            d_tb = "Основной текст письма..."
            data['TEXT_BODY'] = process_text_to_html(st.text_area("Текст", placeholder=d_tb) or d_tb)
            d_tl = "https://stalmetural.ru/contacts/"
            data['TEXT_BTN_LINK'] = st.text_input("Ссылка для кнопки", placeholder=d_tl) or d_tl

    with tabs[3]:
                # --- ВСЕ НАСТРОЙКИ БЛОКОВ ---
        if mode == "cases":
            st.subheader("Настройка блоков")
            with st.expander("1. Участвовали в отгрузке (4 товара)"):
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    d_name = f"Труба №{i}"
                    data[f'PROD_{i}_TITLE'] = col1.text_input("Название", placeholder=d_name, key=f"pr_t{i}") or d_name
                    d_price = "39 500₽/т"
                    data[f'PROD_{i}_PRICE'] = col2.text_input("Цена", placeholder=d_price, key=f"pr_p{i}") or d_price
                    d_desc = "ГОСТ 8639-82, сталь 3пс"
                    data[f'PROD_{i}_DESC'] = st.text_area("Описание", placeholder=d_desc, key=f"pr_d{i}", height=70) or d_desc
                    
                    col3, col4 = st.columns(2)
                    d_img = "https://img.hiteml.com/example.jpg"
                    data[f'PROD_{i}_IMG'] = col3.text_input("URL картинки", placeholder=d_img, key=f"pr_i{i}") or d_img
                    data[f'PROD_{i}_LINK'] = col4.text_input("Ссылка на каталог", placeholder=data.get('LINK_CATALOG', ''), key=f"pr_l{i}") or data.get('LINK_CATALOG', '')
                
                d_extra = "+ еще 8 позиций сопутствующего проката..."
                data['PROD_EXTRA_TEXT'] = st.text_input("Текст под товарами", placeholder=d_extra) or d_extra
                data['ALL_PROD_LINK'] = st.text_input("Ссылка кнопки 'Весь сортамент'", placeholder=data.get('LINK_CATALOG', '')) or data.get('LINK_CATALOG', '')

            with st.expander("2. Не тратьте время на подгонку (3 Услуги)"):
                d_st = "Не тратьте время на подгонку на объекте"
                data['SERVICES_TITLE'] = st.text_input("Главный заголовок услуг", placeholder=d_st) or d_st
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    col1, col2 = st.columns(2)
                    d_sv_t = "Резка в размер"
                    data[f'SERV_{i}_TITLE'] = col1.text_input("Название услуги", placeholder=d_sv_t, key=f"srv_t{i}") or d_sv_t
                    d_sv_d = "Точность до 1 мм"
                    data[f'SERV_{i}_DESC'] = col2.text_input("Краткое описание", placeholder=d_sv_d, key=f"srv_d{i}") or d_sv_d
                    col3, col4 = st.columns(2)
                    d_sv_i = "https://img.hiteml.com/service.jpg"
                    data[f'SERV_{i}_IMG'] = col3.text_input("URL картинки", placeholder=d_sv_i, key=f"srv_i{i}") or d_sv_i
                    data[f'SERV_{i}_LINK'] = col4.text_input("Ссылка", placeholder=data.get('LINK_CATALOG', ''), key=f"srv_l{i}") or data.get('LINK_CATALOG', '')
                    st.markdown("---")

        elif mode == "expert":
            st.subheader("Настройка блоков")
            with st.expander("1. Какой товар подходит?"):
                d_ps_t = "Какой товар подходит под ваши задачи?"
                data['PIPE_SECTION_TITLE'] = st.text_input("Заголовок", placeholder=d_ps_t) or d_ps_t
                for i in range(1, 3):
                    col1, col2 = st.columns(2)
                    d_p_t = f"Труба №{i}"
                    data[f'PIPE_{i}_TITLE'] = col1.text_input("Название", placeholder=d_p_t, key=f"expt_t{i}") or d_p_t
                    d_p_p = "100 000₽/т"
                    data[f'PIPE_{i}_PRICE'] = col2.text_input("Цена", placeholder=d_p_p, key=f"expt_p{i}") or d_p_p
                    d_p_d = "- Преимущество 1\n- Преимущество 2"
                    data[f'PIPE_{i}_DESC'] = process_text_to_html(st.text_area("Описания", placeholder=d_p_d, key=f"expt_d{i}") or d_p_d)
                    col3, col4 = st.columns(2)
                    d_p_i = "https://img.hiteml.com/pipe.jpg"
                    data[f'PIPE_{i}_IMG'] = col3.text_input("URL картинки", placeholder=d_p_i, key=f"expt_i{i}") or d_p_i
                    data[f'PIPE_{i}_LINK'] = col4.text_input("Ссылка", placeholder=data.get('LINK_CATALOG', ''), key=f"expt_l{i}") or data.get('LINK_CATALOG', '')

            with st.expander("2. Также в наличии на складе"):
                d_ss_t = "Также в наличии на складе"
                data['STOCK_SECTION_TITLE'] = st.text_input("Заголовок", placeholder=d_ss_t) or d_ss_t
                for i in range(1, 4):
                    col1, col2 = st.columns(2)
                    d_s_t = f"Товар №{i}"
                    data[f'STOCK_{i}_TITLE'] = col1.text_input("Название", placeholder=d_s_t, key=f"exst_t{i}") or d_s_t
                    d_s_p = "50 000₽/т"
                    data[f'STOCK_{i}_PRICE'] = col2.text_input("Цена", placeholder=d_s_p, key=f"exst_p{i}") or d_s_p
                    d_s_d = "В наличии 20 тонн"
                    data[f'STOCK_{i}_DESC'] = st.text_input("Описание", placeholder=d_s_d, key=f"exst_d{i}") or d_s_d
                    col3, col4 = st.columns(2)
                    d_s_i = "https://img.hiteml.com/stock.jpg"
                    data[f'STOCK_{i}_IMG'] = col3.text_input("URL картинки", placeholder=d_s_i, key=f"exst_i{i}") or d_s_i
                    data[f'STOCK_{i}_LINK'] = col4.text_input("Ссылка", placeholder=data.get('LINK_CATALOG', ''), key=f"exst_l{i}") or data.get('LINK_CATALOG', '')
                    st.markdown("---")

        elif mode == "stock":
            st.subheader("Настройка технических блоков и товаров") 

           # ===================================================
            # БЛОК 2: ГОСТЫ И РАЗМЕРЫ
            # ===================================================
            with st.expander("1. Технический блок (ГОСТы и Размеры)"):
 
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
                    st.markdown("**Текущие стандарты** (кликните на ячейку с ✕ , чтобы удалить):")
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
                    st.markdown("**Текущие размеры** (кликните на ячейку с ✕ , чтобы удалить):")
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

            with st.expander("2. Также в наличии (3 товара)"):
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    d_t, d_d, d_p, d_op = f"Товар {i}", "ГОСТ, марка стали", "50 000₽", "60 000₽"
                    data[f'T_{i}'] = st.text_input("Название", placeholder=d_t, key=f"st_t{i}") or d_t
                    data[f'D_{i}'] = st.text_input("Описание", placeholder=d_d, key=f"st_d{i}") or d_d
                    data[f'P_{i}'] = st.text_input("Цена", placeholder=d_p, key=f"st_p{i}") or d_p
                    data[f'I_{i}'] = st.text_input("URL картинки", placeholder="https://...", key=f"st_i{i}") or ""
                    data[f'L_{i}'] = st.text_input("Ссылка", placeholder=data['LINK_CATALOG'], key=f"st_l{i}") or data['LINK_CATALOG']

            with st.expander("3. Наши отгрузки (2 кейса)"):
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    d_ct, d_cd, d_cdt = "Партия труб", "Отгружено 20 тонн", "15.05.2024"
                    data[f'CASE_TITLE_{i}'] = st.text_input("Заголовок кейса", placeholder=d_ct, key=f"st_ct{i}") or d_ct
                    data[f'CASE_DESC_{i}'] = st.text_input("Описание кейса", placeholder=d_cd, key=f"st_cd{i}") or d_cd
                    data[f'CASE_DATE_{i}'] = st.text_input("Дата", placeholder=d_cdt, key=f"st_cdt{i}") or d_cdt
                    data[f'CASE_IMG_{i}'] = st.text_input("URL фото", placeholder="https://...", key=f"st_ci{i}") or ""

        elif mode == "promo":
            st.subheader("Товарные и структурные блоки")
            
            # --- 1. ПЕРСОНАЛЬНЫЕ ЦЕНЫ (Сетка 2х2) ---
            with st.expander("1. Ваши персональные цены (Сетка 2x2)", expanded=True):
                
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    d_t, d_p, d_op = f"Лист х/к {i}", "495₽/т", "550₽"
                    data[f'T_{i}'] = col1.text_input("Название", placeholder=d_t, key=f"p_t{i}") or d_t
                    data[f'P_{i}'] = col2.text_input("Цена со скидкой", placeholder=d_p, key=f"p_p{i}") or d_p
                    data[f'OLD_P_{i}'] = col3.text_input("Старая цена", placeholder=d_op, key=f"p_op{i}") or d_op
                    
                    d_d = "ГОСТ 16523-97"
                    data[f'D_{i}'] = st.text_input("Описание", placeholder=d_d, key=f"p_d{i}") or d_d
                    data[f'I_{i}'] = st.text_input("URL картинки", placeholder="https://...", key=f"p_i{i}") or ""
                    data[f'L_{i}'] = st.text_input("Ссылка", placeholder=data['LINK_CATALOG'], key=f"p_l{i}") or data['LINK_CATALOG']
                    st.markdown("---")

            # --- 2. ФИКСИРОВАННЫЕ ЦЕНЫ (Сетка 1х3 - малые) ---
            with st.expander("2. Также зафиксировали цены (Малые блоки 1x3)"):
                
                for i in range(1, 4):
                    st.markdown(f"**Малый товар №{i}**")
                    d_sm_t, d_sm_p, d_sm_d = "Сетка цинк", "305₽/т", "ГОСТ 23279-2012"
                    data[f'SMALL_T_{i}'] = st.text_input("Название", placeholder=d_sm_t, key=f"sm_t{i}") or d_sm_t
                    data[f'SMALL_P_{i}'] = st.text_input("Цена", placeholder=d_sm_p, key=f"sm_p{i}") or d_sm_p
                    data[f'SMALL_D_{i}'] = st.text_input("Описание", placeholder=d_sm_d, key=f"sm_d{i}") or d_sm_d
                    data[f'SMALL_I_{i}'] = st.text_input("URL фото", placeholder="https://...", key=f"sm_img{i}") or ""
                    data[f'SMALL_L_{i}'] = st.text_input("Ссылка", placeholder=data['LINK_CATALOG'], key=f"sm_link{i}") or data['LINK_CATALOG']
                    st.markdown("---")

            # --- 3. КАТЕГОРИИ (1х2) ---
            with st.expander("3. Категории товаров"):
                d_sec_t = "Категории товаров"
                data['CAT_SECTION_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_sec_t) or d_sec_t
                for i in range(1, 3):
                    st.markdown(f"**Категория №{i}**")
                    d_ct_t = "Трубный прокат"
                    data[f'CAT_TITLE_{i}'] = st.text_input("Заголовок", placeholder=d_ct_t, key=f"ct_t{i}") or d_ct_t
                    d_ct_d = "Огромный выбор диаметров и стенок"
                    data[f'CAT_DESC_{i}'] = st.text_area("Описание", placeholder=d_ct_d, key=f"ct_d{i}") or d_ct_d
                    data[f'CAT_IMG_{i}'] = st.text_input("URL картинки", placeholder="https://...", key=f"ct_i{i}") or ""
                    data[f'CAT_LINK_{i}'] = st.text_input("Ссылка", placeholder=data['LINK_CATALOG'], key=f"ct_l{i}") or data['LINK_CATALOG']
                    st.markdown("---")

            # --- 4. ОТГРУЗКИ (1х2) ---
            with st.expander("4. Наши отгрузки за неделю"):
                d_sec_title = "Наши отгрузки"
                data['CASE_SECTION_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_sec_title) or d_sec_title
                
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    col_k1, col_k2 = st.columns([2, 1])
                    
                    d_c_title = f"Отгрузка металлопроката {i}"
                    data[f'CASE_TITLE_{i}'] = col_k1.text_input("Заголовок отгрузки", placeholder=d_c_title, key=f"cs_t{i}") or d_c_title
                    
                    d_c_date = "10.06.2024"
                    data[f'CASE_DATE_{i}'] = col_k2.text_input("Дата", placeholder=d_c_date, key=f"cs_dt{i}") or d_c_date
                    
                    d_c_desc = "Укомплектовали и доставили заказ на объект"
                    data[f'CASE_DESC_{i}'] = st.text_input("Описание (что отгрузили)", placeholder=d_c_desc, key=f"cs_d{i}") or d_c_desc
                    
                    data[f'CASE_IMG_{i}'] = st.text_input("URL фото отгрузки", placeholder="https://...", key=f"cs_i{i}") or ""
                    st.markdown("---")

        elif mode == "services":
            st.subheader("Настройка блоков")

            # --- БЛОК 1: ТЕХНОЛОГИИ (3 карточки) ---
            with st.expander("1. Технологии (3 карточки)"):
                d_tech_t = "Технологии, которые сэкономят ваше время"
                data['TECH_SECTION_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_tech_t) or d_tech_t
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    d_sv_t, d_sv_d = "Лазерная резка", "Точность до микрона"
                    data[f'T_{i}'] = st.text_input("Название", placeholder=d_sv_t, key=f"sv_t{i}") or d_sv_t
                    data[f'D_{i}'] = st.text_input("Описание", placeholder=d_sv_d, key=f"sv_d{i}") or d_sv_d
                    data[f'I_{i}'] = st.text_input("URL картинки", placeholder="https://...", key=f"sv_i{i}") or ""
                    data[f'L_{i}'] = st.text_input("Ссылка", placeholder=data.get('LINK_CATALOG', ''), key=f"sv_l{i}") or data.get('LINK_CATALOG', '')
                    st.markdown("---")

            # --- БЛОК 2: СОРТАМЕНТ (2 товара) ---
            with st.expander("2. Сортамент под ваши чертежи"):
                d_sort_t = "Сортамент под ваши чертежи"
                data['SORT_SECTION_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_sort_t) or d_sort_t
                d_sort_i = "Поставляем прокат напрямую с заводов..."
                data['SORT_INTRO'] = process_text_to_html(st.text_area("Вводный текст", placeholder=d_sort_i) or d_sort_i)

                for i in range(1, 3):
                    st.markdown(f"**Товар №{i}**")
                    d_sr_t, d_sr_sp = "Труба БШ", "ГОСТ 8734-75"
                    data[f'SORT_T_{i}'] = st.text_input("Название", placeholder=d_sr_t, key=f"sr_t{i}") or d_sr_t
                    data[f'SORT_SPEC_{i}'] = st.text_input("Характеристика", placeholder=d_sr_sp, key=f"sr_sp{i}") or d_sr_sp
                    d_sr_d = "- Сталь 20\n- Любая нарезка"
                    data[f'SORT_D_{i}'] = process_text_to_html(st.text_area("Описание", placeholder=d_sr_d, key=f"sr_d{i}") or d_sr_d)
                    data[f'SORT_I_{i}'] = st.text_input("URL фото", placeholder="https://...", key=f"sr_i{i}") or ""
                    data[f'SORT_L_{i}'] = st.text_input("Ссылка", placeholder=data.get('LINK_CATALOG', ''), key=f"sr_l{i}") or data.get('LINK_CATALOG', '')
                    st.markdown("---")

# --- БЛОК 3: ОТГРУЗКИ (2 кейса) ---
            with st.expander("3. Монтаж без задержек: отгружаем точно в срок"):
                d_ship_sec_t = "Монтаж без задержек: отгружаем точно в срок"
                data['SHIP_SECTION_TITLE'] = st.text_input("Заголовок раздела", placeholder=d_ship_sec_t) or d_ship_sec_t
                
                for i in range(1, 3):
                    st.markdown(f"**Отгрузка №{i}**")
                    col1, col2 = st.columns(2)
                    
                    d_sh_t = f"Название товара {i}"
                    data[f'SHIP_T_{i}'] = col1.text_input("Название товара", placeholder=d_sh_t, key=f"sh_t{i}") or d_sh_t
                    
                    d_sh_date = "12.06.2024"
                    data[f'SHIP_DATE_{i}'] = col2.text_input("Дата", placeholder=d_sh_date, key=f"sh_dt{i}") or d_sh_date
                    
                    d_sh_d = "Описание процесса отгрузки или логистики"
                    data[f'SHIP_D_{i}'] = st.text_input("Описание", placeholder=d_sh_d, key=f"sh_d{i}") or d_sh_d
                    
                    data[f'SHIP_I_{i}'] = st.text_input("URL фото отгрузки", placeholder="https://...", key=f"sh_i{i}") or ""
                    st.markdown("---")



        else:
            st.info("Блоки для данного шаблона настраиваются индивидуально. Перейдите в другой шаблон.")

    with tabs[4]:
        st.info("Блок Алины зафиксирован в дизайне. Здесь меняется только ссылка кнопки.")
        data['ALINA_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Рассчитать смету'", placeholder="https://stalmetural.ru/contacts/")  or "https://stalmetural.ru/contacts/"

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
