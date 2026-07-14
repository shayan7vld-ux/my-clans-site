import streamlit as st
import requests
import time
import datetime
import csv
import io
import json
import re
import streamlit.components.v1 as components

from deep_translator import GoogleTranslator
TRANSLATOR_AVAILABLE = True

import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="TopReqClans Global", layout="wide", initial_sidebar_state="collapsed")

# ---------- API KEY (از Secrets) ----------
try:
    API_KEY = st.secrets["COC_API_KEY"]
except KeyError:
    st.error("❌ COC_API_KEY is not set in Streamlit Secrets. Please add it.")
    st.stop()

headers = {"Authorization": f"Bearer {API_KEY}"}

LANGUAGES = {
    "en": "🇺🇸 English", "fa": "🇮🇷 فارسی", "es": "🇪🇸 Español", "fr": "🇫🇷 Français",
    "de": "🇩🇪 Deutsch", "ar": "🇸🇦 العربية", "tr": "🇹🇷 Türkçe", "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文", "ja": "🇯🇵 日本語", "ko": "🇰🇷 한국어", "pt": "🇧🇷 Português",
    "it": "🇮🇹 Italiano", "nl": "🇳🇱 Nederlands", "pl": "🇵🇱 Polski", "sv": "🇸🇪 Svenska",
    "no": "🇳🇴 Norsk", "da": "🇩🇰 Dansk", "fi": "🇫🇮 Suomi",
}

TRANSLATIONS = {
    "en": {
        "title": "🏆 TOP REQ CLANS GLOBAL",
        "last_update": "⏱️ Last Update: {time}",
        "force_refresh": "🔄 Force Refresh",
        "search": "🔍 Search",
        "search_placeholder": "Name or tag (clan/player)",
        "admin_panel": "🔐 Admin Panel",
        "username": "Username", "password": "Password",
        "login": "Login", "logout": "Logout",
        "logged_in": "You are logged in as admin.",
        "last_visit_btn": "📂 Last Visit",
        "last_visit_info": "Last visit: {time}",
        "auto_refresh_caption": "Page auto-refreshes every 2 minutes.",
        "add_clan": "➕ Add Clan", "tag_input": "Clan tag (#XXXXXX)",
        "add_btn": "Add", "tag_exists": "This tag already exists.",
        "invalid_tag": "Enter a valid tag starting with #",
        "added_success": "Clan {tag} added!",
        "tracked_clans": "Tracked Clans:", "del_btn": "❌",
        "export_import": "📥 Export / 📤 Import Tags",
        "download_json": "Download Tags (JSON)", "upload_json": "Upload Tags (JSON)",
        "import_success": "Tags replaced successfully.",
        "invalid_json": "Invalid file format.", "error_reading": "Error reading file.",
        "clan_tab": "🏆 Current Season Clans",
        "player_tab": "🔥 Top Season Players",
        "legend_tab": "⭐ Level 300+ Heroes",
        "rank": "Rank", "clan": "Clan", "name": "Name",
        "leader": "Leader", "members": "Members",
        "donated": "Donated", "donated_today": "Today",
        "received": "Received", "lost": "Lost",
        "csv_download": "📥 Download CSV",
        "no_clan_found": "No clan found with these criteria.",
        "no_player_found": "No player found.",
        "no_legend_found": "No players over Level 300 found.",
        "back_btn": "⬅️ Back to Leaderboard",
        "description": "📋 **Description:** {desc}",
        "total_donated": "Total Donated", "total_received": "Total Received",
        "war_wins": "War Wins", "members_tab": "👥 Members",
        "war_tab": "⚔️ War League", "regular_war_tab": "⚔️ Regular War",
        "capital_tab": "🏛️ Capital", "player_profile": "Player Profile",
        "close_profile": "Close Profile",
        "war_not_found": "This clan is not currently in a war league.",
        "war_error": "Error fetching war league data.",
        "regular_war_not_found": "No active regular war.",
        "regular_war_history": "Previous Wars",
        "capital_not_found": "Capital data not available.",
        "capital_error": "Error fetching capital data.",
        "record_alert": "🔥 New highest donation record: {amount:,}!",
        "theme_btn": "🌓 Light/Dark Mode", "lang_btn": "🌐 Language",
        "language_select": "Language",
        "about_title": "📦 About Us", "about_creators": "Creators",
        "about_support": "Support", "about_close": "Close",
        "about_btn": "🧊 About", "war_round": "Round {number}",
        "capital_hall_level": "Capital Hall Level", "capital_league": "Capital League",
        "daily_stats_backup": "🔄 Daily Stats Backup",
        "download_daily": "📥 Download Daily Stats", "upload_daily": "📤 Upload Daily Stats (JSON)",
        "full_backup_title": "📦 Full App Backup",
        "download_full_backup": "📥 Download Full Backup (JSON)",
        "upload_full_backup": "📤 Restore Full Backup (JSON)",
        "full_restore_success": "Full backup restored successfully!",
        "full_restore_invalid": "Invalid backup file.",
        "prev_page": "⬅️ Previous", "next_page": "Next ➡️", "page": "Page",
        "archive_btn": "📅 Archive",
        "archive_title": "Monthly Archive",
        "select_month": "Select Month",
        "no_archive": "No archived data for this month.",
    },
    "fa": {
        "title": "🏆 برترین کلن‌های درخواستی",
        "last_update": "⏱️ آخرین بروزرسانی: {time}",
        "force_refresh": "🔄 بروزرسانی اجباری",
        "search": "🔍 جستجو",
        "search_placeholder": "نام یا تگ (کلن/بازیکن)",
        "admin_panel": "🔐 پنل مدیریت",
        "username": "نام کاربری", "password": "رمز عبور",
        "login": "ورود", "logout": "خروج",
        "logged_in": "شما به‌عنوان مدیر وارد شده‌اید.",
        "last_visit_btn": "📂 آخرین بازدید",
        "last_visit_info": "آخرین بازدید: {time}",
        "auto_refresh_caption": "صفحه هر ۲ دقیقه به‌طور خودکار ریلود می‌شود.",
        "add_clan": "➕ افزودن کلن", "tag_input": "تگ کلن (#XXXXXX)",
        "add_btn": "افزودن", "tag_exists": "این تگ از قبل وجود دارد.",
        "invalid_tag": "تگ معتبر وارد کنید (با # شروع شود).",
        "added_success": "کلن {tag} اضافه شد.",
        "tracked_clans": "کلن‌های ردیابی‌شده:", "del_btn": "❌",
        "export_import": "📥 خروجی / 📤 ورودی تگ‌ها",
        "download_json": "دانلود تگ‌ها (JSON)", "upload_json": "بارگذاری فایل تگ‌ها (JSON)",
        "import_success": "تگ‌ها با موفقیت جایگزین شدند.",
        "invalid_json": "فرمت فایل نامعتبر است.", "error_reading": "خطا در خواندن فایل.",
        "clan_tab": "🏆 کلن‌های فصل جاری",
        "player_tab": "🔥 برترین بازیکنان فصل",
        "legend_tab": "⭐ قهرمانان لول ۳۰۰+",
        "rank": "رتبه", "clan": "کلن", "name": "نام",
        "leader": "لیدر", "members": "اعضا",
        "donated": "اهدا", "donated_today": "امروز",
        "received": "دریافت", "lost": "از دست رفته",
        "csv_download": "📥 دانلود CSV",
        "no_clan_found": "کلنی با این مشخصات یافت نشد.",
        "no_player_found": "بازیکنی پیدا نشد.",
        "no_legend_found": "هیچ بازیکنی با لول بالای ۳۰۰ پیدا نشد.",
        "back_btn": "⬅️ بازگشت به لیدربورد",
        "description": "📋 **توضیحات:** {desc}",
        "total_donated": "کل اهدا", "total_received": "کل دریافت",
        "war_wins": "پیروزی در جنگ", "members_tab": "👥 اعضا",
        "war_tab": "⚔️ لیگ جنگ", "regular_war_tab": "⚔️ وار عادی",
        "capital_tab": "🏛️ کپیتال", "player_profile": "پروفایل بازیکن",
        "close_profile": "بستن پروفایل",
        "war_not_found": "این کلن در حال حاضر در لیگ جنگ نیست.",
        "war_error": "خطا در دریافت اطلاعات لیگ جنگ.",
        "regular_war_not_found": "وار عادی فعالی وجود ندارد.",
        "regular_war_history": "وارهای قبلی",
        "capital_not_found": "اطلاعات کپیتال در دسترس نیست.",
        "capital_error": "خطا در دریافت اطلاعات کپیتال.",
        "record_alert": "🔥 رکورد جدید بالاترین اهدا: {amount:,}!",
        "theme_btn": "🌓 تغییر تم روشن/تاریک", "lang_btn": "🌐 زبان",
        "language_select": "زبان",
        "about_title": "📦 درباره ما", "about_creators": "سازندگان",
        "about_support": "پشتیبانی", "about_close": "بستن",
        "about_btn": "🧊 درباره ما", "war_round": "راند {number}",
        "capital_hall_level": "سطح تالار کپیتال", "capital_league": "لیگ کپیتال",
        "daily_stats_backup": "🔄 پشتیبان آمار روزانه",
        "download_daily": "📥 دانلود آمار روزانه", "upload_daily": "📤 بارگذاری آمار روزانه (JSON)",
        "full_backup_title": "📦 پشتیبان کامل برنامه",
        "download_full_backup": "📥 دانلود پشتیبان کامل (JSON)",
        "upload_full_backup": "📤 بازیابی پشتیبان کامل (JSON)",
        "full_restore_success": "پشتیبان کامل با موفقیت بازیابی شد!",
        "full_restore_invalid": "فایل پشتیبان نامعتبر است.",
        "prev_page": "⬅️ قبلی", "next_page": "بعدی ➡️", "page": "صفحه",
        "archive_btn": "📅 آرشیو",
        "archive_title": "آرشیو ماهانه",
        "select_month": "انتخاب ماه",
        "no_archive": "داده‌ای برای این ماه آرشیو نشده است.",
    }
}

