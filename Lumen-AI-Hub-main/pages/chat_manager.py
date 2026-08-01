import os
import sqlite3
from typing import Any, Dict, Iterator, List, Optional
import ollama
import random
import uuid
import hashlib
import base64
import psutil
import platform
import shutil
import json
from datetime import datetime
import streamlit as st
DEFAULT_MODEL = "smollm2:135m"
THINKING_MODELS = {"qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:1.2b","lfm2.5-thinking:1.2b"}

# =========================
# Utilities
# =========================

def get_time():
    return datetime.now().strftime("%I:%M:%S %p")


def get_date():
    return datetime.now().strftime("%A, %d %B %Y")


def random_number(minimum: int, maximum: int):
    return random.randint(minimum, maximum)


def flip_coin():
    return random.choice(["Heads", "Tails"])


def roll_dice(sides: int = 6):
    return random.randint(1, sides)


def generate_uuid():
    return str(uuid.uuid4())


def generate_password(length: int = 16):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))


def hash_text(text: str, algorithm: str = "sha256"):
    h = hashlib.new(algorithm)
    h.update(text.encode())
    return h.hexdigest()


def encode_base64(text: str):
    return base64.b64encode(text.encode()).decode()


def decode_base64(text: str):
    return base64.b64decode(text.encode()).decode()


def count_words(text: str):
    return len(text.split())


def count_characters(text: str):
    return len(text)


# =========================
# Ollama
# =========================

def list_installed_models():
    models = ollama.list()

    return [
        model["model"]
        for model in models["models"]
    ]


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


# =========================
# Debug
# =========================

def app_version():
    return "Lumen AI Hub v1.0"


def server_status():
    return "Online"


def cpu_usage():
    return {
        "percent": psutil.cpu_percent(interval=1),
        "cores": psutil.cpu_count()
    }


def memory_usage():
    ram = psutil.virtual_memory()

    return {
        "used_gb": round(ram.used / (1024**3), 2),
        "total_gb": round(ram.total / (1024**3), 2),
        "percent": ram.percent
    }


def disk_usage():
    disk = shutil.disk_usage("/")

    return {
        "used_gb": round((disk.total - disk.free) / (1024**3), 2),
        "total_gb": round(disk.total / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2)
    }


