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
    # 1. Сначала обрабатываем ЖИРНЫЙ ТЕКСТ: **слово** превращаем в <strong>слово</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # 2. Обрабатываем переносы строк и буллиты
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
# ==========================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
# ==========================================
st.set_page_config(layout="wide", page_title="Стальметурал | Конструктор", initial_sidebar_state="expanded")

if 'mode' not in st.session_state: st.session_state.mode = None
if 'cute_img' not in st.session_state: st.session_state.cute_img = None
if 'theme' not in st.session_state: st.session_state.theme = "dark"

# ==========================================
# 2. УМНЫЙ CSS (УМЕНЬШЕННАЯ ВЫСОТА)
# ==========================================
base_styles = """
<style>
    /* Полное скрытие системных элементов */
    #MainMenu {visibility: hidden;} 
    header {visibility: hidden; height: 0px !important;} 
    footer {visibility: hidden;}
    
    /* Убираем верхний отступ контейнера */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* КНОПКИ ГЛАВНОГО МЕНЮ - Высота уменьшена в 2 раза (90px) */
    .stButton > button {
        height: 90px !important;
        border-radius: 12px !important;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
        white-space: pre-wrap !important;
        text-align: center !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) !important;
        border-color: #1e69da !important;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1) !important;
    }

    .stButton > button div p {
        font-size: 14px !important;
        font-weight: 700 !important;
    }

    /* КНОПКА ТЕМЫ (Солнышко/Луна) - Высота уменьшена в 2 раза */
    [data-testid="column"]:last-child button {
        height: 25px !important;
        line-height: 1 !important;
        padding: 0 !important;
    }

    /* Главная кнопка сборки (оставляем крупной для удобства) */
    div.stButton > button[kind="primary"] {
        background-color: #1e69da !important;
        color: white !important;
        height: 55px !important;
        border: none !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        transform: none !important;
    }
</style>
"""

if st.session_state.theme == "light":
    theme_css = """
    <style>
        [data-testid="stAppViewContainer"] { background-color: #F8F9FA; color: #111827; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
        .stButton > button { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; color: #111827 !important; }
        .stButton > button:hover { color: #1e69da !important; }
        h1, h2, h3, label, p, .stMarkdown { color: #111827 !important; }
        .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; }
        button[data-baseweb="tab"] p { color: #6B7280 !important; font-weight: 600 !important; }
        button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    </style>
    """
