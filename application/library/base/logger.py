import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config.settings import settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "chatbot") -> logging.Logger:
    _logger = logging.getLogger(name)
    if _logger.handlers:
        return _logger

    _logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # 文件输出
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))), settings.log_dir)
    os.makedirs(log_dir, exist_ok=True)

    # 全量日志
    all_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    all_handler.setFormatter(formatter)
    _logger.addHandler(all_handler)

    # 错误日志（单独文件，便于排查）
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    _logger.addHandler(error_handler)

    return _logger


logger = get_logger()