def auto_translate_dict(target_lang):
    if not TRANSLATOR_AVAILABLE: return None
    try:
        translator = GoogleTranslator(source='en', target=target_lang)
        en_dict = TRANSLATIONS["en"]
        translated = {}
        skip_keys = {"lang_btn", "english", "persian", "language_select", "about_btn"}
        for key, value in en_dict.items():
            if key in skip_keys:
                translated[key] = value
            else:
                translated[key] = translator.translate(value)
        return translated
    except:
        return None

def t(key, **kwargs):
    lang = st.session_state.get("lang", "en")
    if lang not in TRANSLATIONS:
        if TRANSLATOR_AVAILABLE:
            auto_dict = auto_translate_dict(lang)
            if auto_dict:
                TRANSLATIONS[lang] = auto_dict
            else:
                TRANSLATIONS[lang] = TRANSLATIONS["en"]
        else:
            TRANSLATIONS[lang] = TRANSLATIONS["en"]
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = trans.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text

if 'selected_clan_tag' not in st.session_state:
    st.session_state.selected_clan_tag = None
if 'selected_player_tag' not in st.session_state:
    st.session_state.selected_player_tag = None
if 'last_api_fetch' not in st.session_state:
    st.session_state.last_api_fetch = time.time()
if 'cached_clan_data' not in st.session_state:
    st.session_state.cached_clan_data = {}
if 'last_visit' not in st.session_state:
    st.session_state.last_visit = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False
if 'about_click_count' not in st.session_state:
    st.session_state.about_click_count = 0
if 'last_about_click' not in st.session_state:
    st.session_state.last_about_click = 0
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"
if 'max_donations_seen' not in st.session_state:
    st.session_state.max_donations_seen = 0
if 'lang' not in st.session_state:
    st.session_state.lang = "en"
if 'show_about' not in st.session_state:
    st.session_state.show_about = False
if 'app_data' not in st.session_state:
    st.session_state.app_data = None
if 'last_sheets_refresh' not in st.session_state:
    st.session_state.last_sheets_refresh = 0
if 'last_sheets_write' not in st.session_state:
    st.session_state.last_sheets_write = 0
if 'clan_page' not in st.session_state:
    st.session_state.clan_page = 1
if 'player_page' not in st.session_state:
    st.session_state.player_page = 1
if 'legend_page' not in st.session_state:
    st.session_state.legend_page = 1
if 'show_archive' not in st.session_state:
    st.session_state.show_archive = False

ITEMS_PER_PAGE = 50
SHEETS_READ_INTERVAL = 600
SHEETS_WRITE_INTERVAL = 300

# ---------- باز شدن پنل ادمین با لینک مستقیم ----------
if st.query_params.get("admin") == "1":
    st.session_state.show_admin_login = True
    st.query_params.clear()

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict,
            ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets connection error: {e}")
        return None

@st.cache_resource
def get_spreadsheet():
    client = get_gsheet_client()
    if client is None:
        return None
    try:
        sheet_id = st.secrets.get("SPREADSHEET_ID", "1_OOYWwm9HQvgv4Q4fIiE4CtEGKHHUjGPxLH6Qb5tnTE")
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"Cannot open spreadsheet: {e}")
        return None

def get_or_create_worksheet(sh, name, rows=500, cols=1):
    try:
        return sh.worksheet(name)
    except:
        try:
            return sh.add_worksheet(title=name, rows=str(rows), cols=str(cols))
        except:
            return None

def save_json_in_rows(ws, data, max_chars_per_cell=45000):
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        chunks = [json_str[i:i+max_chars_per_cell] for i in range(0, len(json_str), max_chars_per_cell)]
        ws.clear()
        if chunks:
            ws.update('A1:A'+str(len(chunks)), [[chunk] for chunk in chunks], value_input_option='RAW')
    except:
        pass

def load_json_from_rows(ws):
    try:
        values = ws.col_values(1)
        if values and values[0]:
            combined = ''.join(values)
            return json.loads(combined)
        return {}
    except:
        return {}

def load_monthly_archive():
    sh = get_spreadsheet()
    if sh is None: return {}
    try:
        ws = get_or_create_worksheet(sh, "MonthlyArchive", rows=500)
        return load_json_from_rows(ws) if ws else {}
    except:
        return {}

def save_monthly_archive(data):
    sh = get_spreadsheet()
    if sh is None: return
    try:
        ws = get_or_create_worksheet(sh, "MonthlyArchive", rows=500)
        if ws:
            save_json_in_rows(ws, data)
    except:
        pass

