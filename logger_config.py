"""
logger_config.py

This module sets up a logger that logs to both console and file.

Usage:
    from logger_config import setup_logger
    logger = setup_logger(__name__)
"""
import logging
import os

# Path to the log file (ecwbot.log in the project root)
LOG_FILE = os.path.join(os.path.dirname(__file__), 'ecwbot.log')


def setup_logger(name: str) -> logging.Logger:
    """Create and return a logger configured with console and file handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(name)s: %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
