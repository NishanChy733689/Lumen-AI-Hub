import ollama
import random
import uuid
import hashlib
import base64
import psutil
import platform
import shutil
from datetime import datetime

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

TOOLS = {
    # Utilities
    "get_time": get_time,
    "get_date": get_date,
    "random_number": random_number,
    "flip_coin": flip_coin,
    "roll_dice": roll_dice,
    "generate_uuid": generate_uuid,
    "generate_password": generate_password,
    "hash_text": hash_text,
    "encode_base64": encode_base64,
    "decode_base64": decode_base64,
    "count_words": count_words,
    "count_characters": count_characters,

    # Ollama
    "list_installed_models": list_installed_models,
    "show_model_information": show_model_information,
    "delete_model": delete_model,
    "download_model": download_model,
    "update_model": update_model,

    # Debug
    "app_version": app_version,
    "server_status": server_status,
    "cpu_usage": cpu_usage,
    "memory_usage": memory_usage,
    "disk_usage": disk_usage,
    "system_information": system_information,
}