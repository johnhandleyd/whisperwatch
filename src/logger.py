import logging
import os
import sys
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name="whisperwatch"):
    # Format with color codes
    class ColorFormatter(logging.Formatter):
        LEVEL_COLORS = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA
        }

        def format(self, record):
            color = self.LEVEL_COLORS.get(record.levelno, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"logs_{timestamp}.txt")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # prevent duplicates if run multiple times

    # Console handler with color
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.stream.reconfigure(encoding='utf-8')
    console_handler.setLevel(logging.INFO)
    console_format = ColorFormatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
