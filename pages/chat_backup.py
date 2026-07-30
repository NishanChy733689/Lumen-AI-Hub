import streamlit as st
from pages.chat_manager import OllamaChatManager

# 1. Page Configuration
st.set_page_config(
    page_title="AI Chat App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Load External CSS
@st.cache_resource
def load_css():
    css_path = "pages/styles.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

css = load_css()
if css:
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# 3. Instantiate the Chat Manager
if "db_manager" not in st.session_state:
    st.session_state.db_manager = OllamaChatManager()

manager = st.session_state.db_manager

# Ensure the page is only accessible after login
if not st.session_state.get("logged_in", False):
    st.error("❌ Access Denied - Please log in first")
    if st.button("← Back to Login", use_container_width=True):
        st.session_state.clear()
        st.switch_page("main_app.py")
    st.stop()

def get_current_user_id():
    if st.session_state.get("username"):
        return st.session_state.username.lower().strip()
    if st.session_state.get("user_id") is not None:
        return str(st.session_state.user_id)
    return "admin_user"

USER_ID = get_current_user_id()

# --- STATE INITIALIZATION ---
if "processing_prompt" not in st.session_state:
    st.session_state.processing_prompt = None
if "think_mode" not in st.session_state:
    st.session_state.think_mode = False
if "currently_processing" not in st.session_state:
    st.session_state.currently_processing = False

# --- MODEL SELECTION CALLBACK ---
def on_model_change():
    new_model = st.session_state.selected_model_dropdown
    try:
        old_model = manager.get_user_model(USER_ID)
        if old_model != new_model:
            manager.unload_model(old_model)
            manager.set_user_model(USER_ID, new_model)
            if not manager.model_supports_thinking(new_model):
                st.session_state.think_mode = False
            st.toast(f"✅ Model switched to {new_model}", icon="🎯")
    except Exception as e:
        st.error(f"Failed to change model: {str(e)}")

# --- SEND BUTTON HANDLER ---
def handle_send_button():
    user_text = st.session_state.temp_input.strip()
    if user_text and not st.session_state.get("currently_processing", False):
        st.session_state.processing_prompt = user_text
        st.session_state.temp_input = ""

def toggle_think_mode():
    st.session_state.think_mode = not st.session_state.think_mode

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 💬 Chat Settings")
    st.caption(f"User: {USER_ID}")
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        try:
            manager.clear_chat_history(USER_ID)
            st.toast("Chat history cleared", icon="✨")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to clear history: {str(e)}")
    
    st.markdown("---")
    
    if st.button("← Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("main_app.py")

# --- MAIN CHAT DISPLAY ---
try:
    chat_history = manager.get_chat_history(USER_ID)
    
    with st.container():
        if not chat_history and not st.session_state.processing_prompt:
            st.info("👋 Start a conversation with your AI assistant!")
        else:
            for msg in chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg["content"])

        # Process user input
        if st.session_state.processing_prompt:
            user_query = st.session_state.processing_prompt
            st.session_state.currently_processing = True
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_query)
            
            try:
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Processing..."):
                        response_placeholder = st.empty()
                        for response in manager.chat(USER_ID, user_query, think_mode=st.session_state.think_mode):
                            response_placeholder.markdown(response)
                
                st.toast("✅ Response saved!", icon="💾")
                
            except ValueError as e:
                st.error(f"Invalid input: {str(e)}")
            except RuntimeError as e:
                st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
            
            st.session_state.processing_prompt = None
            st.session_state.currently_processing = False
            st.rerun()

except Exception as e:
    st.error(f"Failed to load chat: {str(e)}")

# --- FOOTER (NATIVE AUTO-EXPANDING CHAT INPUT) ---
with st.bottom:
    col_model, col_spacer = st.columns([0.2, 0.8])
    
    # Model dropdown floating just above the chat bar
    with col_model:
        try:
            current_model = manager.get_user_model(USER_ID)
            available_models = manager.get_available_models()

            if current_model not in available_models:
                available_models.insert(0, current_model)

            model_index = available_models.index(current_model)

            st.selectbox(
                label="Model",
                options=available_models,
                index=model_index,
                label_visibility="collapsed",
                key="selected_model_dropdown",
                on_change=on_model_change,
            )
        except Exception as e:
            st.error(f"Model error: {str(e)}")

    # Native auto-expanding input box with built-in send icon
    prompt = st.chat_input("Type your message here...", key="chat_input")
    if prompt:
        handle_send_button(prompt)