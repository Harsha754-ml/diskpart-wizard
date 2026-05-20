# utils/logger.py
# File logger (diskwizard.log)

import logging
import os

LOG_PATH = os.path.join(os.getenv("APPDATA", "."), "DiskWizard", "diskwizard.log")


def get_logger(name: str = "diskwizard") -> logging.Logger:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
