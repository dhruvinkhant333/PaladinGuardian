"""
app.py

Boots the real Qt application. main.py is deliberately a two-line
file — this is where ConfigManager, BreakTimer, and TrayController
actually get wired together, and where the Qt event loop lives.

REFACTOR NOTE (replacing Step 1's threading ticker): Step 1's main.py
drove BreakTimer.tick() from a background thread because no Qt event
loop existed yet. Now that QApplication does, a QTimer on the main
thread is strictly better: no thread to manage, no risk of a
background thread touching a Qt object from the wrong thread (Qt
objects are not generally thread-safe), and it's the same mechanism
core/overlay.py will use in the next step for animating the break
screen.
"""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from constants import APP_ID, APP_NAME, APP_ORG, APP_VERSION, TICK_INTERVAL_SECONDS
from core.timer import BreakTimer
from core.tray import TrayController
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_ORG)
    # This is a tray app with no main window — without this, Qt would
    # quit the whole app the moment a transient dialog (like the About
    # box) closes, which is never what we want here.
    app.setQuitOnLastWindowClosed(False)

    config_manager = ConfigManager()
    app_config = config_manager.load()

    timer = BreakTimer(app_config.timer)
    tray = TrayController(timer)  # noqa: F841 — kept alive by local scope + parented QObjects

    tick_timer = QTimer()
    tick_timer.setInterval(TICK_INTERVAL_SECONDS * 1000)
    tick_timer.timeout.connect(timer.tick)
    tick_timer.start()

    timer.start()

    # aboutToQuit fires regardless of HOW the app quits (tray Quit action,
    # SIGTERM, session logout) — a single save-on-exit path beats trying
    # to catch every possible quit trigger individually.
    app.aboutToQuit.connect(lambda: config_manager.save(app_config))

    logger.info("%s v%s started (app_id=%s).", APP_NAME, APP_VERSION, APP_ID)
    return app.exec()
