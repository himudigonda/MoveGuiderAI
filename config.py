# config.py
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --- API Key Configuration ---
def get_api_key(env_var_name: str) -> str:
    """Gets an API key from environment variables or exits."""
    api_key = os.getenv(env_var_name)
    if not api_key:
        print(f"[ERROR] ‼️ {env_var_name} not found in environment variables.")
        print(f"Please add '{env_var_name}=\"your-key-here\"' to your .env file.")
        sys.exit(1)
    print(f"[INFO] ✅ {env_var_name} loaded successfully.")
    return api_key


# --- Load Specific Keys ---
OPENWEATHER_API_KEY = get_api_key("OPENWEATHER_API_KEY")
