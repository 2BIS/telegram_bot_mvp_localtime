import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

# Опциональный admin chat id для уведомлений
_ADMIN_RAW = os.getenv("ADMIN_CHAT_ID")
ADMIN_CHAT_ID = (
    int(_ADMIN_RAW) if _ADMIN_RAW and _ADMIN_RAW.lstrip("-").isdigit() else None
)

# Логгирование в rotating file (errors only)
LOG_FILE = os.getenv("LOG_FILE", "bot_errors.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))  # 5 MB
LOG_BACKUPS = int(os.getenv("LOG_BACKUPS", "3"))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Внести RotatingFileHandler для ошибок
attach_handler = True
for h in root_logger.handlers:
    if isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', '') == os.path.abspath(LOG_FILE):
        attach_handler = False
        break
if attach_handler:
    err_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding="utf-8")
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger.addHandler(err_handler)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)