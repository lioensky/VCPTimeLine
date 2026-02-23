import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUMMARY_MODEL_URL = os.getenv("SUMMARY_MODEL_URL", "https://api.openai.com/v1/chat/completions")
SUMMARY_MODEL_API_KEY = os.getenv("SUMMARY_MODEL_API_KEY", "")
SUMMARY_MODEL_NAME = os.getenv("SUMMARY_MODEL_NAME", "gpt-4o")
SUMMARY_MODEL_MAX_CONTEXT = int(os.getenv("SUMMARY_MODEL_MAX_CONTEXT", "60000"))
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))

MEMORY_BASE_PATH = os.getenv("MEMORY_BASE_PATH", "")
# Parse ignore folders, handling empty cases
ignore_str = os.getenv("IGNORE_FOLDERS", "")
IGNORE_FOLDERS = [f.strip() for f in ignore_str.split(",") if f.strip()]

def validate_config():
    errors = []
    if not SUMMARY_MODEL_API_KEY:
        errors.append("SUMMARY_MODEL_API_KEY is missing in .env")
    if not MEMORY_BASE_PATH:
        errors.append("MEMORY_BASE_PATH is missing in .env")
    
    if errors:
        return False, "\n".join(errors)
    return True, "Config is valid"
