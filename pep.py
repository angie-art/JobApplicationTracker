import os
import re
import sqlite3
import hashlib
import secrets
from datetime import date, datetime

import pandas as pd
import streamlit as st
import altair as alt


# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Trackr — Job Applications",
    page_icon="⚡",
    layout="wide",
)

DB_PATH = "job_tracker.db"
UPLOAD_DIR = "uploads"


# =========================
# THEME / CSS
# =========================
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800;900&family=DM+Sans:wght@300;400;500;600&display=swap');

        :root {
            --ink:       #0A0A0F;
            --ink-2:     #1A1A2E;
            --ink-3:     #2C2C44;
            --surface:   #12121E;
            --panel:     #1C1C2E;
            --border:    rgba(255,255,255,0.07);
            --border-hi: rgba(255,255,255,0.14);

            --lime:   #C8FF00;
            --cyan:   #00E5FF;
            --coral:  #FF5A5A;
            --amber:  #FFB300;
            --violet: #8B5CF6;
            --emerald:#00E096;

            --text:    #F0F0FF;
            --muted:   rgba(240,240,255,0.45);
            --muted-2: rgba(240,240,255,0.22);

            --r-sm: 10px;
            --r-md: 16px;
            --r-lg: 22px;
            --r-xl: 30px;

            --shadow: 0 4px 24px rgba(0,0,0,0.45);
            --shadow-lg: 0 8px 48px rgba(0,0,0,0.6);
        }

        /* ── Reset chrome ── */
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        #MainMenu, footer { display: none !important; visibility: hidden !important; }

        html, body { background: var(--ink) !important; }

        .stApp {
            background: var(--ink) !important;
            font-family: 'DM Sans', sans-serif;
            color: var(--text) !important;
        }

        .main .block-container {
            padding-top: 1.6rem !important;
            padding-bottom: 3rem !important;
            max-width: 1400px;
        }

        /* ── Global text overrides ── */
        html, body, [class*="css"], p, span, div, label {
            color: var(--text) !important;
        }

        /* ── Lime-background elements always get ink text ── */
        .stButton > button,
        .stButton > button *,
        .page-bar-icon,
        .page-bar-icon *,
        .nav-avatar,
        .nav-avatar *,
        .auth-tab.active,
        .auth-tab.active * {
            color: var(--ink) !important;
        }

        /* ── Headings via Syne ── */
        h1,h2,h3,h4 {
            font-family: 'Syne', sans-serif !important;
            color: var(--text) !important;
        }

        /* ─────────────────────────────────────────
           INPUTS
        ───────────────────────────────────────── */
        input, textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background: var(--ink-3) !important;
            border: 1px solid var(--border-hi) !important;
            border-radius: var(--r-sm) !important;
            color: var(--text) !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            caret-color: var(--lime) !important;
        }

        input:focus, textarea:focus,
        [data-baseweb="input"] input:focus {
            border-color: var(--lime) !important;
            box-shadow: 0 0 0 3px rgba(200,255,0,0.12) !important;
        }

        label,
        .stTextInput label, .stSelectbox label,
        .stDateInput label, .stTextArea label,
        .stFileUploader label {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            color: var(--muted) !important;
            margin-bottom: 4px !important;
        }

        /* select / dropdown */
        [data-baseweb="select"] > div {
            background: var(--ink-3) !important;
            border: 1px solid var(--border-hi) !important;
            border-radius: var(--r-sm) !important;
        }
        [data-baseweb="select"] span,
        [data-baseweb="select"] div {
            color: var(--text) !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            background: transparent !important;
        }
        [data-baseweb="popover"] {
            background: var(--panel) !important;
            border: 1px solid var(--border-hi) !important;
            border-radius: var(--r-md) !important;
        }
        [data-baseweb="menu"] {
            background: var(--panel) !important;
        }
        [data-baseweb="option"] {
            background: transparent !important;
            color: var(--text) !important;
            font-family: 'DM Sans', sans-serif !important;
        }
        [data-baseweb="option"]:hover {
            background: rgba(200,255,0,0.08) !important;
        }

        /* date input */
        [data-baseweb="datepicker"] input,
        [data-testid="stDateInput"] input {
            background: var(--ink-3) !important;
            color: var(--text) !important;
        }

        /* ─────────────────────────────────────────
           BUTTONS
        ───────────────────────────────────────── */
        .stButton > button {
            background: var(--lime) !important;
            color: var(--ink) !important;
            border: none !important;
            border-radius: var(--r-sm) !important;
            padding: 10px 20px !important;
            font-family: 'Syne', sans-serif !important;
            font-weight: 800 !important;
            font-size: 14px !important;
            letter-spacing: 0.04em !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease !important;
            box-shadow: 0 0 0 rgba(200,255,0,0) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 24px rgba(200,255,0,0.30) !important;
            opacity: 0.95 !important;
        }
        .stButton > button:active {
            transform: translateY(0px) !important;
        }

        /* Danger / delete button — second in a pair */
        .delete-btn .stButton > button {
            background: rgba(255,90,90,0.12) !important;
            color: var(--coral) !important;
            border: 1px solid rgba(255,90,90,0.35) !important;
            box-shadow: none !important;
        }
        .delete-btn .stButton > button:hover {
            background: rgba(255,90,90,0.22) !important;
            box-shadow: 0 4px 16px rgba(255,90,90,0.2) !important;
        }

        /* ─────────────────────────────────────────
           METRIC CARDS
        ───────────────────────────────────────── */
        div[data-testid="metric-container"] {
            background: var(--panel) !important;
            border: 1px solid var(--border-hi) !important;
            border-radius: var(--r-md) !important;
            padding: 18px 20px !important;
            box-shadow: var(--shadow) !important;
        }
        div[data-testid="metric-container"] * { color: var(--text) !important; }
        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-family: 'Syne', sans-serif !important;
            font-size: 36px !important;
            font-weight: 900 !important;
        }
        div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
            font-size: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            color: var(--muted) !important;
        }

        /* ─────────────────────────────────────────
           DATAFRAME
        ───────────────────────────────────────── */
        div[data-testid="stDataFrame"] {
            border-radius: var(--r-md) !important;
            overflow: hidden !important;
            border: 1px solid var(--border-hi) !important;
        }
        div[data-testid="stDataFrame"] * {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            color: var(--text) !important;
            background: var(--surface) !important;
        }
        div[data-testid="stDataFrame"] th {
            font-family: 'Syne', sans-serif !important;
            font-size: 12px !important;
            font-weight: 800 !important;
            letter-spacing: 0.07em !important;
            text-transform: uppercase !important;
            color: var(--muted) !important;
            background: var(--ink-2) !important;
        }

        /* ─────────────────────────────────────────
           RADIO (nav)
        ───────────────────────────────────────── */
        [data-testid="stRadio"] label {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            text-transform: none !important;
            letter-spacing: 0 !important;
            color: var(--text) !important;
        }
        [data-testid="stRadio"] > div {
            gap: 4px !important;
        }

        /* ─────────────────────────────────────────
           DOWNLOAD BUTTON
        ───────────────────────────────────────── */
        .stDownloadButton > button {
            background: transparent !important;
            color: var(--lime) !important;
            border: 1px solid rgba(200,255,0,0.35) !important;
            border-radius: var(--r-sm) !important;
            font-family: 'Syne', sans-serif !important;
            font-size: 13px !important;
            font-weight: 800 !important;
            letter-spacing: 0.04em !important;
        }
        .stDownloadButton > button:hover {
            background: rgba(200,255,0,0.08) !important;
            border-color: var(--lime) !important;
        }

        /* ─────────────────────────────────────────
           CUSTOM COMPONENTS
        ───────────────────────────────────────── */

        /* Page title bar */
        .page-bar {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 24px;
        }
        .page-bar-icon {
            width: 44px; height: 44px;
            border-radius: 12px;
            background: var(--lime);
            color: var(--ink);
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        .page-bar-title {
            font-family: 'Syne', sans-serif;
            font-size: 26px;
            font-weight: 900;
            color: var(--text) !important;
            margin: 0;
        }
        .page-bar-sub {
            font-size: 13px;
            color: var(--muted);
            margin: 0;
        }

        /* Section card */
        .s-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: var(--r-lg);
            padding: 28px;
            box-shadow: var(--shadow);
        }
        .s-card + .s-card { margin-top: 18px; }

        /* Status badges */
        .badge {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 20px;
            font-family: 'Syne', sans-serif;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.06em;
        }
        .badge-applied   { background: rgba(0,229,255,0.15); color: var(--cyan);    border: 1px solid rgba(0,229,255,0.3); }
        .badge-interview { background: rgba(255,179,0,0.15); color: var(--amber);   border: 1px solid rgba(255,179,0,0.3); }
        .badge-offer     { background: rgba(0,224,150,0.15); color: var(--emerald); border: 1px solid rgba(0,224,150,0.3); }
        .badge-rejected  { background: rgba(255,90,90,0.15); color: var(--coral);   border: 1px solid rgba(255,90,90,0.3); }

        /* Funnel bars */
        .funnel-row { margin-bottom: 16px; }
        .funnel-meta {
            display: flex; justify-content: space-between;
            font-size: 13px; font-weight: 600;
            margin-bottom: 6px;
        }
        .funnel-meta span:first-child { color: var(--text); }
        .funnel-meta span:last-child  { color: var(--muted); }
        .funnel-track {
            background: var(--ink-3);
            border-radius: 8px;
            height: 10px;
            overflow: hidden;
        }
        .funnel-fill { height: 100%; border-radius: 8px; transition: width 0.7s cubic-bezier(.4,0,.2,1); }
        .funnel-fill-applied   { background: var(--cyan); }
        .funnel-fill-interview { background: var(--amber); }
        .funnel-fill-offer     { background: var(--emerald); }
        .funnel-fill-rejected  { background: var(--coral); }

        /* Sidebar nav */
        .nav-header {
            margin-bottom: 24px;
        }
        .nav-wordmark {
            font-family: 'Syne', sans-serif;
            font-size: 22px;
            font-weight: 900;
            color: var(--text) !important;
            letter-spacing: -0.3px;
        }
        .nav-wordmark span { color: var(--lime) !important; }
        .nav-user-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            background: var(--ink-3);
            border: 1px solid var(--border-hi);
            border-radius: 30px;
            padding: 5px 14px 5px 8px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text) !important;
        }
        .nav-avatar {
            width: 24px; height: 24px;
            background: var(--lime);
            border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
            font-family: 'Syne', sans-serif;
            font-size: 11px;
            font-weight: 900;
            color: var(--ink) !important;
        }
        .nav-divider {
            border: none;
            border-top: 1px solid var(--border);
            margin: 16px 0;
        }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 60px 24px;
        }
        .empty-icon { font-size: 48px; margin-bottom: 16px; }
        .empty-title {
            font-family: 'Syne', sans-serif;
            font-size: 20px; font-weight: 900;
            color: var(--text) !important;
            margin-bottom: 8px;
        }
        .empty-desc { font-size: 14px; color: var(--muted); }

        /* Auth page */
        .auth-outer {
            min-height: 90vh;
            display: flex; align-items: flex-start; justify-content: center;
            padding-top: 48px;
        }
        .auth-card {
            width: 100%;
            max-width: 480px;
            background: var(--panel);
            border: 1px solid var(--border-hi);
            border-radius: var(--r-xl);
            padding: 40px;
            box-shadow: var(--shadow-lg);
        }
        .auth-logo {
            font-family: 'Syne', sans-serif;
            font-size: 30px;
            font-weight: 900;
            margin-bottom: 6px;
            color: var(--text) !important;
        }
        .auth-logo span { color: var(--lime) !important; }
        .auth-tagline {
            font-size: 14px;
            color: var(--muted);
            margin-bottom: 32px;
        }
        .auth-tab-row {
            display: flex;
            background: var(--ink-3);
            border-radius: var(--r-sm);
            padding: 4px;
            margin-bottom: 28px;
            gap: 4px;
        }
        .auth-tab {
            flex: 1; text-align: center;
            padding: 9px;
            border-radius: 8px;
            font-family: 'Syne', sans-serif;
            font-size: 13px; font-weight: 800;
            letter-spacing: 0.04em;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
            color: var(--muted) !important;
        }
        .auth-tab.active {
            background: var(--lime);
            color: var(--ink) !important;
        }

        /* Section label */
        .section-label {
            font-family: 'Syne', sans-serif;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 14px;
        }

        /* Stat accent card */
        .stat-accent {
            background: var(--lime);
            border-radius: var(--r-md);
            padding: 20px;
        }
        .stat-accent * { color: var(--ink) !important; }
        .stat-accent .sv { font-family: 'Syne',sans-serif; font-size: 40px; font-weight:900; }
        .stat-accent .sl { font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; opacity:.7; }

        /* Toggle bar */
        .toggle-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }

        /* Altair chart background fix */
        .vega-embed { background: transparent !important; }
        canvas { background: transparent !important; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--ink-2); }
        ::-webkit-scrollbar-thumb { background: var(--ink-3); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--violet); }

        /* Success / Error alerts */
        [data-testid="stAlert"] {
            border-radius: var(--r-sm) !important;
            border-left-width: 3px !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background: var(--ink-3) !important;
            border: 1px dashed var(--border-hi) !important;
            border-radius: var(--r-md) !important;
        }

        /* Horizontal rule */
        hr { border-color: var(--border) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# =========================
# Database Setup
# =========================
def conn_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def ensure_schema():
    con = conn_db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pin_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_username TEXT NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            date_applied TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            resume_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_username) REFERENCES users(username)
        )
    """)
    con.commit()
    con.close()


ensure_schema()

# =========================
# Auth Helpers
# =========================
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
PIN_REGEX_4    = re.compile(r"^\d{4}$")


def hash_pin(pin: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 120_000)
    return dk.hex()


def create_user(username: str, pin: str):
    username = username.strip()
    if not USERNAME_REGEX.match(username):
        return False, "Username: 3–20 chars, letters / numbers / underscore only."
    if not PIN_REGEX_4.match(pin):
        return False, "PIN must be exactly 4 digits."
    salt_hex = secrets.token_hex(16)
    pin_hash = hash_pin(pin, salt_hex)
    con = conn_db()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, pin_hash, salt, created_at) VALUES (?, ?, ?, ?)",
            (username, pin_hash, salt_hex, datetime.utcnow().isoformat()),
        )
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        return False, "Username already taken."
    con.close()
    return True, "Account created — log in now."


def login_user(username: str, pin: str):
    username = username.strip()
    if not USERNAME_REGEX.match(username):
        return False, "Invalid username."
    if not PIN_REGEX_4.match(pin):
        return False, "PIN must be exactly 4 digits."
    con = conn_db()
    cur = con.cursor()
    cur.execute("SELECT pin_hash, salt FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return False, "No account found — sign up first."
    pin_hash_db, salt_hex = row
    if hash_pin(pin, salt_hex) != pin_hash_db:
        return False, "Wrong PIN."
    return True, "Welcome back."


def logout():
    st.session_state.logged_in    = False
    st.session_state.username     = ""
    st.session_state.current_page = "Applications"
    st.session_state.show_nav     = True


# =========================
# Applications CRUD
# =========================
STATUSES = ["Applied", "Interview", "Offer", "Rejected"]

STATUS_BADGE = {
    "Applied":   "badge-applied",
    "Interview": "badge-interview",
    "Offer":     "badge-offer",
    "Rejected":  "badge-rejected",
}


def status_badge(s: str) -> str:
    css = STATUS_BADGE.get(s, "badge-applied")
    return f'<span class="badge {css}">{s}</span>'


def save_resume_file(username: str, uploaded_file):
    if uploaded_file is None:
        return None
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_user = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
    user_dir  = os.path.join(UPLOAD_DIR, safe_user)
    os.makedirs(user_dir, exist_ok=True)
    filename  = re.sub(r"[^a-zA-Z0-9_.-]", "_", uploaded_file.name)
    full_path = os.path.join(user_dir, f"{int(datetime.utcnow().timestamp())}_{filename}")
    with open(full_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return full_path


def add_application(user_username, company, role, location, date_applied, status, notes, resume_path):
    con = conn_db()
    con.execute(
        """INSERT INTO applications
           (user_username,company,role,location,date_applied,status,notes,resume_path,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (user_username, company.strip(), role.strip(),
         location.strip() if location else "",
         date_applied.isoformat(), status,
         notes.strip() if notes else "",
         resume_path, datetime.utcnow().isoformat()),
    )
    con.commit()
    con.close()


