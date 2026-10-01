"""
Centralised logging configuration for the SIGGRAPH RAG backend.

Usage
-----
from api.logger import get_logger
log = get_logger(__name__)

log.debug("...")
log.info("...")
log.warning("...")
log.error("...")
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Log level — override with env var LOG_LEVEL=DEBUG / INFO / WARNING / ERROR
# ---------------------------------------------------------------------------
_LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "DEBUG").upper()
_LOG_LEVEL = getattr(logging, _LOG_LEVEL_NAME, logging.DEBUG)

# ---------------------------------------------------------------------------
# Log file — optional; set LOG_FILE=logs/rag.log to write to disk as well
# ---------------------------------------------------------------------------
_LOG_FILE = os.getenv("LOG_FILE", "")

# ---------------------------------------------------------------------------
# Formatter — coloured for console, plain for file
# ---------------------------------------------------------------------------
_CONSOLE_FMT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
_FILE_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# ANSI colour codes for the console handler
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


def _build_root_logger() -> logging.Logger:
    root = logging.getLogger("rag")
    if root.handlers:
        # Already configured (e.g. reloaded by uvicorn); skip re-init.
        return root

    root.setLevel(_LOG_LEVEL)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_LOG_LEVEL)
    ch.setFormatter(_ColouredFormatter(fmt=_CONSOLE_FMT, datefmt=_DATE_FMT))
    root.addHandler(ch)

    # Optional file handler
    if _LOG_FILE:
        log_path = Path(_LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(_LOG_LEVEL)
        fh.setFormatter(logging.Formatter(fmt=_FILE_FMT, datefmt=_DATE_FMT))
        root.addHandler(fh)
        root.info("File logging enabled → %s", log_path.resolve())

    # Silence noisy third-party libraries at WARNING level
    for noisy in ("httpx", "httpcore", "urllib3", "qdrant_client", "groq"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return root


# Initialise once at import time
_build_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'rag' namespace."""
    if not name.startswith("rag."):
        name = f"rag.{name}"
    return logging.getLogger(name)