def refresh_app_data():
    sh = get_spreadsheet()
    if sh is None:
        return {'clan_tags': [], 'daily_stats': {}, 'member_snaps': {}, 'war_history': {}, 'donation_baselines': {}}

    data = {}
    try:
        ws = get_or_create_worksheet(sh, "ClanTags", rows=1000)
        if ws:
            tags = ws.col_values(1)
            data['clan_tags'] = [t.strip() for t in tags if t.strip()]
        else:
            data['clan_tags'] = []
    except:
        data['clan_tags'] = []

    for name, key in [("DailyStats", "daily_stats"), ("MemberSnapshots", "member_snaps"), ("WarHistory", "war_history"), ("DonationBaselines", "donation_baselines")]:
        try:
            ws = get_or_create_worksheet(sh, name, rows=2000)
            data[key] = load_json_from_rows(ws) if ws else {}
        except:
            data[key] = {}

    return data

def save_app_data(data, force=False):
    if not force:
        if st.session_state.app_data is not None and data == st.session_state.app_data:
            return
        now = time.time()
        if now - st.session_state.last_sheets_write < SHEETS_WRITE_INTERVAL:
            st.session_state.app_data = data
            return

    sh = get_spreadsheet()
    if sh is None: return

    try:
        ws = get_or_create_worksheet(sh, "ClanTags", rows=1000)
        if ws:
            ws.clear()
            if data.get('clan_tags'):
                ws.update('A1:A'+str(len(data['clan_tags'])), [[t] for t in data['clan_tags']], value_input_option='RAW')
    except:
        pass

    for name, key in [("DailyStats", "daily_stats"), ("MemberSnapshots", "member_snaps"), ("WarHistory", "war_history"), ("DonationBaselines", "donation_baselines")]:
        try:
            ws = get_or_create_worksheet(sh, name, rows=2000)
            if ws:
                save_json_in_rows(ws, data.get(key, {}))
        except:
            pass

    st.session_state.app_data = data
    st.session_state.last_sheets_write = time.time()
    st.session_state.last_sheets_refresh = time.time()

def get_app_data():
    now = time.time()
    if (st.session_state.app_data is None or 
        (now - st.session_state.last_sheets_refresh) > SHEETS_READ_INTERVAL):
        try:
            st.session_state.app_data = refresh_app_data()
        except:
            if st.session_state.app_data is None:
                st.session_state.app_data = {'clan_tags': [], 'daily_stats': {}, 'member_snaps': {}, 'war_history': {}, 'donation_baselines': {}}
        st.session_state.last_sheets_refresh = now
    return st.session_state.app_data

def load_clan_tags_sheets():
    return get_app_data().get('clan_tags', [])

def load_daily_stats_sheets():
    return get_app_data().get('daily_stats', {})

def load_member_snapshot_sheets():
    return get_app_data().get('member_snaps', {})

def load_war_history_sheets():
    return get_app_data().get('war_history', {})

def load_donation_baselines():
    return get_app_data().get('donation_baselines', {})

def save_clan_tags_sheets(tags):
    data = get_app_data()
    data['clan_tags'] = tags
    save_app_data(data, force=True)

def save_daily_stats_sheets(stats):
    data = get_app_data()
    data['daily_stats'] = stats
    save_app_data(data, force=True)

def save_member_snapshot_sheets(snaps):
    data = get_app_data()
    data['member_snaps'] = snaps
    save_app_data(data)

def save_war_history_sheets(history):
    data = get_app_data()
    data['war_history'] = history
    save_app_data(data)

def save_donation_baselines(baselines):
    data = get_app_data()
    data['donation_baselines'] = baselines
    save_app_data(data, force=True)

if 'clan_tags' not in st.session_state:
    st.session_state.clan_tags = load_clan_tags_sheets()

CLAN_TAGS = st.session_state.clan_tags

