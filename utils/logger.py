"""
utils/logger.py

One function, one job: hand back a configured logger. Every other module
calls get_logger(__name__) instead of touching the logging module directly.

WHY this matters for a tray app: it has no terminal window in normal use
(per the spec's "no terminal window" requirement), so logs are the ONLY
way you'll ever debug a problem a user reports. If logging isn't set up
correctly from day one, "it crashed for a user" becomes undebuggable.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from constants import APP_ID, LOG_DIR_PATH

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False  # module-level guard, not mutable app state — see note below


def _configure_root_logger(level: int) -> None:
    """
    Attach handlers to the root logger exactly once per process.

    This is deliberately idempotent rather than a global flag scattered
    across callers: calling get_logger() many times (once per module,
    which is normal) must not attach duplicate handlers, or every log
    line would print N times.
    """
    global _configured
    if _configured:
        return

    LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR_PATH / f"{APP_ID}.log"

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Rotate at 2MB, keep 5 backups — plenty for a low-frequency desktop app,
    # and bounded so logs can never quietly eat the user's disk.
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a module-scoped logger, configuring shared handlers on first call."""
    _configure_root_logger(level)
    return logging.getLogger(name)
