import streamlit as st
import ollama

# ------------------------------
# Backend Functions
# ------------------------------


def list_installed_models():
    models = ollama.list()

    return [model["model"] for model in models["models"]]


def show_model_information(model_name):
    return ollama.show(model_name)


def delete_model(model_name):
    ollama.delete(model_name)
    return f"{model_name} deleted."


def download_model(model_name):
    ollama.pull(model_name)
    return f"{model_name} downloaded."


def update_model(model_name):
    ollama.pull(model_name)
    return f"{model_name} updated."


# ------------------------------
# Streamlit UI
# ------------------------------

st.set_page_config(
    page_title="Lumen AI Hub - Model Manager", page_icon="🤖", layout="wide"
)

st.title("🤖 Lumen AI Hub")
st.subheader("Ollama Model Manager")

st.divider()

# Refresh Button
if st.button("🔄 Refresh Models"):
    st.rerun()

installed_models = list_installed_models()

left, right = st.columns([2, 1])

# ---------------------------------
# Installed Models
# ---------------------------------

with left:

    st.header("Installed Models")

    if installed_models:

        selected_model = st.selectbox("Choose a model", installed_models)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("ℹ Show Info"):

                info = show_model_information(selected_model)

                st.json(info)

        with col2:
            if st.button("🔄 Update"):

                with st.spinner("Updating model..."):
                    st.success(update_model(selected_model))

                st.rerun()

        with col3:
            if st.button("🗑 Delete"):

                with st.spinner("Deleting..."):
                    st.success(delete_model(selected_model))

                st.rerun()

    else:
        st.info("No models installed.")

# ---------------------------------
# Download New Model
# ---------------------------------

with right:

    st.header("Download Model")

    model_name = st.text_input("Model Name", placeholder="e.g. llama3.2:3b")

    if st.button("📥 Download"):

        if model_name.strip():

            with st.spinner("Downloading model..."):
                st.success(download_model(model_name.strip()))

            st.rerun()

        else:
            st.warning("Enter a model name.")

st.divider()

st.caption("Powered by Ollama | Lumen AI Hub")
