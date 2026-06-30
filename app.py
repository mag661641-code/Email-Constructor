import streamlit as st
import os
import time
import requests
import random
import psycopg2
import psycopg2.extras
import hashlib
import json
import re
import base64
from datetime import datetime, timezone, timedelta

_YEK = timezone(timedelta(hours=5))
def _now() -> str:
    return datetime.now(tz=_YEK).strftime("%d.%m.%Y %H:%M")
import streamlit.components.v1 as components

# ==========================================
# 0. БАЗА ДАННЫХ
# ==========================================

@st.cache_resource
def _get_db_url():
    try:
        url = st.secrets["DATABASE_URL"]
    except Exception:
        url = os.environ.get("DATABASE_URL", "")
    if not url:
        st.error("DATABASE_URL не настроен. Добавьте его в Streamlit → Settings → Secrets.")
        st.stop()
    if "sslmode" not in url:
        url += "?sslmode=require"
    return url

def get_db():
    conn = psycopg2.connect(_get_db_url())
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

@st.cache_resource
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            logo_url TEXT,
            accent_color TEXT DEFAULT '#1e69da',
            site_url TEXT,
            catalog_url TEXT,
            about_url TEXT,
            delivery_url TEXT,
            contacts_url TEXT,
            vk_url TEXT,
            tg_url TEXT,
            footer_address TEXT,
            default_email TEXT,
            default_phone TEXT,
            default_city TEXT,
            logo_data TEXT DEFAULT '',
            hero_bg_img TEXT DEFAULT '',
            template_slug TEXT DEFAULT '',
            secondary_color TEXT DEFAULT '#f6f7fc'
        )
    """)
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS logo_data TEXT DEFAULT ''")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS hero_bg_img TEXT DEFAULT ''")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS template_slug TEXT DEFAULT ''")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS secondary_color TEXT DEFAULT '#f6f7fc'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS layout_style TEXT DEFAULT 'stalmetural'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS footer_bg_color TEXT DEFAULT ''")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS footer_bg_img TEXT DEFAULT ''")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS hero_text_color TEXT DEFAULT '#ffffff'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS hero_sub_color TEXT DEFAULT '#cccccc'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS body_title_color TEXT DEFAULT '#282824'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS body_text_color TEXT DEFAULT '#3d4858'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS card_text_color TEXT DEFAULT '#555555'")
    c.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS footer_text_color TEXT DEFAULT '#ffffff'")
    c.execute("UPDATE brands SET template_slug='stalmetural' WHERE name='Стальметурал' AND COALESCE(template_slug,'')=''")
    c.execute("UPDATE brands SET template_slug='inmetprom' WHERE name='Инметпром' AND COALESCE(template_slug,'')=''")
    c.execute("UPDATE brands SET template_slug='metpromenergo' WHERE name='Метпромэнерго' AND COALESCE(template_slug,'')=''")
    c.execute("UPDATE brands SET layout_style='inmetprom' WHERE name='Инметпром' AND COALESCE(layout_style,'stalmetural')='stalmetural'")


    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            brand_id INTEGER REFERENCES brands(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            brand_id INTEGER NOT NULL REFERENCES brands(id),
            template_mode TEXT NOT NULL,
            project_name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            gost_tags TEXT DEFAULT '[]',
            size_tags TEXT DEFAULT '[]',
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contact_templates (
            id SERIAL PRIMARY KEY,
            brand_id INTEGER REFERENCES brands(id),
            name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("SELECT COUNT(*) as cnt FROM brands")
    if c.fetchone()['cnt'] == 0:
        brands = [
            (
                "Стальметурал",
                "https://stalmetural.ru/wp-content/themes/stalmetural/img/logo.svg",
                "#1e69da",
                "https://stalmetural.ru/",
                "https://stalmetural.ru/catalog/",
                "https://stalmetural.ru/about/",
                "https://stalmetural.ru/delivery/",
                "https://stalmetural.ru/contacts/",
                "https://vk.com/stalmetural",
                "https://t.me/stalmetural",
                'ООО "СМУ", г. Екатеринбург, ул. Машиностроителей 10',
                "msk@stalmetural.ru",
                "+7 (499) 130-60-28",
                "в Москве",
                "stalmetural",
            ),
            (
                "Инметпром",
                "https://inmetprom.ru/logo.svg",
                "#1d42a5",
                "https://inmetprom.ru/",
                "https://inmetprom.ru/catalog/",
                "https://inmetprom.ru/about/",
                "https://inmetprom.ru/delivery/",
                "https://inmetprom.ru/contacts/",
                "https://vk.com/inmetprom",
                "https://t.me/inmetprom",
                'ООО "Инметпром", г. Москва, ул. Промышленная 5',
                "info@inmetprom.ru",
                "+7 (495) 000-00-01",
                "в Москве",
                "inmetprom",
            ),
            (
                "Метпромэнерго",
                "https://metpromenergo.ru/logo.svg",
                "#e83e3a",
                "https://metpromenergo.ru/",
                "https://metpromenergo.ru/catalog/",
                "https://metpromenergo.ru/about/",
                "https://metpromenergo.ru/delivery/",
                "https://metpromenergo.ru/contacts/",
                "https://vk.com/metpromenergo",
                "https://t.me/metpromenergo",
                'ООО "МПЭ", г. Санкт-Петербург, пр. Металлистов 22',
                "info@metpromenergo.ru",
                "+7 (812) 000-00-02",
                "в Санкт-Петербурге",
                "metpromenergo",
            ),
        ]
        psycopg2.extras.execute_values(c, """
            INSERT INTO brands
            (name, logo_url, accent_color, site_url, catalog_url, about_url, delivery_url,
             contacts_url, vk_url, tg_url, footer_address, default_email, default_phone, default_city, template_slug)
            VALUES %s
        """, brands)
        conn.commit()

        c.execute("SELECT id, name FROM brands ORDER BY id")
        brand_ids = {row['name']: row['id'] for row in c.fetchall()}

        users = [
            ("stalmetural",  make_hash("smu2024!"),     brand_ids["Стальметурал"]),
            ("inmetprom",    make_hash("imp2024!"),     brand_ids["Инметпром"]),
            ("metpromenergo",make_hash("mpe2024!"),     brand_ids["Метпромэнерго"]),
        ]
        psycopg2.extras.execute_values(c,
            "INSERT INTO users (login, password_hash, brand_id) VALUES %s",
            users
        )
        conn.commit()

    conn.commit()
    conn.close()

@st.cache_resource

def make_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(login: str, password: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.login, u.brand_id, b.name as brand_name,
               b.logo_url, b.accent_color, b.site_url, b.catalog_url,
               b.about_url, b.delivery_url, b.contacts_url,
               b.vk_url, b.tg_url, b.footer_address,
               b.default_email, b.default_phone, b.default_city,
               b.logo_data, b.hero_bg_img, b.template_slug, b.secondary_color,
               b.layout_style, b.footer_bg_color, b.footer_bg_img,
               b.hero_text_color, b.hero_sub_color, b.body_title_color,
               b.body_text_color, b.card_text_color, b.footer_text_color
        FROM users u
        JOIN brands b ON u.brand_id = b.id
        WHERE u.login = %s AND u.password_hash = %s
    """, (login.strip(), make_hash(password)))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_project(brand_id, template_mode, project_name, data_dict, gost_tags, size_tags):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (brand_id, template_mode, project_name, data_json, gost_tags, size_tags, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        brand_id,
        template_mode,
        project_name,
        json.dumps(data_dict, ensure_ascii=False),
        json.dumps(gost_tags, ensure_ascii=False),
        json.dumps(size_tags, ensure_ascii=False),
        _now()
    ))
    conn.commit()
    conn.close()

_AUTOSAVE_SLOT = '__autosave__'

def upsert_autosave(brand_id, template_mode, data_dict, template_variant):
    payload = {**data_dict, '__tv__': template_variant}
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "DELETE FROM projects WHERE brand_id=%s AND template_mode=%s AND project_name=%s",
        (brand_id, template_mode, _AUTOSAVE_SLOT)
    )
    c.execute("""
        INSERT INTO projects (brand_id, template_mode, project_name, data_json, gost_tags, size_tags, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (brand_id, template_mode, _AUTOSAVE_SLOT,
          json.dumps(payload, ensure_ascii=False), '[]', '[]',
          _now()))
    conn.commit()
    conn.close()

def load_autosave(brand_id, template_mode):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT data_json, created_at FROM projects
        WHERE brand_id=%s AND template_mode=%s AND project_name=%s
    """, (brand_id, template_mode, _AUTOSAVE_SLOT))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    d = json.loads(row['data_json'])
    variant = d.pop('__tv__', 'default')
    return d, variant, row['created_at']

def load_projects(brand_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, template_mode, project_name, created_at
        FROM projects WHERE brand_id = %s AND project_name != %s
        ORDER BY id DESC
    """, (brand_id, _AUTOSAVE_SLOT))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def load_project_data(project_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_project(project_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    conn.close()

# Поля контактов, которые входят в шаблон
CONTACT_KEYS = [
    'EMAIL', 'PHONE', 'CITY_IN', 'LINK_LOGO',
    'LINK_CATALOG', 'LINK_COMPANY', 'LINK_DELIVERY',
    'FOOTER_ADDRESS', 'IMP_LINK_PAYMENT', 'IMP_LINK_CONTACTS',
    'ALINA_BTN_LINK',
]

def save_contact_template(brand_id, name, data_dict):
    contacts = {k: data_dict[k] for k in CONTACT_KEYS if data_dict.get(k)}
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO contact_templates (brand_id, name, data_json, created_at)
        VALUES (%s, %s, %s, %s)
    """, (brand_id, name, json.dumps(contacts, ensure_ascii=False),
          _now()))
    conn.commit()
    conn.close()

def load_contact_templates(brand_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, data_json FROM contact_templates
        WHERE brand_id = %s ORDER BY name
    """, (brand_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def delete_contact_template(template_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM contact_templates WHERE id = %s", (template_id,))
    conn.commit()
    conn.close()

def get_all_brands():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM brands ORDER BY name")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_brand(brand_id, name, accent_color, logo_data, hero_bg_img, template_slug,
               site_url, catalog_url, about_url, delivery_url, contacts_url,
               footer_address, default_email, default_phone, default_city,
               secondary_color='#f6f7fc', layout_style='stalmetural', footer_bg_color='',
               footer_bg_img='',
               hero_text_color='#ffffff', hero_sub_color='#cccccc',
               body_title_color='#282824', body_text_color='#3d4858',
               card_text_color='#555555', footer_text_color='#ffffff'):
    conn = get_db()
    c = conn.cursor()
    if brand_id:
        c.execute("""
            UPDATE brands SET name=%s, accent_color=%s, logo_data=%s, hero_bg_img=%s,
            template_slug=%s, site_url=%s, catalog_url=%s, about_url=%s, delivery_url=%s,
            contacts_url=%s, footer_address=%s, default_email=%s, default_phone=%s,
            default_city=%s, secondary_color=%s, layout_style=%s, footer_bg_color=%s,
            footer_bg_img=%s,
            hero_text_color=%s, hero_sub_color=%s, body_title_color=%s,
            body_text_color=%s, card_text_color=%s, footer_text_color=%s
            WHERE id=%s
        """, (name, accent_color, logo_data, hero_bg_img, template_slug,
              site_url, catalog_url, about_url, delivery_url, contacts_url,
              footer_address, default_email, default_phone, default_city,
              secondary_color, layout_style, footer_bg_color, footer_bg_img,
              hero_text_color, hero_sub_color, body_title_color,
              body_text_color, card_text_color, footer_text_color, brand_id))
        conn.commit()
        conn.close()
        _load_all_accounts.clear()
    else:
        c.execute("""
            INSERT INTO brands (name, accent_color, logo_data, hero_bg_img, template_slug,
            site_url, catalog_url, about_url, delivery_url, contacts_url,
            footer_address, default_email, default_phone, default_city, secondary_color,
            layout_style, footer_bg_color, footer_bg_img,
            hero_text_color, hero_sub_color, body_title_color,
            body_text_color, card_text_color, footer_text_color)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (name, accent_color, logo_data, hero_bg_img, template_slug,
              site_url, catalog_url, about_url, delivery_url, contacts_url,
              footer_address, default_email, default_phone, default_city, secondary_color,
              layout_style, footer_bg_color, footer_bg_img,
              hero_text_color, hero_sub_color, body_title_color,
              body_text_color, card_text_color, footer_text_color))
        new_id = c.fetchone()['id']
        conn.commit()
        conn.close()
        _load_all_accounts.clear()
        return new_id