def load_applications(user_username: str) -> pd.DataFrame:
    con = conn_db()
    df  = pd.read_sql_query(
        """SELECT id, company, role, location, date_applied, status, notes, resume_path
           FROM applications WHERE user_username=?
           ORDER BY date(date_applied) DESC, id DESC""",
        con, params=(user_username,),
    )
    con.close()
    if not df.empty:
        df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
    return df


def delete_application(app_id: int, user_username: str):
    con = conn_db()
    con.execute("DELETE FROM applications WHERE id=? AND user_username=?", (app_id, user_username))
    con.commit()
    con.close()


def update_application(app_id, user_username, company, role, location, date_applied, status, notes):
    con = conn_db()
    con.execute(
        """UPDATE applications SET company=?,role=?,location=?,date_applied=?,status=?,notes=?
           WHERE id=? AND user_username=?""",
        (company.strip(), role.strip(), location.strip(), date_applied.isoformat(),
         status, notes.strip(), app_id, user_username),
    )
    con.commit()
    con.close()


# =========================
# UI HELPERS
# =========================
def page_bar(icon: str, title: str, subtitle: str = ""):
    sub_html = f'<p class="page-bar-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-bar">
            <div class="page-bar-icon">{icon}</div>
            <div>
                <p class="page-bar-title">{title}</p>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# AUTH PAGE
