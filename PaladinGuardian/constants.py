"""
constants.py

Central home for values that are truly global and never change at runtime:
app metadata, filesystem locations, and factory-default numbers.

WHY a separate module instead of scattering literals through the codebase:
when the defaults need to change (e.g. shipping a new default work duration),
there should be exactly one line to touch, and no risk of two modules
disagreeing about what "default" means.
"""

from pathlib import Path

# --- App metadata ---------------------------------------------------------
APP_NAME = "Paladin Break Guardian"
APP_ID = "paladin-break-guardian"  # used for config/log dirs, desktop file, tray
APP_VERSION = "0.1.0"
APP_ORG = "PaladinGuardian"

# --- Filesystem locations ---------------------------------------------------
# Follow the XDG Base Directory spec rather than dumping dotfiles in $HOME —
# this is what a "polished enough to open-source" Linux app is expected to do.
XDG_CONFIG_HOME = Path.home() / ".config" / APP_ID
XDG_DATA_HOME = Path.home() / ".local" / "share" / APP_ID
XDG_STATE_HOME = Path.home() / ".local" / "state" / APP_ID

CONFIG_FILE_PATH = XDG_CONFIG_HOME / "config.json"
STATS_FILE_PATH = XDG_DATA_HOME / "statistics.json"
LOG_DIR_PATH = XDG_STATE_HOME / "logs"

# --- Timer defaults (seconds unless noted) ---------------------------------
DEFAULT_WORK_MINUTES = 20
DEFAULT_BREAK_SECONDS = 60
DEFAULT_LONG_BREAK_SECONDS = 300  # 5 minutes
DEFAULT_SESSIONS_BEFORE_LONG_BREAK = 4

# Allowed work-duration presets shown in Settings (minutes).
WORK_DURATION_PRESETS_MIN = (5, 10, 20, 25, 30, 45, 60)

# How often the core timer "ticks". 1 second is coarse enough to be cheap
# and fine enough that a 60-second break countdown never looks jumpy.
TICK_INTERVAL_SECONDS = 1