def delete_brand(brand_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM contact_templates WHERE brand_id = %s", (brand_id,))
    c.execute("DELETE FROM projects WHERE brand_id = %s", (brand_id,))
    c.execute("DELETE FROM users WHERE brand_id = %s", (brand_id,))
    c.execute("DELETE FROM brands WHERE id = %s", (brand_id,))
    conn.commit()
    conn.close()
    _load_all_accounts.clear()

def apply_brand_blocks(html, brand, header_style='default', footer_style='default'):
    if header_style and header_style != 'default':
        header_path = os.path.join("templates", "blocks", f"header_{header_style}.html")
        if os.path.exists(header_path):
            with open(header_path, encoding='utf-8') as f:
                new_header = f.read()
            html = re.sub(
                r'<!-- BLOCK:HEADER_START -->.*?<!-- BLOCK:HEADER_END -->',
                new_header, html, flags=re.DOTALL
            )
    if footer_style and footer_style != 'default':
        footer_path = os.path.join("templates", "blocks", f"footer_{footer_style}.html")
        if os.path.exists(footer_path):
            with open(footer_path, encoding='utf-8') as f:
                new_footer = f.read()
            html = re.sub(
                r'<!-- BLOCK:FOOTER_START -->.*?<!-- BLOCK:FOOTER_END -->',
                new_footer, html, flags=re.DOTALL
            )
    return html

def apply_block_visibility(html, hidden_blocks, custom_html='', block_custom_html=None):
    if block_custom_html is None:
        block_custom_html = {}
    # Merge legacy custom_html string into CUSTOM slot (backward compat)
    _bch = dict(block_custom_html)
    if custom_html and custom_html.strip() and 'CUSTOM' not in _bch:
        _bch['CUSTOM'] = custom_html

    for block_name in hidden_blocks:
        html = re.sub(
            rf'<!-- BLOCK:{re.escape(block_name)}_START -->.*?<!-- BLOCK:{re.escape(block_name)}_END -->',
            '', html, flags=re.DOTALL
        )
    for block_name, bhtml in _bch.items():
        if not bhtml or not bhtml.strip():
            continue
        if block_name == 'CUSTOM':
            html = html.replace(
                '<!-- BLOCK:CUSTOM_START --><!-- BLOCK:CUSTOM_END -->',
                f'<!-- BLOCK:CUSTOM_START -->{bhtml}<!-- BLOCK:CUSTOM_END -->'
            )
        elif block_name not in hidden_blocks:
            html = re.sub(
                rf'<!-- BLOCK:{re.escape(block_name)}_START -->.*?<!-- BLOCK:{re.escape(block_name)}_END -->',
                f'<!-- BLOCK:{block_name}_START -->{bhtml}<!-- BLOCK:{block_name}_END -->',
                html, flags=re.DOTALL
            )
    html = html.replace('<!-- BLOCK:CUSTOM_START --><!-- BLOCK:CUSTOM_END -->', '')
    return html

@st.cache_data(show_spinner=False)
def load_block_library():
    """Извлекает именованные блоки из шаблонов для библиотеки."""
    meta = [
        ("template_promo_inmetprom.html", "HEADER",       "Шапка Инметпром",
         "Логотип, телефон, меню навигации — стиль Инметпром."),
        ("template_promo_inmetprom.html", "CONSULTATION", "Блок консультации",
         "«Не нашли нужную позицию?» — запрос с кнопкой. Стиль Инметпром."),
        ("template_promo_inmetprom.html", "WHY_US",       "Почему выбирают нас (Инметпром)",
         "Ключевые преимущества компании — цветные плашки. Стиль Инметпром."),
        ("template_promo_inmetprom.html", "FOOTER",       "Футер Инметпром",
         "Контакты, адрес, ссылка отписки — стиль Инметпром."),
        ("template_cases.html",           "SERVICES",     "Блок услуг",
         "«Не тратьте время на подгонку» — 3 иконки с описаниями."),
        ("template_cases.html",           "WHY_US",       "Почему выбирают нас (Кейсы)",
         "Ключевые преимущества — список с иконками. Стиль Кейсы."),
        ("template_cases.html",           "MANAGER",      "Блок менеджера",
         "CTA с фото и контактом менеджера — призыв к действию."),
        ("template_promo.html",           "HERO",         "Фоновый баннер (Герой)",
         "Большой баннер с изображением, заголовком и таймером."),
        ("template_promo.html",           "HERO_BTN",     "Кнопка каталога",
         "Кнопка «Перейти в каталог» с акцентным фоном."),
        ("template_stock.html",           "PRODUCTS",     "Таблица товаров на складе",
         "Таблица с ценами, ГОСТами и размерами — раздел «Также в наличии»."),
    ]
    result = []
    tpl_dir = "templates"
    for filename, block_id, name, desc in meta:
        path = os.path.join(tpl_dir, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(
            rf'<!-- BLOCK:{re.escape(block_id)}_START -->(.*?)<!-- BLOCK:{re.escape(block_id)}_END -->',
            content, re.DOTALL)
        if not m:
            continue
        source = filename.replace("template_", "").replace(".html", "")
        result.append({
            "key":    f"{source}__{block_id}",
            "name":   name,
            "desc":   desc,
            "source": source,
            "html":   m.group(1).strip(),
        })
    return result


@st.cache_data(show_spinner=False)
def get_inmetprom_shell():
    """Возвращает (prefix, suffix) — HTML-обёртку из promo_inmetprom без блоков."""
    path = os.path.join("templates", "template_promo_inmetprom.html")
    if not os.path.exists(path):
        return "", ""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    first = re.search(r'<!-- BLOCK:\w+_START -->', content)
    last = None
    for m in re.finditer(r'<!-- BLOCK:\w+_END -->', content):
        last = m
    if first and last:
        return content[:first.start()], content[last.end():]
    return "", ""


# Редактируемые поля конструктора инметпром: {block_key: [{key, label, type, default}]}
BLOCK_FIELDS = {
    "promo_inmetprom__CONSULTATION": [
        {"key": "title", "label": "Заголовок",   "type": "text",     "default": "Не нашли то, что искали?"},
        {"key": "desc",  "label": "Описание",     "type": "textarea", "default": "В нашей компании есть квалифицированные специалисты, готовые вас проконсультировать"},
        {"key": "btn",   "label": "Текст кнопки", "type": "text",     "default": "ПОЛУЧИТЬ КОНСУЛЬТАЦИЮ"},
    ],
    "promo_inmetprom__WHY_US": [
        {"key": "heading",     "label": "Заголовок раздела",    "type": "text",     "default": "Почему выбирают нас"},
        {"key": "card1_title", "label": "Карточка 1: название", "type": "text",     "default": "Надежность"},
        {"key": "card1_text",  "label": "Карточка 1: текст",    "type": "textarea", "default": "18 лет на рынке. Фиксируем цену и проводим 3-этапную проверку качества по ГОСТ."},
        {"key": "card2_title", "label": "Карточка 2: название", "type": "text",     "default": "Логистика"},
        {"key": "card2_text",  "label": "Карточка 2: текст",    "type": "textarea", "default": "38 складов по {{REGION}}. Доставка «до двери» и формирование сложных сборных заказов."},
        {"key": "card3_title", "label": "Карточка 3: название", "type": "text",     "default": "Гибкость"},
        {"key": "card3_text",  "label": "Карточка 3: текст",    "type": "textarea", "default": "Отсрочка до 30 дней и накопительная система скидок для постоянных партнеров."},
    ],
}


def create_user_for_brand(login, password, brand_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO users (login, password_hash, brand_id) VALUES (%s, %s, %s)",
              (login.strip(), make_hash(password), brand_id))
    conn.commit()
    conn.close()
    _load_all_accounts.clear()

# Инициализируем БД при старте
init_db()

# ==========================================
# 1. УМНАЯ ФУНКЦИЯ ОБРАБОТКИ ТЕКСТА
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

def get_stored(key, default=""):
    return st.session_state.data.get(key, default)

def make_badges(items, font_size="11px", padding="3px 8px"):
    span_style = (
        f"display:inline-block;background:#F6F7FC;border:1px solid #d0dff5;"
        f"color:#3D4858;font-size:{font_size};font-weight:400;padding:{padding};"
        f"border-radius:4px;margin:0 4px 6px 0;white-space:nowrap;"
        f"font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;"
    )
    return "".join(f'<span style="{span_style}">{item.strip()}</span>' for item in items if item.strip())

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
# 2. КОНФИГУРАЦИЯ СТРАНИЦЫ
# ==========================================
st.set_page_config(layout="wide", page_title="Конструктор рассылок", initial_sidebar_state="expanded")

# Session state
for key, val in [
    ('data', {}), ('mode', None),
    ('theme', 'dark'), ('gost_tags', []), ('size_tags', []),
    ('authenticated', False), ('user', None),
    ('show_history', False), ('show_account_menu', False),
    ('_ct_reload', True), ('_ct_list', []),
    ('trusted_accounts', []), ('_del_brand_confirm', False),
    ('_autosave_checked', False), ('_autosave_data', None), ('_last_autosave_ts', 0.0),
    ('template_variant', 'default'),
    ('block_visibility', {}),
    ('custom_block_html', ''),
    ('block_custom_html', {}),
    ('custom_html_slot', 'CUSTOM'),
    ('header_style', 'default'),
    ('footer_style', 'default'),
]:
    if key not in st.session_state:
        st.session_state[key] = val

_BRANDS_SELECT = """
    SELECT u.id, u.login, u.brand_id, b.name as brand_name,
           b.logo_url, b.accent_color, b.site_url, b.catalog_url,
           b.about_url, b.delivery_url, b.contacts_url,
           b.vk_url, b.tg_url, b.footer_address,
           b.default_email, b.default_phone, b.default_city,
           b.logo_data, b.hero_bg_img, b.template_slug, b.secondary_color,
           b.layout_style, b.footer_bg_color, b.footer_bg_img,
           b.hero_text_color, b.hero_sub_color, b.body_title_color,
           b.body_text_color, b.card_text_color, b.footer_text_color
    FROM users u JOIN brands b ON u.brand_id = b.id
    WHERE u.login = %s
"""

# ── Авто-восстановление сессии + загрузка trusted_accounts из URL ──────────
if not st.session_state.authenticated:
    _saved_login = st.query_params.get("u", "")
    if _saved_login:
        conn = get_db()
        _c = conn.cursor()
        _c.execute(_BRANDS_SELECT, (_saved_login,))
        _row = _c.fetchone()
        conn.close()
        if _row:
            st.session_state.authenticated = True
            st.session_state.user = dict(_row)

# Загружаем список доверенных аккаунтов для этого устройства из URL
if not st.session_state.trusted_accounts:
    _ta_str = st.query_params.get("accounts", "")
    if _ta_str:
        st.session_state.trusted_accounts = [x for x in _ta_str.split(",") if x]

# Текущий аккаунт всегда в trusted-списке
if st.session_state.user:
    _cur_login = st.session_state.user.get('login', '')
    if _cur_login and _cur_login not in st.session_state.trusted_accounts:
        st.session_state.trusted_accounts.append(_cur_login)
        st.query_params["accounts"] = ",".join(st.session_state.trusted_accounts)
# ───────────────────────────────────────────────────────────────────────────

# ==========================================
# 3. CSS — ДИНАМИЧЕСКИЙ АКЦЕНТНЫЙ ЦВЕТ
# ==========================================
accent = st.session_state.user['accent_color'] if st.session_state.user else "#1e69da"

base_styles = f"""
<style>
    /* Прячем верхнее меню и футер */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{ background: transparent !important; }}
    
    /* Прячем мусор в правом верхнем углу (Share и т.д.) */
    header [data-testid="stToolbar"] {{ display: none !important; visibility: hidden !important; }}

    /* === ПОЛНОСТЬЮ УБИРАЕМ КНОПКИ САЙДБАРА (СТРЕЛКИ) === */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[kind="headerNoPadding"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    .block-container {{ padding-top: 1rem !important; padding-bottom: 0rem !important; }}
    .material-symbols-outlined {{
        font-family: 'Material Symbols Outlined' !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        display: inline-block;
        vertical-align: middle;
        line-height: 1;
        font-size: 22px;
    }}
    html, body, [class*="css"] {{ font-family: 'Plus Jakarta Sans', sans-serif !important; }}
    
    /* Стили кнопок конструктора */
    .stButton > button {{
        height: 90px !important; border-radius: 12px !important;
        transition: all 0.2s ease !important;
        display: flex !important; flex-direction: column !important;
        align-items: center !important; justify-content: center !important;
        gap: 5px !important; white-space: pre-wrap !important;
        text-align: center !important; box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
    .stButton > button:hover {{ transform: translateY(-2px) !important; box-shadow: 0 6px 12px rgba(0,0,0,0.08) !important; }}
    .stButton > button div p {{ font-size: 14px !important; font-weight: 700 !important; }}
    [data-testid="column"]:last-child button {{ height: 25px !important; line-height: 1 !important; padding: 0 !important; }}
    div.stButton > button[kind="primary"] {{ background-color: {accent} !important; color: white !important; height: 55px !important; border: none !important; font-weight: 700 !important; text-transform: uppercase; transform: none !important; }}
    div.stButton > button[kind="primary"]:hover {{ filter: brightness(.88) !important; transform: none !important; }}
    
    /* Стили вкладок */
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: {accent} !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ border-bottom-color: {accent} !important; }}
    
    /* Кнопки внутри expander'ов сайдбара — компактный размер */
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stButton > button {{
        height: 34px !important; padding: 0 10px !important;
        white-space: nowrap !important; overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stButton > button div p {{
        font-size: 13px !important; font-weight: 500 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="column"]:last-child button {{
        height: 34px !important; padding: 0 !important;
    }}

    /* Внутренние отступы popover — поле не прижато к краю */
    [data-baseweb="popover"] [data-testid="stVerticalBlock"] {{ padding: 6px 4px !important; gap: 12px !important; }}
    [data-testid="stPopover"] [data-baseweb="popover"] > div > div {{ padding: 16px !important; }}
</style>
"""

if st.session_state.theme == "light":
    theme_css = f"""<style>
    /* ── Фон ──────────────────────────────────────────────── */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlocksContainer"] {{ background-color: #e8ecf0 !important; }}

    /* ── Сайдбар ──────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: #f2f4f7 !important;
        box-shadow: 4px 0 16px rgba(163,177,198,0.35), -2px 0 0 rgba(255,255,255,0.9) !important;
        border-right: none !important;
    }}
    [data-testid="stSidebar"] * {{ color: #191c1e !important; }}

    /* ── Заголовки и текст ────────────────────────────────── */
    h1, h2, h3, h4, label, p, .stMarkdown {{ color: #191c1e !important; }}
    [data-testid="stMarkdownContainer"] p {{ color: #191c1e !important; }}
    [data-testid="stCaptionContainer"] p {{ color: #767586 !important; }}

    /* ── Вкладки (Silk) — отдельные floating кнопки ────────── */
    [data-testid="stTabs"] [role="tablist"] {{
        background-color: transparent !important;
        border-radius: 0 !important;
        padding: 6px 0 !important;
        box-shadow: none !important;
        gap: 8px !important;
        border-bottom: none !important;
    }}
    button[data-baseweb="tab"] {{
        border-radius: 12px !important;
        border-bottom: none !important;
        padding: 10px 20px !important;
        transition: all 0.18s ease !important;
        background: #f7f9fb !important;
        box-shadow: 6px 6px 12px rgba(163,177,198,0.4),
                    -6px -6px 12px rgba(255,255,255,0.9) !important;
    }}
    button[data-baseweb="tab"] p {{ color: #767586 !important; font-weight: 600 !important; font-size: 13px !important; }}
    button[data-baseweb="tab"]:hover p {{ color: #4648d4 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #eceef0 !important;
        box-shadow: inset 4px 4px 8px rgba(163,177,198,0.35),
                    inset -4px -4px 8px rgba(255,255,255,0.85) !important;
        border-bottom: none !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: {accent} !important; font-weight: 700 !important; }}

    /* ── Кнопки (Silk convex) ─────────────────────────────── */
    .stButton > button {{
        background-color: #f7f9fb !important;
        border: none !important;
        box-shadow: 6px 6px 14px rgba(163,177,198,0.55),
                    -6px -6px 14px rgba(255,255,255,0.95) !important;
        border-radius: 14px !important;
        color: #191c1e !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button p, .stButton > button div p,
    .stButton > button span {{ color: #191c1e !important; }}
    .stButton > button:hover {{
        box-shadow: 8px 8px 18px rgba(163,177,198,0.6),
                    -8px -8px 18px rgba(255,255,255,1.0) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button:active {{
        box-shadow: inset 4px 4px 8px rgba(163,177,198,0.3),
                    inset -4px -4px 8px rgba(255,255,255,0.7) !important;
        transform: scale(0.98) !important;
    }}
    /* Акцентная кнопка */
    div.stButton > button[kind="primary"] {{
        background-color: {accent} !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 6px 6px 14px rgba(0,0,0,0.18),
                    -4px -4px 10px rgba(255,255,255,0.5) !important;
    }}
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] div p,
    div.stButton > button[kind="primary"] span {{ color: #ffffff !important; }}
    div.stButton > button[kind="primary"]:hover {{
        filter: brightness(.9) !important;
        transform: translateY(-1px) !important;
        box-shadow: 8px 8px 18px rgba(0,0,0,0.22) !important;
    }}

    /* ── Инпуты (Silk concave) ────────────────────────────── */
    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
    .stTextInput > div > div, .stTextArea > div > div,
    [data-testid="stNumberInput"] > div > div {{
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }}
    .stTextInput input, .stTextArea textarea,
    [data-testid="stNumberInput"] input {{
        background-color: #f7f9fb !important;
        border: none !important;
        outline: none !important;
        box-shadow: inset 5px 5px 10px rgba(163,177,198,0.35),
                    inset -5px -5px 10px rgba(255,255,255,0.9) !important;
        border-radius: 12px !important;
        color: #191c1e !important;
        caret-color: #191c1e !important;
        padding: 10px 14px !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus,
    [data-testid="stNumberInput"] input:focus {{
        outline: none !important;
        box-shadow: inset 5px 5px 10px rgba(163,177,198,0.35),
                    inset -5px -5px 10px rgba(255,255,255,0.9),
                    0 0 0 2px rgba(70,72,212,0.18) !important;
    }}
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: #767586 !important; opacity: 1 !important; }}
    [data-testid="stTextInput"] button svg {{ fill: #767586 !important; }}
    [data-testid="stTextInput"] button:hover svg {{ fill: #464554 !important; }}

    /* ── Expander (Silk convex card) ──────────────────────── */
    [data-testid="stExpander"] {{
        background-color: #f7f9fb !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        border-radius: 16px !important;
        box-shadow: 8px 8px 18px rgba(163,177,198,0.5),
                    -8px -8px 18px rgba(255,255,255,0.95) !important;
    }}
    [data-testid="stExpander"] details summary,
    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary * {{
        background-color: transparent !important;
        color: #191c1e !important;
    }}
    [data-testid="stExpander"] details summary p {{ font-weight: 700 !important; color: #191c1e !important; }}
    [data-testid="stExpander"] details summary svg {{ fill: #464554 !important; }}

    /* ── Select ───────────────────────────────────────────── */
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div > div {{
        background-color: #f7f9fb !important;
        border: 1px solid rgba(163,177,198,0.2) !important;
        box-shadow: inset 4px 4px 8px rgba(163,177,198,0.3),
                    inset -4px -4px 8px rgba(255,255,255,0.85) !important;
        border-radius: 12px !important;
    }}
    div[data-baseweb="select"] * {{ color: #191c1e !important; }}
    div[data-baseweb="select"] svg {{ fill: #464554 !important; }}
    div[data-baseweb="popover"] > div {{
        background-color: #f7f9fb !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: 10px 10px 20px rgba(163,177,198,0.4),
                    -10px -10px 20px rgba(255,255,255,0.85) !important;
    }}
    ul[role="listbox"] {{ background-color: #f7f9fb !important; border-radius: 12px !important; }}
    ul[role="listbox"] li {{ color: #191c1e !important; background-color: transparent !important; }}
    ul[role="listbox"] li:hover,
    ul[role="listbox"] li[aria-selected="true"] {{ background-color: #eceef0 !important; color: {accent} !important; }}

    /* ── Popover ──────────────────────────────────────────── */
    [data-testid="stPopover"] > div > button {{
        background-color: #f7f9fb !important;
        border: none !important;
        box-shadow: 6px 6px 12px rgba(163,177,198,0.35),
                    -6px -6px 12px rgba(255,255,255,0.85) !important;
        border-radius: 12px !important;
        color: #191c1e !important;
    }}
    [data-testid="stPopover"] > div > button:hover {{
        box-shadow: 8px 8px 16px rgba(163,177,198,0.4),
                    -8px -8px 16px rgba(255,255,255,0.9) !important;
        color: #191c1e !important;
    }}
    [data-testid="stPopover"] > div > button p {{ color: #191c1e !important; }}
    div[data-testid="stPopoverBody"],
    [data-testid="stPopover"] [data-baseweb="popover"] > div {{
        background-color: #f7f9fb !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 18px !important;
        box-shadow: 12px 12px 24px rgba(163,177,198,0.4),
                    -12px -12px 24px rgba(255,255,255,0.85) !important;
    }}

    /* ── File uploader (Silk concave) ─────────────────────── */
    [data-testid="stFileUploader"] {{ background: transparent !important; }}
    [data-testid="stFileUploader"] section {{ background: transparent !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: #f2f4f7 !important;
        border: 2px dashed rgba(163,177,198,0.6) !important;
        border-radius: 14px !important;
        box-shadow: inset 5px 5px 10px rgba(163,177,198,0.3),
                    inset -5px -5px 10px rgba(255,255,255,0.9) !important;
    }}
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small {{ color: #464554 !important; }}
    [data-testid="stFileUploader"] button {{
        background-color: #f7f9fb !important;
        border: none !important;
        box-shadow: 4px 4px 8px rgba(163,177,198,0.3),
                    -4px -4px 8px rgba(255,255,255,0.8) !important;
        border-radius: 10px !important;
        color: #191c1e !important;
    }}

    /* ── Radio, Checkbox ──────────────────────────────────── */
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] > label {{ color: #191c1e !important; }}
    [data-testid="stRadio"] div[role="radiogroup"] label span {{ color: #464554 !important; }}
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] > label {{ color: #191c1e !important; }}

    /* ── Color picker ─────────────────────────────────────── */
    [data-testid="stColorPicker"] > label,
    [data-testid="stColorPicker"] > label p {{ color: #191c1e !important; }}
    /* Caption hex-кода под picker-ом */
    [data-testid="stColorPicker"] + [data-testid="stCaptionContainer"] p {{ color: #767586 !important; font-family: 'Plus Jakarta Sans', monospace !important; font-size: 11px !important; letter-spacing: .04em !important; }}

    /* ── Alert / Info ─────────────────────────────────────── */
    [data-testid="stAlert"] {{
        background-color: #f7f9fb !important;
        border: 1px solid rgba(163,177,198,0.3) !important;
        border-radius: 14px !important;
        box-shadow: 4px 4px 10px rgba(163,177,198,0.3),
                    -4px -4px 10px rgba(255,255,255,0.8) !important;
    }}
    [data-testid="stAlert"] p {{ color: #191c1e !important; }}

    /* ── Metric ───────────────────────────────────────────── */
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"] p {{ color: #767586 !important; }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: #191c1e !important; }}

    /* ── Toggle (silk) ────────────────────────────────────── */
    [data-testid="stToggle"] label {{ color: #191c1e !important; }}
    [data-testid="stToggle"] p {{ color: #191c1e !important; }}
    [data-testid="stToggle"] input + div {{
        background-color: #d0d2dc !important;
        box-shadow: inset 3px 3px 6px rgba(163,177,198,0.4),
                    inset -3px -3px 6px rgba(255,255,255,0.85) !important;
        border: none !important;
    }}
    [data-testid="stToggle"] input:checked + div {{
        background-color: #4648d4 !important;
        box-shadow: inset 3px 3px 6px rgba(50,50,180,0.3),
                    inset -3px -3px 6px rgba(100,100,255,0.2) !important;
    }}
    </style>"""
else:
    theme_css = f"""<style>
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlocksContainer"] {{ background-color: #0F1117 !important; color: #F3F4F6; }}
    [data-testid="stSidebar"] {{
        background-color: #161922 !important;
        box-shadow: 6px 0 20px rgba(0,0,0,0.4) !important;
        border-right: none !important;
    }}
    h1, h2, h3, label, p {{ color: #F3F4F6 !important; }}

    /* Вкладки — тёмная тема (floating кнопки) */
    [data-testid="stTabs"] [role="tablist"] {{
        background-color: transparent !important;
        border-radius: 0 !important;
        padding: 6px 0 !important;
        box-shadow: none !important;
        gap: 8px !important;
        border-bottom: none !important;
    }}
    button[data-baseweb="tab"] {{
        border-radius: 12px !important;
        border-bottom: none !important;
        padding: 10px 20px !important;
        transition: all 0.18s ease !important;
        background: #1A1C24 !important;
        box-shadow: 5px 5px 10px rgba(0,0,0,0.4),
                    -3px -3px 8px rgba(255,255,255,0.04) !important;
    }}
    button[data-baseweb="tab"] p {{ color: #9CA3AF !important; font-weight: 600 !important; font-size: 13px !important; }}
    button[data-baseweb="tab"]:hover p {{ color: {accent} !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #13151d !important;
        box-shadow: inset 3px 3px 7px rgba(0,0,0,0.45),
                    inset -2px -2px 5px rgba(255,255,255,0.03) !important;
        border-bottom: none !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: {accent} !important; font-weight: 700 !important; }}

    /* Кнопки — тёмная тема (Silk dark) */
    .stButton > button {{
        background-color: #1A1C24 !important;
        border: none !important;
        color: #F3F4F6 !important;
        box-shadow: 5px 5px 10px rgba(0,0,0,0.35),
                    -3px -3px 8px rgba(255,255,255,0.04) !important;
        border-radius: 14px !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button p, .stButton > button div p,
    .stButton > button span {{ color: #F3F4F6 !important; }}
    .stButton > button:hover {{
        background-color: #22253A !important;
        box-shadow: 7px 7px 14px rgba(0,0,0,0.4),
                    -3px -3px 8px rgba(255,255,255,0.05) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button:active {{
        box-shadow: inset 3px 3px 6px rgba(0,0,0,0.35),
                    inset -2px -2px 5px rgba(255,255,255,0.03) !important;
        transform: scale(0.98) !important;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {accent} !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 6px 6px 14px rgba(0,0,0,0.4), -2px -2px 8px rgba(255,255,255,0.05) !important;
    }}
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] div p,
    div.stButton > button[kind="primary"] span {{ color: #ffffff !important; }}
    div.stButton > button[kind="primary"]:hover {{
        filter: brightness(.85) !important;
        box-shadow: 8px 8px 18px rgba(0,0,0,0.45) !important;
        transform: translateY(-1px) !important;
    }}

    /* Глазок пароля — тёмная тема */
    [data-testid="stTextInput"] button svg {{ fill: #9CA3AF !important; }}
    [data-testid="stTextInput"] button:hover svg {{ fill: #D1D5DB !important; }}

    /* Инпуты — тёмная тема (Silk dark concave) */
    .stTextInput input, .stTextArea textarea {{
        background-color: #161922 !important;
        color: #F3F4F6 !important;
        caret-color: #F3F4F6 !important;
        border: none !important;
        box-shadow: inset 4px 4px 8px rgba(0,0,0,0.35),
                    inset -3px -3px 6px rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
    }}
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color: #6B7280 !important; opacity: 1 !important; }}

    /* Expander — тёмная тема */
    [data-testid="stExpander"] {{
        background-color: #161922 !important;
        border: none !important;
        border-radius: 16px !important;
        box-shadow: 6px 6px 12px rgba(0,0,0,0.4),
                    -3px -3px 8px rgba(255,255,255,0.03) !important;
    }}
    [data-testid="stExpander"] details summary,
    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary * {{ background-color: transparent !important; color: #F3F4F6 !important; }}
    [data-testid="stExpander"] details summary p {{ font-weight: 700 !important; }}
    [data-testid="stExpander"] details summary svg {{ fill: #F3F4F6 !important; }}

    /* Select — тёмная тема */
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div > div {{
        background-color: #161922 !important;
        border: none !important;
        box-shadow: inset 3px 3px 6px rgba(0,0,0,0.3),
                    inset -2px -2px 5px rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
    }}
    div[data-baseweb="select"] * {{ color: #F3F4F6 !important; }}
    div[data-baseweb="select"] svg {{ fill: #F3F4F6 !important; }}
    div[data-baseweb="popover"] > div {{
        background-color: #1A1C24 !important;
        border: none !important;
        border-radius: 14px !important;
        box-shadow: 8px 8px 16px rgba(0,0,0,0.5), -2px -2px 8px rgba(255,255,255,0.03) !important;
    }}
    ul[role="listbox"] {{ background-color: #1A1C24 !important; border-radius: 12px !important; }}
    ul[role="listbox"] li {{ color: #F3F4F6 !important; background-color: transparent !important; }}
    ul[role="listbox"] li:hover, ul[role="listbox"] li[aria-selected="true"] {{ background-color: #374151 !important; color: #60a5fa !important; }}
    /* Popover «Сохранить» — тёмная тема */
    [data-testid="stPopover"] > div > button {{
        background-color: #1A1C24 !important;
        border: 1px solid #3e4452 !important;
        color: #F3F4F6 !important;
    }}
    [data-testid="stPopover"] > div > button:hover {{ background-color: #2D3140 !important; color: #F3F4F6 !important; border-color: #5a627a !important; }}
    [data-testid="stPopover"] > div > button p {{ color: #F3F4F6 !important; }}
    div[data-testid="stPopoverBody"], [data-testid="stPopover"] [data-baseweb="popover"] > div {{
        background-color: #1E2130 !important; border: 1px solid #374151 !important;
        border-radius: 12px !important; padding: 18px !important;
        box-shadow: 0 8px 28px rgba(0,0,0,.45) !important;
    }}

    /* File uploader — тёмная тема */
    [data-testid="stFileUploader"] {{ background: transparent !important; }}
    [data-testid="stFileUploader"] section {{ background: transparent !important; }}
    [data-testid="stFileUploaderDropzone"] {{
        background-color: #1F2937 !important;
        border: 1px dashed #374151 !important;
        border-radius: 8px !important;
    }}
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {{ color: #D1D5DB !important; }}
    [data-testid="stFileUploader"] button {{
        background-color: #374151 !important;
        border: 1px solid #4B5563 !important;
        color: #F3F4F6 !important;
    }}

    /* Radio кнопки — тёмная тема */
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] > label {{ color: #F3F4F6 !important; }}
    [data-testid="stRadio"] div[role="radiogroup"] label span {{ color: #D1D5DB !important; }}

    /* Checkbox — тёмная тема */
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] > label {{ color: #F3F4F6 !important; }}

    /* Caption — тёмная тема */
    [data-testid="stCaptionContainer"] p {{ color: #9CA3AF !important; }}

    /* Color picker — тёмная тема */
    [data-testid="stColorPicker"] > label {{ color: #F3F4F6 !important; }}
    [data-testid="stColorPicker"] > label p {{ color: #F3F4F6 !important; }}

    /* Markdown внутри основного контента — тёмная тема */
    [data-testid="stMarkdownContainer"] p {{ color: #F3F4F6 !important; }}

    /* Alert / Info / Warning — тёмная тема */
    [data-testid="stAlert"] {{
        background-color: #1e3a5f !important;
        border: 1px solid #2563eb !important;
        border-radius: 8px !important;
    }}
    [data-testid="stAlert"] p {{ color: #93c5fd !important; }}

    /* Metric — тёмная тема */
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"] p {{ color: #9CA3AF !important; }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: #F3F4F6 !important; }}

    /* ── SK-карточки в тёмной теме ────────────────────────── */
    .sk-card {{
        background: #161922 !important;
        box-shadow: 6px 6px 12px rgba(0,0,0,0.4),
                    -3px -3px 8px rgba(255,255,255,0.03) !important;
    }}
    .sk-title {{ color: #F3F4F6 !important; }}

    /* ── Toggle (silk dark) ───────────────────────────────── */
    [data-testid="stToggle"] label {{ color: #d8daf0 !important; }}
    [data-testid="stToggle"] p {{ color: #d8daf0 !important; }}
    [data-testid="stToggle"] input + div {{
        background-color: #1e2030 !important;
        box-shadow: inset 3px 3px 6px rgba(0,0,0,0.4),
                    inset -2px -2px 5px rgba(255,255,255,0.04) !important;
        border: none !important;
    }}
    [data-testid="stToggle"] input:checked + div {{
        background-color: #4648d4 !important;
        box-shadow: inset 2px 2px 4px rgba(20,20,120,0.4),
                    inset -2px -2px 4px rgba(100,100,255,0.15) !important;
    }}
    .sk-page-title {{ color: #F3F4F6 !important; }}
    .sk-page-sub {{ color: #9CA3AF !important; }}
    .sk-label {{ color: #D1D5DB !important; }}
    .sk-label-sub {{ color: #6B7280 !important; }}
    </style>"""

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)
st.markdown(base_styles, unsafe_allow_html=True)
st.markdown(theme_css, unsafe_allow_html=True)


# ==========================================
# 4. ЭКРАН АВТОРИЗАЦИИ
# ==========================================
if not st.session_state.authenticated:
    # Кнопка темы в правом верхнем углу (доступна до входа)
    _login_tl, _login_tr = st.columns([12, 1])
    with _login_tr:
        _login_theme_icon = "☀" if st.session_state.theme == "dark" else "☾"
        if st.button(_login_theme_icon, key="theme_btn_login"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

    st.markdown("""
    <div style="max-width:420px; margin:40px auto 0;">
        <h1 style="text-align:center; margin-bottom:8px;">Вход в конструктор</h1>
        <p style="text-align:center; opacity:.6; margin-bottom:32px;">Введите логин и пароль вашего бренда</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        login_val = st.text_input("Логин", placeholder="stalmetural", key="login_input")
        pass_val  = st.text_input("Пароль", type="password", placeholder="••••••••", key="pass_input")
        if st.button("ВОЙТИ", type="primary", use_container_width=True):
            user = check_login(login_val, pass_val)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.query_params["u"] = user['login']
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

    st.stop()

# ==========================================
# 5. ХЕЛПЕРЫ (после авторизации)
# ==========================================
user   = st.session_state.user
brand  = user  # содержит все поля бренда

def set_mode(name):
    st.session_state.mode = name
    st.session_state.template_variant = 'default'
    st.session_state.block_visibility = {}
    st.session_state.custom_block_html = ''
    st.session_state.block_custom_html = {}
    st.session_state.custom_html_slot = 'CUSTOM'
    st.session_state.header_style = 'default'
    st.session_state.footer_style = 'default'
    st.session_state['_autosave_checked'] = False
    st.session_state['_autosave_data'] = None
    st.session_state['_last_autosave_ts'] = 0.0

def cached_input(label, key, default="", placeholder="", col=None, area=False, height=100, max_chars=None, help=None):
    current = st.session_state.data.get(key, "")
    ph = placeholder or default
    widget = (col if col else st)
    if area:
        val = widget.text_area(label, value=current, placeholder=ph, key=key, height=height, max_chars=max_chars, help=help)
    else:
        val = widget.text_input(label, value=current, placeholder=ph, key=key, max_chars=max_chars, help=help)
    st.session_state.data[key] = val
    return val if val else default

def image_input(label, key, default="", placeholder="", col=None):
    widget = col if col else st
    current = st.session_state.data.get(key, "")
    current_url = "" if current.startswith("data:") else current

    url_val = widget.text_input(
        label,
        value=current_url,
        placeholder=placeholder or default or "https://...",
        key=f"__url_{key}",
    )
    uploaded = widget.file_uploader(
        "📎 или загрузить файл с компьютера",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        key=f"__up_{key}",
    )

    if uploaded is not None:
        cache_key = f"__b64_{key}"
        cached = st.session_state.get(cache_key, {})
        if cached.get("name") == uploaded.name and cached.get("size") == uploaded.size:
            val = cached["data"]
        else:
            b64_data = base64.b64encode(uploaded.read()).decode()
            mime = uploaded.type or "image/jpeg"
            val = f"data:{mime};base64,{b64_data}"
            st.session_state[cache_key] = {"name": uploaded.name, "size": uploaded.size, "data": val}
    elif url_val:
        val = url_val
    else:
        val = default

    st.session_state.data[key] = val
    return val if val else default

MENU_ITEMS_ALL = {
    "stock":    {"title": "ПОСТУПЛЕНИЕ",    "desc": "Наличие, ГОСТы"},
    "promo":    {"title": "СПЕЦПРЕДЛОЖЕНИЕ","desc": "Товары, таймер"},
    "services": {"title": "УСЛУГИ",         "desc": "Обработка, резка"},
    "cases":    {"title": "ОТГРУЗКИ",       "desc": "Фото, статистика"},
    "expert":   {"title": "ЭКСПЕРТНОЕ",     "desc": "Статьи и советы"},
}
MENU_ITEMS_INMETPROM = {
    "stock":              {"title": "ПОСТУПЛЕНИЕ",     "desc": "Наличие, ГОСТы"},
    "promo_inmetprom":    {"title": "СПЕЦПРЕДЛОЖЕНИЕ", "desc": "Товары, скидки"},
    "services":           {"title": "УСЛУГИ",          "desc": "Обработка, резка"},
    "cases":              {"title": "ОТГРУЗКИ",        "desc": "Фото, статистика"},
    "expert":             {"title": "ЭКСПЕРТНОЕ",      "desc": "Статьи и советы"},
}

# Варианты дизайна для каждого режима:
# (id_варианта, Название, Описание, имя_файла_суффикс_или_None)
TEMPLATE_VARIANTS = {
    "stock": [
        ("default",   "Классический", "Широкий фоновый баннер, таблица товаров с ценами", None),
        ("inmetprom", "Современный",  "Баннер с фото товара справа, описание в 2 строки", "inmetprom"),
    ],
    "promo": [
        ("default",   "Стандарт", "Таймер обратного отсчёта + скидка на фоне баннера", None),
        ("inmetprom", "Яркий",    "Баннер с фото товара справа, без таймера", "inmetprom"),
    ],
    "promo_inmetprom": [
        ("inmetprom", "Яркий", "Баннер с фото товара справа, без таймера", "inmetprom"),
    ],
    "services": [("default", "Стандарт", "Список услуг с иконками и описанием", None)],
    "cases":    [
        ("default",   "Стандарт",   "Фото отгрузки + статистика + блок услуг", None),
        ("inmetprom", "Современный", "Баннер с фото, 3 товара + 4 кейса отгрузок", "inmetprom"),
    ],
    "expert":   [
        ("default",   "Стандарт",   "Экспертная статья с иллюстрацией справа", None),
        ("inmetprom", "Современный", "Баннер с фото, статья + 3 товара + категории", "inmetprom"),
    ],
}

# Поддержка замены шапки/футера через BLOCK-маркеры
HEADER_BLOCK_SUPPORTED = {
    "stock": {"default": True, "inmetprom": True},
    "promo": {"default": False, "inmetprom": True},
    "promo_inmetprom": {"inmetprom": True},
    "cases": {"default": False},
    "services": {"default": False},
    "expert": {"default": False},
}
FOOTER_BLOCK_SUPPORTED = {
    "stock": {"default": True, "inmetprom": True},
    "promo": {"default": True, "inmetprom": True},
    "promo_inmetprom": {"inmetprom": True},
    "cases": {"default": False},
    "services": {"default": False},
    "expert": {"default": False},
}

# Блоки которые можно скрыть: {mode: [(block_id, label, hint), ...]}
OPTIONAL_BLOCKS = {
    "stock": {
        "default":   [("PRODUCTS", "Таблица товаров", "Раздел «Также в наличии на складе» с ценами и ГОСТами")],
        "inmetprom": [],
    },
    "promo": {
        "default":   [
            ("HERO",     "Фоновый баннер",  "Изображение со скидкой и заголовком на фоне фото"),
            ("HERO_BTN", "Кнопка каталога", "Кнопка «Перейти в каталог» после блока таймера"),
        ],
        "inmetprom": [
            ("CONSULTATION", "Блок консультации", "«Не нашли нужную позицию?» — форма запроса"),
            ("WHY_US",       "Почему выбирают нас", "Ключевые преимущества компании"),
        ],
    },
    "promo_inmetprom": {
        "inmetprom": [
            ("CONSULTATION", "Блок консультации", "«Не нашли нужную позицию?» — форма запроса"),
            ("WHY_US",       "Почему выбирают нас", "Ключевые преимущества компании"),
        ],
    },
    "cases": {
        "default": [
            ("SERVICES", "Блок услуг",          "«Не тратьте время на подгонку» — 3 услуги"),
            ("WHY_US",   "Почему выбирают нас",  "Ключевые преимущества компании"),
            ("MANAGER",  "Блок менеджера",       "CTA с контактом менеджера для связи"),
        ],
        "inmetprom": [],
    },
    "expert":   {"default": [], "inmetprom": []},
    "services": {"default": []},
}

def get_menu_items(brand_name: str) -> dict:
    if brand_name == "Инметпром":
        return MENU_ITEMS_INMETPROM
    return MENU_ITEMS_ALL
# ==========================================
# 6. БОКОВАЯ ПАНЕЛЬ
# ==========================================
_sidebar_dark = st.session_state.theme == "dark"
_sb_bg      = "#161922" if _sidebar_dark else "#F5F5F7"
_sb_txt     = "#F5F5F7" if _sidebar_dark else "#1D1D1F"
_sb_sub     = "rgba(245,245,247,.45)" if _sidebar_dark else "rgba(29,29,31,.4)"
_sb_btn_bg  = "rgba(255,255,255,.07)" if _sidebar_dark else "rgba(0,0,0,.06)"
_sb_btn_hover    = "#2D3140" if _sidebar_dark else "#E5E7EB"
_sb_btn_hover_bd = "#5a627a" if _sidebar_dark else "#9CA3AF"
_sb_div     = "rgba(255,255,255,.10)" if _sidebar_dark else "rgba(0,0,0,.08)"

@st.cache_resource
def _load_all_accounts():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.login, b.name, b.accent_color
        FROM users u JOIN brands b ON u.brand_id = b.id
        ORDER BY b.name
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

_all_accounts = _load_all_accounts()

@st.dialog("Новый бренд", width="large")
def _dialog_new_brand():
    _dlg_dark = st.session_state.get('theme', 'dark') == 'dark'
    _dlg_bg   = "#1e1e1e" if _dlg_dark else "#ffffff"
    _dlg_brd  = "#383838" if _dlg_dark else "#e2e6ef"
    _dlg_txt  = "#efefef" if _dlg_dark else "#191c1e"
    _dlg_sub  = "#909090" if _dlg_dark else "#8a92a8"
    _dlg_inp  = "#272727" if _dlg_dark else "#ffffff"
    _dlg_inp2 = "#2e2e2e" if _dlg_dark else "#f7f9fb"

    st.markdown(f"""<style>
    /* Прячем хедер пока открыт диалог */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    /* Оверлей на весь экран */
    [data-testid="stDialog"] {{
        align-items: center !important;
        padding-top: 0 !important;
        background-color: rgba(0,0,0,0.55) !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 9999 !important;
    }}
    [data-testid="stDialog"] > div {{
        border-radius: 20px !important;
        overflow: hidden !important;
    }}
    /* Весь контейнер диалога + скролл-область */
    div[role="dialog"],
    div[role="dialog"] > div,
    [data-testid="stDialogScrollableContent"],
    [data-testid="stDialogScrollableContent"] > div {{
        background-color: {_dlg_bg} !important;
        border-radius: 20px !important;
    }}
    /* Заголовок «Новый бренд» + кнопка закрытия */
    div[role="dialog"] h2 {{ color: {_dlg_txt} !important; }}
    div[role="dialog"] button[aria-label="Close"] {{
        color: {_dlg_sub} !important;
    }}
    /* Лейблы и текст */
    div[role="dialog"] label {{ color: {_dlg_txt} !important; font-size:13px !important; font-weight:500 !important; }}
    div[role="dialog"] p, div[role="dialog"] span {{ color: {_dlg_txt} !important; }}
    /* Инпуты */
    div[role="dialog"] .stTextInput > div {{
        background-color: {_dlg_inp} !important;
        border: 1px solid {_dlg_brd} !important;
        border-radius: 8px !important;
    }}
    div[role="dialog"] input[type="text"],
    div[role="dialog"] input[type="password"] {{
        background-color: {_dlg_inp} !important;
        color: {_dlg_txt} !important;
    }}
    div[role="dialog"] input::placeholder {{ color: {_dlg_sub} !important; }}
    div[role="dialog"] hr {{ border-color: {_dlg_brd} !important; opacity:.5; }}
    </style>""", unsafe_allow_html=True)

    st.markdown(f'<p style="color:{_dlg_sub};font-size:13px;margin:0 0 16px">Заполните основные данные. Остальное можно настроить позже в разделе «Бренд».</p>', unsafe_allow_html=True)

    # Строка 1: Название + поле hex цвета + свотч
    r1a, r1b, r1c = st.columns([10, 5, 1])
    _bname = r1a.text_input("Название компании *", placeholder="Стальметурал", key="_nb_name")
    _bcolor_hex = r1b.text_input("Цвет бренда (HEX)", value="#1e69da", key="_nb_color_hex")
    _bcolor = _bcolor_hex if _bcolor_hex.startswith('#') and len(_bcolor_hex) in (4, 7) else "#1e69da"
    r1c.markdown(f'<div style="width:36px;height:36px;background:{_bcolor};border-radius:8px;border:1px solid {_dlg_brd};margin-top:28px"></div>', unsafe_allow_html=True)

    # Строка 2: Email | Телефон
    r2a, r2b = st.columns(2)
    _bemail = r2a.text_input("Email", placeholder="info@company.com", key="_nb_email")
    _bphone = r2b.text_input("Телефон", placeholder="+7 (000) 000-00-00", key="_nb_phone")

    # Строка 3: Сайт | Каталог
    r3a, r3b = st.columns(2)
    _bsite = r3a.text_input("Сайт", placeholder="https://company.com", key="_nb_site")
    _bcat  = r3b.text_input("Каталог (ссылка)", placeholder="https://company.com/catalog/", key="_nb_cat")

    # Строка 4: Адрес (полная ширина)
    _bfoot = st.text_input("Адрес для футера письма", placeholder='ООО "Компания", г. Город, ул. Улица, д. 1', key="_nb_foot")

    st.divider()
    st.markdown(f'<p style="color:{_dlg_sub};font-size:12px;font-weight:600;letter-spacing:.5px;margin:0 0 8px">ДАННЫЕ ДЛЯ ВХОДА В КОНСТРУКТОР</p>', unsafe_allow_html=True)

    # Строка 5: Логин | Пароль
    r5a, r5b = st.columns(2)
    _blogin = r5a.text_input("Логин *", key="_nb_login")
    _bpass  = r5b.text_input("Пароль *", type="password", key="_nb_pass")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("Создать бренд", key="_nb_save", use_container_width=True, type="primary"):
        if not _bname.strip():
            st.error("Введите название компании")
        elif not _blogin.strip() or not _bpass.strip():
            st.error("Введите логин и пароль")
        else:
            _new_id = save_brand(
                None, _bname.strip(), _bcolor, '', '', '',
                _bsite, _bcat, '', '', '',
                _bfoot, _bemail, _bphone, ''
            )
            create_user_for_brand(_blogin.strip(), _bpass.strip(), _new_id)
            _load_all_accounts.clear()
            st.success(f"Бренд «{_bname.strip()}» создан! Войдите через «Войти в другой аккаунт».")

with st.sidebar:
    # --- Шапка бренда ---
    st.markdown(f"""
    <style>
    section[data-testid="stSidebar"] {{
        background: {_sb_bg} !important;
    }}
    /* Все кнопки в сайдбаре — одинаковая ширина и высота */
    section[data-testid="stSidebar"] .stButton > button {{
        width: 100% !important;
        height: 44px !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        letter-spacing: -.1px !important;
        background: {_sb_btn_bg} !important;
        color: {_sb_txt} !important;
        border: 1px solid {_sb_div} !important;
        margin-bottom: 0 !important;
        text-align: left !important;
        padding: 0 16px !important;
        box-shadow: none !important;
        transform: none !important;
        white-space: nowrap !important;
        transition: background .18s ease, border-color .18s ease !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {_sb_btn_hover} !important;
        color: {_sb_txt} !important;
        border-color: {_sb_btn_hover_bd} !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover p {{ color: {_sb_txt} !important; }}
    /* Кнопка Выйти — особый стиль (по ключу, чтобы не цеплять остальные) */
    .st-key-sb_logout button {{
        background: transparent !important;
        color: {_sb_sub} !important;
        border: 1px solid {_sb_div} !important;
    }}
    .st-key-sb_logout button:hover {{
        background: rgba(255,59,48,.12) !important;
        color: #FF3B30 !important;
        border-color: rgba(255,59,48,.3) !important;
    }}
    .st-key-sb_logout button:hover p {{ color: #FF3B30 !important; }}
    .sb-brand-block {{ padding: 20px 4px 4px; }}
    .sb-brand-label {{ font-size:10px; font-weight:600; letter-spacing:1.4px; text-transform:uppercase; color:{_sb_sub}; margin-bottom:4px; }}
    .sb-brand-name  {{ font-size:20px; font-weight:700; letter-spacing:-.4px; color:{_sb_txt}; line-height:1.2; }}
    .sb-brand-login {{ font-size:12px; color:{_sb_sub}; margin-top:2px; }}
    .sb-divider     {{ height:1px; background:{_sb_div}; margin:14px 0; border:none; }}
    .sb-acc-label   {{ font-size:10px; font-weight:600; letter-spacing:1.3px; text-transform:uppercase; color:{_sb_sub}; margin:0 4px 8px; }}
    </style>
    <div class="sb-brand-block">
        <div class="sb-brand-label">Бренд</div>
        <div class="sb-brand-name">{brand['brand_name']}</div>
        <div class="sb-brand-login">{user['login']}</div>
    </div>
    <div class="sb-divider"></div>
    """, unsafe_allow_html=True)

    if st.session_state.mode is not None:
        if st.button("← Главное меню", key="sb_back", use_container_width=True):
            if st.session_state.data:
                upsert_autosave(
                    brand['brand_id'],
                    st.session_state.mode,
                    dict(st.session_state.data),
                    st.session_state.get('template_variant', 'default')
                )
            set_mode(None)
            st.rerun()

    hist_label = "История проектов" if not st.session_state.show_history else "← Конструктор"
    if st.button(hist_label, key="sb_hist", use_container_width=True):
        st.session_state.show_history = not st.session_state.show_history
        st.rerun()

    # --- Аккаунты (только в главном меню) ---
    if st.session_state.mode is None and not st.session_state.show_history:
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        # Быстрое переключение между уже залогиненными аккаунтами
        _trusted = st.session_state.get('trusted_accounts', [])
        _trusted_others = [l for l in _trusted if l != user['login']]
        if _trusted_others:
            with st.expander("Переключить аккаунт"):
                for _tl in _trusted_others:
                    _ta_name = next((a['name'] for a in _all_accounts if a['login'] == _tl), _tl)
                    if st.button(_ta_name, key=f"sb_sw_{_tl}", use_container_width=True):
                        _sw_conn = get_db()
                        _sw_c = _sw_conn.cursor()
                        _sw_c.execute(_BRANDS_SELECT, (_tl,))
                        _sw_row = _sw_c.fetchone()
                        _sw_conn.close()
                        if _sw_row:
                            st.session_state.user          = dict(_sw_row)
                            st.session_state.authenticated = True
                            st.session_state.data          = {}
                            st.session_state.mode          = None
                            st.session_state.show_history  = False
                            st.session_state['_ct_reload'] = True
                            st.query_params["u"] = _tl
                            st.rerun()

        # Вход в новый аккаунт (требует пароль)
        with st.expander("Войти в другой аккаунт"):
            _sw_login = st.text_input("Логин", key="sw_login_inp")
            _sw_pass  = st.text_input("Пароль", type="password", key="sw_pass_inp")
            if st.button("Войти", key="sw_login_btn", use_container_width=True, type="primary"):
                _sw_result = check_login(_sw_login, _sw_pass)
                if _sw_result:
                    if _sw_login not in st.session_state.trusted_accounts:
                        st.session_state.trusted_accounts.append(_sw_login)
                        st.query_params["accounts"] = ",".join(st.session_state.trusted_accounts)
                    st.session_state.user          = _sw_result
                    st.session_state.authenticated = True
                    st.session_state.data          = {}
                    st.session_state.mode          = None
                    st.session_state.show_history  = False
                    st.session_state['_ct_reload'] = True
                    st.query_params["u"] = _sw_login
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")

    # --- Добавить новый бренд ---
    if st.session_state.mode is None and not st.session_state.show_history:
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
        if st.button("＋ Добавить бренд", key="_nb_open_btn", use_container_width=True):
            _dialog_new_brand()

    # --- Шаблоны контактов ---
    if st.session_state.mode is not None and not st.session_state.show_history:
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
        with st.expander("Шаблоны контактов"):
            if st.session_state.get('_ct_reload', True):
                st.session_state['_ct_list'] = load_contact_templates(brand['brand_id'])
                st.session_state['_ct_reload'] = False
            templates_ct = st.session_state.get('_ct_list', [])

            if templates_ct:
                for tmpl in templates_ct:
                    col_t, col_d = st.columns([4, 1])
                    if col_t.button(tmpl['name'], key=f"ct_apply_{tmpl['id']}", use_container_width=True):
                        for k, v in json.loads(tmpl['data_json']).items():
                            st.session_state.data[k] = v
                            st.session_state[k] = v  # обновляем состояние виджета
                        st.rerun()
                    if col_d.button("✕", key=f"ct_del_{tmpl['id']}", use_container_width=True):
                        delete_contact_template(tmpl['id'])
                        st.session_state['_ct_reload'] = True
                        st.rerun()
            else:
                st.caption("Нет сохранённых шаблонов")

            st.markdown("---")
            ct_new_name = st.text_input("Название", placeholder="Казахстан", key="ct_new_name",
                                        label_visibility="collapsed")
            if st.button("Сохранить текущие контакты", key="ct_save", use_container_width=True):
                if ct_new_name.strip():
                    save_contact_template(brand['brand_id'], ct_new_name.strip(), st.session_state.data)
                    st.session_state['_ct_reload'] = True
                    st.success(f"Сохранено: «{ct_new_name}»")
                    st.rerun()
                else:
                    st.warning("Введите название шаблона")


    # --- Выйти (только в главном меню, не внутри шаблона) ---
    if st.session_state.mode is None and not st.session_state.show_history:
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
        if st.button("Выйти", key="sb_logout", use_container_width=True):
            for k in ['authenticated', 'user', 'data', 'mode',
                      'gost_tags', 'size_tags', 'show_history']:
                if k in st.session_state:
                    del st.session_state[k]
            st.query_params.clear()
            st.rerun()

# ==========================================
# 7. ВЕРХНЯЯ ПАНЕЛЬ — кнопка темы
# ==========================================
_top_l, _top_theme = st.columns([12, 1])

with _top_theme:
    _theme_icon = "☀" if st.session_state.theme == "dark" else "☾"
    if st.button(_theme_icon, key="theme_btn_top"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ==========================================
# 8. ИСТОРИЯ ПРОЕКТОВ
# ==========================================
_card_bg     = "rgba(255,255,255,.05)" if _sidebar_dark else "#FFFFFF"
_card_border = "rgba(255,255,255,.10)" if _sidebar_dark else "rgba(0,0,0,.08)"
_tag_colors  = {
    "stock":    ("#E8F5E9","#2E7D32","#1B5E20"),
    "promo":    ("#FFF3E0","#E65100","#BF360C"),
    "services": ("#E3F2FD","#1565C0","#0D47A1"),
    "cases":    ("#F3E5F5","#6A1B9A","#4A148C"),
    "expert":   ("#E8EAF6","#283593","#1A237E"),
}
_tag_colors_dark = {
    "stock":    ("rgba(46,125,50,.25)","#81C784","#81C784"),
    "promo":    ("rgba(230,81,0,.25)","#FFB74D","#FFB74D"),
    "services": ("rgba(21,101,192,.25)","#64B5F6","#64B5F6"),
    "cases":    ("rgba(106,27,154,.25)","#CE93D8","#CE93D8"),
    "expert":   ("rgba(40,53,147,.25)","#9FA8DA","#9FA8DA"),
}

if st.session_state.show_history:
    st.markdown(f"""
    <h1 style="font-size:32px; font-weight:700; letter-spacing:-.6px; margin-bottom:24px;">
        История проектов
    </h1>
    """, unsafe_allow_html=True)

    projects = load_projects(brand['brand_id'])

    if not projects:
        st.markdown(f"""
        <div style="padding:40px 32px; border-radius:16px;
             background:{_card_bg}; border:1px solid {_card_border};
             text-align:center; color:{_sb_sub}; font-size:15px;">
            Проектов пока нет.<br>Создайте письмо и нажмите «Сохранить проект».
        </div>
        """, unsafe_allow_html=True)
    else:
        menu_items = get_menu_items(brand['brand_name'])
        for proj in projects:
            m_id   = proj['template_mode']
            m_title = menu_items.get(m_id, {}).get('title', m_id)
            tcolors = (_tag_colors_dark if _sidebar_dark else _tag_colors).get(
                m_id, ("rgba(120,120,128,.2)","#888","#666"))
            tag_bg, tag_txt, _ = tcolors

            col_a, col_b, col_c = st.columns([6, 1, 1])
            with col_a:
                st.markdown(f"""
                <div style="padding:16px 20px; border-radius:14px;
                     background:{_card_bg}; border:1px solid {_card_border};
                     display:flex; align-items:center; gap:14px;">
                    <div>
                        <div style="font-size:15px; font-weight:600;
                             color:{_sb_txt}; letter-spacing:-.2px; margin-bottom:5px;">
                            {proj['project_name']}
                        </div>
                        <span style="display:inline-block; padding:2px 9px;
                              border-radius:20px; font-size:11px; font-weight:600;
                              letter-spacing:.4px; text-transform:uppercase;
                              background:{tag_bg}; color:{tag_txt};">
                            {m_title}
                        </span>
                        <span style="font-size:12px; color:{_sb_sub}; margin-left:8px;">
                            {proj['created_at']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("Открыть", key=f"open_{proj['id']}", use_container_width=True):
                    full = load_project_data(proj['id'])
                    st.session_state.data      = json.loads(full['data_json'])
                    st.session_state.gost_tags = json.loads(full['gost_tags'])
                    st.session_state.size_tags = json.loads(full['size_tags'])
                    st.session_state.mode      = full['template_mode']
                    st.session_state.show_history = False
                    st.rerun()
            with col_c:
                if st.button("Удалить", key=f"del_{proj['id']}", use_container_width=True):
                    delete_project(proj['id'])
                    st.rerun()
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 8. ГЛАВНОЕ МЕНЮ ШАБЛОНОВ
# ==========================================
if st.session_state.mode is None:
    st.markdown(f"<h1 style='text-align:center;'>Конструктор рассылок</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; opacity:0.7;'>Бренд: <b>{brand['brand_name']}</b> · Выберите шаблон</p><br>", unsafe_allow_html=True)

    menu_items = get_menu_items(brand['brand_name'])
    cols = st.columns(5)
    for i, (m_id, info) in enumerate(menu_items.items()):
        with cols[i]:
            if st.button(f"{info['title']}\n{info['desc']}", key=m_id, use_container_width=True):
                set_mode(m_id)
                st.rerun()

else:
    # ==========================================
    # 9. РЕДАКТОР
    # ==========================================
    mode = st.session_state.mode
    menu_items = get_menu_items(brand['brand_name'])
    if 'data' not in st.session_state:
        st.session_state.data = {}
    data = st.session_state.data

    _title_col, _save_col = st.columns([5, 1])
    with _title_col:
        st.title(f"Шаблон: {menu_items[mode]['title']}")
    with _save_col:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        with st.popover("Сохранить", use_container_width=True):
            proj_name = st.text_input(
                "Название проекта",
                placeholder="Оставьте пустым для авто",
                key="save_project_name"
            )
            if st.button("Сохранить проект", use_container_width=True, key="save_btn", type="primary"):
                name = proj_name.strip() or f"{menu_items[mode]['title']} {datetime.now(tz=_YEK).strftime('%d.%m %H:%M')}"
                save_project(
                    brand_id      = brand['brand_id'],
                    template_mode = mode,
                    project_name  = name,
                    data_dict     = {k: v for k, v in st.session_state.data.items()},
                    gost_tags     = st.session_state.gost_tags,
                    size_tags     = st.session_state.size_tags
                )
                st.success(f"Сохранено: «{name}»")

    # ── Периодический автосейв (раз в 30 сек на любом ререндере) ─────────────
    _ts = time.time()
    if st.session_state.data and (_ts - st.session_state.get('_last_autosave_ts', 0.0)) > 30:
        upsert_autosave(brand['brand_id'], mode, dict(st.session_state.data),
                        st.session_state.get('template_variant', 'default'))
        st.session_state['_last_autosave_ts'] = _ts

    # ── Проверка наличия черновика — один раз при входе в режим ──────────────
    if not st.session_state.get('_autosave_checked', False):
        st.session_state['_autosave_data'] = load_autosave(brand['brand_id'], mode)
        st.session_state['_autosave_checked'] = True
    _as = st.session_state.get('_autosave_data')
    if _as:
        _as_d, _as_v, _as_t = _as
        st.markdown("""<style>
        .st-key-_as_restore button, .st-key-_as_dismiss button {
            min-height: 28px !important; height: 28px !important;
            padding: 0 8px !important; font-size: 12px !important;
        }
        </style>""", unsafe_allow_html=True)
        _as_wrap, _ = st.columns([2, 1])
        with _as_wrap:
            with st.container(border=True):
                _asc1, _asc2, _asc3 = st.columns([5, 1.5, 0.6])
                _asc1.markdown(f"Черновик от **{_as_t}**")
                if _asc2.button("↩ Восстановить", key="_as_restore", use_container_width=True):
                    for k, v in _as_d.items():
                        st.session_state.data[k] = v
                        st.session_state[k] = v
                    st.session_state.template_variant = _as_v
                    st.session_state['_autosave_data'] = None
                    st.rerun()
                if _asc3.button("✕", key="_as_dismiss", use_container_width=True):
                    st.session_state['_autosave_data'] = None
                    st.rerun()
    # ──────────────────────────────────────────────────────────────────────────

    # ==========================================
# FRAGMENT FUNCTIONS FOR EACH TAB
# (each tab rerenders independently on interaction)
# ==========================================

    @st.fragment
    def _tab_brand():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        # ── CSS секций бренда ─────────────────────────────────
        st.markdown("""<style>
        .sk-card {
            background: #f7f9fb;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.85);
            box-shadow: 8px 8px 18px rgba(163,177,198,0.5),
                        -8px -8px 18px rgba(255,255,255,0.95);
            padding: 18px 20px 12px 20px;
            margin-bottom: 14px;
        }
        .sk-head {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }
        .sk-bar {
            width: 4px;
            height: 22px;
            background: #4648d4;
            border-radius: 2px;
            flex-shrink: 0;
        }
        .sk-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 700;
            font-size: 13px;
            color: #191c1e;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: 0;
        }
        .sk-page-title {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 26px;
            font-weight: 700;
            color: #191c1e;
            margin: 0 0 6px;
        }
        .sk-page-sub {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 15px;
            color: #767586;
            margin: 0 0 28px;
        }
        .sk-label {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: #191c1e;
            margin: 5px 0 0;
            padding: 0;
            line-height: 1.5;
        }
        .sk-label-sub {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 11px;
            color: #767586;
            margin: 0;
            padding: 0;
            line-height: 1.3;
        }
        </style>""", unsafe_allow_html=True)

        # ── Заголовок страницы ────────────────────────────────
        st.markdown(f"""
        <p class="sk-page-title">Идентификация и активы</p>
        <p class="sk-page-sub">Управляйте логотипом, цветами и оформлением писем
          для бренда <b>{brand.get('brand_name','')}</b></p>
        """, unsafe_allow_html=True)

        # ── Двухколоночный макет ──────────────────────────────
        _is_locked_design = bool(brand.get('template_slug', ''))
        _col_l, _col_r = st.columns([4, 7], gap="large")

        # ════════════ ЛЕВАЯ КОЛОНКА ════════════
        with _col_l:

            # ── Логотип ──────────────────────────
            _cur_logo = brand.get('logo_data') or brand.get('logo_url', '')
            if _cur_logo:
                if _cur_logo.startswith('data:'):
                    st.image(_cur_logo, width=160)
                else:
                    st.markdown(
                        f'<img src="{_cur_logo}" width="160" style="max-height:80px;object-fit:contain;display:block;margin-bottom:8px">',
                        unsafe_allow_html=True)
            _logo_up = st.file_uploader("Загрузить логотип", type=["png","jpg","jpeg","webp"],
                                         key="brand_logo_up")
            _new_logo = _cur_logo
            if _logo_up:
                _new_logo = f"data:{_logo_up.type};base64,{base64.b64encode(_logo_up.read()).decode()}"

            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

            # ── Цвета бренда ─────────────────────
            if not _is_locked_design:
                st.markdown("""<div class="sk-card">
                  <div class="sk-head">
                    <div class="sk-bar"></div>
                    <span class="sk-title">Цвета бренда</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                _ca1, _ca2 = st.columns([7, 3])
                _ca1.markdown("""<p class="sk-label">Основной цвет бренда</p>
                  <p class="sk-label-sub">Кнопки, ссылки, акценты письма</p>""",
                  unsafe_allow_html=True)
                _new_accent = _ca2.color_picker("", value=brand.get('accent_color', '#1e69da'),
                    key="brand_accent_pick", label_visibility="collapsed")
                _ca2.caption(_new_accent.upper())

                _cb1, _cb2 = st.columns([7, 3])
                _cb1.markdown("""<p class="sk-label">Дополнительный цвет</p>
                  <p class="sk-label-sub">Фон карточек и блоков</p>""",
                  unsafe_allow_html=True)
                _new_secondary = _cb2.color_picker("", value=brand.get('secondary_color', '#f6f7fc'),
                    key="brand_secondary_pick", label_visibility="collapsed")
                _cb2.caption(_new_secondary.upper())
            else:
                _new_accent = brand.get('accent_color', '#1e69da')
                _new_secondary = brand.get('secondary_color', '#f6f7fc')

        # ════════════ ПРАВАЯ КОЛОНКА ════════════
        with _col_r:

            # ── Фоновые изображения ───────────────
            _new_hero = brand.get('hero_bg_img', '')
            _new_footer_img = brand.get('footer_bg_img', '')
            if not _is_locked_design:
                st.markdown("""<div class="sk-card">
                  <div class="sk-head">
                    <div class="sk-bar"></div>
                    <span class="sk-title">Фоны письма</span>
                  </div>
                </div>""", unsafe_allow_html=True)
                _img1, _img2 = st.columns(2)
                with _img1:
                    st.caption("Фон шапки")
                    _cur_hero = brand.get('hero_bg_img', '')
                    if _cur_hero and _cur_hero.startswith('data:'):
                        st.image(_cur_hero, width=200)
                    elif _cur_hero:
                        st.caption(f"{_cur_hero[:40]}…")
                    _hero_up = st.file_uploader("Загрузить фон шапки",
                        type=["jpg","jpeg","png","webp"], key="brand_hero_up")
                    _new_hero = _cur_hero
                    if _hero_up:
                        _new_hero = f"data:{_hero_up.type};base64,{base64.b64encode(_hero_up.read()).decode()}"
                with _img2:
                    st.caption("Фон футера")
                    _cur_footer_img = brand.get('footer_bg_img', '')
                    if _cur_footer_img and _cur_footer_img.startswith('data:'):
                        st.image(_cur_footer_img, width=200)
                    elif _cur_footer_img:
                        st.caption(f"{_cur_footer_img[:40]}…")
                    _footer_img_up = st.file_uploader("Загрузить фон футера",
                        type=["jpg","jpeg","png","webp"], key="brand_footer_img_up")
                    _new_footer_img = _cur_footer_img
                    if _footer_img_up:
                        _new_footer_img = f"data:{_footer_img_up.type};base64,{base64.b64encode(_footer_img_up.read()).decode()}"
            else:
                pass

        # ── Кнопка сохранения ─────────────────────────────────
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("Сохранить настройки бренда", key="brand_save_btn",
                     type="primary", use_container_width=True):
            save_brand(
                brand['brand_id'], brand['brand_name'],
                _new_accent, _new_logo, _new_hero,
                brand.get('template_slug', ''),
                brand.get('site_url', ''), brand.get('catalog_url', ''),
                brand.get('about_url', ''), brand.get('delivery_url', ''),
                brand.get('contacts_url', ''), brand.get('footer_address', ''),
                brand.get('default_email', ''), brand.get('default_phone', ''),
                brand.get('default_city', ''), _new_secondary,
                brand.get('layout_style', 'stalmetural'),
                brand.get('footer_bg_color') or brand.get('accent_color', '#1e69da'),
                _new_footer_img,
                brand.get('hero_text_color', '#ffffff'),
                brand.get('hero_sub_color', '#cccccc'),
                brand.get('body_title_color', '#282824'),
                brand.get('body_text_color', '#3d4858'),
                brand.get('card_text_color', '#555555'),
                brand.get('footer_text_color', '#ffffff')
            )
            st.session_state.user['accent_color']     = _new_accent
            st.session_state.user['secondary_color']  = _new_secondary
            st.session_state.user['logo_data']        = _new_logo
            st.session_state.user['hero_bg_img']      = _new_hero
            st.session_state.user['footer_bg_img']    = _new_footer_img
            st.success("Настройки бренда сохранены!")
            st.rerun(scope="app")

        # ── Дополнительные настройки ──────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        with st.expander("Редактировать название и ссылки бренда"):
            _edit_name  = st.text_input("Название бренда", value=brand.get('brand_name',''), key="edit_bname")
            _ec1, _ec2  = st.columns(2)
            _edit_site  = _ec1.text_input("Сайт", value=brand.get('site_url',''), key="edit_site")
            _edit_cat   = _ec2.text_input("Каталог (ссылка)", value=brand.get('catalog_url',''), key="edit_cat")
            _edit_about = _ec1.text_input("О компании (ссылка)", value=brand.get('about_url',''), key="edit_about")
            _edit_deliv = _ec2.text_input("Доставка (ссылка)", value=brand.get('delivery_url',''), key="edit_deliv")
            _edit_cont  = _ec1.text_input("Контакты (ссылка)", value=brand.get('contacts_url',''), key="edit_cont")
            _edit_foot  = st.text_input("Адрес в футере", value=brand.get('footer_address',''), key="edit_foot")
            _edit_email = _ec1.text_input("Email по умолчанию", value=brand.get('default_email',''), key="edit_email")
            _edit_phone = _ec2.text_input("Телефон по умолчанию", value=brand.get('default_phone',''), key="edit_phone")
            _edit_city  = _ec1.text_input("Город (предлог: «в Москве»)", value=brand.get('default_city',''), key="edit_city")
            if st.button("Сохранить", key="edit_brand_urls_btn", type="primary"):
                save_brand(
                    brand['brand_id'], _edit_name.strip() or brand['brand_name'],
                    brand.get('accent_color','#1e69da'),
                    brand.get('logo_data',''), brand.get('hero_bg_img',''),
                    brand.get('template_slug',''),
                    _edit_site, _edit_cat, _edit_about, _edit_deliv, _edit_cont,
                    _edit_foot, _edit_email, _edit_phone, _edit_city,
                    brand.get('secondary_color','#f6f7fc'),
                    brand.get('layout_style','stalmetural'),
                    brand.get('footer_bg_color',''),
                    brand.get('footer_bg_img',''),
                    brand.get('hero_text_color','#ffffff'),
                    brand.get('hero_sub_color','#cccccc'),
                    brand.get('body_title_color','#282824'),
                    brand.get('body_text_color','#3d4858'),
                    brand.get('card_text_color','#555555'),
                    brand.get('footer_text_color','#ffffff')
                )
                st.session_state.user['brand_name']    = _edit_name.strip() or brand['brand_name']
                st.session_state.user['site_url']      = _edit_site
                st.session_state.user['catalog_url']   = _edit_cat
                st.session_state.user['about_url']     = _edit_about
                st.session_state.user['delivery_url']  = _edit_deliv
                st.session_state.user['contacts_url']  = _edit_cont
                st.session_state.user['footer_address']= _edit_foot
                st.session_state.user['default_email'] = _edit_email
                st.session_state.user['default_phone'] = _edit_phone
                st.session_state.user['default_city']  = _edit_city
                st.success("Данные бренда сохранены!")
                st.rerun(scope="app")

        with st.expander("Удалить бренд"):
            st.warning(f"Вы собираетесь удалить бренд **{brand.get('brand_name','')}** и все его данные (проекты, шаблоны контактов, пользователей). Это действие необратимо.")
            _del_confirm = st.checkbox("Да, я понимаю — удалить", key="del_brand_check")
            if st.button("Удалить бренд", key="del_brand_btn", type="primary", disabled=not _del_confirm):
                _del_id = brand['brand_id']
                delete_brand(_del_id)
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.trusted_accounts = [
                    l for l in st.session_state.trusted_accounts
                    if l != user['login']
                ]
                st.query_params["accounts"] = ",".join(st.session_state.trusted_accounts)
                if st.query_params.get("u","") == user['login']:
                    st.query_params["u"] = ""
                st.success("Бренд удалён.")
                st.rerun(scope="app")



    @st.fragment
    def _tab_contacts():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        c1, c2 = st.columns(2)

        d_email = brand['default_email']
        data['EMAIL'] = cached_input("Email филиала", "EMAIL", d_email, d_email, col=c1) or d_email

        d_phone = brand['default_phone']
        data['PHONE'] = cached_input("Телефон филиала", "PHONE", d_phone, d_phone, col=c1) or d_phone

        data['PHONE_DIGITS'] = "".join(filter(str.isdigit, data['PHONE']))
        if not data['PHONE_DIGITS'].startswith('+'): data['PHONE_DIGITS'] = "+" + data['PHONE_DIGITS']
        data['PHONE_LINK'] = f"tel:{data['PHONE_DIGITS']}"

        d_city = brand['default_city']
        data['CITY_IN'] = cached_input("Город", "CITY_IN", d_city, d_city, col=c2) or d_city

        d_logo = brand['site_url']
        data['LINK_LOGO'] = cached_input("Ссылка при клике на логотип", "LINK_LOGO", d_logo, d_logo, col=c2) or d_logo

        col_m1, col_m2, col_m3 = st.columns(3)
        d_cat = brand['catalog_url']
        data['LINK_CATALOG'] = cached_input("Ссылка 'Каталог'", "LINK_CATALOG", d_cat, d_cat, col=col_m1) or d_cat

        d_about = brand['about_url']
        data['LINK_COMPANY'] = cached_input("Ссылка 'О компании/Кейсы'", "LINK_COMPANY", d_about, d_about, col=col_m2) or d_about

        d_deliv = brand['delivery_url']
        data['LINK_DELIVERY'] = cached_input("Ссылка 'Доставка'", "LINK_DELIVERY", d_deliv, d_deliv, col=col_m3) or d_deliv

        d_addr = brand['footer_address']
        data['FOOTER_ADDRESS'] = cached_input("Адрес в футере", "FOOTER_ADDRESS", d_addr, d_addr) or d_addr

        if brand.get('layout_style') == 'inmetprom' and mode != "promo_inmetprom":
            col_pay1, col_pay2 = st.columns(2)
            d_pay = brand.get('site_url', '').rstrip('/') + '/oplata/'
            data['LINK_PAYMENT'] = cached_input("Ссылка 'Оплата'", "IMP_LINK_PAYMENT", d_pay, d_pay, col=col_pay1) or d_pay
            d_cont = brand.get('contacts_url', '')
            data['LINK_CONTACTS'] = cached_input("Ссылка 'Контакты'", "IMP_LINK_CONTACTS", d_cont, d_cont, col=col_pay2) or d_cont

        # Авто-подстановки из настроек бренда для всех режимов
        data['ACCENT_COLOR']      = brand.get('accent_color', '#1e69da')
        data['ACCENT_COLOR_DARK'] = brand.get('accent_color', '#1e69da')
        data['COLOR_SECONDARY']   = brand.get('secondary_color', '#f6f7fc')
        data['BRAND_LOGO']        = brand.get('logo_data') or brand.get('logo_url', '')
        data['HERO_BG_IMG']       = brand.get('hero_bg_img', '')
        data['FOOTER_BG_COLOR']   = brand.get('footer_bg_color') or brand.get('accent_color', '#1e69da')
        data['FOOTER_BG_IMG']     = brand.get('footer_bg_img') or brand.get('hero_bg_img', '')
        data['LINK_PAYMENT']      = brand.get('site_url', '').rstrip('/') + '/oplata/'
        data['HERO_TEXT_COLOR']   = brand.get('hero_text_color') or '#ffffff'
        data['HERO_SUB_COLOR']    = brand.get('hero_sub_color') or '#cccccc'
        data['BODY_TITLE_COLOR']  = brand.get('body_title_color') or '#282824'
        data['BODY_TEXT_COLOR']   = brand.get('body_text_color') or '#3d4858'
        data['CARD_TEXT_COLOR']   = brand.get('card_text_color') or '#555555'
        data['FOOTER_TEXT_COLOR'] = brand.get('footer_text_color') or '#ffffff'

        if mode == "promo_inmetprom":
            # Дополнительные подстановки для ИнМетПром
            data['LOGO_URL']          = brand.get('logo_data') or brand.get('logo_url', '')
            data['LOGO_FOOTER_URL']   = brand.get('logo_data') or brand.get('logo_url', '')

        # Ссылка Оплата
            col_pay1, col_pay2 = st.columns(2)
            d_pay = brand['site_url'].rstrip('/') + '/oplata/'
            data['LINK_PAYMENT'] = cached_input(
                "Ссылка 'Оплата'", "IMP_LINK_PAYMENT", d_pay, d_pay, col=col_pay1) or d_pay

        # Ссылка Контакты / Консультация
            d_cont = brand['contacts_url']
            data['LINK_CONTACTS'] = cached_input(
                "Ссылка 'Контакты/Консультация'", "IMP_LINK_CONTACTS", d_cont, d_cont, col=col_pay2) or d_cont

        data['UnsubscribeUrl'], data['webversion'], data['email'] = "{{UnsubscribeUrl}}", "{{webversion}}", "{{email}}"



    @st.fragment
    def _tab_banner():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        _vars = TEMPLATE_VARIANTS.get(mode, [("default", "Стандарт", "", None)])
        _effective_mode = 'promo' if mode == 'promo_inmetprom' else mode

        # Backward compat: старые проекты promo_inmetprom → вариант inmetprom
        if mode == 'promo_inmetprom' and st.session_state.template_variant == 'default':
            st.session_state.template_variant = 'inmetprom'

        template_variant = st.session_state.template_variant
        _var_ids = [v[0] for v in _vars]
        if template_variant not in _var_ids:
            template_variant = _var_ids[0]
            st.session_state.template_variant = template_variant

        _locked = bool(brand.get('template_slug', ''))

        # Для залоченных брендов принудительно устанавливаем вариант из layout_style
        if _locked and mode not in ('promo_inmetprom',):
            _auto_v = brand.get('layout_style', '')
            if _auto_v and _auto_v in _var_ids:
                st.session_state.template_variant = _auto_v
                template_variant = _auto_v

        # --- Выбор дизайна (карточки + radio, только если доступно >1 вариант и бренд не залочен) ---
        if len(_vars) > 1 and not _locked:
            _var_labels = {v[0]: v[1] for v in _vars}
            _var_descs  = {v[0]: v[2] for v in _vars}
            st.markdown("""<div class="sk-card">
              <div class="sk-head"><div class="sk-bar"></div>
              <span class="sk-title">ДИЗАЙН ПИСЬМА</span></div>
            </div>""", unsafe_allow_html=True)
            _is_dark_v = st.session_state.get('theme', 'dark') == 'dark'
            _vpc_bg = "#252840" if _is_dark_v else "#f7f9fb"
            _vpc_text = "#d8daf0" if _is_dark_v else "#191c1e"
            _vpc_sub  = "#7a82a8" if _is_dark_v else "#767586"
            _vpc_shadow = ("4px 4px 8px rgba(0,0,0,.35),-4px -4px 8px rgba(255,255,255,.04)"
                           if _is_dark_v else
                           "4px 4px 8px rgba(163,177,198,.4),-4px -4px 8px rgba(255,255,255,.9)")
            _VAR_PREVIEWS = {
                "default":   ("linear-gradient(135deg,#1e69da 0%,#4e89ef 100%)",
                              "linear-gradient(90deg,#f0f0f0 0%,#e0e0e0 100%)"),
                "inmetprom": ("linear-gradient(135deg,#1a1d2e 0%,#2d3148 100%)",
                              "linear-gradient(90deg,#252840 0%,#1e2132 100%)"),
            }
            _vgrid = f'<div style="display:grid;grid-template-columns:{"1fr " * len(_vars)};gap:10px;margin:8px 0 14px">'
            for _vi_id, _vi_lbl, _vi_desc, _ in _vars:
                _sb = "2px solid #4648d4" if template_variant == _vi_id else "2px solid transparent"
                _top_bg, _bot_bg = _VAR_PREVIEWS.get(_vi_id, _VAR_PREVIEWS["default"])
                _vgrid += (
                    f'<div style="border-radius:12px;padding:12px 14px;background:{_vpc_bg};'
                    f'border:{_sb};box-shadow:{_vpc_shadow}">'
                    f'<div style="height:30px;border-radius:6px 6px 0 0;margin-bottom:2px;background:{_top_bg}"></div>'
                    f'<div style="height:10px;border-radius:0 0 4px 4px;margin-bottom:8px;background:{_bot_bg}"></div>'
                    f'<p style="margin:0 0 3px;font-size:13px;font-weight:700;color:{_vpc_text}">{_vi_lbl}</p>'
                    f'<p style="margin:0;font-size:11px;color:{_vpc_sub};line-height:1.3">{_vi_desc}</p>'
                    f'</div>'
                )
            _vgrid += "</div>"
            st.markdown(_vgrid, unsafe_allow_html=True)
            _sel = st.radio(
                "Дизайн",
                _var_ids,
                format_func=lambda x: _var_labels[x],
                index=_var_ids.index(template_variant),
                horizontal=True,
                key="variant_radio",
                label_visibility="collapsed",
            )
            if _sel != st.session_state.template_variant:
                st.session_state.template_variant = _sel
                st.rerun(scope="app")
            template_variant = _sel
            st.markdown("---")

        # ── Стиль шапки и футера ────────────────────────────────
        _hdr_supported = HEADER_BLOCK_SUPPORTED.get(mode, {}).get(template_variant, False) and not _locked
        _ftr_supported = FOOTER_BLOCK_SUPPORTED.get(mode, {}).get(template_variant, False) and not _locked
        st.markdown("""<div class="sk-card">
          <div class="sk-head"><div class="sk-bar"></div>
          <span class="sk-title">СТИЛЬ ШАПКИ И ФУТЕРА</span></div>
        </div>""", unsafe_allow_html=True)
        _hdr_cur = st.session_state.get('header_style', 'default')
        _ftr_cur = st.session_state.get('footer_style', 'default')
        _is_dark = st.session_state.get('theme', 'dark') == 'dark'
        _pc_bg     = "#252840" if _is_dark else "#f7f9fb"
        _pc_text   = "#d8daf0" if _is_dark else "#191c1e"
        _pc_sub    = "#7a82a8" if _is_dark else "#767586"
        _pc_shadow = ("4px 4px 8px rgba(0,0,0,.35),-4px -4px 8px rgba(255,255,255,.04)"
                      if _is_dark else
                      "4px 4px 8px rgba(163,177,198,.4),-4px -4px 8px rgba(255,255,255,.9)")
        _HEADER_STYLES = [
            ("default",   "Широкий баннер",  "Фоновое фото на всю ширину"),
            ("inmetprom", "Тёмная шапка",    "Тёмная полоса + отдельный баннер"),
        ]
        _FOOTER_STYLES = [
            ("default",   "Минималистичный", "Лого + контакты"),
            ("inmetprom", "Расширенный",      "Лого + навигация + контакты"),
        ]
        _sc1, _sc2 = st.columns(2)
        with _sc1:
            st.markdown('<p class="sk-label">Шапка письма</p>', unsafe_allow_html=True)
            if _hdr_supported:
                _hdr_preview = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:6px 0 10px">'
                for _hs_id, _hs_lbl, _hs_desc in _HEADER_STYLES:
                    _sb = "2px solid #4648d4" if _hdr_cur == _hs_id else "2px solid transparent"
                    _pbg = "linear-gradient(135deg,#1e69da 0%,#4e89ef 100%)" if _hs_id == "default" else "linear-gradient(135deg,#1a1d2e 0%,#2d3148 100%)"
                    _hdr_preview += (
                        f'<div style="border-radius:10px;padding:10px 12px;background:{_pc_bg};border:{_sb};'
                        f'box-shadow:{_pc_shadow}">'
                        f'<div style="height:28px;border-radius:6px;margin-bottom:7px;background:{_pbg}"></div>'
                        f'<p style="margin:0;font-size:12px;font-weight:600;color:{_pc_text}">{_hs_lbl}</p>'
                        f'<p style="margin:0;font-size:10px;color:{_pc_sub}">{_hs_desc}</p>'
                        f'</div>'
                    )
                _hdr_preview += "</div>"
                st.markdown(_hdr_preview, unsafe_allow_html=True)
                _hdr_new = st.radio("Шапка", [h[0] for h in _HEADER_STYLES],
                    format_func=lambda x: next(h[1] for h in _HEADER_STYLES if h[0] == x),
                    index=next((i for i, h in enumerate(_HEADER_STYLES) if h[0] == _hdr_cur), 0),
                    key="banner_hdr_radio", label_visibility="collapsed", horizontal=True)
                if _hdr_new != _hdr_cur:
                    st.session_state.header_style = _hdr_new
                    st.rerun(scope="app")
            else:
                st.caption("Зафиксировано в дизайне бренда" if _locked else "Шапка встроена в дизайн баннера для этого шаблона")
        with _sc2:
            st.markdown('<p class="sk-label">Футер письма</p>', unsafe_allow_html=True)
            if _ftr_supported:
                _ftr_preview = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:6px 0 10px">'
                for _fs_id, _fs_lbl, _fs_desc in _FOOTER_STYLES:
                    _sb = "2px solid #4648d4" if _ftr_cur == _fs_id else "2px solid transparent"
                    _ftr_preview += (
                        f'<div style="border-radius:10px;padding:10px 12px;background:{_pc_bg};border:{_sb};'
                        f'box-shadow:{_pc_shadow}">'
                        f'<div style="height:28px;border-radius:6px;margin-bottom:7px;background:linear-gradient(135deg,#3d4858 0%,#1a1d2e 100%)"></div>'
                        f'<p style="margin:0;font-size:12px;font-weight:600;color:{_pc_text}">{_fs_lbl}</p>'
                        f'<p style="margin:0;font-size:10px;color:{_pc_sub}">{_fs_desc}</p>'
                        f'</div>'
                    )
                _ftr_preview += "</div>"
                st.markdown(_ftr_preview, unsafe_allow_html=True)
                _ftr_new = st.radio("Футер", [f[0] for f in _FOOTER_STYLES],
                    format_func=lambda x: next(f[1] for f in _FOOTER_STYLES if f[0] == x),
                    index=next((i for i, f in enumerate(_FOOTER_STYLES) if f[0] == _ftr_cur), 0),
                    key="banner_ftr_radio", label_visibility="collapsed", horizontal=True)
                if _ftr_new != _ftr_cur:
                    st.session_state.footer_style = _ftr_new
                    st.rerun(scope="app")
            else:
                st.caption("Зафиксировано в дизайне бренда" if _locked else "Футер встроен в дизайн для этого шаблона")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ── Цвета текста в письме ────────────────────────────
        _tc_banner_cfg = [
            ("HERO_TEXT_COLOR",  "Текст шапки",      "Контакты, навигация в шапке",
             brand.get('hero_text_color') or '#ffffff'),
            ("HERO_SUB_COLOR",   "Подзаголовок",     "Тег / строка под заголовком",
             brand.get('hero_sub_color') or '#cccccc'),
            ("BODY_TITLE_COLOR", "Заголовки блоков", "H2 в теле письма",
             brand.get('body_title_color') or '#282824'),
            ("BODY_TEXT_COLOR",  "Основной текст",   "Параграфы и описания",
             brand.get('body_text_color') or '#3d4858'),
            ("CARD_TEXT_COLOR",  "Текст в карточках","Описания в карточках товаров",
             brand.get('card_text_color') or '#555555'),
            ("FOOTER_TEXT_COLOR","Текст футера",     "Навигация, контакты, дисклеймер",
             brand.get('footer_text_color') or '#ffffff'),
        ]
        if not _locked:
            with st.expander("Цвета текста в письме"):
                for _dk, _dlbl, _dhint, _ddef in _tc_banner_cfg:
                    _cur_c = st.session_state.data.get(_dk, _ddef)
                    _cl, _cp = st.columns([7, 3])
                    _cl.markdown(
                        f'<p class="sk-label">{_dlbl}</p><p class="sk-label-sub">{_dhint}</p>',
                        unsafe_allow_html=True)
                    _picked_c = _cp.color_picker("", value=_cur_c, key=f"banner_tc_{_dk}",
                        label_visibility="collapsed")
                    _cp.caption(_picked_c.upper())
                    data[_dk] = _picked_c
        else:
            for _dk, _dlbl, _dhint, _ddef in _tc_banner_cfg:
                data[_dk] = _ddef

        st.markdown("---")

        d_pre = "Узнайте подробности в письме..."
        data['PREHEADER_TEXT'] = cached_input("Прехедер", "PREHEADER_TEXT", d_pre, d_pre) or d_pre
        st.markdown("---")

        if _effective_mode == "promo":
            if template_variant == 'inmetprom':
                d_ht = "Арматура со скидкой 10%"
                raw_ht = cached_input(
                    "Заголовок (Enter = перенос строки)",
                    "IMP_HERO_TITLE", d_ht, d_ht, area=True, height=75) or d_ht
                data['HERO_TITLE'] = raw_ht.replace('\n', '<br>')
                d_dl = "со скидкой 10%"
                data['DISCOUNT_LABEL'] = cached_input(
                    "Метка скидки", "IMP_DISCOUNT_LABEL", d_dl, d_dl) or d_dl
                st.markdown("---")
                d_l1 = "На стальную арматуру предоставляется скидка 10% от текущей цены"
                data['HERO_DESC_LINE1'] = cached_input(
                    "Описание — строка 1", "IMP_HERO_DESC_L1", d_l1, d_l1) or d_l1
                d_l2 = "Условия и сроки действия предложения уточняются у менеджера"
                data['HERO_DESC_LINE2'] = cached_input(
                    "Описание — строка 2", "IMP_HERO_DESC_L2", d_l2, d_l2) or d_l2
                st.markdown("---")
                d_btn = brand.get('catalog_url', '')
                data['HERO_BTN_LINK'] = cached_input(
                    "Ссылка кнопки 'Перейти в каталог'",
                    "IMP_HERO_BTN_LINK", d_btn, d_btn) or d_btn
                data['HERO_PRODUCT_IMG'] = image_input(
                    "Картинка товара справа", "IMP_HERO_PRODUCT_IMG", "", "") or ""
            else:
                d_ht = "НА КВАДРАТ ЧУГУННЫЙ"
                raw_ht = cached_input("Заголовок (Enter для переноса)", "promo_HERO_TITLE", d_ht, d_ht, area=True, height=75) or d_ht
                data['HERO_TITLE'] = raw_ht.replace('\n', '<br>')
                d_dl = "СКИДКА 10%"
                data['DISCOUNT_LABEL'] = cached_input("Метка скидки", "promo_DISCOUNT_LABEL", d_dl, d_dl) or d_dl

        elif _effective_mode == "stock":
            d_ht = "ТРУБА ПРОФИЛЬНАЯ"
            data['HERO_TITLE'] = cached_input("Заголовок на баннере", "stock_HERO_TITLE", d_ht, d_ht) or d_ht
            if template_variant == 'inmetprom':
                d_btn = data.get('LINK_CATALOG', '')
                data['HERO_BTN_LINK'] = cached_input("Ссылка кнопки «Узнать цены и наличие»", "stock_HERO_BTN_LINK", d_btn, d_btn) or d_btn

        elif _effective_mode == "cases":
            if template_variant == 'inmetprom':
                d_l1 = "Металлопрокат —"
                data['HERO_DESC_LINE1'] = cached_input("Описание — строка 1", "cas_imp_HERO_DESC_L1", d_l1, d_l1) or d_l1
                d_ht = "отгрузка по России"
                data['HERO_TITLE'] = cached_input("Заголовок", "cas_imp_HERO_TITLE", d_ht, d_ht) or d_ht
                d_l2 = "и в страны СНГ"
                data['HERO_DESC_LINE2'] = cached_input("Описание — строка 2", "cas_imp_HERO_DESC_L2", d_l2, d_l2) or d_l2
                d_bg = brand.get('hero_bg_img', '')
                data['HERO_BG_IMG'] = image_input("Фоновая картинка баннера", "cas_imp_HERO_BG_IMG", d_bg, d_bg) or d_bg
                d_btn = data.get('LINK_CATALOG', '')
                data['HERO_BTN_LINK'] = cached_input("Ссылка кнопки «Рассчитать доставку»", "cas_imp_HERO_BTN_LINK", d_btn, d_btn) or d_btn
            else:
                d_ht = "НУЖЕН МЕТАЛЛ ТОЧНО В СРОК И ПО ГОСТУ?"
                data['HERO_TITLE'] = cached_input("Заголовок на баннере", "cases_HERO_TITLE", d_ht, d_ht) or d_ht
                d_hi = "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=633kxjmua5h3e6auf9n3p3mtxkbqyuz5g9t4bxmiwacn4se1m7mm8f3xb9kfj4sdqs7u6wy3p67hniwanz5qzpz6e3oafgod1gfpiyt35tefhp8sjg7t3fqc9p5i93btrk54ju1mbjtetk"
                data['HERO_IMG'] = image_input("Картинка отгрузки", "cases_HERO_IMG", d_hi, d_hi) or d_hi
                data['HERO_BTN_LINK'] = cached_input("Ссылка кнопки", "cases_HERO_BTN_LINK", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', '')) or data.get('LINK_CATALOG', '')

        elif _effective_mode == "expert":
            if template_variant == 'inmetprom':
                d_l1 = "ДОПУСКИ ПО ГОСТ:"
                data['HERO_DESC_LINE1'] = cached_input("Описание — строка 1", "exp_imp_HERO_DESC_L1", d_l1, d_l1) or d_l1
                d_ht = "КАК НЕ КУПИТЬ 920 КГ"
                data['HERO_TITLE'] = cached_input("Заголовок", "exp_imp_HERO_TITLE", d_ht, d_ht) or d_ht
                d_l2 = "ПО ЦЕНЕ ТОННЫ"
                data['HERO_DESC_LINE2'] = cached_input("Описание — строка 2", "exp_imp_HERO_DESC_L2", d_l2, d_l2) or d_l2
                d_bg = brand.get('hero_bg_img', '')
                data['HERO_BG_IMG'] = image_input("Фоновая картинка баннера", "exp_imp_HERO_BG_IMG", d_bg, d_bg) or d_bg
            else:
                d_ht = "БЕСШОВНАЯ ИЛИ ЭЛЕКТРОСВАРНАЯ"
                data['HERO_TITLE'] = cached_input("Заголовок на баннере", "expert_HERO_TITLE", d_ht, d_ht) or d_ht
                d_hi = "https://img.hiteml.com/en/v5/user-files?userId=8128470&resource=himg&disposition=inline&name=6uyisxkcb9z7eaauf9n3p3mtxknbsdqxp466f8gerep3qqo3qg9gbanpmbuqopttjmnzyzspdqyqxfm55dgtdc1xhua6ni8nrnmqq1qo538z6idf768zyjwfpoohe8gbci4z3phict9wqfg496t8gqbqy5r6b3tjcs34m6na"
                data['HERO_IMG'] = image_input("Картинка справа", "expert_HERO_IMG", d_hi, d_hi) or d_hi
                data['HERO_BTN_LINK'] = cached_input("Ссылка кнопки", "expert_HERO_BTN_LINK", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', '')) or data.get('LINK_CATALOG', '')

        else:
            d_ht = "МЕТАЛЛОПРОКАТ ОТ ПРОИЗВОДИТЕЛЯ"
            data['HERO_TITLE'] = cached_input("Заголовок баннера", f"{mode}_HERO_TITLE", d_ht, d_ht) or d_ht



    @st.fragment
    def _tab_texts():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        st.markdown(f"""
        <div style="background-color:{accent}33; padding:10px; border-radius:5px; border:1px solid {accent}; margin-bottom:15px;">
            <strong>Как оформлять текст:</strong><br>
            • <b>**текст**</b> — жирный | <b>- пункт</b> — список | <b>Enter</b> — новая строка
        </div>
        """, unsafe_allow_html=True)

        _tv_texts = st.session_state.get('template_variant', 'default')

        if mode in ("promo", "promo_inmetprom"):
            _promo_is_imp = (mode == "promo_inmetprom") or _tv_texts == "inmetprom"
            if not _promo_is_imp:
                # ── Стандартный дизайн спецпредложения ───────────────────────
                st.subheader("Главная статья")
                title_def = "Снижаем стоимость на партию"
                data['TEXT_TITLE'] = cached_input("Заголовок статьи", f"{mode}_TEXT_TITLE", title_def, title_def) or title_def
                pre_def = "Мы открываем **спецпредложение**..."
                t_pre_raw = cached_input("Текст ДО ссылки", f"{mode}_TEXT_PRE", pre_def, pre_def, area=True, height=100) or pre_def
                col_a1, col_a2 = st.columns(2)
                word_def = "партию квадрата"
                a_word = cached_input("Слово-ссылка", f"{mode}_LINK_WORD", word_def, word_def, col=col_a1) or word_def
                link_def = "https://stalmetural.ru/catalog/"
                a_link = cached_input("Куда ведет", f"{mode}_LINK_HREF", link_def, link_def, col=col_a2) or link_def
                post_def = "из наличия."
                t_post_raw = cached_input("Текст ПОСЛЕ ссылки", f"{mode}_TEXT_POST", post_def, post_def, area=True, height=80) or post_def
                data['TEXT_BODY'] = f'{process_text_to_html(t_pre_raw)} <a href="{a_link}" style="text-decoration:none; color:{accent}; font-weight:bold;">{a_word}</a> {process_text_to_html(t_post_raw)}'
                st.markdown("---")
                st.subheader("Блок P.S.")
                ps_c = st.columns(3)
                n1 = cached_input("Товар 1", f"{mode}_PS_N1", "профнастил", "профнастил", col=ps_c[0]) or "профнастил"
                n2 = cached_input("Товар 2", f"{mode}_PS_N2", "втулки", "втулки", col=ps_c[1]) or "втулки"
                n3 = cached_input("Товар 3", f"{mode}_PS_N3", "услуги", "услуги", col=ps_c[2]) or "услуги"
                ps_l = st.columns(3)
                l1 = cached_input("Ссылка на товар 1", f"{mode}_PS_L1", data['LINK_CATALOG'], data['LINK_CATALOG'], col=ps_l[0]) or data['LINK_CATALOG']
                l2 = cached_input("Ссылка на товар 2", f"{mode}_PS_L2", data['LINK_CATALOG'], data['LINK_CATALOG'], col=ps_l[1]) or data['LINK_CATALOG']
                l3 = cached_input("Ссылка на товар 3", f"{mode}_PS_L3", data['LINK_CATALOG'], data['LINK_CATALOG'], col=ps_l[2]) or data['LINK_CATALOG']
                ls = f"color:{accent}; text-decoration:none; font-weight:bold;"
                data['PS_BLOCK'] = f'P.S. Также в наличии <a href="{l1}" style="{ls}">{n1}</a>, <a href="{l2}" style="{ls}">{n2}</a> и <a href="{l3}" style="{ls}">{n3}</a>. Напишите нам в ответ на это письмо – подберем решение.'
            else:
                # ── Дизайн «Яркий» (Инметпром) ───────────────────────────────
                st.subheader("Основной текстовый блок")
                d_tt = "Зафиксируйте цену до сезонного дефицита"
                data['TEXT_TITLE'] = cached_input("Заголовок блока", "IMP_TEXT_TITLE", d_tt, d_tt) or d_tt
                d_tb = ("Мы открываем ограниченный резерв: отгружаем партию арматуры из наличия "
                        "со **скидкой 10%**. Это возможность закрыть потребность объекта по старым "
                        "прайсам, не дожидаясь июньского пика цен.")
                raw_tb = cached_input("Вводный текст", "IMP_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=100) or d_tb
                data['TEXT_BODY'] = process_text_to_html(raw_tb)
                st.markdown("---")
                st.markdown("**4 блока преимуществ:**")
                defaults_bt = ["Бронирование прайса", "Приоритетная отгрузка",
                               "Резка без отходов",   "Контроль ГОСТ"]
                defaults_bd = [
                    "Спеццена закрепляется за вами в день обращения.",
                    "Акционный объём уже собран и готов к выезду.",
                    "Нарежем партию в размер. Платите только за полезный вес.",
                    "Весь металл прошёл проверку. Сертификаты при отгрузке.",
                ]
                for i in range(1, 5):
                    col_b1, col_b2 = st.columns([1, 2])
                    data[f'BULLET_TITLE_{i}'] = cached_input(
                        f"Заголовок {i}", f"IMP_BULLET_TITLE_{i}",
                        defaults_bt[i-1], defaults_bt[i-1], col=col_b1) or defaults_bt[i-1]
                    data[f'BULLET_TEXT_{i}'] = cached_input(
                        f"Текст {i}", f"IMP_BULLET_TEXT_{i}",
                        defaults_bd[i-1], defaults_bd[i-1], col=col_b2) or defaults_bd[i-1]
                st.markdown("---")
                d_cta = "Свяжитесь с менеджером сейчас, чтобы забронировать объём из акционной партии:"
                data['CTA_TEXT'] = cached_input("Текст перед кнопкой CTA", "IMP_CTA_TEXT", d_cta, d_cta) or d_cta
                d_dead = "Предложение до 31.05.2026"
                data['OFFER_DEADLINE'] = cached_input(
                    "Подпись под кнопкой (дедлайн)", "IMP_OFFER_DEADLINE", d_dead, d_dead) or d_dead

        elif mode == "expert":
            if _tv_texts == 'inmetprom':
                st.subheader("Основной текстовый блок")
                d_tt = "Как не платить за «воздух» при закупке листа?"
                data['TEXT_TITLE'] = cached_input("Заголовок статьи", "exp_imp_TEXT_TITLE", d_tt, d_tt) or d_tt
                d_tb = ("Многие выбирают поставщика по минимальной цене, забывая о **минусовых допусках**. "
                        "По ГОСТ 19903 лист 10 мм может оказаться 9,2 мм.\n\n"
                        "Поставщик экономит на металле, а вы переплачиваете за **80 кг «воздуха»** "
                        "в каждой тонне. Конструкция теряет в прочности, а вы – в деньгах.\n\n"
                        "В ИНМЕТПРОМ мы исключаем такие схемы.")
                raw_tb = cached_input("Текст статьи", "exp_imp_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=200) or d_tb
                data['TEXT_BODY'] = process_text_to_html(raw_tb)
            else:
                st.subheader("Основная статья блога")
                d_title = "Выбираем трубу без переплат"
                data['TEXT_TITLE'] = cached_input("Заголовок статьи", f"{mode}_TEXT_TITLE", d_title, d_title) or d_title
                d_body = (
                    "Часто в смету закладывают дорогую бесшовную трубу там, где можно безопасно использовать электросварную.\n\n"
                    "**Где можно сэкономить до 40%?**\n"
                    "Электросварная труба (ЭСВ) идеально подходит для легких металлоконструкций, заборов и систем ЖКХ с низким давлением.\n\n"
                    "**Где рисковать нельзя?**\n"
                    "В нефтегазовой промышленности необходима только бесшовная труба (БШ)."
                )
                text_body_raw = cached_input("Текст статьи", f"{mode}_TEXT_BODY_RAW", d_body, d_body, area=True, height=250) or d_body
                data['TEXT_BODY'] = process_text_to_html(text_body_raw)
                d_link = brand['contacts_url']
                data['TEXT_BTN_LINK'] = cached_input("Ссылка для кнопки 'Связаться с нами'", f"{mode}_TEXT_BTN_LINK", d_link, d_link) or d_link

        elif mode == "stock":
            if _tv_texts == 'inmetprom':
                st.subheader("Вводная статья")
                st.caption("Заголовок публикуется после фиксированного «СВЕЖЕЕ ПОСТУПЛЕНИЕ:»")
                d_tt = "ЛИСТ ГОРЯЧЕКАТАНЫЙ НА СКЛАДЕ"
                data['TEXT_TITLE'] = cached_input("Название товара / поступления", "stock_imp_TEXT_TITLE", d_tt, d_tt) or d_tt
                d_tb = "Разгрузили 450 тонн горячекатаного листа. В наличии все толщины: от 2 мм до плит 300 мм из стали 09Г2С и Ст3."
                raw_tb = cached_input("Вводный абзац", "stock_imp_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=100) or d_tb
                data['TEXT_BODY'] = process_text_to_html(raw_tb)
            else:
                st.subheader("Вводная статья и преимущества")
                d_tt = "Профильная труба всех типоразмеров"
                data['TEXT_TITLE'] = cached_input("Главный заголовок", f"{mode}_TEXT_TITLE", d_tt, d_tt) or d_tt
                d_tb = "Обновили складской запас профильного проката. В наличии все позиции..."
                raw_tb = cached_input("Вводный абзац", f"{mode}_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=100) or d_tb
                data['TEXT_BODY'] = process_text_to_html(raw_tb)
                st.markdown("**Ключевые пункты (Буллиты):**")
                for i in range(1, 4):
                    col_b1, col_b2 = st.columns([1, 2])
                    d_bt = f"Заголовок {i}"
                    d_bd = f"Описание пункта {i}"
                    data[f'BULLET_TITLE_{i}'] = cached_input(f"Заголовок {i}", f"{mode}_BULLET_TITLE_{i}", d_bt, d_bt, col=col_b1) or d_bt
                    data[f'BULLET_TEXT_{i}']  = cached_input(f"Текст {i}",     f"{mode}_BULLET_TEXT_{i}",  d_bd, d_bd, col=col_b2) or d_bd

        elif mode == "cases":
            if _tv_texts == 'inmetprom':
                st.subheader("Основной текстовый блок")
                d_tt = "Ваш заказ на объекте точно в срок"
                data['TEXT_TITLE'] = cached_input("Заголовок", "cas_imp_TEXT_TITLE", d_tt, d_tt) or d_tt
                d_tb = ("В ИНМЕТПРОМ мы знаем: на стройплощадке время – это деньги. "
                        "Мы не просто продаем металл, мы выстраиваем цепочку поставок "
                        "так, чтобы ваш объект не простаивал ни часа.")
                raw_tb = cached_input("Вводный текст", "cas_imp_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=120) or d_tb
                data['TEXT_BODY'] = process_text_to_html(raw_tb)
            else:
                st.subheader("Текст кейса (История успеха)")
                d_ct = "Металл с гарантией: проверка по ГОСТ и полный пакет документов"
                data['CASE_MAIN_TITLE'] = cached_input("Заголовок статьи", f"{mode}_CASE_MAIN_TITLE", d_ct, d_ct) or d_ct
                d_ctask = "Недостаточная толщина стенки может остановить стройку..."
                raw_task = cached_input("Задача", f"{mode}_CASE_TASK_RAW", d_ctask, d_ctask, area=True, height=100) or d_ctask
                data['CASE_TASK'] = process_text_to_html(raw_task)
                d_csteps = "- **Замеры перед погрузкой**\n- **Полная документация**"
                raw_steps = cached_input("Что сделали", f"{mode}_CASE_STEPS_RAW", d_csteps, d_csteps, area=True, height=100) or d_csteps
                data['CASE_STEPS'] = process_text_to_html(raw_steps)
                d_cres = "Ваш объект не будет простаивать из-за брака."
                data['CASE_RESULT'] = cached_input("Результат", f"{mode}_CASE_RESULT", d_cres, d_cres) or d_cres

        elif mode == "services":
            st.subheader("Основной текстовый блок")
            d_title = "Больше, чем просто продажа металла"
            data['TEXT_TITLE'] = cached_input("Заголовок раздела", f"{mode}_TEXT_TITLE", d_title, d_title) or d_title
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
            raw_body = cached_input("Основной текст", f"{mode}_TEXT_BODY_RAW", d_body, d_body, area=True, height=300) or d_body
            data['TEXT_BODY'] = process_text_to_html(raw_body)

        else:
            d_tt = "Заголовок статьи"
            data['TEXT_TITLE'] = cached_input("Заголовок статьи", f"{mode}_TEXT_TITLE", d_tt, d_tt) or d_tt
            d_tb = "Основной текст письма..."
            raw_tb = cached_input("Текст", f"{mode}_TEXT_BODY_RAW", d_tb, d_tb, area=True, height=100) or d_tb
            data['TEXT_BODY'] = process_text_to_html(raw_tb)
            d_tl = brand['contacts_url']
            data['TEXT_BTN_LINK'] = cached_input("Ссылка для кнопки", f"{mode}_TEXT_BTN_LINK", d_tl, d_tl) or d_tl



    @st.fragment
    def _tab_blocks():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        _eff_mode_blocks = 'promo' if mode == 'promo_inmetprom' else mode
        _tv_blocks = st.session_state.get('template_variant', 'default')
        _mode_block_map = OPTIONAL_BLOCKS.get(mode, OPTIONAL_BLOCKS.get(_eff_mode_blocks, {}))
        if isinstance(_mode_block_map, dict):
            _opt_blocks = _mode_block_map.get(_tv_blocks, _mode_block_map.get('default', []))
        else:
            _opt_blocks = _mode_block_map

        _bv = st.session_state.block_visibility
        _is_dark_blk = st.session_state.get('theme', 'dark') == 'dark'
        _bbg   = "#252840" if _is_dark_blk else "#f7f9fb"
        _btxt  = "#d8daf0" if _is_dark_blk else "#191c1e"
        _bsub  = "#7a82a8" if _is_dark_blk else "#767586"
        _bacc  = "#6b6de0" if _is_dark_blk else accent
        _bsh   = ("6px 6px 12px rgba(0,0,0,.3),-6px -6px 12px rgba(255,255,255,.05)"
                  if _is_dark_blk else
                  "6px 6px 12px rgba(163,177,198,.4),-6px -6px 12px rgba(255,255,255,.9)")
        _bsh_in = ("inset 4px 4px 8px rgba(0,0,0,.4),inset -2px -2px 5px rgba(255,255,255,.04)"
                   if _is_dark_blk else
                   "inset 4px 4px 8px rgba(163,177,198,.3),inset -4px -4px 8px rgba(255,255,255,.85)")

        _is_imp = (_tv_blocks == 'inmetprom')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')

        # Цвета карточек в стиле Silk Edition
        _card_bg  = ("#2a2d4a" if _is_dark_blk else "#ffffff")
        _card_sh  = ("4px 4px 12px rgba(0,0,0,.35),-2px -2px 6px rgba(255,255,255,.04)"
                     if _is_dark_blk else
                     "4px 4px 12px rgba(163,177,198,.45),-4px -4px 8px rgba(255,255,255,.85)")
        _pill_bg  = ("rgba(107,109,224,.18)" if _is_dark_blk else "rgba(91,91,230,.10)")
        _dash_bd  = ("#4a4d70" if _is_dark_blk else "#c5c8e8")
        _code_bg  = ("#1a1c2e" if _is_dark_blk else "#f0f2fa")
        _code_hdr = ("#252840" if _is_dark_blk else "#e4e8f5")
        _code_txt = ("#e0e4ff" if _is_dark_blk else _btxt)

        _bch_now = st.session_state.get('block_custom_html', {})
        _can_hdr = HEADER_BLOCK_SUPPORTED.get(mode, {}).get(_tv_blocks, False)
        _can_ftr = FOOTER_BLOCK_SUPPORTED.get(mode, {}).get(_tv_blocks, False)

        if _is_imp:
            # ══════════════════════════════════════════════════════════════════
            # КОНСТРУКТОР ПИСЬМА (только для инметпром)
            # ══════════════════════════════════════════════════════════════════
            _ctor_blocks = st.session_state.get('constructor_blocks', [])
            _ctor_keys   = [b['key'] for b in _ctor_blocks]

            # ── Текущая сборка ──────────────────────────────────────────────

            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:20px 0 6px">'
                f'<div style="background:{_bacc};color:#fff;font-size:13px;font-weight:700;'
                f'width:24px;height:24px;border-radius:50%;display:flex;align-items:center;'
                f'justify-content:center;flex-shrink:0">1</div>'
                f'<span style="font-size:18px;font-weight:700;color:{_btxt}">Сборка письма</span>'
                f'<span style="font-size:12px;color:{_bsub};margin-left:4px">— выбранные блоки в нужном порядке</span>'
                f'</div>', unsafe_allow_html=True)

            if not _ctor_blocks:
                st.markdown(
                    f'<div style="background:{_card_bg};border-radius:14px;padding:20px 18px;'
                    f'box-shadow:{_card_sh};margin:4px 0 16px;text-align:center;'
                    f'color:{_bsub};font-size:14px">'
                    f'Здесь появятся блоки, которые ты выберешь ниже&nbsp;&nbsp;↓</div>',
                    unsafe_allow_html=True)
            else:
                _btn_div = "#4a4d70" if _is_dark_blk else "#d8dce8"
                _icon_btn = f"""
                    height: 46px !important; min-height: 46px !important;
                    width: 44px !important; padding: 0 !important;
                    font-size: 16px !important; font-weight: 400 !important;
                    border-radius: 10px !important;
                    background-color: {_card_bg} !important;
                    color: {_bsub} !important;
                    border: 1.5px solid {_btn_div} !important;
                    box-shadow: none !important; transform: none !important;
                    cursor: pointer !important;
                """
                _set_bg = "#f3f5f8" if not _is_dark_blk else "#1e2035"
                st.markdown(f"""<style>
                /* Строка карточки+кнопок — минимальный gap */
                [data-testid="stHorizontalBlock"]:has(div[class*="st-key-ctor_up"]) {{
                    gap: 6px !important;
                    align-items: center !important;
                    margin: 4px 0 !important;
                }}
                /* ↑ ↓ — отдельные кнопки, стиль как у + */
                div[class*="st-key-ctor_up"] button,
                div[class*="st-key-ctor_dn"] button {{ {_icon_btn} }}
                div[class*="st-key-ctor_up"] button:hover,
                div[class*="st-key-ctor_dn"] button:hover {{
                    color: {_btxt} !important; border-color: {_btxt} !important;
                }}
                div[class*="st-key-ctor_up"] button:disabled,
                div[class*="st-key-ctor_dn"] button:disabled {{
                    opacity: 0.25 !important; cursor: default !important;
                    pointer-events: none !important;
                }}
                div[class*="st-key-ctor_up"] button p,
                div[class*="st-key-ctor_dn"] button p {{
                    color: inherit !important; font-size: 16px !important;
                }}
                /* ✕ — серый, стиль как у + */
                div[class*="st-key-ctor_rm"] button {{ {_icon_btn} color: #999999 !important; }}
                div[class*="st-key-ctor_rm"] button:hover {{
                    color: #666666 !important; border-color: #aaaaaa !important;
                }}
                div[class*="st-key-ctor_rm"] button p {{
                    color: inherit !important; font-size: 16px !important;
                }}
                /* Скрытые Streamlit-кнопки (визуал — в HTML выше, JS .click() работает на display:none) */
                [data-testid="stHorizontalBlock"]:has(div[class*="st-key-ctor_up"]) {{
                    display: none !important;
                }}
                /* Настройки — без верхнего отступа, прилегают к карточке */
                div[class*="st-key-ctor_settings"] {{
                    margin-top: 0 !important;
                    padding-top: 0 !important;
                }}
                /* + кнопки — нейтральные */
                div[class*="st-key-ctor_add"] button {{ {_icon_btn} cursor: pointer !important; }}
                div[class*="st-key-ctor_add"] button:hover {{
                    color: {_bacc} !important; border-color: {_bacc} !important;
                    background-color: {_card_bg} !important;
                }}
                div[class*="st-key-ctor_add"] button:disabled {{
                    opacity: 0.4 !important; cursor: default !important;
                }}
                div[class*="st-key-ctor_add"] button p,
                div[class*="st-key-ctor_add"] button span {{
                    color: inherit !important; font-size: 20px !important;
                }}
                /* Секция настроек блока — визуально отделена */
                div[class*="st-key-ctor_settings"] {{
                    background: {_set_bg} !important;
                    border-radius: 12px !important;
                    border-left: 3px solid {_btn_div} !important;
                    padding: 8px 12px !important;
                    margin: 2px 0 10px 0 !important;
                }}
                /* Кнопка "Очистить всё" — отступ сверху */
                div[class*="st-key-ctor_clear"] {{
                    margin-top: 20px !important;
                }}
                </style>""", unsafe_allow_html=True)

                # Стиль HTML-кнопок управления (визуальные, вызывают скрытые Streamlit-кнопки)
                _bs = (
                    f"width:44px;height:100%;min-height:54px;flex-shrink:0;"
                    f"border:1.5px solid {_btn_div};background:{_card_bg};"
                    f"border-radius:10px;cursor:pointer;font-size:16px;color:{_bsub};"
                    f"display:flex;align-items:center;justify-content:center;padding:0;"
                )
                _bs_rm = _bs + "color:#999999;"

                for _ci, _cb in enumerate(_ctor_blocks):
                    _cb_desc = _cb.get('desc', '')
                    _bfields = BLOCK_FIELDS.get(_cb['key'], [])
                    _is_first = _ci == 0
                    _is_last  = _ci == len(_ctor_blocks) - 1

                    # Подсказка внутри карточки если нет настроек
                    _hint_html = (
                        f'<p style="margin:4px 0 0;font-size:11px;color:{_bsub}">'
                        f'Использует данные из вкладки «Текст»</p>'
                    ) if not _bfields else ''
                    _desc_html = (
                        f'<p style="margin:3px 0 0;font-size:12px;color:{_bsub}">{_cb_desc}</p>'
                    ) if _cb_desc else ''

                    # Стили с учётом активности (disabled — opacity, иначе полный стиль + onclick)
                    _bs_dis = _bs + "opacity:0.22;cursor:default;"
                    _up_btn = f'<button disabled style="{_bs_dis}">↑</button>' if _is_first else \
                              f'<button onclick="document.querySelector(\'.st-key-ctor_up_{_ci} button\').click()" style="{_bs}">↑</button>'
                    _dn_btn = f'<button disabled style="{_bs_dis}">↓</button>' if _is_last else \
                              f'<button onclick="document.querySelector(\'.st-key-ctor_dn_{_ci} button\').click()" style="{_bs}">↓</button>'
                    _rm_btn = f'<button onclick="document.querySelector(\'.st-key-ctor_rm_{_ci} button\').click()" style="{_bs_rm}">×</button>'

                    # Визуальная строка: карточка + кнопки как единый flex
                    st.markdown(f'''
                    <div style="display:flex;align-items:stretch;gap:6px;margin:4px 0">
                      <div style="flex:1;background:{_card_bg};border-radius:14px;
                                  padding:14px 18px;box-shadow:{_card_sh};
                                  display:flex;align-items:center;gap:14px">
                        <span style="color:{_bacc};font-size:13px;font-weight:700;
                                     min-width:18px;text-align:center;flex-shrink:0">{_ci+1}</span>
                        <div>
                          <p style="margin:0;font-size:15px;font-weight:600;color:{_btxt}">{_cb["name"]}</p>
                          {_desc_html}{_hint_html}
                        </div>
                      </div>
                      {_up_btn}{_dn_btn}{_rm_btn}
                    </div>
                    ''', unsafe_allow_html=True)

                    # Скрытые реальные Streamlit-кнопки (триггерятся из HTML выше)
                    _hc1, _hc2, _hc3, _ = st.columns([1, 1, 1, 20])
                    with _hc1:
                        if st.button("↑", key=f"ctor_up_{_ci}", disabled=_is_first):
                            _ctor_blocks[_ci], _ctor_blocks[_ci-1] = _ctor_blocks[_ci-1], _ctor_blocks[_ci]
                            st.session_state['constructor_blocks'] = _ctor_blocks
                            st.rerun()
                    with _hc2:
                        if st.button("↓", key=f"ctor_dn_{_ci}", disabled=_is_last):
                            _ctor_blocks[_ci], _ctor_blocks[_ci+1] = _ctor_blocks[_ci+1], _ctor_blocks[_ci]
                            st.session_state['constructor_blocks'] = _ctor_blocks
                            st.rerun()
                    with _hc3:
                        if st.button("✕", key=f"ctor_rm_{_ci}"):
                            _ctor_blocks.pop(_ci)
                            st.session_state['constructor_blocks'] = _ctor_blocks
                            st.rerun()

                    # Настройки блока — прямо под карточкой без отступа
                    if _bfields:
                        with st.container(key=f"ctor_settings_{_ci}"):
                            with st.expander(f"Настройки: {_cb['name']}"):
                                for _bf in _bfields:
                                    _fkey = f"bparam__{_cb['key']}__{_bf['key']}"
                                    if _fkey not in st.session_state:
                                        st.session_state[_fkey] = _bf['default']
                                    if _bf['type'] == 'textarea':
                                        st.text_area(_bf['label'], key=_fkey, height=80)
                                    else:
                                        st.text_input(_bf['label'], key=_fkey)

                st.markdown(f"""<style>
                div[class*="st-key-ctor_clear"] button {{
                    height:28px!important;min-height:28px!important;
                    padding:0 10px!important;font-size:13px!important;
                    border-radius:6px!important;border:1px solid {_btn_div}!important;
                    background:transparent!important;color:{_bsub}!important;
                    box-shadow:none!important;transform:none!important;
                    cursor:pointer!important;
                }}
                div[class*="st-key-ctor_clear"] button:hover {{
                    border-color:#e53935!important;color:#e53935!important;
                    background:transparent!important;
                }}
                div[class*="st-key-ctor_clear"] button p {{color:inherit!important;font-size:13px!important;}}
                </style>""", unsafe_allow_html=True)
                if st.button("Очистить всё", key="ctor_clear"):
                    st.session_state['constructor_blocks'] = []
                    st.rerun(scope="app")

            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

            # ── Доступные блоки для добавления ──────────────────────────────
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:28px 0 6px">'
                f'<div style="background:{_bacc};color:#fff;font-size:13px;font-weight:700;'
                f'width:24px;height:24px;border-radius:50%;display:flex;align-items:center;'
                f'justify-content:center;flex-shrink:0">2</div>'
                f'<span style="font-size:18px;font-weight:700;color:{_btxt}">Доступные блоки</span>'
                f'<span style="font-size:12px;color:{_bsub};margin-left:4px">— нажми ＋ чтобы добавить в сборку</span>'
                f'</div>', unsafe_allow_html=True)

            _lib_all = load_block_library()
            _lib_imp = [b for b in _lib_all if 'inmetprom' in b['source']]
            for _blk in _lib_imp:
                _already = _blk['key'] in _ctor_keys
                _lc1, _lc2 = st.columns([10, 1], gap="small")
                with _lc1:
                    st.markdown(
                        f'<div style="background:{_card_bg};border-radius:14px;'
                        f'padding:14px 18px;box-shadow:{_card_sh};margin:4px 0;'
                        f'display:flex;align-items:center;gap:14px">'
                        f'<div style="flex:1">'
                        f'<p style="margin:0;font-size:15px;font-weight:600;color:'
                        f'{_bacc if _already else _btxt}">'
                        f'{"✓ " if _already else ""}{_blk["name"]}</p>'
                        f'<p style="margin:3px 0 0;font-size:12px;color:{_bsub}">'
                        f'{_blk["desc"]}</p>'
                        f'</div></div>', unsafe_allow_html=True)
                with _lc2:
                    if st.button("＋", key=f"ctor_add_{_blk['key']}",
                                 disabled=_already):
                        _ctor_blocks.append({"key": _blk['key'], "name": _blk['name'], "desc": _blk.get('desc', ''), "html": _blk['html']})
                        st.session_state['constructor_blocks'] = _ctor_blocks
                        st.rerun(scope="app")


            st.markdown("---")

            with st.expander("Свой HTML", expanded=False):
                _slots = [("CUSTOM", "Добавить блок перед футером")]
                for _si, _sl, _ in _opt_blocks:
                    _slots.append((_si, f"Заменить «{_sl}»"))
                if _can_hdr:
                    _slots.append(("HEADER", "Заменить шапку (лого, навигация)"))
                if _can_ftr:
                    _slots.append(("FOOTER", "Заменить футер (контакты, адрес)"))
                _slots.append(("FULL", "Заменить весь шаблон целиком"))

                _slot_ids    = [s[0] for s in _slots]
                _slot_labels = [s[1] for s in _slots]
                _cur_slot = st.session_state.get('custom_html_slot', 'CUSTOM')
                if _cur_slot not in _slot_ids:
                    _cur_slot = 'CUSTOM'

                _bch      = st.session_state.get('block_custom_html', {})
                _has_code = any(_bch.get(sid, '').strip() for sid, _ in _slots)

                _sel_label = st.selectbox(
                    "Куда вставить:",
                    options=_slot_labels,
                    index=_slot_ids.index(_cur_slot),
                    key="custom_slot_sel_imp")
                _sel_slot_id = _slot_ids[_slot_labels.index(_sel_label)]
                st.session_state.custom_html_slot = _sel_slot_id

                if _sel_slot_id == "FULL":
                    st.caption("⚠️ Весь шаблон заменяется. Переменные {{PHONE}}, {{EMAIL}} и др. всё равно подставятся")

                _cur_custom = _bch.get(_sel_slot_id, '')
                _ph = ("<table width='600' border='0' cellpadding='0' cellspacing='0'>\n"
                       "  <tr><td style='padding:20px'>Ваш HTML здесь</td></tr>\n"
                       "</table>" if _sel_slot_id != 'FULL' else
                       "<!DOCTYPE html>\n<html>\n<head>...</head>\n<body>\n"
                       "  <!-- полный шаблон -->\n</body>\n</html>")

                _custom = st.text_area(
                    "HTML-код:",
                    value=_cur_custom,
                    height=240,
                    key=f"custom_html_imp_{_sel_slot_id}",
                    placeholder=_ph)

                if _custom and _custom.strip():
                    _bch[_sel_slot_id] = _custom
                    st.caption(f"✓ Активно · {len(_custom)} символов")
                elif _sel_slot_id in _bch:
                    del _bch[_sel_slot_id]
                st.session_state.block_custom_html = _bch

        else:
            # ══════════════════════════════════════════════════════════════════
            # СТАНДАРТНЫЙ РЕЖИМ (все бренды кроме инметпром)
            # ══════════════════════════════════════════════════════════════════

            # ── 1. Управление блоками ──────────────────────────────────────────
            if _opt_blocks and not _is_stalmetural:
                with st.expander("Управление блоками", expanded=False):
                    _n_active = sum(1 for _bi, _, _ in _opt_blocks if _bv.get(_bi, True))
                    st.markdown(
                        f'<div style="display:flex;align-items:center;justify-content:space-between;'
                        f'margin:4px 0 16px">'
                        f'<span style="font-size:20px;font-weight:700;color:{_btxt}">Управление блоками</span>'
                        f'<span style="font-size:13px;font-weight:600;color:{_bacc};background:{_pill_bg};'
                        f'padding:5px 16px;border-radius:20px">{_n_active} активных</span>'
                        f'</div>', unsafe_allow_html=True)

                    for _blk_id, _blk_label, _blk_hint in _opt_blocks:
                        _cur_vis = _bv.get(_blk_id, True)
                        _bc1, _bc2 = st.columns([9, 1], gap="small")
                        with _bc1:
                            st.markdown(
                                f'<div style="background:{_card_bg};border-radius:14px;'
                                f'padding:14px 18px;box-shadow:{_card_sh};margin:4px 0;'
                                f'display:flex;align-items:center;gap:14px">'
                                f'<span style="color:{_bsub};font-size:18px;line-height:1;'
                                f'letter-spacing:2px;cursor:grab">⠿</span>'
                                f'<div style="flex:1">'
                                f'<p style="margin:0;font-size:15px;font-weight:600;color:{_btxt}">'
                                f'{_blk_label}</p>'
                                f'<p style="margin:3px 0 0;font-size:12px;color:{_bsub}">{_blk_hint}</p>'
                                f'</div></div>', unsafe_allow_html=True)
                        with _bc2:
                            st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
                            _new_vis = st.toggle("", value=_cur_vis, key=f"blk_vis_{_blk_id}",
                                                label_visibility="collapsed")
                        _bv[_blk_id] = _new_vis
                    st.session_state.block_visibility = _bv
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

            # ── 2. Библиотека блоков ───────────────────────────────────────────
            if not _is_stalmetural:
                with st.expander("Библиотека блоков", expanded=False):
                    st.markdown(
                        f'<div style="display:flex;align-items:center;justify-content:space-between;'
                        f'margin:4px 0 14px">'
                        f'<span style="font-size:20px;font-weight:700;color:{_btxt}">Библиотека блоков</span>'
                        f'<span style="font-size:12px;color:{_bsub}">нажми ＋ → блок встанет перед футером</span>'
                        f'</div>', unsafe_allow_html=True)

                    if not _is_dark_blk:
                        st.markdown("""<style>
                        div[class*="st-key-lib_ins"] button {
                            background-color: #f7f9fb !important;
                            color: #191c1e !important;
                            box-shadow: 4px 4px 8px rgba(163,177,198,0.45),
                                        -4px -4px 8px rgba(255,255,255,0.9) !important;
                            border: none !important;
                        }
                        div[class*="st-key-lib_ins"] button p,
                        div[class*="st-key-lib_ins"] button span { color: #191c1e !important; }
                        div[class*="st-key-lib_ins"] button:hover {
                            box-shadow: 6px 6px 12px rgba(163,177,198,0.55),
                                        -6px -6px 12px rgba(255,255,255,1.0) !important;
                            transform: translateY(-1px) !important;
                        }
                        </style>""", unsafe_allow_html=True)

                    _lib_all = load_block_library()
                    if _lib_all:
                        for _blk in _lib_all:
                            _is_ins = _bch_now.get('CUSTOM', '').strip() == _blk['html'].strip()
                            _lc1, _lc2 = st.columns([6, 1], gap="small")
                            with _lc1:
                                st.markdown(
                                    f'<div style="background:{_card_bg};border-radius:14px;'
                                    f'padding:14px 18px;box-shadow:{_card_sh};margin:4px 0;'
                                    f'display:flex;align-items:center;gap:14px">'
                                    f'<span style="color:{_bsub};font-size:18px;line-height:1;'
                                    f'letter-spacing:2px">⠿</span>'
                                    f'<div style="flex:1">'
                                    f'<p style="margin:0;font-size:15px;font-weight:600;color:'
                                    f'{_bacc if _is_ins else _btxt}">'
                                    f'{"✓ " if _is_ins else ""}{_blk["name"]}</p>'
                                    f'<p style="margin:3px 0 0;font-size:12px;color:{_bsub}">'
                                    f'{_blk["desc"]} · <em>{_blk["source"]}</em></p>'
                                    f'</div></div>', unsafe_allow_html=True)
                            with _lc2:
                                st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
                                if st.button("＋", key=f"lib_ins_{_blk['key']}", use_container_width=True,
                                             help="Вставить блок перед футером"):
                                    _bch_ins = st.session_state.get('block_custom_html', {})
                                    _bch_ins['CUSTOM'] = _blk['html']
                                    st.session_state.block_custom_html = _bch_ins
                                    st.session_state['custom_html_CUSTOM'] = _blk['html']
                                    st.session_state.custom_html_slot = 'CUSTOM'
                                    st.rerun(scope="app")
                    else:
                        st.caption("Блоки из шаблонов не найдены")

                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

            # ── 3. Свой HTML ───────────────────────────────────────────────────
            if not _is_stalmetural:
                with st.expander("Свой HTML", expanded=False):
                    _slots = [("CUSTOM", "Добавить блок перед футером")]
                    for _si, _sl, _ in _opt_blocks:
                        _slots.append((_si, f"Заменить «{_sl}»"))
                    if _can_hdr:
                        _slots.append(("HEADER", "Заменить шапку (лого, навигация)"))
                    if _can_ftr:
                        _slots.append(("FOOTER", "Заменить футер (контакты, адрес)"))
                    _slots.append(("FULL", "Заменить весь шаблон целиком"))

                    _slot_ids    = [s[0] for s in _slots]
                    _slot_labels = [s[1] for s in _slots]
                    _cur_slot = st.session_state.get('custom_html_slot', 'CUSTOM')
                    if _cur_slot not in _slot_ids:
                        _cur_slot = 'CUSTOM'

                    _bch      = st.session_state.get('block_custom_html', {})
                    _has_code = any(_bch.get(sid, '').strip() for sid, _ in _slots)

                    _any_active_str = (f'<span style="font-size:12px;font-weight:600;color:{_bacc};'
                                       f'background:{_pill_bg};padding:5px 14px;border-radius:20px">'
                                       f'активно</span>' if _has_code else '')
                    st.markdown(
                        f'<div style="background:{_code_hdr};border-radius:16px 16px 0 0;'
                        f'padding:14px 20px;display:flex;align-items:center;justify-content:space-between;'
                        f'margin-top:4px">'
                        f'<div style="display:flex;align-items:center;gap:10px">'
                        f'<span style="font-size:18px;color:{_bacc}">&lt;/&gt;</span>'
                        f'<span style="font-size:20px;font-weight:700;color:{_code_txt}">Свой HTML</span>'
                        f'</div>{_any_active_str}</div>',
                        unsafe_allow_html=True)

                    st.markdown(
                        f'<div style="background:{_code_bg};border-radius:0 0 16px 16px;'
                        f'padding:16px 18px 18px;margin-bottom:8px">', unsafe_allow_html=True)

                    _sel_label = st.selectbox(
                        "Куда вставить:",
                        options=_slot_labels,
                        index=_slot_ids.index(_cur_slot),
                        key="custom_slot_sel")
                    _sel_slot_id = _slot_ids[_slot_labels.index(_sel_label)]
                    st.session_state.custom_html_slot = _sel_slot_id

                    if _sel_slot_id == "FULL":
                        st.caption("⚠️ Весь шаблон заменяется. Переменные {{PHONE}}, {{EMAIL}} и др. всё равно подставятся")

                    _cur_custom = _bch.get(_sel_slot_id, '')
                    _ph = ("<table width='600' border='0' cellpadding='0' cellspacing='0'>\n"
                           "  <tr><td style='padding:20px'>Ваш HTML здесь</td></tr>\n"
                           "</table>" if _sel_slot_id != 'FULL' else
                           "<!DOCTYPE html>\n<html>\n<head>...</head>\n<body>\n"
                           "  <!-- полный шаблон -->\n</body>\n</html>")

                    _custom = st.text_area(
                        "HTML-код:",
                        value=_cur_custom,
                        height=240,
                        key=f"custom_html_{_sel_slot_id}",
                        placeholder=_ph)

                    st.markdown('</div>', unsafe_allow_html=True)

                    if _custom.strip():
                        _bch[_sel_slot_id] = _custom
                        st.caption(f"✓ Активно · {len(_custom)} символов")
                    elif _sel_slot_id in _bch:
                        del _bch[_sel_slot_id]
                    st.session_state.block_custom_html = _bch

                    st.markdown("---")

        if mode == "cases":
          if _tv_blocks == 'inmetprom':
            # ── Инметпром: отгрузки — 3 товара + 4 кейса ──────────────────
            st.subheader("Товары и кейсы отгрузок")
            with st.expander("1. Товары в наличии (3 карточки)", expanded=True):
                d_sec = "Готовы к немедленной отправке"
                data['SORT_SECTION_TITLE'] = cached_input("Заголовок раздела", "cas_imp_sort_sec", d_sec, d_sec) or d_sec
                st.markdown("---")
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    d_t = f"Балка двутавровая {i}"
                    data[f'SORT_T_{i}'] = cached_input("Название", f"cas_imp_t_{i}", d_t, d_t, col=col1) or d_t
                    d_d = "Несущий профиль для перекрытий"
                    data[f'SORT_D_{i}'] = cached_input("Описание", f"cas_imp_d_{i}", d_d, d_d, col=col2) or d_d
                    col3, col4 = st.columns(2)
                    d_pr = f"{45000 + i * 500}₽/т"
                    data[f'SORT_PRICE_{i}'] = cached_input("Цена", f"cas_imp_pr_{i}", d_pr, d_pr, col=col3) or d_pr
                    col5, col6 = st.columns(2)
                    data[f'SORT_I_{i}'] = image_input("Фото товара", f"cas_imp_i_{i}", "", "", col=col5) or ""
                    data[f'SORT_L_{i}'] = cached_input("Ссылка", f"cas_imp_l_{i}", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col6) or data.get('LINK_CATALOG', '')
                    st.markdown("---")
            with st.expander("2. Что отгрузили (4 кейса)"):
                d_ship_sec = "Что отгрузили на этой неделе"
                data['SHIP_SECTION_TITLE'] = cached_input("Заголовок раздела", "cas_imp_ship_sec", d_ship_sec, d_ship_sec) or d_ship_sec
                for i in range(1, 5):
                    st.markdown(f"**Кейс №{i}**")
                    col1, col2 = st.columns(2)
                    d_sh_t = f"Металлопрокат — кейс {i}"
                    data[f'SHIP_T_{i}'] = cached_input("Название", f"cas_imp_sh_t_{i}", d_sh_t, d_sh_t, col=col1) or d_sh_t
                    d_sh_dt = "20.05.2026"
                    data[f'SHIP_DATE_{i}'] = cached_input("Дата", f"cas_imp_sh_dt_{i}", d_sh_dt, d_sh_dt, col=col2) or d_sh_dt
                    d_sh_d = "г. Москва, срок поставки 5 дней"
                    data[f'SHIP_D_{i}'] = cached_input("Город и срок", f"cas_imp_sh_d_{i}", d_sh_d, d_sh_d) or d_sh_d
                    col3, col4 = st.columns(2)
                    data[f'SHIP_I_{i}'] = image_input("Фото", f"cas_imp_sh_i_{i}", "", "", col=col3) or ""
                    data[f'SHIP_LINK_{i}'] = cached_input("Ссылка", f"cas_imp_sh_l_{i}", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col4) or data.get('LINK_CATALOG', '')
                    st.markdown("---")
          else:
            st.subheader("Настройка содержимого блоков")
            with st.expander("1. Участвовали в отгрузке (4 товара)"):
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    d_t = f"Труба №{i}"
                    data[f'PROD_{i}_TITLE'] = cached_input("Название", f"{mode}_prod_{i}_title", d_t, d_t, col=col1) or d_t
                    d_p = "39 500₽/т"
                    data[f'PROD_{i}_PRICE'] = cached_input("Цена", f"{mode}_prod_{i}_price", d_p, d_p, col=col2) or d_p
                    d_desc = "ГОСТ 8639-82, сталь 3пс"
                    _raw_prod_d = cached_input("Описание", f"{mode}_prod_{i}_desc", d_desc, d_desc, area=True, height=70) or d_desc
                    data[f'PROD_{i}_DESC'] = process_text_to_html(_raw_prod_d)
                    col3, col4 = st.columns(2)
                    d_img = "https://img.hiteml.com/example.jpg"
                    data[f'PROD_{i}_IMG']  = image_input("Картинка", f"{mode}_prod_{i}_img", d_img, d_img, col=col3) or d_img
                    data[f'PROD_{i}_LINK'] = cached_input("Ссылка на каталог", f"{mode}_prod_{i}_link", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG',''), col=col4) or data.get('LINK_CATALOG','')
                d_extra = "+ еще 8 позиций сопутствующего проката..."
                data['PROD_EXTRA_TEXT'] = cached_input("Текст под товарами", f"{mode}_prod_extra_text", d_extra, d_extra) or d_extra
                data['ALL_PROD_LINK']   = cached_input("Ссылка кнопки 'Весь сортамент'", f"{mode}_all_prod_link", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG','')) or data.get('LINK_CATALOG','')

            with st.expander("2. Не тратьте время на подгонку (3 Услуги)"):
                d_st = "Не тратьте время на подгонку на объекте"
                data['SERVICES_TITLE'] = cached_input("Главный заголовок услуг", f"{mode}_services_title", d_st, d_st) or d_st
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    col1, col2 = st.columns(2)
                    d_sv_t = "Резка в размер"
                    data[f'SERV_{i}_TITLE'] = cached_input("Название услуги", f"{mode}_serv_{i}_title", d_sv_t, d_sv_t, col=col1) or d_sv_t
                    d_sv_d = "Точность до 1 мм"
                    _raw_serv_d = cached_input("Краткое описание", f"{mode}_serv_{i}_desc",  d_sv_d, d_sv_d, col=col2) or d_sv_d
                    data[f'SERV_{i}_DESC'] = process_text_to_html(_raw_serv_d)
                    col3, col4 = st.columns(2)
                    d_sv_i = "https://img.hiteml.com/service.jpg"
                    data[f'SERV_{i}_IMG']  = image_input("Картинка", f"{mode}_serv_{i}_img", d_sv_i, d_sv_i, col=col3) or d_sv_i
                    data[f'SERV_{i}_LINK'] = cached_input("Ссылка",       f"{mode}_serv_{i}_link", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG',''), col=col4) or data.get('LINK_CATALOG','')
                    st.markdown("---")

        elif mode == "expert":
          if _tv_blocks == 'inmetprom':
            # ── Инметпром: экспертное — 3 товара + 2 категории ─────────────
            st.subheader("Товары и категории")
            with st.expander("1. Товары на складе (3 карточки)", expanded=True):
                d_sec = "Проверенный металл на складе"
                data['SORT_SECTION_TITLE'] = cached_input("Заголовок раздела", "exp_imp_sort_sec", d_sec, d_sec) or d_sec
                st.markdown("---")
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2 = st.columns(2)
                    d_t = ["Лист холоднокатаный", "Уголок стальной", "Квадрат нержавеющий"][i-1]
                    data[f'SORT_T_{i}'] = cached_input("Название", f"exp_imp_t_{i}", d_t, d_t, col=col1) or d_t
                    d_d = ["Идеален под покраску и гибку", "Строгое соответствие веса погонному метру", "Стойкость к агрессивным средам"][i-1]
                    data[f'SORT_D_{i}'] = cached_input("Описание", f"exp_imp_d_{i}", d_d, d_d, col=col2) or d_d
                    col3, col4 = st.columns(2)
                    data[f'SORT_PRICE_{i}'] = cached_input("Цена (новая)", f"exp_imp_pr_{i}", "1000₽/кг", "1000₽/кг", col=col3) or "1000₽/кг"
                    data[f'SORT_OLD_PRICE_{i}'] = cached_input("Цена (старая)", f"exp_imp_opr_{i}", "1200₽", "1200₽", col=col4) or "1200₽"
                    col5, col6 = st.columns(2)
                    data[f'SORT_I_{i}'] = image_input("Фото товара", f"exp_imp_i_{i}", "", "", col=col5) or ""
                    data[f'SORT_L_{i}'] = cached_input("Ссылка", f"exp_imp_l_{i}", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col6) or data.get('LINK_CATALOG', '')
                    st.markdown("---")
            with st.expander("2. Категории товаров (2 плитки)"):
                d_cat_sec = "Категории товаров"
                data['CAT_SECTION_TITLE'] = cached_input("Заголовок раздела", "exp_imp_cat_sec", d_cat_sec, d_cat_sec) or d_cat_sec
                st.markdown("---")
                _cat_defaults = [("Трубный прокат", "Нержавеющий металлопрокат")]
                for i in range(1, 3):
                    st.markdown(f"**Категория №{i}**")
                    col1, col2 = st.columns(2)
                    d_ct = ["Трубный прокат", "Нержавеющий металлопрокат"][i-1]
                    data[f'CAT_T_{i}'] = cached_input("Название", f"exp_imp_cat_t_{i}", d_ct, d_ct, col=col1) or d_ct
                    data[f'CAT_L_{i}'] = cached_input("Ссылка", f"exp_imp_cat_l_{i}", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col2) or data.get('LINK_CATALOG', '')
                    data[f'CAT_I_{i}'] = image_input("Фото категории", f"exp_imp_cat_i_{i}", "", "") or ""
                    st.markdown("---")
          else:
            st.subheader("Настройка блоков")
            with st.expander("1. Какой товар подходит?"):
                d_ps_t = "Какой товар подходит под ваши задачи?"
                data['PIPE_SECTION_TITLE'] = cached_input("Заголовок", f"{mode}_pipe_section_title", d_ps_t, d_ps_t) or d_ps_t
                for i in range(1, 3):
                    col1, col2 = st.columns(2)
                    d_p_t = f"Труба №{i}"
                    data[f'PIPE_{i}_TITLE'] = cached_input("Название", f"{mode}_pipe_{i}_title", d_p_t, d_p_t, col=col1) or d_p_t
                    d_p_p = "100 000₽/т"
                    data[f'PIPE_{i}_PRICE'] = cached_input("Цена", f"{mode}_pipe_{i}_price", d_p_p, d_p_p, col=col2) or d_p_p
                    d_p_d = "- Преимущество 1\n- Преимущество 2"
                    raw_pd = cached_input("Описания", f"{mode}_pipe_{i}_desc_raw", d_p_d, d_p_d, area=True, height=80, max_chars=220, help="До 220 символов — чтобы кнопка «Купить» оставалась на одном уровне в обеих карточках.") or d_p_d
                    data[f'PIPE_{i}_DESC'] = process_text_to_html(raw_pd)
                    col3, col4 = st.columns(2)
                    d_p_i = "https://img.hiteml.com/pipe.jpg"
                    data[f'PIPE_{i}_IMG']  = image_input("Картинка", f"{mode}_pipe_{i}_img", d_p_i, d_p_i, col=col3) or d_p_i
                    data[f'PIPE_{i}_LINK'] = cached_input("Ссылка",       f"{mode}_pipe_{i}_link", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG',''), col=col4) or data.get('LINK_CATALOG','')

            with st.expander("2. Также в наличии на складе"):
                d_ss_t = "Также в наличии на складе"
                data['STOCK_SECTION_TITLE'] = cached_input("Заголовок", f"{mode}_stock_section_title", d_ss_t, d_ss_t) or d_ss_t
                for i in range(1, 4):
                    col1, col2 = st.columns(2)
                    d_s_t = f"Товар №{i}"
                    data[f'STOCK_{i}_TITLE'] = cached_input("Название", f"{mode}_stock_{i}_title", d_s_t, d_s_t, col=col1) or d_s_t
                    d_s_p = "50 000₽/т"
                    data[f'STOCK_{i}_PRICE'] = cached_input("Цена", f"{mode}_stock_{i}_price", d_s_p, d_s_p, col=col2) or d_s_p
                    d_s_d = "В наличии 20 тонн"
                    _raw_stock_d = cached_input("Описание", f"{mode}_stock_{i}_desc", d_s_d, d_s_d) or d_s_d
                    data[f'STOCK_{i}_DESC'] = process_text_to_html(_raw_stock_d)
                    col3, col4 = st.columns(2)
                    d_s_i = "https://img.hiteml.com/stock.jpg"
                    data[f'STOCK_{i}_IMG']  = image_input("Картинка", f"{mode}_stock_{i}_img", d_s_i, d_s_i, col=col3) or d_s_i
                    data[f'STOCK_{i}_LINK'] = cached_input("Ссылка",       f"{mode}_stock_{i}_link", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG',''), col=col4) or data.get('LINK_CATALOG','')

            with st.expander("3. Наши отгрузки (2 кейса)"):
                d_ship_sec_t = "Наши отгрузки"
                data['SHIP_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_ship_section_title", d_ship_sec_t, d_ship_sec_t) or d_ship_sec_t
                for i in range(1, 3):
                    st.markdown(f"**Отгрузка №{i}**")
                    col1, col2 = st.columns(2)
                    d_sh_t = f"Труба №{i}"
                    data[f'SHIP_{i}_TITLE'] = cached_input("Название товара", f"{mode}_ship_t_{i}",  d_sh_t, d_sh_t, col=col1) or d_sh_t
                    d_sh_date = "12.06.2024"
                    data[f'SHIP_{i}_DATE']  = cached_input("Дата",            f"{mode}_ship_dt_{i}", d_sh_date, d_sh_date, col=col2) or d_sh_date
                    d_sh_d = "Описание процесса отгрузки или логистики"
                    _raw_ship_d = cached_input("Описание",        f"{mode}_ship_d_{i}", d_sh_d, d_sh_d) or d_sh_d
                    data[f'SHIP_{i}_DESC'] = process_text_to_html(_raw_ship_d)

                    col3, col4 = st.columns(2)
                    data[f'SHIP_{i}_IMG']   = image_input("Фото", f"{mode}_ship_i_{i}", "", "", col=col3) or ""
                    data[f'SHIP_{i}_LINK']  = cached_input("Ссылка",          f"{mode}_ship_l_{i}", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG',''), col=col4) or data.get('LINK_CATALOG','')
                    st.markdown("---")


        elif mode == "stock":
            if _tv_blocks == 'inmetprom':
                # ── Инметпром: поступление + отгрузки ──────────────────────
                st.subheader("Товары и отгрузки")

                with st.expander("1. Товары в наличии (3 карточки)", expanded=True):
                    d_sec_s = "Акционные товары недели"
                    data['SORT_SECTION_TITLE'] = cached_input("Заголовок раздела товаров", "imp_st_sort_sec", d_sec_s, d_sec_s) or d_sec_s
                    st.markdown("---")
                    for i in range(1, 4):
                        st.markdown(f"**Товар №{i}**")
                        col1, col2 = st.columns(2)
                        d_t = f"Арматура А500С {i * 10} мм"
                        data[f'SORT_T_{i}'] = cached_input("Название",  f"imp_st_t_{i}", d_t, d_t, col=col1) or d_t
                        d_d = "Для монтажа конструкций"
                        data[f'SORT_D_{i}'] = cached_input("Описание",  f"imp_st_d_{i}", d_d, d_d, col=col2) or d_d
                        col3, col4 = st.columns(2)
                        d_pr = f"{45000 + i * 500}₽/т"
                        data[f'SORT_PRICE_{i}']     = cached_input("Цена (новая)",    f"imp_st_pr_{i}",  d_pr, d_pr, col=col3) or d_pr
                        d_opr = f"{50000 + i * 500}₽/т"
                        data[f'SORT_OLD_PRICE_{i}'] = cached_input("Цена (старая)",   f"imp_st_opr_{i}", d_opr, d_opr, col=col4) or d_opr
                        col5, col6 = st.columns(2)
                        data[f'SORT_I_{i}'] = image_input("Фото товара", f"imp_st_i_{i}", "", "", col=col5) or ""
                        data[f'SORT_L_{i}'] = cached_input("Ссылка на товар", f"imp_st_l_{i}", data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col6) or data.get('LINK_CATALOG', '')
                        st.markdown("---")

                with st.expander("2. Что заказывали (2 кейса)"):
                    d_sec = "Что заказывали вчера"
                    data['SHIP_SECTION_TITLE'] = cached_input("Заголовок раздела отгрузок", "imp_st_ship_sec", d_sec, d_sec) or d_sec
                    for i in range(1, 3):
                        st.markdown(f"**Кейс №{i}**")
                        col1, col2 = st.columns(2)
                        d_sh_t = f"Металлопрокат — кейс {i}"
                        data[f'SHIP_T_{i}']    = cached_input("Название",   f"imp_st_sh_t_{i}",  d_sh_t,     d_sh_t,     col=col1) or d_sh_t
                        d_sh_dt = "19.05.2026"
                        data[f'SHIP_DATE_{i}'] = cached_input("Дата",       f"imp_st_sh_dt_{i}", d_sh_dt,    d_sh_dt,    col=col2) or d_sh_dt
                        d_sh_d = "г. Москва, срок поставки 3 дня"
                        data[f'SHIP_D_{i}']    = cached_input("Город и срок", f"imp_st_sh_d_{i}", d_sh_d, d_sh_d) or d_sh_d
                        col3, col4 = st.columns(2)
                        data[f'SHIP_I_{i}']    = image_input("Фото",        f"imp_st_sh_i_{i}",  "",         "",         col=col3) or ""
                        data[f'SHIP_LINK_{i}'] = cached_input("Ссылка",     f"imp_st_sh_l_{i}",  data.get('LINK_CATALOG', ''), data.get('LINK_CATALOG', ''), col=col4) or data.get('LINK_CATALOG', '')
                        st.markdown("---")

            else:
                st.subheader("Настройка технических блоков и товаров")

                with st.expander("1. Технический блок (ГОСТы и Размеры)"):
                    st.markdown("##### Стандарты производства (ГОСТ / ТУ)")
                    gost_preset = st.selectbox("Быстрый выбор по типу металла", options=list(GOST_PRESETS.keys()), key="gost_preset_select")
                    if gost_preset != "Своя настройка":
                        if st.button("↺ Загрузить стандарты для выбранного типа", key="load_gost"):
                            st.session_state.gost_tags = GOST_PRESETS[gost_preset].copy()
                            st.rerun(scope="app")
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
                            st.rerun(scope="app")
                    else:
                        st.info("Список стандартов пуст. Добавьте вручную ниже.")
                    col_g1, col_g2 = st.columns([3, 1])
                    new_gost = col_g1.text_input("Добавить стандарт вручную", placeholder="Например: ГОСТ 8639-82 или EN 10219", key="new_gost_input")
                    if col_g2.button("＋ Добавить", key="add_gost_btn", use_container_width=True):
                        if new_gost.strip() and new_gost.strip() not in st.session_state.gost_tags:
                            st.session_state.gost_tags.append(new_gost.strip())
                            st.rerun(scope="app")
                    data['GOST_BLOCK'] = make_badges(st.session_state.gost_tags, font_size="11px", padding="3px 8px")

                    st.markdown("---")
                    st.markdown("##### Ходовые размеры в наличии (мм)")
                    size_preset = st.selectbox("Быстрый выбор размеров по типу", options=list(SIZE_PRESETS.keys()), key="size_preset_select")
                    if size_preset != "Своя настройка":
                        if st.button("↺ Загрузить размеры для выбранного типа", key="load_size"):
                            st.session_state.size_tags = SIZE_PRESETS[size_preset].copy()
                            st.rerun(scope="app")
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
                            st.rerun(scope="app")
                    else:
                        st.info("Список размеров пуст. Добавьте вручную ниже.")
                    col_s1, col_s2 = st.columns([3, 1])
                    new_size = col_s1.text_input("Добавить размер вручную", placeholder="Например: 80×80 или Ø 57", key="new_size_input")
                    if col_s2.button("＋ Добавить", key="add_size_btn", use_container_width=True):
                        if new_size.strip() and new_size.strip() not in st.session_state.size_tags:
                            st.session_state.size_tags.append(new_size.strip())
                            st.rerun(scope="app")
                    data['SIZE_BLOCK'] = make_badges(st.session_state.size_tags, font_size="12px", padding="4px 10px")

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
                        d_t, d_d, d_p = f"Товар {i}", "ГОСТ, марка стали", "50 000₽"
                        data[f'SMALL_T_{i}'] = cached_input("Название",    f"{mode}_also_t_{i}", d_t, d_t) or d_t
                        _raw_also_d = cached_input("Описание",    f"{mode}_also_d_{i}", d_d, d_d) or d_d
                        data[f'SMALL_D_{i}'] = process_text_to_html(_raw_also_d)
                        data[f'SMALL_P_{i}'] = cached_input("Цена",        f"{mode}_also_p_{i}", d_p, d_p) or d_p
                        data[f'SMALL_I_{i}'] = image_input("Картинка", f"{mode}_also_i_{i}", "", "") or ""
                        data[f'SMALL_L_{i}'] = cached_input("Ссылка",      f"{mode}_also_l_{i}", data['LINK_CATALOG'], data['LINK_CATALOG']) or data['LINK_CATALOG']

                with st.expander("3. Наши отгрузки (2 кейса)"):
                    for i in range(1, 3):
                        st.markdown(f"**Кейс №{i}**")
                        d_ct, d_cd, d_cdt = "Партия труб", "Отгружено 20 тонн", "15.05.2024"
                        data[f'CASE_TITLE_{i}'] = cached_input("Заголовок кейса", f"{mode}_case_title_{i}", d_ct, d_ct) or d_ct
                        _raw_cd = cached_input("Описание кейса",  f"{mode}_case_desc_{i}",  d_cd, d_cd) or d_cd
                        data[f'CASE_DESC_{i}'] = process_text_to_html(_raw_cd)
                        data[f'CASE_DATE_{i}']  = cached_input("Дата",            f"{mode}_case_date_{i}",  d_cdt, d_cdt) or d_cdt
                        data[f'CASE_IMG_{i}']   = image_input("Фото", f"{mode}_case_img_{i}", "", "") or ""
            data['EXPERT_LINK'] = data.get('ALINA_BTN_LINK') or data.get('IMP_LINK_CONTACTS', '')

        elif mode == "promo":
            st.subheader("Товарные и структурные блоки")

            with st.expander("1. Ваши персональные цены (Сетка 2x2)", expanded=True):
                for i in range(1, 5):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    d_t, d_p, d_op = f"Лист х/к {i}", "495₽/т", "550₽"
                    data[f'T_{i}']     = cached_input("Название",       f"{mode}_t_{i}",  d_t,  d_t,  col=col1) or d_t
                    data[f'P_{i}']     = cached_input("Цена со скидкой",f"{mode}_p_{i}",  d_p,  d_p,  col=col2) or d_p
                    data[f'OLD_P_{i}'] = cached_input("Старая цена",    f"{mode}_op_{i}", d_op, d_op, col=col3) or d_op
                    d_d = "ГОСТ 16523-97"
                    _raw_d = cached_input("Описание",    f"{mode}_d_{i}", d_d, d_d) or d_d
                    data[f'D_{i}'] = process_text_to_html(_raw_d)
                    data[f'I_{i}'] = image_input("Картинка", f"{mode}_i_{i}", "", "") or ""
                    data[f'L_{i}'] = cached_input("Ссылка",      f"{mode}_l_{i}", data['LINK_CATALOG'], data['LINK_CATALOG']) or data['LINK_CATALOG']
                    st.markdown("---")

            with st.expander("2. Также зафиксировали цены (Малые блоки 1x3)"):
                for i in range(1, 4):
                    st.markdown(f"**Малый товар №{i}**")
                    d_sm_t, d_sm_p, d_sm_d = "Сетка цинк", "305₽/т", "ГОСТ 23279-2012"
                    data[f'SMALL_T_{i}'] = cached_input("Название",  f"{mode}_sm_t_{i}",   d_sm_t, d_sm_t) or d_sm_t
                    data[f'SMALL_P_{i}'] = cached_input("Цена",      f"{mode}_sm_p_{i}",   d_sm_p, d_sm_p) or d_sm_p
                    _raw_sm_d = cached_input("Описание",  f"{mode}_sm_d_{i}",   d_sm_d, d_sm_d) or d_sm_d
                    data[f'SMALL_D_{i}'] = process_text_to_html(_raw_sm_d)
                    data[f'SMALL_I_{i}'] = image_input("Фото", f"{mode}_sm_img_{i}", "", "") or ""
                    data[f'SMALL_L_{i}'] = cached_input("Ссылка",    f"{mode}_sm_link_{i}",data['LINK_CATALOG'], data['LINK_CATALOG']) or data['LINK_CATALOG']
                    st.markdown("---")

            with st.expander("3. Категории товаров"):
                d_sec_t = "Категории товаров"
                data['CAT_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_cat_section_title", d_sec_t, d_sec_t) or d_sec_t
                for i in range(1, 3):
                    st.markdown(f"**Категория №{i}**")
                    d_ct_t = "Трубный прокат"
                    data[f'CAT_TITLE_{i}'] = cached_input("Заголовок", f"{mode}_cat_title_{i}", d_ct_t, d_ct_t) or d_ct_t
                    d_ct_d = "Огромный выбор диаметров и стенок"
                    _raw_cat_d = cached_input("Описание",  f"{mode}_cat_desc_{i}",  d_ct_d, d_ct_d, area=True, height=80) or d_ct_d
                    data[f'CAT_DESC_{i}'] = process_text_to_html(_raw_cat_d)
                    data[f'CAT_IMG_{i}']   = image_input("Картинка", f"{mode}_cat_img_{i}", "", "") or ""
                    data[f'CAT_LINK_{i}']  = cached_input("Ссылка",    f"{mode}_cat_link_{i}", data['LINK_CATALOG'], data['LINK_CATALOG']) or data['LINK_CATALOG']
                    st.markdown("---")

            with st.expander("4. Наши отгрузки за неделю"):
                d_sec_title = "Наши отгрузки"
                data['CASE_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_case_section_title", d_sec_title, d_sec_title) or d_sec_title
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    col_k1, col_k2 = st.columns([2, 1])
                    d_c_title = f"Отгрузка металлопроката {i}"
                    data[f'CASE_TITLE_{i}'] = cached_input("Заголовок отгрузки",      f"{mode}_case_title_{i}", d_c_title, d_c_title, col=col_k1) or d_c_title
                    d_c_date = "10.06.2024"
                    data[f'CASE_DATE_{i}']  = cached_input("Дата",                    f"{mode}_case_date_{i}",  d_c_date,  d_c_date,  col=col_k2) or d_c_date
                    d_c_desc = "Укомплектовали и доставили заказ на объект"
                    _raw_case_d = cached_input("Описание (что отгрузили)",f"{mode}_case_desc_{i}",  d_c_desc,  d_c_desc) or d_c_desc
                    data[f'CASE_DESC_{i}'] = process_text_to_html(_raw_case_d)
                    data[f'CASE_IMG_{i}']   = image_input("Фото отгрузки", f"{mode}_case_img_{i}", "", "") or ""
                    st.markdown("---")

        elif mode == "services":
            st.subheader("Настройка блоков")

            with st.expander("1. Технологии (3 карточки)"):
                d_tech_t = "Технологии, которые сэкономят ваше время"
                data['TECH_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_tech_section_title", d_tech_t, d_tech_t) or d_tech_t
                for i in range(1, 4):
                    st.markdown(f"**Услуга №{i}**")
                    d_sv_t, d_sv_d = "Лазерная резка", "Точность до микрона"
                    data[f'T_{i}'] = cached_input("Название",    f"{mode}_sv_t_{i}", d_sv_t, d_sv_t) or d_sv_t
                    _raw_sv_d = cached_input("Описание",    f"{mode}_sv_d_{i}", d_sv_d, d_sv_d) or d_sv_d
                    data[f'D_{i}'] = process_text_to_html(_raw_sv_d)
                    data[f'I_{i}'] = image_input("Картинка", f"{mode}_sv_i_{i}", "", "") or ""
                    data[f'L_{i}'] = cached_input("Ссылка",      f"{mode}_sv_l_{i}", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG','')) or data.get('LINK_CATALOG','')
                    st.markdown("---")

            with st.expander("2. Сортамент под ваши чертежи"):
                d_sort_t = "Сортамент под ваши чертежи"
                data['SORT_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_sort_section_title", d_sort_t, d_sort_t) or d_sort_t
                d_sort_i = "Поставляем прокат напрямую с заводов..."
                raw_sort_i = cached_input("Вводный текст", f"{mode}_sort_intro_raw", d_sort_i, d_sort_i, area=True, height=80) or d_sort_i
                data['SORT_INTRO'] = process_text_to_html(raw_sort_i)
                for i in range(1, 3):
                    st.markdown(f"**Товар №{i}**")
                    d_sr_t, d_sr_sp = "Труба БШ", "ГОСТ 8734-75"
                    data[f'SORT_T_{i}']    = cached_input("Название",       f"{mode}_sr_t_{i}",    d_sr_t,  d_sr_t) or d_sr_t
                    data[f'SORT_SPEC_{i}'] = cached_input("Характеристика", f"{mode}_sr_sp_{i}",   d_sr_sp, d_sr_sp) or d_sr_sp
                    d_sr_d = "- Сталь 20\n- Любая нарезка"
                    raw_sr_d = cached_input("Описание", f"{mode}_sr_d_{i}_raw", d_sr_d, d_sr_d, area=True, height=80) or d_sr_d
                    data[f'SORT_D_{i}'] = process_text_to_html(raw_sr_d)
                    data[f'SORT_I_{i}'] = image_input("Фото", f"{mode}_sr_i_{i}", "", "") or ""
                    data[f'SORT_L_{i}'] = cached_input("Ссылка",  f"{mode}_sr_l_{i}", data.get('LINK_CATALOG',''), data.get('LINK_CATALOG','')) or data.get('LINK_CATALOG','')
                    st.markdown("---")

            with st.expander("3. Монтаж без задержек: отгружаем точно в срок"):
                d_ship_sec_t = "Монтаж без задержек: отгружаем точно в срок"
                data['SHIP_SECTION_TITLE'] = cached_input("Заголовок раздела", f"{mode}_ship_section_title", d_ship_sec_t, d_ship_sec_t) or d_ship_sec_t
                for i in range(1, 3):
                    st.markdown(f"**Отгрузка №{i}**")
                    col1, col2 = st.columns(2)
                    d_sh_t = f"Название товара {i}"
                    data[f'SHIP_T_{i}']    = cached_input("Название товара", f"{mode}_sh_t_{i}",  d_sh_t, d_sh_t, col=col1) or d_sh_t
                    d_sh_date = "12.06.2024"
                    data[f'SHIP_DATE_{i}'] = cached_input("Дата",            f"{mode}_sh_dt_{i}", d_sh_date, d_sh_date, col=col2) or d_sh_date
                    d_sh_d = "Описание процесса отгрузки или логистики"
                    _raw_sh_d = cached_input("Описание",       f"{mode}_sh_d_{i}", d_sh_d, d_sh_d) or d_sh_d
                    data[f'SHIP_D_{i}'] = process_text_to_html(_raw_sh_d)
                    data[f'SHIP_I_{i}'] = image_input("Фото отгрузки", f"{mode}_sh_i_{i}", "", "") or ""
                    st.markdown("---")

        elif mode == "promo_inmetprom":
            st.subheader("Товарные блоки и дополнительные секции")

            # ---- 1. Акционные позиции (3 товара) ----
            with st.expander("1. Акционные позиции со склада (3 товара)", expanded=True):
                defaults_t  = ["Арматура 10 мм", "Арматура 12 мм", "Арматура 8 мм"]
                defaults_d  = ["Для вспомогательного армирования",
                               "Для стандартных фундаментов",
                               "Для ответственных несущих конструкций"]
                defaults_p  = ["51 504₽/т", "51 264₽/т", "52 340₽/т"]
                defaults_op = ["57 226₽",   "56 960₽",   "58 155₽"]
                defaults_l  = [
                    brand['catalog_url'] + "armatura/armatura-10-mm-gost-34028-2016/",
                    brand['catalog_url'] + "armatura/armatura-12-mm-gost-34028-2016/",
                    brand['catalog_url'] + "armatura/armatura-8-mm-gost-34028-2016-l-11-7-m/",
                ]
                for i in range(1, 4):
                    st.markdown(f"**Товар №{i}**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    data[f'T_{i}'] = cached_input(
                        "Название", f"IMP_t_{i}", defaults_t[i-1], defaults_t[i-1], col=col1) or defaults_t[i-1]
                    data[f'P_{i}'] = cached_input(
                        "Цена со скидкой", f"IMP_p_{i}", defaults_p[i-1], defaults_p[i-1], col=col2) or defaults_p[i-1]
                    data[f'OLD_P_{i}'] = cached_input(
                        "Старая цена", f"IMP_op_{i}", defaults_op[i-1], defaults_op[i-1], col=col3) or defaults_op[i-1]
                    raw_d = cached_input(
                        "Описание", f"IMP_d_{i}", defaults_d[i-1], defaults_d[i-1]) or defaults_d[i-1]
                    data[f'D_{i}'] = process_text_to_html(raw_d)
                    col4, col5 = st.columns(2)
                    data[f'I_{i}'] = image_input(
                        "Картинка товара", f"IMP_i_{i}", "", "", col=col4) or ""
                    data[f'L_{i}'] = cached_input(
                        "Ссылка на товар", f"IMP_l_{i}", defaults_l[i-1], defaults_l[i-1], col=col5) or defaults_l[i-1]
                    st.markdown("---")

            # ---- 2. Что отгрузили на этой неделе (2 кейса) ----
            with st.expander("2. Что отгрузили на этой неделе (2 кейса)"):
                defaults_ct   = ["Труба электросварная", "Гайки"]
                defaults_cdesc = ["г. Екатеринбург, срок поставки 3 дня",
                                  "г. Волгоград, срок поставки 5 дней"]
                defaults_cdate = ["12.05.2026", "13.05.2026"]
                defaults_clink = [
                    brand['catalog_url'] + "trubnyj-prokat/truba-stalnaya-elektrosvarnaya/",
                    brand['catalog_url'] + "krepeg-i-metizy/gajka/",
                ]
                for i in range(1, 3):
                    st.markdown(f"**Кейс №{i}**")
                    col_k1, col_k2 = st.columns([2, 1])
                    data[f'CASE_TITLE_{i}'] = cached_input(
                        "Название товара", f"IMP_case_t_{i}",
                        defaults_ct[i-1], defaults_ct[i-1], col=col_k1) or defaults_ct[i-1]
                    data[f'CASE_DATE_{i}'] = cached_input(
                        "Дата", f"IMP_case_date_{i}",
                        defaults_cdate[i-1], defaults_cdate[i-1], col=col_k2) or defaults_cdate[i-1]
                    raw_cd = cached_input(
                        "Описание (город, срок)", f"IMP_case_d_{i}",
                        defaults_cdesc[i-1], defaults_cdesc[i-1]) or defaults_cdesc[i-1]
                    data[f'CASE_DESC_{i}'] = process_text_to_html(raw_cd)
                    col_k3, col_k4 = st.columns(2)
                    data[f'CASE_IMG_{i}'] = image_input(
                        "Фото отгрузки", f"IMP_case_img_{i}", "", "", col=col_k3) or ""
                    st.markdown("---")

            # ---- 3. Почему выбирают нас ----
            with st.expander("3. Почему выбирают нас (Регион)"):
                st.info("Дизайн и текст этого блока зафиксированы. Вы можете изменить только регион (например: РФ, СНГ и тд).")
                d_region = "РФ"
                data['REGION'] = cached_input(
                    "Регион складов", "IMP_REGION",
                    d_region, d_region) or d_region


        else:
            st.info("Блоки для данного шаблона настраиваются индивидуально. Перейдите в другой шаблон.")



    @st.fragment
    def _tab_expert():
        brand = st.session_state.user
        mode = st.session_state.mode
        accent = brand['accent_color'] if brand else '#1e69da'
        data = st.session_state.data
        template_variant = st.session_state.get('template_variant', 'default')
        _is_stalmetural = (brand.get('template_slug', '') == 'stalmetural')
        _is_imp = (template_variant == 'inmetprom')
        _ = accent  # suppress unused warning

        st.info("Блок менеджера зафиксирован в дизайне. Здесь меняется только ссылка кнопки.")
        d_alink = brand['contacts_url']
        data['ALINA_BTN_LINK'] = cached_input("Ссылка для кнопки 'Рассчитать смету'", "ALINA_BTN_LINK", d_alink, d_alink) or d_alink

        # ==========================================


    # ── Инициализация дефолтных значений из бренда (до табов, вне фрагментов) ──
    # Гарантирует подстановку в HTML даже если пользователь не заходил на таб
    _d = st.session_state.data
    _b = brand
    if 'BRAND_LOGO' not in _d:
        _d['BRAND_LOGO']       = _b.get('logo_data') or _b.get('logo_url', '')
    if 'LOGO_URL' not in _d:
        _d['LOGO_URL']         = _b.get('logo_data') or _b.get('logo_url', '')
    if 'LOGO_FOOTER_URL' not in _d:
        _d['LOGO_FOOTER_URL']  = _b.get('logo_data') or _b.get('logo_url', '')
    if 'ACCENT_COLOR' not in _d:
        _d['ACCENT_COLOR']     = _b.get('accent_color', '#1e69da')
    if 'ACCENT_COLOR_DARK' not in _d:
        _d['ACCENT_COLOR_DARK']= _b.get('accent_color', '#1e69da')
    if 'COLOR_SECONDARY' not in _d:
        _d['COLOR_SECONDARY']  = _b.get('secondary_color', '#f6f7fc')
    if 'HERO_BG_IMG' not in _d:
        _d['HERO_BG_IMG']      = _b.get('hero_bg_img', '')
    if 'FOOTER_BG_COLOR' not in _d:
        _d['FOOTER_BG_COLOR']  = _b.get('footer_bg_color') or _b.get('accent_color', '#1e69da')
    if 'FOOTER_BG_IMG' not in _d:
        _d['FOOTER_BG_IMG']    = _b.get('footer_bg_img') or _b.get('hero_bg_img', '')
    if 'EMAIL' not in _d:
        _d['EMAIL']            = _b.get('default_email', '')
    if 'PHONE' not in _d:
        _d['PHONE']            = _b.get('default_phone', '')
    if 'CITY_IN' not in _d:
        _d['CITY_IN']          = _b.get('default_city', '')
    if 'LINK_CATALOG' not in _d:
        _d['LINK_CATALOG']     = _b.get('catalog_url', '')
    if 'LINK_COMPANY' not in _d:
        _d['LINK_COMPANY']     = _b.get('about_url', '')
    if 'LINK_DELIVERY' not in _d:
        _d['LINK_DELIVERY']    = _b.get('delivery_url', '')
    if 'LINK_LOGO' not in _d:
        _d['LINK_LOGO']        = _b.get('site_url', '')
    if 'FOOTER_ADDRESS' not in _d:
        _d['FOOTER_ADDRESS']   = _b.get('footer_address', '')
    if 'BODY_TITLE_COLOR' not in _d:
        _d['BODY_TITLE_COLOR'] = _b.get('body_title_color') or '#282824'
    if 'BODY_TEXT_COLOR' not in _d:
        _d['BODY_TEXT_COLOR']  = _b.get('body_text_color') or '#3d4858'
    if 'CARD_TEXT_COLOR' not in _d:
        _d['CARD_TEXT_COLOR']  = _b.get('card_text_color') or '#555555'
    if 'FOOTER_TEXT_COLOR' not in _d:
        _d['FOOTER_TEXT_COLOR']= _b.get('footer_text_color') or '#ffffff'
    if 'HERO_TEXT_COLOR' not in _d:
        _d['HERO_TEXT_COLOR']  = _b.get('hero_text_color') or '#ffffff'
    if 'HERO_SUB_COLOR' not in _d:
        _d['HERO_SUB_COLOR']   = _b.get('hero_sub_color') or '#cccccc'
    if 'UnsubscribeUrl' not in _d:
        _d['UnsubscribeUrl']   = '{{UnsubscribeUrl}}'
    if 'webversion' not in _d:
        _d['webversion']       = '{{webversion}}'
    if 'email' not in _d:
        _d['email']            = '{{email}}'
    # Дефолты текстов для stock (отгрузка)
    if mode == 'stock' and 'TEXT_TITLE' not in _d:
        _d['TEXT_TITLE'] = 'Профильная труба всех типоразмеров'
    if mode == 'stock' and 'TEXT_BODY' not in _d:
        _d['TEXT_BODY']  = 'Обновили складской запас профильного проката. В наличии все позиции.'
    # ─────────────────────────────────────────────────────────────────────────

    tabs = st.tabs(["Бренд", "Контакты", "Баннер", "Тексты", "Блоки", "Эксперт"])

    # ---- ТАБ 0: БРЕНД ----
    with tabs[0]:
        _tab_brand()
    # ---- ТАБ 1: КОНТАКТЫ ----
    with tabs[1]:
        _tab_contacts()
    # ---- ТАБ 2: БАННЕР ----
    with tabs[2]:
        _tab_banner()
    # ---- ТАБ 3: ТЕКСТЫ ----
    with tabs[3]:
        _tab_texts()
    # ---- ТАБ 4: БЛОКИ ----
    with tabs[4]:
        _tab_blocks()
    # ---- ТАБ 5: ЭКСПЕРТ ----
    with tabs[5]:
        _tab_expert()
    # 10. СБОРКА HTML
    # ==========================================
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    st.write("---")

    if st.button("Собрать HTML", type="primary", use_container_width=True, key="build_btn"):
        upsert_autosave(
            brand['brand_id'], mode,
            dict(st.session_state.data),
            st.session_state.get('template_variant', 'default')
        )
        _build_variant  = st.session_state.get('template_variant', 'default')
        _build_eff_mode = 'promo' if mode == 'promo_inmetprom' else mode
        if _build_variant == 'default':
            file_path = os.path.join("templates", f"template_{_build_eff_mode}.html")
        else:
            _candidate = os.path.join("templates", f"template_{_build_eff_mode}_{_build_variant}.html")
            file_path = _candidate if os.path.exists(_candidate) else os.path.join("templates", f"template_{_build_eff_mode}.html")
        if not os.path.exists(file_path):
            file_path = os.path.join("templates", f"template_{_build_eff_mode}.html")
        # Если инметпром-шаблон для этого режима не существует — принудительно используем конструктор
        _is_brand_imp = (brand.get('layout_style', '') == 'inmetprom' or
                         brand.get('template_slug', '') == 'inmetprom')
        _imp_template_missing = (
            (_build_variant == 'inmetprom' or _is_brand_imp) and
            not os.path.exists(os.path.join("templates", f"template_{_build_eff_mode}_inmetprom.html"))
        )
        try:
            _bch_build = st.session_state.get('block_custom_html', {})
            _full_html = _bch_build.get('FULL', '').strip()
            _ctor_build = st.session_state.get('constructor_blocks', [])
            if _imp_template_missing and not _ctor_build:
                st.warning("Добавь блоки в конструктор (вкладка «Блоки») — шаблона Инметпром для этого режима пока нет.")
                html = None
            elif _ctor_build and (_build_variant == 'inmetprom' or _is_brand_imp):
                # Сборка из блоков конструктора
                _prefix, _suffix = get_inmetprom_shell()
                _parts = []
                for _b in _ctor_build:
                    _bhtml = _b['html']
                    for _bf in BLOCK_FIELDS.get(_b['key'], []):
                        _fkey = f"bparam__{_b['key']}__{_bf['key']}"
                        _fval = st.session_state.get(_fkey, _bf['default'])
                        if _fval != _bf['default']:
                            _bhtml = _bhtml.replace(_bf['default'], _fval)
                    _parts.append(_bhtml)
                _blocks_html = "\n".join(_parts)
                html = _prefix + _blocks_html + _suffix
                for key, val in st.session_state.data.items():
                    replacement = str(val) if val else ""
                    html = html.replace(f"{{{{{key}}}}}", replacement)
                st.success(f"Готово! (конструктор · {len(_ctor_build)} блоков)")
            elif _full_html:
                # Полная замена — используем код пользователя как есть, только подставляем переменные
                html = _full_html
                for key, val in st.session_state.data.items():
                    replacement = str(val) if val else ""
                    html = html.replace(f"{{{{{key}}}}}", replacement)
                st.success("Готово! (полный шаблон из вкладки «Блоки»)")
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    html = f.read()
                html = apply_brand_blocks(
                    html, brand,
                    header_style=st.session_state.get('header_style', 'default'),
                    footer_style=st.session_state.get('footer_style', 'default'),
                )
                # Скрыть блоки и вставить кастомный блок
                _bv = st.session_state.get('block_visibility', {})
                _hidden = [blk for blk, visible in _bv.items() if not visible]
                html = apply_block_visibility(html, _hidden, block_custom_html=_bch_build)
                for key, val in st.session_state.data.items():
                    replacement = str(val) if val else ""
                    html = html.replace(f"{{{{{key}}}}}", replacement)
                st.success("Готово!")

            if html is None:
                pass
            else:
              components.html(html, height=800, scrolling=True)

            # Проверяем, есть ли метка таймера в коде
            if html and "<!-- TIMER_SPLIT -->" in html:
                part1, part2 = html.split("<!-- TIMER_SPLIT -->")
                st.info("⏱ В этом шаблоне предусмотрено место под таймер. Скопируйте код двумя частями, а между ними вставьте код таймера в Unisender.")
                
                tab_p1, tab_p2, tab_full = st.tabs(["Часть 1 (ДО таймера)", "Часть 2 (ПОСЛЕ таймера)", "Полный код"])
                with tab_p1:
                    st.code(part1.strip(), language="html")
                with tab_p2:
                    st.code(part2.strip(), language="html")
                with tab_full:
                    st.code(html, language="html")
            elif html:
                with st.expander("Скопировать код"):
                    st.code(html, language="html")

        except Exception as e:
            st.error(f"Файл шаблона `{file_path}` не найден или произошла ошибка! {e}")