# =========================
def login_page():
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"

    st.markdown("<div class='auth-outer'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="auth-logo">Track<span>r</span></div>
        <p class="auth-tagline">Your job search, beautifully organised.</p>
        """,
        unsafe_allow_html=True,
    )

    # Custom tab switcher via radio
    view = st.radio(
        "Auth mode",
        ["Log in", "Sign up"],
        horizontal=True,
        index=0 if st.session_state.auth_view == "login" else 1,
        label_visibility="collapsed",
        key="auth_radio",
    )
    st.session_state.auth_view = "login" if view == "Log in" else "signup"

    st.write("")

    if st.session_state.auth_view == "login":
        username = st.text_input("Username", placeholder="e.g. angela_01", key="login_username")
        pin      = st.text_input("4-digit PIN", type="password", placeholder="••••", key="login_pin")
        st.write("")
        if st.button("Log in →", use_container_width=True):
            ok, msg = login_user(username, pin)
            if ok:
                st.session_state.logged_in    = True
                st.session_state.username     = username.strip()
                st.session_state.current_page = "Applications"
                st.session_state.show_nav     = True
                st.rerun()
            else:
                st.error(msg)
    else:
        username = st.text_input("Choose a username", placeholder="e.g. angela_01", key="signup_username")
        pin1     = st.text_input("Create 4-digit PIN", type="password", placeholder="••••", key="signup_pin1")
        pin2     = st.text_input("Confirm PIN",         type="password", placeholder="••••", key="signup_pin2")
        st.write("")
        if st.button("Create account →", use_container_width=True):
            if pin1 != pin2:
                st.error("PINs don't match.")
            else:
                ok, msg = create_user(username, pin1)
                if ok:
                    st.success(msg)
                    st.session_state.auth_view   = "login"
                    st.session_state.auth_radio  = "Log in"
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("</div></div>", unsafe_allow_html=True)


# =========================
# NAVIGATION
# =========================
def render_navigation():
    initials = st.session_state.username[:2].upper() if st.session_state.username else "??"
    st.markdown(
        f"""
        <div class="nav-header">
            <div class="nav-wordmark">Track<span>r</span></div>
            <div class="nav-user-chip">
                <span class="nav-avatar">{initials}</span>
                {st.session_state.username}
            </div>
        </div>
        <hr class="nav-divider"/>
        """,
        unsafe_allow_html=True,
    )

    pages = ["Applications", "Dashboard", "Add Application", "Statistics", "Settings"]
    icons = {"Applications": "📋", "Dashboard": "📌", "Add Application": "➕", "Statistics": "📊", "Settings": "⚙️"}

    page = st.radio(
        "nav",
        [f"{icons[p]}  {p}" for p in pages],
        index=pages.index(st.session_state.current_page),
        label_visibility="collapsed",
        key="nav_radio",
    )

    # Strip icon
    selected = page.split("  ", 1)[-1].strip()
    st.session_state.current_page = selected

    st.markdown("<hr class='nav-divider'/>", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True, key="logout_nav"):
        logout()
        st.rerun()


# =========================
# PAGES
# =========================
def page_add_application():
    page_bar("➕", "Add Application", "Log a new job you've applied to")

    with st.container():
        st.markdown("<div class='s-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Job details</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            company  = st.text_input("Company Name",    placeholder="e.g. Google")
            role     = st.text_input("Role / Position", placeholder="e.g. Data Analyst Intern")
            location = st.text_input("Location",        placeholder="e.g. Remote / Lagos")
        with c2:
            date_applied = st.date_input("Date Applied", value=date.today())
            status       = st.selectbox("Status", STATUSES)
            notes        = st.text_area("Notes (optional)", placeholder="Anything worth remembering…", height=120)

        st.markdown("<div class='section-label' style='margin-top:18px;'>Resume</div>", unsafe_allow_html=True)
        resume_file = st.file_uploader("Attach resume (PDF or DOCX)", type=["pdf", "docx"], label_visibility="collapsed")

        st.write("")
        if st.button("Save Application →", use_container_width=True):
            if not company.strip() or not role.strip():
                st.error("Company name and role are required.")
            else:
                resume_path = save_resume_file(st.session_state.username, resume_file)
                add_application(st.session_state.username, company, role, location,
                                date_applied, status, notes, resume_path)
                st.success("Application saved ✓")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def page_my_applications(df: pd.DataFrame):
    page_bar("📋", "Applications", f"{len(df)} total")

    if df.empty:
        st.markdown(
            """
            <div class="s-card">
              <div class="empty-state">
                <div class="empty-icon">📭</div>
                <div class="empty-title">Nothing here yet</div>
                <div class="empty-desc">Hit "Add Application" to start tracking your job search.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown("<div class='s-card'>", unsafe_allow_html=True)

    # Search + status filter row
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        search = st.text_input("Search", placeholder="Search company or role…", label_visibility="collapsed")
    with fc2:
        status_filter = st.selectbox("Filter by status", ["All"] + STATUSES, label_visibility="collapsed")

    show = df.copy()
    if search.strip():
        s    = search.strip().lower()
        show = show[show["company"].str.lower().str.contains(s, na=False)
                    | show["role"].str.lower().str.contains(s, na=False)]
    if status_filter != "All":
        show = show[show["status"] == status_filter]

    # Badge count row
    badges_html = "  ".join([
        f'{status_badge(s)} <b style="font-size:13px;margin-left:2px;">{int(show["status"].value_counts().get(s, 0))}</b>'
        for s in STATUSES if show["status"].value_counts().get(s, 0) > 0
    ])
    st.markdown(f'<div style="margin:12px 0 16px 0; display:flex; gap:8px; flex-wrap:wrap;">{badges_html}</div>',
                unsafe_allow_html=True)

    display_df = show.rename(columns={
        "company": "Company", "role": "Role", "location": "Location",
        "date_applied": "Date", "status": "Status",
        "notes": "Notes", "resume_path": "Resume", "id": "ID",
    })
    st.dataframe(display_df[["ID","Company","Role","Location","Date","Status","Notes"]],
                 use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  Export CSV", data=csv,
                       file_name="trackr_applications.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Edit / Delete panel ──
    if show.empty:
        return

    st.markdown("<div class='s-card' style='margin-top:18px;'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Edit or delete an application</div>", unsafe_allow_html=True)

    selected_id  = st.selectbox("Select by ID", show["id"].tolist(), label_visibility="collapsed")
    selected_row = df[df["id"] == selected_id].iloc[0]

    ec1, ec2 = st.columns(2)
    with ec1:
        e_company  = st.text_input("Company",  value=str(selected_row["company"]),          key="e_company")
        e_role     = st.text_input("Role",      value=str(selected_row["role"]),             key="e_role")
        e_location = st.text_input("Location",  value=str(selected_row["location"] or ""),  key="e_loc")
    with ec2:
        e_date   = st.date_input("Date Applied", value=selected_row["date_applied"],         key="e_date")
        e_status = st.selectbox("Status", STATUSES, index=STATUSES.index(selected_row["status"]), key="e_status")
        e_notes  = st.text_area("Notes", value=str(selected_row["notes"] or ""), height=120, key="e_notes")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Save changes →", use_container_width=True, key="save_edit"):
            update_application(selected_id, st.session_state.username,
                               e_company, e_role, e_location, e_date, e_status, e_notes)
            st.success("Updated ✓")
            st.rerun()
    with b2:
        st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
        if st.button("Delete application", use_container_width=True, key="del_app"):
            delete_application(selected_id, st.session_state.username)
            st.warning("Deleted.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    resume_path = selected_row.get("resume_path")
    if isinstance(resume_path, str) and resume_path.strip() and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            st.download_button("📎  Download attached resume", data=f.read(),
                               file_name=os.path.basename(resume_path), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def page_dashboard(df: pd.DataFrame):
    total  = len(df)
    counts = {s: 0 for s in STATUSES}
    if not df.empty:
        vc = df["status"].value_counts()
        for s in STATUSES:
            counts[s] = int(vc.get(s, 0))

    page_bar("📌", "Dashboard", "Your job search at a glance")

    # ── Top stat row ──
    cols = st.columns(5)
    accent_values = [
        ("⚡ Total",     total,              "lime"),
        ("📤 Applied",   counts["Applied"],  "cyan"),
        ("🎤 Interview", counts["Interview"],"amber"),
        ("🎉 Offer",     counts["Offer"],    "emerald"),
        ("✗  Rejected",  counts["Rejected"], "coral"),
    ]
    color_map = {
        "lime":    ("var(--lime)",    "var(--ink)"),
        "cyan":    ("rgba(0,229,255,0.12)",   "var(--cyan)"),
        "amber":   ("rgba(255,179,0,0.12)",   "var(--amber)"),
        "emerald": ("rgba(0,224,150,0.12)",   "var(--emerald)"),
        "coral":   ("rgba(255,90,90,0.12)",   "var(--coral)"),
    }
    for col, (label, val, c_key) in zip(cols, accent_values):
        bg, fg = color_map[c_key]
        with col:
            st.markdown(
                f"""
                <div style="background:{bg};border-radius:14px;padding:18px 16px;
                            border:1px solid rgba(255,255,255,0.07);box-shadow:0 4px 20px rgba(0,0,0,0.35);">
                    <div style="font-family:'Syne',sans-serif;font-size:32px;font-weight:900;
                                color:{fg};">{val}</div>
                    <div style="font-size:12px;font-weight:700;letter-spacing:.07em;
                                text-transform:uppercase;color:{fg};opacity:.7;margin-top:4px;">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    if total > 0:
        st.markdown("<div class='s-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Application funnel</div>", unsafe_allow_html=True)

        funnel_colors = {
            "Applied":   ("var(--cyan)",    counts["Applied"]),
            "Interview": ("var(--amber)",   counts["Interview"]),
            "Offer":     ("var(--emerald)", counts["Offer"]),
            "Rejected":  ("var(--coral)",   counts["Rejected"]),
        }
        for s, (color, cnt) in funnel_colors.items():
            pct = cnt / total * 100 if total else 0
            css = s.lower()
            st.markdown(
                f"""
                <div class="funnel-row">
                    <div class="funnel-meta">
                        <span>{s}</span>
                        <span>{cnt} &nbsp;·&nbsp; {pct:.0f}%</span>
                    </div>
                    <div class="funnel-track">
                        <div class="funnel-fill funnel-fill-{css}" style="width:{pct}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def page_statistics(df: pd.DataFrame):
    page_bar("📊", "Statistics", "Visual breakdown of your applications")

    if df.empty:
        st.markdown(
            """
            <div class="s-card">
              <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div class="empty-title">No data yet</div>
                <div class="empty-desc">Add applications and your charts will appear here.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    status_colors  = ["#00E5FF", "#FFB300", "#00E096", "#FF5A5A"]
    color_scale    = alt.Scale(domain=STATUSES, range=status_colors)

    counts_df = (
        df["status"].fillna("Unknown")
        .value_counts().reindex(STATUSES, fill_value=0)
        .reset_index()
    )
    counts_df.columns = ["Status", "Count"]

    chart_config = alt.themes.enable("dark") if hasattr(alt.themes, "enable") else None
    bg = "#12121E"

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("<div class='s-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>By status (donut)</div>", unsafe_allow_html=True)
        pie = (
            alt.Chart(counts_df)
            .mark_arc(innerRadius=65, stroke="#12121E", strokeWidth=3)
            .encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Status:N", scale=color_scale,
                                legend=alt.Legend(title=None, orient="bottom",
                                                  labelColor="#F0F0FF", labelFont="DM Sans",
                                                  labelFontSize=13, symbolSize=100)),
                tooltip=["Status:N", "Count:Q"],
            )
            .properties(height=280, background=bg)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='s-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>By status (bar)</div>", unsafe_allow_html=True)
        bar = (
            alt.Chart(counts_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Status:N", sort=STATUSES, axis=alt.Axis(labelAngle=0,
                         labelColor="#F0F0FF", labelFont="DM Sans", labelFontSize=13,
                         tickColor="transparent", domainColor="transparent")),
                y=alt.Y("Count:Q", axis=alt.Axis(labelColor="#F0F0FF", labelFont="DM Sans",
                         gridColor="rgba(255,255,255,0.06)")),
                color=alt.Color("Status:N", scale=color_scale, legend=None),
                tooltip=["Status:N", "Count:Q"],
            )
            .properties(height=280, background=bg)
            .configure_view(strokeWidth=0)
            .configure_axis(domainColor="transparent")
        )
        st.altair_chart(bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Timeline chart
    if len(df) > 1:
        st.markdown("<div class='s-card' style='margin-top:18px;'>", unsafe_allow_html=True)
        st.markdown("<div class='section-label'>Applications over time</div>", unsafe_allow_html=True)
        timeline = df.copy()
        timeline["date_applied"] = pd.to_datetime(timeline["date_applied"])
        timeline_agg = (
            timeline.groupby("date_applied").size().reset_index(name="Count")
        )
        area = (
            alt.Chart(timeline_agg)
            .mark_area(
                line={"color": "#C8FF00", "strokeWidth": 2},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color="rgba(200,255,0,0.35)", offset=0),
                        alt.GradientStop(color="rgba(200,255,0,0.00)", offset=1),
                    ],
                    x1=0, x2=0, y1=1, y2=0,
                ),
            )
            .encode(
                x=alt.X("date_applied:T", axis=alt.Axis(labelColor="#F0F0FF", labelFont="DM Sans",
                          gridColor="rgba(255,255,255,0.06)", domainColor="transparent",
                          tickColor="transparent", format="%b %d")),
                y=alt.Y("Count:Q", axis=alt.Axis(labelColor="#F0F0FF", labelFont="DM Sans",
                          gridColor="rgba(255,255,255,0.06)")),
                tooltip=[alt.Tooltip("date_applied:T", title="Date", format="%b %d %Y"),
                         alt.Tooltip("Count:Q", title="Applications")],
            )
            .properties(height=220, background=bg)
            .configure_view(strokeWidth=0)
            .configure_axis(domainColor="transparent")
        )
        st.altair_chart(area, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def page_settings():
    page_bar("⚙️", "Settings")

    st.markdown("<div class='s-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Account</div>", unsafe_allow_html=True)

    initials = st.session_state.username[:2].upper()
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:16px;padding:16px 0 20px 0;">
            <div style="width:52px;height:52px;border-radius:50%;background:var(--lime);
                        display:flex;align-items:center;justify-content:center;
                        font-family:'Syne',sans-serif;font-size:18px;font-weight:900;
                        color:var(--ink);">{initials}</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;">
                    {st.session_state.username}</div>
                <div style="font-size:13px;color:var(--muted);margin-top:2px;">Trackr account</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Sign out →", use_container_width=True, key="logout_settings"):
        logout()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_main_content(df: pd.DataFrame):
    page = st.session_state.current_page
    if   page == "Applications":    page_my_applications(df)
    elif page == "Dashboard":       page_dashboard(df)
    elif page == "Add Application": page_add_application()
    elif page == "Statistics":      page_statistics(df)
    elif page == "Settings":        page_settings()


# =========================
# TOGGLE BAR
# =========================
def render_toggle_bar():
    c1, _ = st.columns([1, 6])
    with c1:
        label = "✕ Hide" if st.session_state.show_nav else "☰ Menu"
        if st.button(label, use_container_width=True):
            st.session_state.show_nav = not st.session_state.show_nav
            st.rerun()


# =========================
# MAIN
# =========================
for key, default in [("logged_in", False), ("username", ""),
                      ("show_nav", True), ("current_page", "Applications")]:
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state.logged_in:
    login_page()
    st.stop()

render_toggle_bar()
df = load_applications(st.session_state.username)

if st.session_state.show_nav:
    left_col, right_col = st.columns([1, 3.5], gap="large")
    with left_col:
        render_navigation()
    with right_col:
        render_main_content(df)
else:
    render_main_content(df)