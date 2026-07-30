import streamlit as st
import subprocess
import os
from pages.chat_manager import OllamaChatManager

# Custom dark UI injection to match your look
st.markdown(
    """
    <style>
    .stApp { background-color: #232429; color: #ffffff; }
    div[data-baseweb="input"] { background-color: #35383f !important; border-radius: 8px !important; border: none !important; }
    div[data-baseweb="input"] input { color: #ffffff !important; }
    .stButton>button { background-color: #4d5059 !important; color: #ffffff !important; border: none !important; }
    </style>
    """, 
    unsafe_allow_html=True
)

st.title("📥 Model Downloader Hub")
st.write("Pull native Ollama models or Hugging Face repositories straight to your system.")

# Initialize the manager class for structural model checks
if "db_manager" not in st.session_state:
    st.session_state.db_manager = OllamaChatManager()
manager = st.session_state.db_manager

# Form Layout
with st.form("download_form"):
    model_id = st.text_input(
        "Enter Model ID", 
        placeholder="e.g. qwen2.5:0.5b or hf.co/Bartowski/Llama-3-8B-Instruct-GGUF:Q4_K_M"
    ).strip()
    
    submit_btn = st.form_submit_button(label="Start Pull Operation")


if submit_btn and model_id:
    # 1. Clean out accidental quotation marks from inputs
    cleaned_model_id = model_id.replace('"', '').replace("'", "")
    
    with st.spinner(f"Pulling model '{cleaned_model_id}'... Please wait."):
        try:
            # Execute background worker shell subprocess to run the download command
            # Using st.spinner prevents UI interactions while the download completes
            result = subprocess.run(
                ["ollama", "pull", cleaned_model_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            st.success(f"Model '{cleaned_model_id}' downloaded successfully!")
            st.toast("Model list refreshed!", icon="✅")
            
        except subprocess.CalledProcessError as e:
            # Fallback error handling (e.g., handling Rate Limits / HTTP 429 from earlier)
            st.error(f"Download failed. Check the name syntax or connection status.")
            st.code(e.stderr if e.stderr else "Unknown CLI process failure.")

# Bottom dashboard section: list what's currently available on the machine
st.subheader("📦 Locally Installed Models")
try:
    installed_models = manager.get_available_models()
    for idx, name in enumerate(installed_models, 1):
        st.write(f"{idx}. `{name}`")
except Exception:
    st.write("Unable to parse current model registry lists.")
