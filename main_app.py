import sqlite3
import streamlit as st

# ==========================================
#   DATABASE AUTHENTICATION SECURE HOOKS
# ==========================================
DB_PATH = "pages/chat_history.db"


def configure_app_shell() -> None:
    """Keep the login experience standalone without exposing the app page nav."""
    st.set_page_config(
        page_title="Lumen AI Login",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    try:
        st.set_option("client.showSidebarNavigation", False)
    except Exception:
        pass


configure_app_shell()


def init_sqlite_db():
    """Initializes the database structure before the UI loads."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()


def verify_user_login(username: str, password_raw: str):
    """Verifies user entry records against database blocks."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username FROM users WHERE username = ? AND password = ?",
            (username.lower().strip(), password_raw),
        )
        return cursor.fetchone()


def register_user(username: str, password_raw: str) -> bool:
    """Saves a fresh registration block directly to the database file."""
    if not username or not password_raw:
        return False
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username.lower().strip(), password_raw),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False  # Username taken


# ==========================================
#   CUSTOM FUNCTIONAL LOGIN PAGE LAYOUT
# ==========================================
def render_login_view():
    """Renders the standalone login and registration portal interface."""
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none !important;}</style>",
        unsafe_allow_html=True,
    )
    # Apply dark mode styling
    st.markdown(
        """
        <style>
        /* Dark mode background */
        .stApp {
            background: linear-gradient(135deg, #1a1d23 0%, #232429 100%) !important;
        }
        
        /* Input fields */
        div[data-baseweb="input"] {
            background-color: #35383f !important;
            border-radius: 10px !important;
            border: 1.5px solid #4d5059 !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-baseweb="input"]:hover {
            border-color: #0066cc !important;
            box-shadow: 0 0 12px rgba(0, 102, 204, 0.2) !important;
        }
        
        div[data-baseweb="input"] input {
            color: #ffffff !important;
            font-size: 14px !important;
        }
        
        div[data-baseweb="input"] input::placeholder {
            color: #8f9199 !important;
        }
        
        /* Button styling */
        div[data-baseweb="button"] button {
            background-color: #0066cc !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-baseweb="button"] button:hover {
            background-color: #0055aa !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0, 102, 204, 0.4) !important;
        }
        
        /* Tabs styling */
        button[role="tab"] {
            color: #8f9199 !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        
        button[role="tab"][aria-selected="true"] {
            color: #0066cc !important;
            border-bottom-color: #0066cc !important;
        }
        
        /* Alert boxes */
        div[data-testid="stAlert"] {
            border-radius: 10px !important;
            padding: 14px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("Lumen AI hub Access Portal")
        st.caption("Secure Local Authentication Unit")

        tab_login, tab_register = st.tabs(
            ["🔑 Account Authentication", "➕ Register New User"]
        )

        with tab_login:
            user_field = st.text_input("Username:", key="login_user").strip()
            pass_field = st.text_input(
                "Password:", type="password", key="login_pass"
            ).strip()

            if st.button("Access Dashboard Terminal", use_container_width=True):
                account_match = verify_user_login(user_field, pass_field)
                if account_match:
                    st.session_state.logged_in = True
                    st.session_state.user_id = account_match[0]
                    st.session_state.username = account_match[1]
                    st.success("Access Granted. Initializing dashboard space...")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with tab_register:
            reg_user = st.text_input("Create Username ID:", key="reg_user").strip()
            reg_pass = st.text_input(
                "Set Access Password:", type="password", key="reg_pass"
            ).strip()

            if st.button("Commit Profile to Database", use_container_width=True):
                if len(reg_user) < 3 or len(reg_pass) < 4:
                    st.warning("Username must be >= 3 chars, Password >= 4 chars.")
                else:
                    if register_user(reg_user, reg_pass):
                        st.success("Registration complete! Switch to the login tab.")
                    else:
                        st.error("Username already taken.")


# ==========================================
#   APPLICATION SESSION STATE ROUTER
# ==========================================
init_sqlite_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # If not authenticated, force display of standalone functional view loop
    render_login_view()
else:
    # switch the user to the chat
    st.switch_page("pages/chat.py")
