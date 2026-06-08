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

# ==========================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
# ==========================================
st.set_page_config(layout="wide", page_title="Стальметурал | Конструктор", initial_sidebar_state="expanded")

if 'mode' not in st.session_state: st.session_state.mode = None
if 'cute_img' not in st.session_state: st.session_state.cute_img = None
if 'theme' not in st.session_state: st.session_state.theme = "dark"

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
    theme_css = """<style>[data-testid="stAppViewContainer"] { background-color: #F8F9FA; color: #111827; } [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; } .stButton > button { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; color: #111827 !important; } .stButton > button:hover { color: #1e69da !important; } h1, h2, h3, label, p, .stMarkdown { color: #111827 !important; } .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; } button[data-baseweb="tab"] p { color: #6B7280 !important; font-weight: 600 !important; } button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }</style>"""
else:
    theme_css = """<style>[data-testid="stAppViewContainer"] { background-color: #0F1117; color: #F3F4F6; } [data-testid="stSidebar"] { background-color: #161922; } .stButton > button { background-color: #1A1C24 !important; border: 1px solid #3e4452 !important; color: #F3F4F6 !important; } h1, h2, h3, label, p { color: #F3F4F6 !important; } .stTextInput input, .stTextArea textarea { background-color: #1F2937 !important; color: #F3F4F6 !important; border: 1px solid #374151 !important; } button[data-baseweb="tab"] p { color: #9CA3AF !important; font-weight: 600 !important; } button[data-baseweb="tab"][aria-selected="true"] p { color: #1e69da !important; }</style>"""

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
        
        else:
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", "Заголовок")
            t_raw = st.text_area("Текст", "Текст...")
            data['TEXT_BODY'] = process_text_to_html(t_raw)
            data['TEXT_BTN_LINK'] = st.text_input("Ссылка для кнопки", "https://stalmetural.ru/contacts/")

    with tabs[3]:
        if mode == "expert":
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
