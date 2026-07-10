import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "bot.db"

CLAWBOT_BASE_URL = os.getenv("CLAWBOT_BASE_URL", "https://ilinkai.weixin.qq.com")
BOT_TYPE = int(os.getenv("BOT_TYPE", "3"))

WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

PAGE_SIZE = int(os.getenv("PAGE_SIZE", "10"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
