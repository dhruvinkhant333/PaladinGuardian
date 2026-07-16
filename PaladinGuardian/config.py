"""
config.py

Defines the SHAPE of persisted configuration as dataclasses. This file
knows nothing about JSON, files, or disk — that's utils/config_manager.py's
job. Keeping "what the config looks like" separate from "how it's stored"
means we could swap JSON for SQLite later without touching a single field
definition here.

Only the timer-related settings are implemented in this step. Appearance,
Companion, Sound, and Notification settings arrive in later steps (their
dataclasses will hang off AppConfig the same way TimerConfig does) — they
are intentionally NOT stubbed out here with fake defaults, because a
config field with no code reading it yet is just a lie waiting to be
discovered.
"""

from dataclasses import dataclass, field

from constants import (
    DEFAULT_BREAK_SECONDS,
    DEFAULT_LONG_BREAK_SECONDS,
    DEFAULT_SESSIONS_BEFORE_LONG_BREAK,
    DEFAULT_WORK_MINUTES,
)

# Bump this if a future step changes the on-disk shape in a way that
# requires migrating old config files. ConfigManager checks it on load.
CONFIG_SCHEMA_VERSION = 1


@dataclass
class TimerConfig:
    """Everything the break-timer state machine needs to know."""

    work_duration_minutes: int = DEFAULT_WORK_MINUTES
    break_duration_seconds: int = DEFAULT_BREAK_SECONDS
    long_break_duration_seconds: int = DEFAULT_LONG_BREAK_SECONDS
    sessions_before_long_break: int = DEFAULT_SESSIONS_BEFORE_LONG_BREAK

    auto_start_on_login: bool = False
    launch_hidden: bool = False

    # Idle detection is wired up in a later step (utils/idle_detector.py),
    # but the user-facing setting belongs in General Settings now, so we
    # store it here even though nothing reads it yet.
    pause_while_idle: bool = True
    idle_threshold_seconds: int = 120


@dataclass
class AppConfig:
    """Root config object. Grows one nested dataclass per settings category."""

    schema_version: int = CONFIG_SCHEMA_VERSION
    timer: TimerConfig = field(default_factory=TimerConfig)