def system_information():
    return {
        "os": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

# =========================
# Registry
# =========================



class OllamaChatManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "chat_history.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.username=st.session_state.get("username", "anonymous").lower().strip() or "anonymous"
        self._init_db()

        self.TOOLS = [
                # Utilities
                get_time,
                get_date,
                random_number,
                flip_coin,
                roll_dice,
                generate_uuid,
                generate_password,
                hash_text,
                encode_base64,
                decode_base64,
                count_words,
                count_characters,

                # Ollama
                list_installed_models,
                show_model_information,
                delete_model,
                download_model,
            update_model,
            #User information
            self.save_preference,
            self.retrieve_preferences,

                # Debug
                app_version,
                server_status,
                cpu_usage,
                memory_usage,
                disk_usage,
                system_information,
                
            ]

    def _connect_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize the database with simplified schema (one chat per user)."""
        with self._connect_db() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    uid TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL
                )
                """
            )
           

            # Create the preferences table
            # Storing each preference as a new row allows us to easily "append" to a user's list
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    preference TEXT NOT NULL
                )
            ''')
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()
    def save_preference(self,preference: str):
        """
        Appends a new preference for the user. 
        Because we use a relational table, inserting a new row acts like appending to a list.
        """
        # Use the built-in connection manager which handles the correct db_path
        with self._connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_preferences (username, preference)
                VALUES (?, ?)
            ''', (self.username, preference))
            conn.commit()
            
        print(f"[PREFERENCES] Saved new preference for '{self.username}'.")
        return f"Successfully saved preference for {self.username}."

    def retrieve_preferences(self) -> list:
        """
        Retrieves all preferences for a given username and returns them as a Python list.
        This list can be injected into the system prompt for your Ollama models.
        """
        with self._connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT preference FROM user_preferences WHERE username = ?
            ''', (self.username,))

            # Fetch all matching rows. 
            # Since _connect_db uses sqlite3.Row, we access it by column name.
            results = cursor.fetchall()
            preferences_list = [row["preference"] for row in results]

        return preferences_list

    def _sanitize_text(self, value: Any, fallback: str = "") -> str:
        if value is None:
            return fallback
        if isinstance(value, str):
            text = value.strip()
        else:
            text = str(value).strip()
        return text if text else fallback

    def _normalize_uid(self, uid: Optional[str]) -> str:
        uid_text = self._sanitize_text(uid, "anonymous")
        return uid_text.lower().strip() or "anonymous"

    def _build_messages_payload(self, history: List[Dict[str, str]], current_prompt: str) -> List[Dict[str, str]]:
        """Convert stored history into a clean message list for Ollama without duplicating the latest prompt."""
        
        # 1. Fetch user preferences
        

        # 3. Initialize messages with the system prompt
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]
        
        # 4. Append chat history
        for item in history:
            role = self._sanitize_text(item.get("role"), "user").lower()
            if role not in {"user", "assistant", "system", "tool"}:
                role = "user"
            content = self._sanitize_text(item.get("content"), "")
            if content:
                messages.append({"role": role, "content": content})

        # 5. Append current prompt
        current_prompt_text = self._sanitize_text(current_prompt, "")
        if current_prompt_text:
            messages.append({"role": "user", "content": current_prompt_text})
        print(f"[DEBUG] message load {messages} ")
        return messages

    # ==========================================
    #       CORE INFRASTRUCTURE UTILS
    # ==========================================

    def set_user_model(self, uid: str, model_name: str) -> bool:
        """Assign or update the preferred model for a user."""
        safe_uid = self._normalize_uid(uid)
        safe_model = self._sanitize_text(model_name, DEFAULT_MODEL)
        
        try:
            with self._connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_settings (uid, model_name)
                    VALUES (?, ?)
                    ON CONFLICT(uid) DO UPDATE SET model_name = excluded.model_name
                    """,
                    (safe_uid, safe_model),
                )
                conn.commit()
                print(f"[MODEL] Set model '{safe_model}' for user '{safe_uid}'")
                return True
        except Exception as exc:
            print(f"[ERROR] Failed to set model: {exc}")
            raise

    def get_user_model(self, uid: str, default_model: str = DEFAULT_MODEL) -> str:
        """Retrieve a user's model, falling back to a default when missing."""
        safe_uid = self._normalize_uid(uid)
        
        try:
            with self._connect_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT model_name FROM user_settings WHERE uid = ?", (safe_uid,))
                row = cursor.fetchone()
                if row and row["model_name"]:
                    model = row["model_name"]
                    print(f"[MODEL] Retrieved model '{model}' for user '{safe_uid}'")
                    return model
        except Exception as exc:
            print(f"[ERROR] Failed to retrieve model: {exc}")
            raise

        # Set default if not found
        print(f"[MODEL] No model found for '{safe_uid}', setting default '{default_model}'")
        self.set_user_model(safe_uid, default_model)
        return default_model

    def model_supports_thinking(self, model_name: str) -> bool:
        """Check whether the selected model supports explicit think mode."""
        if not model_name:
            return False
        return self._sanitize_text(model_name).lower().strip() in THINKING_MODELS

    def append_message(self, uid: str, role: str, content: str) -> None:
        """Persist a message for the user."""
        safe_uid = self._normalize_uid(uid)
        safe_role = self._sanitize_text(role, "assistant").lower()
        if safe_role not in {"user", "assistant", "system"}:
            safe_role = "assistant"

        safe_content = self._sanitize_text(content, "")
        if not safe_content:
            raise ValueError("Message content cannot be empty")

        with self._connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (uid, role, content) VALUES (?, ?, ?)",
                (safe_uid, safe_role, safe_content),
            )
            conn.commit()

    def get_chat_history(self, uid: str, max_messages: int = 5) -> List[Dict[str, str]]:
        """Retrieve the recent conversation history for a user."""
        safe_uid = self._normalize_uid(uid)
        safe_limit = max(1, min(int(max_messages or 10), 50))
        
        with self._connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content
                FROM (
                    SELECT role, content, timestamp
                    FROM chat_history
                    WHERE uid = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
                ORDER BY timestamp ASC
                """,
                (safe_uid, safe_limit),
            )
            rows = cursor.fetchall()
            user_prefs = self.retrieve_preferences(self.username)
            print(f"[PREFERENCES] Retrieved preferences for '{self.username}': {user_prefs}")
                    # 2. Build the dynamic system prompt
            system_content = "You are a helpful AI assistant."
            if user_prefs:
                        system_content += f"\n\nPlease adhere to the following user preferences:\n{json.dumps(user_prefs)}"
            formatted_rows = []
            for row in rows:
                formatted_rows.append({"role": "system", "content": system_content})
                formatted_rows.append({"role": row["role"], "content": row["content"]} for row in rows)
            return formatted_rows
            

    def clear_chat_history(self, uid: str) -> None:
        """Clear all chat history for a user."""
        safe_uid = self._normalize_uid(uid)
        with self._connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE uid = ?", (safe_uid,))
            conn.commit()
            print(f"[CHAT] Cleared history for user '{safe_uid}'")

    from typing import Iterator


    # Ensure TOOL_MAP is built from your list of tool functions
    # (assumingself.TOOLS is either a list of functions or a dict of name -> function)
    def tool_support(self, model_name: str) -> bool:
        """Checks if a model explicitly supports tool/function calling."""
        # List of known function calling model families
        tool_capable_keywords = ["granite3.3:2b","lfm2.5-thinking:1.2b", 'functiongemma:270m', "llama3.1", "llama3.2", "llama3.3", "qwen2.5", "mistral-nemo", "command-r"]
        
        
        model_lower = model_name.lower()
        return True if model_lower in tool_capable_keywords else False

    
    def chat(self, uid: str, prompt: str, think_mode: bool = False) -> Iterator[str]:
        """Process an inference request, handle potential tool execution, and stream/persist the result."""
        safe_uid = self._normalize_uid(uid)
        safe_prompt = self._sanitize_text(prompt, "")
        if not safe_prompt:
            raise ValueError("Prompt cannot be empty")

        model = self.get_user_model(safe_uid)
        
        # Verify model is available
        available_models = self.get_available_models()
        if model not in available_models:
            error_msg = f"Model '{model}' not available. Available: {', '.join(available_models)}"
            print(f"[ERROR] {error_msg}")
            raise RuntimeError(error_msg)
        
        if think_mode and self.model_supports_thinking(model):
            safe_prompt = "/think " + safe_prompt

        history = self.get_chat_history(safe_uid, max_messages=8)
        messages_payload = self._build_messages_payload(history, safe_prompt)

        self.append_message(safe_uid, "user", safe_prompt)

        # Build lookup map ifself.TOOLS is a list, or use as-is ifself.TOOLS is a dict
        if isinstance(self.TOOLS, list):
            tool_map = {func.__name__: func for func in self.TOOLS}
            tools_param =self.TOOLS
        elif isinstance(self.TOOLS, dict):
            tool_map =self.TOOLS
            tools_param = list(self.TOOLS.values())
        else:
            tool_map = {}
            tools_param = None
        
        try:
            print(f"[CHAT] Sending request to model: {model}")
            print(f"[CHAT] Messages payload: {messages_payload}")
            chat_kwargs = {
                "model": model,
                "messages": messages_payload,
                "stream": True,
                "options": {
                    "num_ctx": 1024,
                    "num_predict": 512,
                    "num_gpu": 24,
                    "num_batch": 32,
                    "temperature": 0.7,
                    "repeat_penalty": 1.1,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }

            # ONLY attach the tools key if the model explicitly supports it
            if self.tool_support(model) and tools_param:
                chat_kwargs["tools"] = tools_param
            response = ollama.chat(**chat_kwargs)

            full_response = ""
            collected_tool_calls = []

            # 1. Iterate over the stream chunks
            for chunk in response:
                msg = chunk.get("message", {}) if isinstance(chunk, dict) else getattr(chunk, "message", None)
                
                if msg:
                    # Check for text content
                    content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                    if content:
                        full_response += content
                        yield content

                    # Check for tool calls
                    tool_calls = msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)
                    if tool_calls:
                        collected_tool_calls.extend(tool_calls)

            # 2. Handle Tool Execution (if model requested any tool calls)
            if collected_tool_calls:
                print(f"[DEBUG] Tool calls detected: {collected_tool_calls}")
                
                # Append assistant message with requested tool calls ONCE
                messages_payload.append({
                    "role": "assistant",
                    "content": full_response,
                    "tool_calls": collected_tool_calls
                })

                # Process each tool call and execute
                for tool in collected_tool_calls:
                    # Handle both dictionary and object formats
                    if isinstance(tool, dict):
                        tool_name = tool["function"]["name"]
                        args = tool["function"]["arguments"]
                    else:
                        tool_name = tool.function.name
                        args = tool.function.arguments

                    if tool_name in tool_map:
                        print(f"[CHAT] Executing tool '{tool_name}' with args: {args}")
                        result = tool_map[tool_name](**args)
                        
                        # Append tool response
                        messages_payload.append({
                            "role": "tool",
                            "content": str(result)
                        })
                    else:
                        print(f"[WARNING] Tool '{tool_name}' requested but not found in tool_map")

                second_response = ollama.chat(**chat_kwargs)
                

                # Reset full_response for final persistence, then stream second response
                full_response = ""
                for chunk in second_response:
                    msg = chunk.get("message", {}) if isinstance(chunk, dict) else getattr(chunk, "message", None)
                    if msg:
                        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                        if content:
                            full_response += content
                            yield content

            if not full_response.strip():
                raise RuntimeError("Model returned an empty response")

            # Persist assistant's complete text output to history
            self.append_message(safe_uid, "assistant", full_response)

        except Exception as exc:
            print(f"[ERROR] Inference failed: {str(exc)}")
            import traceback
            traceback.print_exc()
            raise

    def unload_model(self, model_name: str) -> None:
        """Force Ollama to release a model from its memory cache."""
        safe_model = self._sanitize_text(model_name, DEFAULT_MODEL)
        try:
            ollama.generate(model=safe_model, prompt="", keep_alive=0)
            print(f"[VRAM] Unloaded model: {safe_model}")
        except Exception as exc:
            print(f"[WARNING] Could not unload model: {exc}")

    def get_available_models(self) -> List[str]:
        """Fetch the list of models available locally from Ollama."""
        try:
            print(f"[OLLAMA] Attempting to list models...")
            model_data = ollama.list()
            
            # Handle ListResponse object (has .models attribute)
            if hasattr(model_data, 'models'):
                models = model_data.models
            elif isinstance(model_data, dict):
                models = model_data.get("models", [])
            else:
                models = []
            
            available_models: List[str] = []
            for model_entry in models:
                if hasattr(model_entry, 'model'):
                    candidate = model_entry.model
                    if candidate:
                        available_models.append(candidate)
                elif isinstance(model_entry, dict):
                    candidate = model_entry.get("model") or model_entry.get("name") or ""
                    if candidate:
                        available_models.append(candidate)
            
            print(f"[OLLAMA] Found {len(available_models)} models")
            if available_models:
                return available_models
        except Exception as exc:
            print(f"[ERROR] Could not connect to Ollama: {exc}")
            raise

        raise RuntimeError("No models available and Ollama is not responding")

