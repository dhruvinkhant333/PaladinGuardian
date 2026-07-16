"""
utils/config_manager.py

Reads and writes AppConfig to a JSON file on disk. This is the ONLY module
that touches config file I/O — every other part of the app receives an
AppConfig object and never sees a Path or a json module.

Two deliberate reliability choices, since this file guards the user's
settings and statistics:

1. Atomic writes: we write to a temp file and os.replace() it over the
   real one. A crash or power loss mid-write leaves the OLD file intact
   instead of a half-written, unparseable JSON file.

2. Fail-soft reads: a missing or corrupt config file falls back to
   defaults and logs a warning, rather than crashing the app on startup.
   A background wellness tool that refuses to launch because of a bad
   config file is worse than one that quietly resets to defaults.
"""

import dataclasses
import json
import os
from pathlib import Path
from typing import Any

from config import AppConfig, CONFIG_SCHEMA_VERSION, TimerConfig
from constants import CONFIG_FILE_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Loads and persists a single AppConfig to a JSON file."""

    def __init__(self, path: Path = CONFIG_FILE_PATH) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> AppConfig:
        """Load AppConfig from disk, falling back to defaults on any problem."""
        if not self._path.exists():
            logger.info("No config file at %s — using defaults.", self._path)
            return AppConfig()

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "Config file at %s is unreadable (%s) — falling back to defaults.",
                self._path, exc,
            )
            return AppConfig()

        return self._from_dict(raw)

    def save(self, config: AppConfig) -> None:
        """Persist AppConfig to disk atomically, creating parent dirs as needed."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(dataclasses.asdict(config), indent=2, sort_keys=True)

        tmp_path = self._path.with_suffix(".json.tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, self._path)  # atomic on POSIX
        logger.debug("Config saved to %s", self._path)

    @staticmethod
    def _from_dict(raw: dict[str, Any]) -> AppConfig:
        """
        Reconstruct AppConfig from a plain dict, tolerating missing or
        unknown keys so an older config file (or a hand-edited one) never
        crashes the app — unknown keys are dropped, missing keys use the
        dataclass default.
        """
        if raw.get("schema_version") != CONFIG_SCHEMA_VERSION:
            logger.info(
                "Config schema_version %s != current %s — no migration "
                "needed yet, applying defaults for any new fields.",
                raw.get("schema_version"), CONFIG_SCHEMA_VERSION,
            )

        timer_raw = raw.get("timer", {})
        known_timer_fields = {f.name for f in dataclasses.fields(TimerConfig)}
        timer_kwargs = {k: v for k, v in timer_raw.items() if k in known_timer_fields}
        timer = TimerConfig(**timer_kwargs)

        return AppConfig(schema_version=CONFIG_SCHEMA_VERSION, timer=timer)
