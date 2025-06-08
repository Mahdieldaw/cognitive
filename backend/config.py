import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    WORKFLOWS_DIR = os.getenv("WORKFLOWS_DIR", "workflows")
    QUEUE_STATE_FILE = os.getenv("QUEUE_STATE_FILE", "queue-state.json")
    MAX_PARALLEL_NODES = int(os.getenv("MAX_PARALLEL_NODES", "4"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

settings = Settings()