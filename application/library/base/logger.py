import logging
import sys

from config.settings import settings


def get_logger(name: str = "chatbot") -> logging.Logger:
    _logger = logging.getLogger(name)
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _logger.addHandler(handler)
        _logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    return _logger


logger = get_logger()
