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
    page_title="Job Application Tracker",
    page_icon="🗂️",
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
        [data-testid="stHeader"] {display: none;}
        [data-testid="stToolbar"] {display: none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        .main .block-container{
            padding-top: 0.6rem !important;
            padding-bottom: 2rem !important;
            max-width: 1350px;
        }

        [data-testid="stAppViewContainer"]{
            padding-top: 0rem !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 20%, rgba(255, 109, 195, 0.30), transparent 45%),
                radial-gradient(circle at 80% 15%, rgba(124, 77, 255, 0.35), transparent 45%),
                linear-gradient(135deg, #ffffff 0%, #fff7fb 35%, #f6f1ff 100%);
        }

        html, body, [class*="css"]  {
            color: #111111 !important;
        }

        .card {
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(170, 140, 255, 0.35);
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 12px 28px rgba(20, 10, 40, 0.10);
        }

        .app-title {
            font-size: 40px;
            font-weight: 900;
            letter-spacing: -0.5px;
            margin: 0;
            padding: 0;
            color: #111 !important;
        }

        .app-subtitle {
            font-size: 16px;
            font-weight: 700;
            margin-top: 6px;
            color: #111 !important;
            opacity: 0.9;
        }

        .card-title {
            font-size: 20px;
            font-weight: 900;
            margin-bottom: 10px;
            color: #111 !important;
        }

        .nav-panel {
            background: linear-gradient(180deg, #2d0b59 0%, #150a2e 100%);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 20px;
            padding: 18px 16px 18px 16px;
            box-shadow: 0 16px 34px rgba(34, 10, 60, 0.24);
            margin-bottom: 14px;
        }

        .nav-title {
            color: #ffffff !important;
            font-size: 24px;
            font-weight: 900;
            margin-bottom: 4px;
        }

        .nav-user {
            color: rgba(255,255,255,0.88) !important;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .stButton > button {
            background: linear-gradient(135deg, #7c4dff 0%, #ff4db8 100%) !important;
            color: white !important;
            border: 0 !important;
            border-radius: 12px !important;
            padding: 10px 14px !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 18px rgba(124,77,255,0.20);
        }

        .stButton > button:hover {
            opacity: 0.92;
            transform: translateY(-1px);
        }

        input, textarea, [data-baseweb="input"] input {
            color: #111111 !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }

        label, .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label {
            font-size: 16px !important;
            font-weight: 900 !important;
            color: #111111 !important;
        }

        [data-baseweb="select"] span {
            color: #111111 !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }

        div[data-testid="metric-container"] {
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(255, 77, 184, 0.20);
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 10px 24px rgba(20, 10, 40, 0.08);
        }

        div[data-testid="metric-container"] * {
            color: #111111 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 34px !important;
            font-weight: 900 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
            font-size: 16px !important;
            font-weight: 900 !important;
        }

        div[data-testid="stDataFrame"] * {
            font-size: 15px !important;
            font-weight: 700 !important;
            color: #111 !important;
        }

        div[data-testid="stDataFrame"] th {
            font-size: 16px !important;
            font-weight: 900 !important;
        }

        .menu-hint {
            font-size: 14px;
            font-weight: 700;
            color: #3d2d5c;
            margin-top: -6px;
            margin-bottom: 10px;
        }
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
PIN_REGEX_4 = re.compile(r"^\d{4}$")


def hash_pin(pin: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 120_000)
    return dk.hex()


def create_user(username: str, pin: str):
    username = username.strip()

    if not USERNAME_REGEX.match(username):
        return False, "Username must be 3–20 characters (letters, numbers, underscore only)."
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
        return False, "That username is already taken. Try another one."

    con.close()
    return True, "Account created! Please log in."


def login_user(username: str, pin: str):
    username = username.strip()

    if not USERNAME_REGEX.match(username):
        return False, "Enter a valid username (3–20 chars, letters/numbers/_)."
    if not PIN_REGEX_4.match(pin):
        return False, "PIN must be exactly 4 digits."

    con = conn_db()
    cur = con.cursor()
    cur.execute("SELECT pin_hash, salt FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    con.close()

    if not row:
        return False, "No account found. Please sign up."

    pin_hash_db, salt_hex = row
    pin_hash_try = hash_pin(pin, salt_hex)

    if pin_hash_try != pin_hash_db:
        return False, "Wrong PIN. Try again."

    return True, "Login successful."


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.current_page = "My Applications"
    st.session_state.show_nav = True


# =========================
# Applications CRUD
# =========================
STATUSES = ["Applied", "Interview", "Offer", "Rejected"]


def save_resume_file(username: str, uploaded_file):
    if uploaded_file is None:
        return None

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_user = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
    user_dir = os.path.join(UPLOAD_DIR, safe_user)
    os.makedirs(user_dir, exist_ok=True)

    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", uploaded_file.name)
    full_path = os.path.join(user_dir, f"{int(datetime.utcnow().timestamp())}_{filename}")

    with open(full_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return full_path


def add_application(user_username: str, company: str, role: str, location: str, date_applied: date,
                    status: str, notes: str, resume_path):
    con = conn_db()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO applications (user_username, company, role, location, date_applied, status, notes, resume_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_username,
            company.strip(),
            role.strip(),
            location.strip() if location else "",
            date_applied.isoformat(),
            status,
            notes.strip() if notes else "",
            resume_path,
            datetime.utcnow().isoformat(),
        ),
    )
    con.commit()
    con.close()


def load_applications(user_username: str) -> pd.DataFrame:
    con = conn_db()
    df = pd.read_sql_query(
        """
        SELECT id, company, role, location, date_applied, status, notes, resume_path
        FROM applications
        WHERE user_username=?
        ORDER BY date(date_applied) DESC, id DESC
        """,
        con,
        params=(user_username,),
    )
    con.close()

    if df.empty:
        return df

    df["date_applied"] = pd.to_datetime(df["date_applied"]).dt.date
    return df


def delete_application(app_id: int, user_username: str):
    con = conn_db()
    cur = con.cursor()
    cur.execute("DELETE FROM applications WHERE id=? AND user_username=?", (app_id, user_username))
    con.commit()
    con.close()


def update_application(app_id: int, user_username: str, company: str, role: str, location: str,
                      date_applied: date, status: str, notes: str):
    con = conn_db()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE applications
        SET company=?, role=?, location=?, date_applied=?, status=?, notes=?
        WHERE id=? AND user_username=?
        """,
        (company.strip(), role.strip(), location.strip(), date_applied.isoformat(),
         status, notes.strip(), app_id, user_username),
    )
    con.commit()
    con.close()


# =========================
# UI Parts
# =========================
def app_header():
    st.markdown(
        f"""
        <div class="card">
            <div class="app-title">Job Application Tracker</div>
            <div class="app-subtitle">Hi {st.session_state.username}, track your applications beautifully — bold, clear, and easy to use 💜</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def login_page():
    st.markdown(
        """
        <style>
        .login-wrap{
            max-width: 650px;
            margin: 14px auto 0 auto;
            padding: 18px;
            border-radius: 22px;
            background:
              radial-gradient(circle at 10% 10%, rgba(255, 77, 184, 0.38), transparent 55%),
              radial-gradient(circle at 90% 15%, rgba(124, 77, 255, 0.45), transparent 55%),
              linear-gradient(135deg, rgba(255,255,255,0.55), rgba(255,255,255,0.25));
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 18px 44px rgba(20, 10, 40, 0.16);
            backdrop-filter: blur(10px);
        }
        .login-wrap .app-title,
        .login-wrap .app-subtitle,
        .login-wrap .card-title{
            color: #0B0F18 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "Log in"

    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="card" style="margin-bottom:14px;">
            <div class="app-title" style="font-size: 34px;">Job Application Tracker</div>
            <div class="app-subtitle">Log in with your username and 4-digit PIN</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.auth_view = st.radio(
        "Choose",
        ["Log in", "Sign up"],
        horizontal=True,
        index=0 if st.session_state.auth_view == "Log in" else 1,
        label_visibility="collapsed",
    )

    if st.session_state.auth_view == "Log in":
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Log in</div>", unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="e.g. angela_01", key="login_username")
        pin = st.text_input("4-digit PIN", type="password", placeholder="1234", key="login_pin")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Log in", use_container_width=True):
                ok, msg = login_user(username, pin)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
                    st.session_state.current_page = "My Applications"
                    st.session_state.show_nav = True
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with col2:
            st.caption("Tip: PIN must be exactly 4 digits.")

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Create account</div>", unsafe_allow_html=True)

        username = st.text_input("Choose a username", placeholder="e.g. angela_01", key="signup_username")
        pin1 = st.text_input("Create 4-digit PIN", type="password", placeholder="1234", key="signup_pin1")
        pin2 = st.text_input("Confirm PIN", type="password", placeholder="1234", key="signup_pin2")

        if st.button("Create account", use_container_width=True):
            if pin1 != pin2:
                st.error("PINs do not match.")
            else:
                ok, msg = create_user(username, pin1)
                if ok:
                    st.success(msg)
                    st.session_state.auth_view = "Log in"
                    st.session_state.login_username = username.strip()
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_toggle_bar():
    c1, c2 = st.columns([1, 6])

    with c1:
        if st.session_state.show_nav:
            if st.button("✕ Hide Menu", use_container_width=True):
                st.session_state.show_nav = False
                st.rerun()
        else:
            if st.button("☰ Menu", use_container_width=True):
                st.session_state.show_nav = True
                st.rerun()

    with c2:
        st.markdown(
            "<div class='menu-hint'>Use the menu button to show or hide navigation anytime.</div>",
            unsafe_allow_html=True,
        )


def render_navigation():
    st.markdown(
        f"""
        <div class="nav-panel">
            <div class="nav-title">🗂️ Job Tracker</div>
            <div class="nav-user">Logged in as <b>{st.session_state.username}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["My Applications", "Dashboard", "Add Application", "Statistics", "Settings"],
        index=["My Applications", "Dashboard", "Add Application", "Statistics", "Settings"].index(
            st.session_state.current_page
        ),
        key="nav_radio",
        label_visibility="collapsed",
    )

    st.session_state.current_page = page

    st.write("")
    if st.button("Logout", use_container_width=True, key="logout_nav"):
        logout()
        st.rerun()


def page_add_application():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>➕ Add Application</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("Company Name", placeholder="e.g. Google")
        role = st.text_input("Role / Position", placeholder="e.g. Data Analyst Intern")
        location = st.text_input("Location", placeholder="e.g. Remote / Lagos")
    with c2:
        date_applied = st.date_input("Date Applied", value=date.today())
        status = st.selectbox("Application Status", STATUSES)
        notes = st.text_area("Notes (optional)", placeholder="Any notes about the application…", height=110)

    resume_file = st.file_uploader("Upload Resume used for this application (PDF/DOCX)", type=["pdf", "docx"])

    if st.button("Save Application", use_container_width=True):
        if not company.strip() or not role.strip():
            st.error("Company name and Role/Position are required.")
        else:
            resume_path = save_resume_file(st.session_state.username, resume_file)
            add_application(
                st.session_state.username,
                company,
                role,
                location,
                date_applied,
                status,
                notes,
                resume_path,
            )
            st.success("Saved! ✅")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def page_my_applications(df: pd.DataFrame):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>📋 My Applications</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No applications yet. Go to Add Application to start.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    search = st.text_input("Search (Company or Role)", placeholder="Type to search...")
    show = df.copy()
    if search.strip():
        s = search.strip().lower()
        show = show[
            show["company"].str.lower().str.contains(s, na=False)
            | show["role"].str.lower().str.contains(s, na=False)
        ]

    display_df = show.rename(
        columns={
            "company": "Company",
            "role": "Role / Position",
            "location": "Location",
            "date_applied": "Date Applied",
            "status": "Status",
            "notes": "Notes",
            "resume_path": "Resume File",
            "id": "ID",
        }
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download as CSV",
        data=csv,
        file_name="job_applications.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("### ✏️ Edit / 🗑️ Delete")

    selected_id = st.selectbox("Select an application ID to edit/delete", show["id"].tolist())
    selected_row = df[df["id"] == selected_id].iloc[0]

    ec1, ec2 = st.columns(2)
    with ec1:
        e_company = st.text_input("Edit Company Name", value=str(selected_row["company"]))
        e_role = st.text_input("Edit Role / Position", value=str(selected_row["role"]))
        e_location = st.text_input("Edit Location", value=str(selected_row["location"] or ""))
    with ec2:
        e_date = st.date_input("Edit Date Applied", value=selected_row["date_applied"])
        e_status = st.selectbox("Edit Status", STATUSES, index=STATUSES.index(selected_row["status"]))
        e_notes = st.text_area("Edit Notes", value=str(selected_row["notes"] or ""), height=110)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Save Changes", use_container_width=True):
            update_application(selected_id, st.session_state.username, e_company, e_role, e_location, e_date, e_status, e_notes)
            st.success("Updated ✅")
            st.rerun()

    with b2:
        if st.button("Delete Application", use_container_width=True):
            delete_application(selected_id, st.session_state.username)
            st.warning("Deleted 🗑️")
            st.rerun()

    resume_path = selected_row.get("resume_path")
    if isinstance(resume_path, str) and resume_path.strip() and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            st.download_button(
                "📎 Download attached resume for selected application",
                data=f.read(),
                file_name=os.path.basename(resume_path),
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


def page_dashboard(df: pd.DataFrame):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>📌 Dashboard</div>", unsafe_allow_html=True)

    total = len(df)
    counts = {s: 0 for s in STATUSES}
    if not df.empty:
        vc = df["status"].value_counts()
        for s in STATUSES:
            counts[s] = int(vc.get(s, 0))

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total", total)
    m2.metric("Applied", counts["Applied"])
    m3.metric("Interview", counts["Interview"])
    m4.metric("Offer", counts["Offer"])
    m5.metric("Rejected", counts["Rejected"])

    st.markdown("</div>", unsafe_allow_html=True)


def page_statistics(df: pd.DataFrame):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>📊 Statistics</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("Add applications first to see charts.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    counts_df = (
        df["status"]
        .fillna("Unknown")
        .value_counts()
        .reindex(STATUSES, fill_value=0)
        .reset_index()
    )
    counts_df.columns = ["Status", "Count"]

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Status Breakdown (Pie)")
        pie = (
            alt.Chart(counts_df)
            .mark_arc(innerRadius=60)
            .encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Status:N"),
                tooltip=["Status:N", "Count:Q"],
            )
        )
        st.altair_chart(pie, use_container_width=True)

    with c2:
        st.subheader("Status Count (Bar)")
        bar = (
            alt.Chart(counts_df)
            .mark_bar()
            .encode(
                x=alt.X("Status:N", sort=STATUSES),
                y=alt.Y("Count:Q"),
                tooltip=["Status:N", "Count:Q"],
            )
        )
        st.altair_chart(bar, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def page_settings():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-title'>⚙️ Settings</div>", unsafe_allow_html=True)

    st.write("For now, Settings includes only Logout.")
    if st.button("Logout", use_container_width=True, key="logout_settings"):
        logout()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_main_content(df: pd.DataFrame):
    page = st.session_state.current_page

    if page == "My Applications":
        page_my_applications(df)
    elif page == "Dashboard":
        page_dashboard(df)
    elif page == "Add Application":
        page_add_application()
    elif page == "Statistics":
        page_statistics(df)
    elif page == "Settings":
        page_settings()


# =========================
# Main
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "show_nav" not in st.session_state:
    st.session_state.show_nav = True
if "current_page" not in st.session_state:
    st.session_state.current_page = "My Applications"

if not st.session_state.logged_in:
    login_page()
    st.stop()

app_header()
render_toggle_bar()

df = load_applications(st.session_state.username)

if st.session_state.show_nav:
    left_col, right_col = st.columns([1.1, 3.2], gap="large")

    with left_col:
        render_navigation()

    with right_col:
        render_main_content(df)
else:
    render_main_content(df)