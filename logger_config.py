import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level_str, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    if logger.hasHandlers():
        logger.handlers.clear()

    fmt = '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
    formatter = logging.Formatter(fmt)

    # Консоль
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Файловый с ротацией
    raw_path = os.getenv('LOG_FILE', 'app.log')
    base_dir = Path(__file__).resolve().parent
    log_path = (Path(raw_path) if Path(raw_path).is_absolute()
                else base_dir / raw_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