# ---------- Cube ----------
st.markdown("""
<style>
.cube-container {
    position: fixed;
    top: 15px;
    left: 15px;
    z-index: 9999;
    width: 40px;
    height: 40px;
    perspective: 80px;
    cursor: pointer;
}
.cube {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    animation: rotateCube 4s infinite linear;
}
.cube-face {
    position: absolute;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #ffaa45, #ff7b00);
    border: 1px solid #fff;
    opacity: 0.9;
}
.front  { transform: rotateY(0deg) translateZ(20px); }
.back   { transform: rotateY(180deg) translateZ(20px); }
.right  { transform: rotateY(90deg) translateZ(20px); }
.left   { transform: rotateY(-90deg) translateZ(20px); }
.top    { transform: rotateX(90deg) translateZ(20px); }
.bottom { transform: rotateX(-90deg) translateZ(20px); }
@keyframes rotateCube {
    from { transform: rotateX(0deg) rotateY(0deg); }
    to   { transform: rotateX(360deg) rotateY(360deg); }
}
</style>
<div class="cube-container" onclick="
    var sidebar = window.parent.document.querySelector('[data-testid=stSidebar]');
    if (sidebar) sidebar.style.display = 'block';
    var btn = window.parent.document.querySelector('button[data-testid=baseButton-header]');
    if (btn) btn.click();
">
    <div class="cube">
        <div class="cube-face front"></div>
        <div class="cube-face back"></div>
        <div class="cube-face right"></div>
        <div class="cube-face left"></div>
        <div class="cube-face top"></div>
        <div class="cube-face bottom"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Hidden auto-refresh
st.markdown("""
<style>
button:has(span:contains("hiddenRefresh")) {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

if st.button("hiddenRefresh", key="hidden_refresh_btn"):
    pass

components.html("""
<script>
setInterval(function() {
    const buttons = window.parent.document.querySelectorAll('button');
    for (let btn of buttons) {
        if (btn.innerText.includes('hiddenRefresh')) {
            btn.click();
            break;
        }
    }
}, 120000);
</script>
""", height=0)

def fetch_all_data():
    current_time = time.time()
    if current_time - st.session_state.last_api_fetch > 120 or not st.session_state.cached_clan_data:
        new_cache = {}
        for tag in CLAN_TAGS:
            clean_tag = tag.replace("#", "%23")
            url = f"https://cocproxy.royaleapi.dev/v1/clans/{clean_tag}"
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    new_cache[tag] = res.json()
            except:
                continue
        if new_cache:
            st.session_state.cached_clan_data = new_cache
            st.session_state.last_api_fetch = current_time

fetch_all_data()
seconds_ago = int(time.time() - st.session_state.last_api_fetch)
time_string = f"{seconds_ago}s ago" if seconds_ago < 60 else f"{seconds_ago // 60}m {seconds_ago % 60}s ago"

def get_theme_css():
    if st.session_state.theme == "light":
        return """
        <style>
        .stApp { background-color: #f5f5f7; color: #1c1e21; }
        .header-container { background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.1); }
        .header-title { color: #1c1e21; text-shadow: 0 0 10px #ffaa45; }
        .update-box { background: rgba(255,170,65,0.1); color: #cc5500; border-color: #cc5500; }
        .custom-table { background: rgba(255,255,255,0.6); }
        .custom-table th { background: rgba(240,240,240,0.9); color: #cc5500; border-bottom-color: #cc5500; }
        .custom-table td { color: #1c1e21; border-bottom-color: rgba(0,0,0,0.1); }
        .custom-table tr:hover { background-color: rgba(0,0,0,0.03); }
        .glass-card { background: rgba(255,255,255,0.4) !important; border-color: rgba(0,0,0,0.1) !important; border-top-color: #ffaa45 !important; }
        .glass-metric { background: rgba(255,255,255,0.3); border-color: rgba(0,0,0,0.05); }
        .lvl-badge, .th-badge { color: #fff; }
        .war-card { background: rgba(255,255,255,0.8); border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; padding: 10px; margin: 10px 0; backdrop-filter: blur(10px); }
        .clan-card { background: rgba(255,255,255,0.6) !important; border: 1px solid rgba(0,0,0,0.1) !important; border-radius: 16px; padding: 15px; margin-bottom: 12px; backdrop-filter: blur(20px); transition: all 0.2s; display: flex; align-items: center; }
        .clan-card:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .war-card h4 { margin-top: 0; } .war-clan-name { font-weight: bold; }
        .war-stats { display: flex; justify-content: space-between; }
        .stat-label { font-size: 10px; color: #6c757d; display: block; }
        .stat-value { font-size: 16px; font-weight: bold; }
        .clan-name-text {
            font-size: 18px;
            font-weight: bold;
            color: #000;
            text-shadow: 0 0 10px rgba(255,170,69,0.8), 0 0 20px rgba(255,170,69,0.5);
        }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color: #0d1117; color: #c9d1d9; }
        .header-container { background: rgba(22, 27, 34, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); }
        .header-title { color: #f0f6fc; text-shadow: 0 0 15px #ffaa45; }
        .update-box { background: rgba(255, 170, 65, 0.15); border: 1px solid #ffaa45; color: #ffaa45; }
        .custom-table { background: rgba(22, 27, 34, 0.6); }
        .custom-table th { background: rgba(33, 38, 45, 0.9); color: #ffaa45; border-bottom-color: #ffaa45; }
        .custom-table td { color: #c9d1d9; border-bottom-color: rgba(255, 255, 255, 0.05); }
        .custom-table tr:hover { background-color: rgba(255, 255, 255, 0.04); }
        .glass-card { background: rgba(255, 255, 255, 0.04) !important; border-color: rgba(255, 255, 255, 0.1) !important; border-top-color: #ffaa45 !important; }
        .glass-metric { background: rgba(255, 255, 255, 0.03); border-color: rgba(255, 255, 255, 0.08); }
        .lvl-badge { background-color: #1f6feb; } .th-badge { background-color: #da70d6; }
        .war-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px; margin: 10px 0; backdrop-filter: blur(10px); }
        .clan-card { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 16px; padding: 15px; margin-bottom: 12px; backdrop-filter: blur(20px); transition: all 0.2s; display: flex; align-items: center; }
        .clan-card:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .war-card h4 { color: #ffaa45; margin-top: 0; } .war-clan-name { font-weight: bold; color: #f0f6fc; }
        .war-stats { display: flex; justify-content: space-between; color: #c9d1d9; }
        .stat-label { font-size: 10px; color: #8b949e; display: block; }
        .stat-value { font-size: 16px; font-weight: bold; }
        .clan-name-text {
            font-size: 18px;
            font-weight: bold;
            color: #000;
            text-shadow: 0 0 10px rgba(255,170,69,0.8), 0 0 20px rgba(255,170,69,0.5);
        }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

st.markdown("""
<style>
@keyframes dance {
    0% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-10px) rotate(5deg); }
    100% { transform: translateY(0) rotate(-5deg); }
}
.dancer { font-size: 45px; display: inline-block; animation: dance 0.5s infinite alternate ease-in-out; text-align: center; width: 100%; margin-top: 10px; }
.table-wrapper { overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); margin-top: 15px; }
.custom-table { width: 100%; min-width: 800px; border-collapse: collapse; }
.custom-table th { padding: 12px 8px; font-weight: bold; text-align: center; font-size: 14px; }
.custom-table td { padding: 10px 8px; text-align: center; font-size: 14px; }
.glass-card { backdrop-filter: blur(20px); border-radius: 16px; padding: 20px; margin-bottom: 25px; }
.glass-metric { backdrop-filter: blur(10px); border-radius: 12px; padding: 15px; text-align: center; border-bottom: 3px solid #45f3ff; }
@media (max-width: 768px) {
    .header-title { font-size: 28px; }
    .update-box { font-size: 12px; padding: 6px 12px; }
    .dancer { font-size: 32px; }
    .custom-table th, .custom-table td { font-size: 12px; padding: 8px 4px; }
    .glass-metric h2 { font-size: 20px; }
    .clan-card { flex-wrap: wrap; }
}
</style>
""", unsafe_allow_html=True)

# ---- Parse & daily stats ----
all_clans_list = []
all_players_list = []

for tag, data in st.session_state.cached_clan_data.items():
    total_donations = sum(m.get('donations', 0) for m in data.get('memberList', []))
    total_received = sum(m.get('donationsReceived', 0) for m in data.get('memberList', []))
    leader_name = next((m['name'] for m in data.get('memberList', []) if m['role'] == 'leader'), "Unknown")
    all_clans_list.append({
        "name": data['name'], "tag": data['tag'], "level": data['clanLevel'],
        "leader": leader_name, "members": data['members'], "donations": total_donations,
        "received": total_received, "badge": data.get('badgeUrls', {}).get('medium', ''),
        "description": data.get('description', 'No Description Set.'), "points": data.get('clanPoints', 0),
        "location": data.get('location', {}).get('name', 'International'), "members_raw": data.get('memberList', []),
        "war_wins": data.get('warWins', 0), "war_ties": data.get('warTies', 0), "war_losses": data.get('warLosses', 0),
        "capital_hall_level": data.get('clanCapital', {}).get('capitalHallLevel', 0),
        "capital_league": data.get('capitalLeague', {}).get('name', 'Unranked'),
        "war_league": data.get('league', {}).get('name', 'Unranked'),
        "war_league_icon": data.get('league', {}).get('iconUrls', {}).get('small', ''),
    })
    for m in data.get('memberList', []):
        all_players_list.append({
            "name": m['name'], "clan_name": data['name'], "clan_badge": data.get('badgeUrls', {}).get('small', ''),
            "level": m.get('expLevel', 0), "donations": m.get('donations', 0), "received": m.get('donationsReceived', 0),
            "role": m['role'].capitalize(), "tag": m['tag'], "trophies": m.get('trophies', 0),
            "versus_trophies": m.get('versusTrophies', 0), "town_hall": m.get('townHallLevel', 0),
            "donations_today": 0,
        })

baselines = load_donation_baselines()
now = datetime.datetime.now()
today_830 = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 30))
if now < today_830:
    day_start = today_830 - datetime.timedelta(days=1)
else:
    day_start = today_830
day_key = day_start.strftime("%Y-%m-%d %H:%M")
if day_key not in baselines:
    baselines[day_key] = {}
    for clan in all_clans_list:
        baselines[day_key][clan['tag']] = clan['donations']
    cutoff = day_start - datetime.timedelta(days=7)
    baselines = {k: v for k, v in baselines.items() if k >= cutoff.strftime("%Y-%m-%d %H:%M")}
    save_donation_baselines(baselines)

current_baselines = baselines.get(day_key, {})
for clan in all_clans_list:
    baseline = current_baselines.get(clan['tag'])
    if baseline is None:
        baseline = clan['donations']
        current_baselines[clan['tag']] = baseline
        save_donation_baselines(baselines)
    clan['donations_today'] = max(0, clan['donations'] - baseline)

daily_stats = load_daily_stats_sheets()
yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
yesterday_players = daily_stats.get(yesterday_str, {}).get("players", {})
for player in all_players_list:
    yesterday_total = yesterday_players.get(player['tag'], 0)
    player['donations_today'] = max(0, player['donations'] - yesterday_total)

member_snaps = load_member_snapshot_sheets()
new_snaps = {}
season_lost = daily_stats.get("season_lost", {})
monthly_archive = load_monthly_archive()

for clan in all_clans_list:
    tag = clan['tag']
    current_members = {m['tag']: m['donations'] for m in clan['members_raw']}
    last_members = member_snaps.get(tag, {})
    left_players = set(last_members.keys()) - set(current_members.keys())
    new_lost = sum(last_members[p] for p in left_players)
    baseline = current_baselines.get(tag, clan['donations'])
    if baseline > 0 and clan['donations'] < baseline * 0.1:
        month_key = day_start.strftime("%Y-%m")
        if month_key not in monthly_archive:
            monthly_archive[month_key] = []
        monthly_archive[month_key].append({
            "name": clan['name'],
            "tag": clan['tag'],
            "level": clan['level'],
            "donations": baseline,
            "received": clan['received'],
            "members": clan['members'],
            "leader": clan['leader']
        })
        season_lost[tag] = 0
    else:
        season_lost[tag] = season_lost.get(tag, 0) + new_lost

    clan['lost_season'] = season_lost[tag]
    new_snaps[tag] = current_members

save_monthly_archive(monthly_archive)
save_member_snapshot_sheets(new_snaps)
daily_stats["season_lost"] = season_lost
today_snapshot = {
    "clans": {c['tag']: {"donations": c['donations'], "received": c['received']} for c in all_clans_list},
    "players": {p['tag']: p['donations'] for p in all_players_list}
}
daily_stats[datetime.date.today().isoformat()] = today_snapshot
save_daily_stats_sheets(daily_stats)

if all_clans_list:
    all_clans_list = sorted(all_clans_list, key=lambda x: x['donations'], reverse=True)

current_max = max(c['donations'] for c in all_clans_list) if all_clans_list else 0
if current_max > st.session_state.max_donations_seen:
    st.session_state.max_donations_seen = current_max
    st.toast(t("record_alert", amount=current_max), icon="🎉")

def filter_clans(clan_list, query):
    if not query: return clan_list
    q = query.lower()
    return [c for c in clan_list if q in c['name'].lower() or q in c['tag'].lower()]

def filter_players(player_list, query):
    if not query: return player_list
    q = query.lower()
    return [p for p in player_list if q in p['name'].lower() or q in p['tag'].lower()]

def show_player_profile(player):
    st.markdown(f"""
    <div class="glass-card">
        <img src="{player['clan_badge']}" width="40" style="vertical-align:middle"> 
        <strong>{player['name']}</strong> – {player['role']}<br>
        🏆 Trophies: {player['trophies']:,} | 🛖 TH: {player.get('town_hall', '؟')}<br>
        🔥 Donated: {player['donations']:,} | 📥 Received: {player['received']:,} | ⭐ Level: {player['level']}<br>
        Tag: {player['tag']}
    </div>
    """, unsafe_allow_html=True)

def csv_download_button(data, filename, columns, headers):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow([row.get(col, "") for col in columns])
    st.download_button(t("csv_download"), output.getvalue(), file_name=filename, mime="text/csv")

def add_war_to_history_sheets(clan_tag, war_data):
    history = load_war_history_sheets()
    if clan_tag not in history:
        history[clan_tag] = []
    war_tag = war_data.get("warTag")
    if not any(w.get("warTag") == war_tag for w in history[clan_tag]):
        history[clan_tag].append(war_data)
    save_war_history_sheets(history)

def paginate(items, page_key):
    page = st.session_state.get(page_key, 1)
    total = len(items)
    total_pages = max(1, -(-total // ITEMS_PER_PAGE))
    if page < 1:
        st.session_state[page_key] = 1
        page = 1
    elif page > total_pages:
        st.session_state[page_key] = total_pages
        page = total_pages
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    return items[start:end], page, total_pages, total

def show_pagination(total_pages, page, total, page_key):
    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        with col1:
            if st.button(t("prev_page"), key=f"prev_{page_key}"):
                st.session_state[page_key] = max(1, page - 1)
                st.rerun()
        with col3:
            st.write(f"{t('page')} {page} / {total_pages} ({total})")
        with col5:
            if st.button(t("next_page"), key=f"next_{page_key}"):
                st.session_state[page_key] = min(total_pages, page + 1)
                st.rerun()

# ---------- Sidebar ----------
with st.sidebar:
    if st.button(t("about_btn"), use_container_width=True):
        now = time.time()
        if now - st.session_state.last_about_click < 5:
            st.session_state.about_click_count += 1
        else:
            st.session_state.about_click_count = 1
        st.session_state.last_about_click = now
        if st.session_state.about_click_count >= 3:
            st.session_state.show_admin_login = True
            st.session_state.about_click_count = 0
        st.session_state.show_about = not st.session_state.show_about
        st.rerun()

    if st.session_state.show_about:
        with st.container():
            st.subheader(t("about_title"))
            st.markdown(f"""
            **{t("about_creators")}**  
            📱 Telegram: @amiirdelavari  
            📱 Telegram: @Leader_mr_reza  
            📷 Instagram: @amiirdelavari  

            **{t("about_support")}**  
            🆘 Support: @amiirdelavari  
            """)
            if st.button(t("about_close")):
                st.session_state.show_about = False
                st.rerun()

    st.header(t("lang_btn"))
    lang_options = list(LANGUAGES.values())
    lang_codes = list(LANGUAGES.keys())
    if st.session_state.lang not in lang_codes:
        st.session_state.lang = "en"
    current_index = lang_codes.index(st.session_state.lang)
    selected_display = st.selectbox(t("language_select"), lang_options, index=current_index)
    selected_code = lang_codes[lang_options.index(selected_display)]
    if selected_code != st.session_state.lang:
        st.session_state.lang = selected_code
        st.rerun()

    if st.button(t("theme_btn")):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    st.header(t("search"))
    search_query = st.text_input(t("search_placeholder"))

    if st.session_state.admin_authenticated:
        st.markdown("---")
        st.header(t("admin_panel"))
        st.success(t("logged_in"))
        if st.button(t("logout")):
            st.session_state.admin_authenticated = False
            st.session_state.show_admin_login = False
            st.rerun()

        if st.button(t("last_visit_btn")):
            st.info(t("last_visit_info", time=st.session_state.last_visit))
        st.caption(t("auto_refresh_caption"))

        st.markdown("---")
        st.subheader(t("add_clan"))
        new_tag = st.text_input(t("tag_input"), max_chars=15)
        if st.button(t("add_btn"), key="add_clan_btn"):
            if new_tag and new_tag.startswith("#") and len(new_tag) > 1:
                clean = new_tag.strip().upper()
                if clean not in st.session_state.clan_tags:
                    st.session_state.clan_tags.append(clean)
                    save_clan_tags_sheets(st.session_state.clan_tags)
                    st.success(t("added_success", tag=clean))
                    st.session_state.last_api_fetch = 0.0
                    st.rerun()
                else:
                    st.warning(t("tag_exists"))
            else:
                st.error(t("invalid_tag"))

        st.markdown(f"**{t('tracked_clans')}**")
        for i, tag in enumerate(st.session_state.clan_tags):
            col1, col2 = st.columns([4, 1])
            with col1: st.write(tag)
            with col2:
                if st.button(t("del_btn"), key=f"del_{i}"):
                    st.session_state.clan_tags.pop(i)
                    save_clan_tags_sheets(st.session_state.clan_tags)
                    st.session_state.last_api_fetch = 0.0
                    st.rerun()

        st.subheader(t("export_import"))
        tags_json = json.dumps(st.session_state.clan_tags)
        st.download_button(t("download_json"), tags_json, file_name="clan_tags.json")
        uploaded_file = st.file_uploader(t("upload_json"), type="json")
        if uploaded_file is not None:
            try:
                imported = json.loads(uploaded_file.getvalue().decode())
                if isinstance(imported, list) and all(isinstance(tag, str) for tag in imported):
                    st.session_state.clan_tags = imported
                    save_clan_tags_sheets(imported)
                    st.success(t("import_success"))
                    st.session_state.last_api_fetch = 0.0
                    st.rerun()
                else:
                    st.error(t("invalid_json"))
            except:
                st.error(t("error_reading"))

        st.subheader(t("full_backup_title"))
        if st.button(t("download_full_backup")):
            full_data = get_app_data()
            st.download_button("Click to download", json.dumps(full_data), "full_backup.json")
        uploaded_full = st.file_uploader(t("upload_full_backup"), type="json", key="full_restore")
        if uploaded_full is not None:
            try:
                data = json.loads(uploaded_full.getvalue().decode())
                save_app_data(data, force=True)
                st.session_state.clan_tags = data.get('clan_tags', [])
                st.success(t("full_restore_success"))
                st.rerun()
            except:
                st.error(t("full_restore_invalid"))

        st.subheader(t("daily_stats_backup"))
        if st.button(t("download_daily")):
            stats = load_daily_stats_sheets()
            st.download_button("Download", json.dumps(stats), "daily_stats.json")
        uploaded_daily = st.file_uploader(t("upload_daily"), type="json", key="daily_upload")
        if uploaded_daily is not None:
            try:
                data = json.loads(uploaded_daily.getvalue().decode())
                save_daily_stats_sheets(data)
                st.success("Daily stats uploaded!")
                st.rerun()
            except:
                st.error("Invalid daily stats file.")

    elif st.session_state.show_admin_login:
        st.markdown("---")
        st.header(t("admin_panel"))
        username = st.text_input(t("username"))
        password = st.text_input(t("password"), type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("login")):
                if username == "amirdelavari" and password == "Amirgameover1382":
                    st.session_state.admin_authenticated = True
                    st.session_state.show_admin_login = False
                    st.success(t("logged_in"))
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        with col2:
            if st.button("Cancel"):
                st.session_state.show_admin_login = False
                st.rerun()

# ---------- Force Refresh + Archive ----------
col_refresh, col_archive, _ = st.columns([2, 2, 6])
with col_refresh:
    if st.button(t("force_refresh"), use_container_width=True):
        st.session_state.last_api_fetch = 0.0
        st.rerun()
with col_archive:
    if st.button(t("archive_btn"), use_container_width=True):
        st.session_state.show_archive = True

# ---------- Main Header ----------
col_head, col_dance = st.columns([8, 2])
with col_head:
    st.markdown(f'<div class="header-container"><div class="header-title" style="font-size:42px;">{t("title")}</div><div class="update-box">{t("last_update", time=time_string)}</div></div>', unsafe_allow_html=True)
with col_dance:
    st.markdown('<div class="dancer">🕺🤖</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="display: flex; justify-content: center; margin: 10px 0;">'
    '<a href="https://link.clashofclans.com/?action=OpenGlobalChat&chatId=Paa8aa7e0a64a43658cef0bd6c58f2704" target="_blank" '
    'style="text-decoration: none; background: linear-gradient(135deg, #ffaa45, #ff7b00); color: white; padding: 10px 25px; border-radius: 12px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 10px rgba(255,170,69,0.4);">'
    '💬 Global Chat</a></div>',
    unsafe_allow_html=True
)

@st.dialog(t("archive_title"))
def show_archive_dialog():
    archive = load_monthly_archive()
    months = sorted(archive.keys(), reverse=True)
    if not months:
        st.info(t("no_archive"))
        return
    selected_month = st.selectbox(t("select_month"), months)
    if selected_month:
        entries = archive[selected_month]
        if entries:
            st.write(f"**{len(entries)} clans**")
            df = []
            for e in entries:
                df.append({
                    "Name": e['name'],
                    "Tag": e['tag'],
                    "Level": e['level'],
                    "Donations": f"{e['donations']:,}",
                    "Received": f"{e['received']:,}",
                    "Members": e['members'],
                    "Leader": e['leader']
                })
            st.table(df)
        else:
            st.info(t("no_archive"))

if st.session_state.show_archive:
    show_archive_dialog()
    st.session_state.show_archive = False

# ---------- Routing ----------
if st.session_state.selected_clan_tag:
    selected_clan = next((c for c in all_clans_list if c['tag'] == st.session_state.selected_clan_tag), None)
    if selected_clan:
        col_back_title, col_back_btn = st.columns([8, 2])
        with col_back_btn:
            if st.button(t("back_btn"), use_container_width=True):
                st.session_state.selected_clan_tag = None
                st.session_state.selected_player_tag = None
                st.rerun()

        league_icon_html = ""
        if selected_clan['war_league_icon']:
            league_icon_html = f'<img src="{selected_clan["war_league_icon"]}" width="24" style="vertical-align:middle; margin-left:8px;" title="{selected_clan["war_league"]}">'

        st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <img src="{selected_clan['badge']}" width="85">
                    <div>
                        <h2 style="color: inherit; margin: 0;">{selected_clan['name']}</h2>
                        <p style="color: #ffaa45;">{selected_clan['tag']} | {t('leader')}: {selected_clan['leader']}</p>
                    </div>
                </div>
                <div>
                    <span style="color:#00ffcc; font-weight:bold;">Level {selected_clan['level']} {league_icon_html}</span><br>
                    <span style="color:gray;">{selected_clan['location']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info(t("description", desc=selected_clan['description']))

        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            st.markdown(f'<div class="glass-metric"><p>{t("total_donated")}</p><h2>{selected_clan["donations"]:,}</h2></div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f'<div class="glass-metric" style="border-bottom-color: #c5a1ff;"><p>{t("total_received")}</p><h2>{selected_clan["received"]:,}</h2></div>', unsafe_allow_html=True)
        with m_col3:
            st.markdown(f'<div class="glass-metric" style="border-bottom-color: #ffaa45;"><p>{t("donated_today")}</p><h2>{selected_clan.get("donations_today", 0):,}</h2></div>', unsafe_allow_html=True)
        with m_col4:
            st.markdown(f'<div class="glass-metric" style="border-bottom-color: #ff6b6b;"><p>{t("lost")}</p><h2>{selected_clan.get("lost_season", 0):,}</h2></div>', unsafe_allow_html=True)
        with m_col5:
            st.markdown(f'<div class="glass-metric" style="border-bottom-color: #45f3ff;"><p>{t("war_wins")}</p><h2>{selected_clan.get("war_wins", 0)}</h2></div>', unsafe_allow_html=True)

        tab_overview, tab_regular_war, tab_war_league, tab_capital = st.tabs([
            t("members_tab"), t("regular_war_tab"), t("war_tab"), t("capital_tab")
        ])

        with tab_overview:
            sorted_m = sorted(selected_clan['members_raw'], key=lambda x: x.get('donations', 0), reverse=True)
            if st.session_state.selected_player_tag:
                player = next((p for p in all_players_list if p['tag'] == st.session_state.selected_player_tag), None)
                if player:
                    st.subheader(t("player_profile"))
                    show_player_profile(player)
                    if st.button(t("close_profile")):
                        st.session_state.selected_player_tag = None
                        st.rerun()
                else:
                    st.session_state.selected_player_tag = None

            table_html = f"<div class='table-wrapper'><table class='custom-table'><thead><tr><th>{t('rank')}</th><th>{t('name')}</th><th>{t('role')}</th><th>{t('level')}</th><th>🔥 {t('donations')}</th><th>🔥 {t('donated_today')}</th><th>📥 {t('received_col')}</th></tr></thead><tbody>"
            for idx, m in enumerate(sorted_m, 1):
                player_tag = m['tag']
                player_data = next((p for p in all_players_list if p['tag'] == player_tag), None)
                today_donations = player_data.get('donations_today', 0) if player_data else 0
                table_html += f"<tr><td>{idx}</td><td><a href='?player={player_tag}' style='color:white; font-weight:bold;'>{m['name']}</a></td><td>{m['role']}</td><td><span class='lvl-badge'>⭐ {m.get('expLevel',0)}</span></td><td style='color:#00ffcc'>{m.get('donations',0):,}</td><td style='color:#ffaa45; font-weight:bold;'>{today_donations:,}</td><td>{m.get('donationsReceived',0):,}</td></tr>"
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)

            if 'player' in st.query_params:
                player_tag = st.query_params['player']
                if player_tag != st.session_state.get('selected_player_tag'):
                    st.session_state.selected_player_tag = player_tag
                    st.query_params.clear()
                    st.rerun()

        with tab_regular_war:
            st.subheader(t("regular_war_tab"))
            try:
                clean = selected_clan['tag'].replace("#", "%23")
                war_url = f"https://cocproxy.royaleapi.dev/v1/clans/{clean}/currentwar"
                resp = requests.get(war_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    war_data = resp.json()
                    state = war_data.get("state", "notInWar")
                    if state == "notInWar":
                        st.info(t("regular_war_not_found"))
                    else:
                        clan = war_data.get("clan", {})
                        opponent = war_data.get("opponent", {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            <div class="war-card">
                                <img src="{clan.get('badgeUrls',{}).get('small','')}" width="30" style="vertical-align:middle">
                                <span class="war-clan-name">{clan.get('name','Unknown')}</span>
                                <div class="war-stats">
                                    <span>⭐ {clan.get('stars',0)}</span>
                                    <span>{clan.get('destructionPercentage',0):.1f}%</span>
                                    <span>Attacks: {clan.get('attacks',0)}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                            <div class="war-card">
                                <img src="{opponent.get('badgeUrls',{}).get('small','')}" width="30" style="vertical-align:middle">
                                <span class="war-clan-name">{opponent.get('name','Unknown')}</span>
                                <div class="war-stats">
                                    <span>⭐ {opponent.get('stars',0)}</span>
                                    <span>{opponent.get('destructionPercentage',0):.1f}%</span>
                                    <span>Attacks: {opponent.get('attacks',0)}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.caption(f"State: {state} – War tag: {war_data.get('warTag','?')}")
                        if state == "warEnded":
                            history_entry = {
                                "warTag": war_data.get("warTag"),
                                "clanName": clan.get("name"),
                                "clanStars": clan.get("stars", 0),
                                "clanDestruction": clan.get("destructionPercentage", 0),
                                "opponentName": opponent.get("name"),
                                "opponentStars": opponent.get("stars", 0),
                                "opponentDestruction": opponent.get("destructionPercentage", 0),
                                "date": datetime.date.today().isoformat(),
                                "result": "win" if clan.get("stars", 0) > opponent.get("stars", 0) else "loss" if clan.get("stars", 0) < opponent.get("stars", 0) else "draw"
                            }
                            add_war_to_history_sheets(selected_clan['tag'], history_entry)
                else:
                    st.info(t("regular_war_not_found"))
            except:
                st.error(t("war_error"))

            st.subheader(t("regular_war_history"))
            history = load_war_history_sheets()
            clan_wars = history.get(selected_clan['tag'], [])
            if clan_wars:
                war_table = "<div class='table-wrapper'><table class='custom-table'><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Stars</th><th>Destruction</th></tr></thead><tbody>"
                for w in reversed(clan_wars[-10:]):
                    war_table += f"<tr><td>{w.get('date','?')}</td><td>{w.get('opponentName','Unknown')}</td><td>{w.get('result','?')}</td><td>⭐ {w.get('clanStars',0)}</td><td>{w.get('clanDestruction',0):.1f}%</td></tr>"
                war_table += "</tbody></table></div>"
                st.markdown(war_table, unsafe_allow_html=True)
            else:
                st.info("No war history yet.")

        with tab_war_league:
            try:
                clean = selected_clan['tag'].replace("#", "%23")
                war_url = f"https://cocproxy.royaleapi.dev/v1/clans/{clean}/currentwar/leaguegroup"
                resp = requests.get(war_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    league = resp.json()
                    st.subheader(t("war_tab"))
                    rounds = league.get('rounds', [])
                    for round_idx, rnd in enumerate(rounds, 1):
                        st.markdown(f"### {t('war_round', number=round_idx)}")
                        war_tags = rnd.get('warTags', [])
                        if not war_tags:
                            st.info("No wars in this round.")
                            continue
                        for war_tag in war_tags:
                            try:
                                war_detail_url = f"https://cocproxy.royaleapi.dev/v1/clanwarleagues/wars/{war_tag.replace('#', '%23')}"
                                war_resp = requests.get(war_detail_url, headers=headers, timeout=5)
                                if war_resp.status_code == 200:
                                    war = war_resp.json()
                                    clan1 = war.get('clan', {})
                                    clan2 = war.get('opponent', {})
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"""
                                        <div class="war-card">
                                            <img src="{clan1.get('badgeUrls',{}).get('small','')}" width="30" style="vertical-align:middle">
                                            <span class="war-clan-name">{clan1.get('name','Unknown')}</span>
                                            <div class="war-stats">
                                                <span>⭐ {clan1.get('stars',0)}</span>
                                                <span>{clan1.get('destructionPercentage',0):.1f}%</span>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    with col2:
                                        st.markdown(f"""
                                        <div class="war-card">
                                            <img src="{clan2.get('badgeUrls',{}).get('small','')}" width="30" style="vertical-align:middle">
                                            <span class="war-clan-name">{clan2.get('name','Unknown')}</span>
                                            <div class="war-stats">
                                                <span>⭐ {clan2.get('stars',0)}</span>
                                                <span>{clan2.get('destructionPercentage',0):.1f}%</span>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    st.caption(f"War tag: {war_tag}")
                                else:
                                    st.write(f"War {war_tag} (could not load details)")
                            except:
                                st.write(f"War {war_tag} (details unavailable)")
                else:
                    st.info(t("war_not_found"))
            except:
                st.error(t("war_error"))

        with tab_capital:
            st.subheader(t("capital_tab"))
            col1, col2 = st.columns(2)
            with col1:
                st.metric(t("capital_hall_level"), selected_clan.get('capital_hall_level', 0))
            with col2:
                st.metric(t("capital_league"), selected_clan.get('capital_league', 'Unranked'))
            try:
                clean = selected_clan['tag'].replace("#", "%23")
                capital_url = f"https://cocproxy.royaleapi.dev/v1/clans/{clean}/capitalraidseasons"
                resp = requests.get(capital_url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    capital = resp.json()
                    st.subheader("Last Raid Weekend")
                    if 'items' in capital and len(capital['items']) > 0:
                        last = capital['items'][0]
                        st.write(f"Attacks: {last.get('attackCount',0)}")
                        st.write(f"Districts destroyed: {last.get('districtsDestroyed',0)}")
                        st.write(f"Total loot: {last.get('capitalTotalLoot',0):,}")
                    else:
                        st.info(t("capital_not_found"))
                else:
                    st.info(t("capital_not_found"))
            except:
                st.error(t("capital_error"))

else:
    tab1, tab2, tab3 = st.tabs([t("clan_tab"), t("player_tab"), t("legend_tab")])

    with tab1:
        filtered_clans = filter_clans(all_clans_list, search_query)
        if filtered_clans:
            csv_download_button(filtered_clans, "clans.csv",
                                columns=["rank","name","tag","leader","members","donations","donations_today","received","lost"],
                                headers=[t("rank"), t("clan_name_column"), t("clan_tag_column"), t("leader"), t("members"), t("donated"), t("donated_today"), t("received"), t("lost")])
            page_items, page, total_pages, total = paginate(filtered_clans, "clan_page")
            for rank, clan in enumerate(page_items, (page - 1) * ITEMS_PER_PAGE + 1):
                with st.container():
                    st.markdown('<div class="clan-card">', unsafe_allow_html=True)
                    col_rank, col_badge, col_info, col_stats = st.columns([0.5, 1, 3, 6])
                    with col_rank:
                        st.markdown(f"**{rank}**")
                    with col_badge:
                        st.image(clan['badge'], width=45)
                    with col_info:
                        # Clan name as plain text (no link)
                        st.markdown(f'<span class="clan-name-text">{clan["name"]}</span>', unsafe_allow_html=True)
                        # Open button
                        if st.button("🛡️ Open", key=f"open_{clan['tag']}"):
                            st.session_state.selected_clan_tag = clan['tag']
                            st.rerun()
                        st.caption(f"{clan['tag']} • 👑 {clan['leader']} • 👥 {clan['members']}/50")
                    with col_stats:
                        s_cols = st.columns(4)
                        with s_cols[0]:
                            st.markdown(f"<span class='stat-label'>{t('donated')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='stat-value' style='color:#00ffcc;'>{clan['donations']:,}</span>", unsafe_allow_html=True)
                        with s_cols[1]:
                            st.markdown(f"<span class='stat-label'>{t('donated_today')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='stat-value' style='color:#ffaa45;'>{clan.get('donations_today', 0):,}</span>", unsafe_allow_html=True)
                        with s_cols[2]:
                            st.markdown(f"<span class='stat-label'>{t('received')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='stat-value' style='color:#ff6b6b;'>{clan['received']:,}</span>", unsafe_allow_html=True)
                        with s_cols[3]:
                            st.markdown(f"<span class='stat-label'>{t('lost')}</span>", unsafe_allow_html=True)
                            st.markdown(f"<span class='stat-value' style='color:#ff4444;'>{clan.get('lost_season', 0):,}</span>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            show_pagination(total_pages, page, total, "clan_page")
        else:
            st.info(t("no_clan_found"))

    with tab2:
        all_players = sorted(all_players_list, key=lambda x: x['donations'], reverse=True)
        filtered_players = filter_players(all_players, search_query)
        if filtered_players:
            csv_download_button(filtered_players, "players.csv",
                                columns=["rank","name","clan_name","level","donations","received"],
                                headers=[t("rank"), t("player_name_column"), t("clan_name_column"), t("level"), t("donated"), t("received")])
            page_items, page, total_pages, total = paginate(filtered_players, "player_page")
            p_table = f"<div class='table-wrapper'><table class='custom-table'><thead><tr><th>{t('rank')}</th><th>{t('name')}</th><th>{t('clan')}</th><th>{t('level')}</th><th>🔥 {t('donated')}</th><th>📥 {t('received_col')}</th></tr></thead><tbody>"
            for idx, p in enumerate(page_items, (page - 1) * ITEMS_PER_PAGE + 1):
                p_table += f"<tr><td>{idx}</td><td><a href='?player={p['tag']}' style='color:white; font-weight:bold;'>{p['name']}</a></td><td><img src='{p['clan_badge']}' width='20'> {p['clan_name']}</td><td><span class='lvl-badge'>⭐ {p['level']}</span></td><td style='color:#00ffcc'>{p['donations']:,}</td><td>{p['received']:,}</td></tr>"
            p_table += "</tbody></table></div>"
            st.markdown(p_table, unsafe_allow_html=True)
            show_pagination(total_pages, page, total, "player_page")
            if 'player' in st.query_params:
                player_tag = st.query_params['player']
                st.session_state.selected_player_tag = player_tag
                st.query_params.clear()
                st.rerun()
            if st.session_state.selected_player_tag:
                player = next((p for p in all_players if p['tag'] == st.session_state.selected_player_tag), None)
                if player:
                    st.subheader(t("player_profile"))
                    show_player_profile(player)
                    if st.button(t("close_profile")):
                        st.session_state.selected_player_tag = None
                        st.rerun()
        else:
            st.info(t("no_player_found"))

    with tab3:
        high_lvl = [p for p in all_players_list if p['level'] >= 300]
        high_lvl = sorted(high_lvl, key=lambda x: x['level'], reverse=True)
        filtered_high = filter_players(high_lvl, search_query)
        if filtered_high:
            page_items, page, total_pages, total = paginate(filtered_high, "legend_page")
            h_table = f"<div class='table-wrapper'><table class='custom-table'><thead><tr><th>{t('rank')}</th><th>{t('name')}</th><th>{t('clan')}</th><th>{t('level')}</th><th>🔥 {t('donated')}</th></tr></thead><tbody>"
            for idx, p in enumerate(page_items, (page - 1) * ITEMS_PER_PAGE + 1):
                h_table += f"<tr><td>{idx}</td><td><a href='?player={p['tag']}' style='color:gold; font-weight:bold;'>🏆 {p['name']}</a></td><td><img src='{p['clan_badge']}' width='20'> {p['clan_name']}</td><td><span class='th-badge'>💎 {p['level']}</span></td><td style='color:#00ffcc'>{p['donations']:,}</td></tr>"
            h_table += "</tbody></table></div>"
            st.markdown(h_table, unsafe_allow_html=True)
            show_pagination(total_pages, page, total, "legend_page")
            if 'player' in st.query_params:
                player_tag = st.query_params['player']
                st.session_state.selected_player_tag = player_tag
                st.query_params.clear()
                st.rerun()
            if st.session_state.selected_player_tag:
                player = next((p for p in all_players_list if p['tag'] == st.session_state.selected_player_tag), None)
                if player:
                    st.subheader(t("player_profile"))
                    show_player_profile(player)
                    if st.button(t("close_profile")):
                        st.session_state.selected_player_tag = None
                        st.rerun()
        else:
            st.info(t("no_legend_found"))