else:
    theme_css = """
    <style>
        [data-testid="stAppViewContainer"] { background-color: #0F1117; color: #F3F4F6; }
        [data-testid="stSidebar"] { background-color: #161922; }
        .stButton > button { background-color: #1A1C24 !important; border: 1px solid #3e4452 !important; color: #F3F4F6 !important; }
        h1, h2, h3, label, p { color: #F3F4F6 !important; }
        .stTextInput input, .stTextArea textarea { background-color: #1F2937 !important; color: #F3F4F6 !important; border: 1px solid #374151 !important; }
        button[data-baseweb="tab"] p { color: #9CA3AF !important; font-weight: 600 !important; }
        button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }
    </style>
    """

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

        data['CITY_IN'] = c2.text_input("Город (в чем? где?)", "в Москве")
        data['LINK_CATALOG'] = c1.text_input("Ссылка 'Каталог'", "https://stalmetural.ru/catalog/")
        data['LINK_COMPANY'] = c2.text_input("Ссылка 'О компании'", "https://stalmetural.ru/about/")
        data['LINK_DELIVERY'] = c2.text_input("Ссылка 'Доставка'", "https://stalmetural.ru/delivery/")
        data['FOOTER_ADDRESS'] = st.text_input("Адрес в футере", "ООО \"СМУ\", г. Екатеринбург, ул. Машиностроителей 10")
        data['UnsubscribeUrl'], data['webversion'], data['email'] = "{{UnsubscribeUrl}}", "{{webversion}}", "{{email}}"

    with tabs[1]:
        # --- ОБЩЕЕ ДЛЯ ВСЕХ: ПРЕХЕДЕР ---
        data['PREHEADER_TEXT'] = st.text_input("Прехедер (текст, который видно в списке писем)", "Узнайте подробности в письме...")
        
        # --- БАННЕР МЕНЯЕТСЯ ОТ РЕЖИМА ---
        if mode == "promo":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере (начинать с "НА")', "НА КВАДРАТ ЧУГУННЫЙ")
            data['DISCOUNT_LABEL'] = st.text_input("Метка скидки", "СКИДКА 10%")
        
        elif mode == "stock":
            data['HERO_TITLE'] = st.text_input('Заголовок на баннере (например: ЛИСТ ГОРЯЧЕКАТАНЫЙ)', "ТРУБА ПРОФИЛЬНАЯ")
            st.caption("В шаблоне 'Поступление' заголовок обычно отображается крупно в центре баннера.")
        
        elif mode == "cases":
            data['HERO_TITLE'] = st.text_input('Текст на баннере (вопрос или оффер)', "ГОРИТ ОБЪЕКТ ИЗ-ЗА СЛОЖНОЙ ЗАЯВКИ?")
        
        else:
            data['HERO_TITLE'] = st.text_input('Заголовок баннера', "МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ")

    with tabs[2]:
        # Инструкция (видна всем)
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
            
            # Собираем основной текст (обрабатываем только части до и после ссылки)
            data['TEXT_BODY'] = f'{process_text_to_html(t_pre_raw)} <a href="{a_link}" style="text-decoration:none; color:#1e69da; font-weight:bold;">{a_word}</a> {process_text_to_html(t_post_raw)}'

            st.markdown("---")
            st.subheader("📎 Блок P.S. (под статьей)")
            ps_c = st.columns(3)
            with ps_c[0]: n1 = st.text_input("Доп. товар 1", "чугунные круги")
            with ps_c[1]: n2 = st.text_input("Доп. товар 2", "втулки")
            with ps_c[2]: n3 = st.text_input("Доп. товар 3", "услуги металлообработки")
            
            # Формируем финальный PS_BLOCK
            data['PS_BLOCK'] = f'P.S. Также в наличии <a href="{data["LINK_CATALOG"]}" style="color:#1e69da; font-weight:bold; text-decoration:none;">{n1}</a>, <a href="{data["LINK_CATALOG"]}" style="color:#1e69da; font-weight:bold; text-decoration:none;">{n2}</a> и <a href="{data["LINK_CATALOG"]}" style="color:#1e69da; font-weight:bold; text-decoration:none;">{n3}</a>. Напишите нам.'
       
        elif mode == "stock":
            st.subheader("Текст для статьи 'Поступление'")
            data['STOCK_MAIN_TITLE'] = st.text_input("Заголовок статьи", "Склад пополнен: Профильная труба всех типоразмеров")
            stock_intro_raw = st.text_area("Вводный абзац", "Обновили складской запас профильного проката. В наличии все позиции...")
            data['STOCK_INTRO'] = process_text_to_html(stock_intro_raw)

        elif mode == "cases":
            st.subheader("Текст кейса (История успеха)")
            data['CASE_TITLE'] = st.text_input("Заголовок кейса", "Как мы укомплектовали 12 позиций за 24 часа")
            case_task_raw = st.text_area("Задача (что просил клиент)", "Снабженцу требовалось за сутки...")
            data['CASE_TASK'] = process_text_to_html(case_task_raw)
            
            case_real_raw = st.text_area("Реализация (что мы сделали)", "- Сборный груз за 3 часа")
            data['CASE_REALIZATION'] = process_text_to_html(case_real_raw)

    with tabs[3]:
        # --- ВСЕ НАСТРОЙКИ БЛОКОВ ---
        if mode == "cases":
            st.subheader("⚙️ Настройка кейса отгрузки")
            with st.expander("1. Описание истории", expanded=True):
                data['CASE_MAIN_TITLE'] = st.text_input("Заголовок кейса", "Как мы укомплектовали 12 позиций...")
                data['CASE_TASK'] = st.text_area("Задача", "Снабженцу требовалось...")
                data['CASE_STEPS'] = st.text_area("Реализация", "- Сборный груз...")
                data['CASE_RESULT'] = st.text_input("Результат", "Машина прибыла на объект...")

            with st.expander("2. Статистика (иконки)"):
                data['CASE_STAT_1'] = st.text_input("Срок", "24 часа")
                data['CASE_STAT_2'] = st.text_input("Объем", "12 типов изделий")
                data['CASE_STAT_3'] = st.text_input("Выгода", "Одна машина вместо трех")

            with st.expander("3. Товары (2 шт.)"):
                for i in range(1, 3):
                    st.markdown(f"**Товар №{i}**")
                    data[f'T_{i}'] = st.text_input("Название", key=f"cs_t{i}")
                    data[f'D_{i}'] = st.text_input("Описание", key=f"cs_d{i}")
                    data[f'I_{i}'] = st.text_input("URL картинки", key=f"cs_img{i}")
                    data[f'L_{i}'] = st.text_input("Ссылка", data['LINK_CATALOG'], key=f"cs_l{i}")

        elif mode == "stock":
            st.subheader("📦 Настройка контента Поступления")
            with st.expander("1. Блок бесплатного аудита", expanded=True):
                data['AUDIT_TITLE'] = st.text_input("Заголовок", "Бесплатный аудит сметы и чертежей*")
                data['AUDIT_SUB'] = st.text_input("Подзаголовок", "Индивидуальный расчет условий под ваш объем")
                data['AUDIT_LINK'] = st.text_input("Ссылка кнопки", data['LINK_CATALOG'])

            with st.expander("2. Описание и Буллиты"):
                data['TEXT_TITLE'] = st.text_input("Заголовок текста", "Труба всех типоразмеров")
                data['TEXT_BODY'] = st.text_area("Вводный текст", "Обновили складской запас...")
                for i in range(1, 4):
                    data[f'BULLET_{i}'] = st.text_input(f"Пункт списка {i}", key=f"st_blt{i}")

            with st.expander("3. Технический блок (ГОСТы и Размеры)"):
                data['GOST_BLOCK'] = st.text_area("ГОСТы (через пробел)", "ГОСТ 8639-82", key="st_gst")
                data['SIZE_BLOCK'] = st.text_area("Размеры (через пробел)", "20х20 40x40", key="st_sz")

            with st.expander("4. Также в наличии (3 товара)"):
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    data[f'T_{i}'] = st.text_input("Название", key=f"st_t{i}")
                    data[f'D_{i}'] = st.text_input("Описание", key=f"st_d{i}")
                    data[f'P_{i}'] = st.text_input("Цена", key=f"st_p{i}")
                    data[f'OLD_P_{i}'] = st.text_input("Старая цена (для зачеркивания)", key=f"st_op{i}")
                    data[f'I_{i}'] = st.text_input("URL картинки", key=f"st_i{i}")
                    data[f'L_{i}'] = st.text_input("Ссылка", data['LINK_CATALOG'], key=f"st_l{i}")

            with st.expander("5. Наши отгрузки (2 кейса)"):
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    data[f'CASE_TITLE_{i}'] = st.text_input("Заголовок кейса", key=f"st_ct{i}")
                    data[f'CASE_DESC_{i}'] = st.text_input("Описание кейса", key=f"st_cd{i}")
                    data[f'CASE_DATE_{i}'] = st.text_input("Дата", key=f"st_cdt{i}")
                    data[f'CASE_IMG_{i}'] = st.text_input("URL картинки кейса", key=f"st_ci{i}")

        elif mode == "promo":
            st.subheader("📦 Товарные и структурные блоки")
            
            # --- 1. ПЕРСОНАЛЬНЫЕ ЦЕНЫ (Сетка 2х2) ---
            with st.expander("1. Ваши персональные цены (Сетка 2x2)", expanded=True):
                data['PERSONAL_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Ваши персональные цены")
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
                data['FIXED_SECTION_TITLE'] = st.text_input("Заголовок раздела", "Также зафиксировали цены на эти позиции")
                for i in range(1, 4):
                    st.markdown(f"**Малый товар №{i}**")
                    col1, col2 = st.columns([2, 1])
                    data[f'SMALL_T_{i}'] = col1.text_input("Название", key=f"sm_t{i}")
                    data[f'SMALL_P_{i}'] = col2.text_input("Цена", key=f"sm_p{i}")
                    
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
    with tabs[4]:
        st.info("Имя и фото эксперта зафиксированы в HTML-шаблоне. Здесь меняется только ссылка при клике.")
        data['EXPERT_LINK'] = st.text_input("Ссылка для кнопки", "https://stalmetural.ru/contacts/")

    st.write("---")
    if st.button("СОБРАТЬ ФИНАЛЬНЫЙ HTML", type="primary", use_container_width=True):
# Умный поиск файла (в папке templates или в корне)
        file_name = f"template_{mode}.html"
        file_path = os.path.join("templates", file_name)
        
        if not os.path.exists(file_path):
            file_path = file_name # Если в папке нет, ищем в корне
        try:
            with open(file_path, "r", encoding="utf-8") as f: html = f.read()
            for key, val in data.items():
                if val: html = html.replace(f"{{{{{key}}}}}", str(val))
            
            st.success("Готово!")
            
            # Логика разделения кода для шаблона ПРОМО
            if mode == "promo" and "<!-- TIMER_SPLIT -->" in html:
                parts = html.split("<!-- TIMER_SPLIT -->")
                
                # Показываем превью с "заглушкой" вместо таймера
                preview_html = parts[0] + "<div style='color:#fff; font-size:16px; font-weight:bold;'>[СЮДА ВСТАНЕТ ВАШ ТАЙМЕР]</div>" + parts[1]
                components.html(preview_html, height=800, scrolling=True)
                
                st.info("👇 Скопируйте Часть 1, вставьте в вашу систему, затем вставьте код вашего таймера, а после него — Часть 2.")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Часть 1 (ДО таймера)")
                    st.code(parts[0], language="html")
                with col2:
                    st.subheader("Часть 2 (ПОСЛЕ таймера)")
                    st.code(parts[1], language="html")
            else:
                components.html(html, height=800, scrolling=True)
                with st.expander("Скопировать код"): st.code(html, language="html")
        except Exception as e: 
            st.error(f"Файл шаблона не найден или произошла ошибка! {e}")
