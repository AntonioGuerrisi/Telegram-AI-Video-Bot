import logging
import os
from logging.handlers import RotatingFileHandler


LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _ensure_logs_dir():
    os.makedirs(LOGS_DIR, exist_ok=True)


def setup_app_logger(log_level: str) -> logging.Logger:
    _ensure_logs_dir()
    logger = logging.getLogger("tg_video_bot")
    logger.setLevel(log_level.upper())
    logger.handlers = []

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_log_path = os.path.join(LOGS_DIR, "bot.log")
    file_handler = RotatingFileHandler(
        app_log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_user_logger(user_id: int) -> logging.Logger:
    _ensure_logs_dir()
    logger = logging.getLogger(f"user_{user_id}")
    logger.setLevel(logging.INFO)
    logger.handlers = []

    formatter = logging.Formatter(
        "%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    user_log_path = os.path.join(LOGS_DIR, f"user_{user_id}.log")
    file_handler = RotatingFileHandler(
        user_log_path, maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
