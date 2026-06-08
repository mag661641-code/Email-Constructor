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
    "cases": {"title": "ОТГРУЗКИ", "desc": "Новый кейс отгрузки"},
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
    tabs = st.tabs(["Контакты и Ссылки", "Баннер", "Тексты", "Блоки", "Эксперт"])

    # --- ВКЛАДКА 1: КОНТАКТЫ И БАЗОВЫЕ ССЫЛКИ ---
    with tabs[0]:
        c1, c2 = st.columns(2)
        data['EMAIL'] = c1.text_input("Email филиала", "msk@stalmetural.ru")
        data['PHONE'] = c1.text_input("Телефон филиала", "+7 (499) 130-60-28")
        
        # Авто-генерация ссылки для звонка
        phone_digits = "".join(filter(str.isdigit, data['PHONE']))
        if not phone_digits.startswith('+'): phone_digits = "+" + phone_digits
        data['PHONE_LINK'] = f"tel:{phone_digits}"

        data['LINK_LOGO'] = c2.text_input("Ссылка при клике на логотип", "https://stalmetural.ru/")
        
        st.markdown("**Меню навигации:**")
        col_m1, col_m2, col_m3 = st.columns(3)
        data['LINK_CATALOG'] = col_m1.text_input("Ссылка 'Каталог'", "https://stalmetural.ru/catalog/")
        data['LINK_COMPANY'] = col_m2.text_input("Ссылка 'О компании/Кейсы'", "https://stalmetural.ru/about/")
        data['LINK_DELIVERY'] = col_m3.text_input("Ссылка 'Доставка'", "https://stalmetural.ru/delivery/")
        
        data['FOOTER_ADDRESS'] = st.text_input("Адрес в футере", "ООО \"СМУ\", г. Екатеринбург, ул. Машиностроителей 10, оф. 100")
        data['UnsubscribeUrl'], data['webversion'], data['email'] = "{{UnsubscribeUrl}}", "{{webversion}}", "{{email}}"

    # --- ВКЛАДКА 2: БАННЕР ---
    with tabs[1]:
        data['PREHEADER_TEXT'] = st.text_input("Прехедер (текст в почтовике перед открытием)", "Собрали трубы, отводы и листы в один заказ за 3 часа...")
        st.markdown("---")
        
        if mode == "cases":
            data['HERO_TITLE'] = st.text_input("Главный заголовок", "ОПЕРАТИВНАЯ КОМПЛЕКТАЦИЯ СЛОЖНЫХ ЗАКАЗОВ")
            data['HERO_BG_IMG'] = st.text_input("Фон баннера (Картинка)", "https://cp.unisender.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=6dzzhth5h9wnshauf9n3p3mtxkdp4i7bgic7eirrduaxtfryt35pt4dso8hrqam4e713iwazy1cr56")
            data['HERO_IMG'] = st.text_input("Картинка справа от текста", "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=633kxjmua5h3e6auf9n3p3mtxkbqyuz5g9t4bxmiwacn4se1m7mm8f3xb9kfj4sdqs7u6wy3p67hniwanz5qzpz6e3oafgod1gfpiyt35tefhp8sjg7t3fqc9p5i93btrk54ju1mbjtetk")
            data['HERO_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Рассчитать проект'", data['LINK_CATALOG'])
        else:
            # Для остальных шаблонов
            data['HERO_TITLE'] = st.text_input('Заголовок баннера', "МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ")

    # --- ВКЛАДКА 3: ТЕКСТЫ (С УМНЫМ ФОРМАТИРОВАНИЕМ) ---
    with tabs[2]:
        st.markdown("""
        <div style="background-color: #1e69da33; padding: 10px; border-radius: 5px; border: 1px solid #1e69da; margin-bottom: 15px;">
            <strong>Инструкция по форматированию текста:</strong><br>
            • <b>**текст**</b> — сделает текст жирным<br>
            • <b>- пункт</b> или <b>* пункт</b> — превратится в аккуратный список с точечками<br>
            • <b>Enter</b> — автоматически создаст новую строку
        </div>
        """, unsafe_allow_html=True)

        if mode == "cases":
            data['CASE_MAIN_TITLE'] = st.text_input("Главный заголовок статьи", "Металл с гарантией: проверка по ГОСТ и полный пакет документов при отгрузке")
            
            task_raw = st.text_area("Задача / Вводный текст", "Недостаточная толщина стенки, отсутствие сертификатов или дефекты поверхности могут остановить стройку на недели. В «Стальметурал» мы внедрили трехступенчатый контроль отгрузки, чтобы вы спали спокойно.", height=100)
            data['CASE_TASK'] = process_text_to_html(task_raw)
            
            steps_raw = st.text_area("Что мы сделали (Список / Буллиты)", 
                "- **Замеры перед погрузкой:** Проверяем толщину стенки и параметры металла на соответствие ГОСТу.\n"
                "- **Полная документация:** Пакет оригинальных сертификатов передается водителю сразу – никаких «дошлем почтой».\n"
                "- **Точность до миллиметра:** Собственный цех резки на ЧПУ гарантирует, что детали встанут как влитые.", height=150)
            data['CASE_STEPS'] = process_text_to_html(steps_raw)
            
            data['CASE_RESULT'] = st.text_input("Результат (выводится в рамке снизу)", "Ваш объект не будет простаивать из-за брака.")
            
        else:
            data['TEXT_TITLE'] = st.text_input("Заголовок статьи", "Заголовок")
            t_raw = st.text_area("Текст", "Текст...")
            data['TEXT_BODY'] = process_text_to_html(t_raw)

    # --- ВКЛАДКА 4: БЛОКИ ---
    with tabs[3]:
        if mode == "cases":
            st.subheader("⚙️ Настройка блоков (Товары, Услуги, Статистика)")
            
            with st.expander("1. Статистика (3 иконки под текстом)"):
                for i in range(1, 4):
                    st.markdown(f"**Характеристика №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'STAT_{i}_TITLE'] = col1.text_input("Название (Например: Срок)", key=f"s_t{i}")
                    data[f'STAT_{i}_DESC'] = col2.text_input("Значение (Например: 24 часа)", key=f"s_d{i}")
                    data[f'STAT_{i}_IMG'] = st.text_input("URL иконки", key=f"s_i{i}")
                    st.markdown("---")

            with st.expander("2. Участвовали в отгрузке (4 товара)", expanded=True):
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'PROD_{i}_TITLE'] = col1.text_input("Название", key=f"pr_t{i}")
                    data[f'PROD_{i}_PRICE'] = col2.text_input("Цена (Например: 39 500₽/т)", key=f"pr_p{i}")
                    data[f'PROD_{i}_DESC'] = st.text_area("Описание (ГОСТ, марка)", key=f"pr_d{i}", height=70)
                    col3, col4 = st.columns(2)
                    data[f'PROD_{i}_IMG'] = col3.text_input("URL картинки товара", key=f"pr_i{i}")
                    data[f'PROD_{i}_LINK'] = col4.text_input("Ссылка на каталог", data['LINK_CATALOG'], key=f"pr_l{i}")
                    st.markdown("---")
                
                data['PROD_EXTRA_TEXT'] = st.text_input("Текст под товарами", "+ еще 8 позиций сопутствующего проката и метизов укомплектованы в эту же машину")
                data['ALL_PROD_LINK'] = st.text_input("Ссылка кнопки 'Посмотреть весь сортамент'", data['LINK_CATALOG'])

            with st.expander("3. Не тратьте время на подгонку (3 Услуги)"):
                data['SERVICES_TITLE'] = st.text_input("Главный заголовок услуг", "Не тратьте время на подгонку на объекте")
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    col1, col2 = st.columns(2)
                    data[f'SERV_{i}_TITLE'] = col1.text_input("Название услуги", key=f"srv_t{i}")
                    data[f'SERV_{i}_DESC'] = col2.text_input("Краткое описание", key=f"srv_d{i}")
                    col3, col4 = st.columns(2)
                    data[f'SERV_{i}_IMG'] = col3.text_input("URL картинки услуги", key=f"srv_i{i}")
                    data[f'SERV_{i}_LINK'] = col4.text_input("Ссылка 'Заказать'", data['LINK_CATALOG'], key=f"srv_l{i}")
                    st.markdown("---")

    # --- ВКЛАДКА 5: ЭКСПЕРТ ---
    with tabs[4]:
        st.info("Блок Алины (Эксперт) зафиксирован в дизайне. Здесь можно изменить только ссылку кнопки.")
        data['ALINA_BTN_LINK'] = st.text_input("Ссылка для кнопки 'Рассчитать смету'", "https://stalmetural.ru/contacts/")

    st.write("---")
    if st.button("СОБРАТЬ ФИНАЛЬНЫЙ HTML", type="primary", use_container_width=True):
        # Ищем шаблон
        file_name = f"template_{mode}.html"
        file_path = os.path.join("templates", file_name)
        if not os.path.exists(file_path): file_path = file_name
        
        try:
            with open(file_path, "r", encoding="utf-8") as f: 
                html = f.read()
            
            # Замена всех переменных в HTML
            for key, val in data.items():
                if val: html = html.replace(f"{{{{{key}}}}}", str(val))
            
            st.success("Готово! Ваш шаблон успешно собран.")
            
            # Превью и вывод кода
            components.html(html, height=800, scrolling=True)
            with st.expander("Скопировать код"): 
                st.code(html, language="html")
                
        except Exception as e: 
            st.error(f"Файл шаблона `{file_name}` не найден или произошла ошибка! {e}")
