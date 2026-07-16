"""
core/tray.py

The system tray icon and its menu. This is intentionally "dumb": every
menu action is a direct pass-through to a BreakTimer method that already
existed before this file was written (start/pause/resume/skip_break/
take_break_now). tray.py adds NO new business logic — if you ever find
yourself writing an if-statement here that decides what the timer
should do, that logic belongs in core/timer.py instead, not here.

Settings and Statistics windows don't exist yet (later steps). Rather
than omitting those menu items until then, they're wired to a small
"coming soon" dialog — a user of the running app should see the item
they expect and learn it's not ready yet, not wonder if it's missing
by mistake.

WHY QObject as a base class: TrayController needs to receive Qt's
signals (BreakTimer's Signal callables work fine as plain functions,
so this isn't strictly required for that) — but subclassing QObject
lets Qt manage this object's lifetime alongside its parent (main
app window/QApplication), which matters once this stops being the
only long-lived object in the app.
"""

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from constants import APP_NAME, APP_VERSION
from core.timer import BreakTimer, TimerState
from utils.logger import get_logger

logger = get_logger(__name__)


def _build_placeholder_icon() -> QIcon:
    """
    Draw a simple 64x64 icon in code so the tray has something to show
    without depending on assets/icons/ being populated.

    This is explicitly a placeholder, not a design decision: real
    character-themed icons arrive with the Companion feature (see the
    empty assets/characters/ directory in the roadmap). Swapping this
    for QIcon("assets/icons/tray_default.png") later is a one-line change.
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#4a4e69"))
    painter.setPen(QColor("#22223b"))
    painter.drawEllipse(2, 2, size - 4, size - 4)

    painter.setPen(QColor("#f2e9e4"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(28)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "P")
    painter.end()

    return QIcon(pixmap)


class TrayController(QObject):
    """Owns the QSystemTrayIcon + menu and binds each item to a BreakTimer command."""

    def __init__(self, timer: BreakTimer, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = timer

        self._tray_icon = QSystemTrayIcon(_build_placeholder_icon(), self)
        self._tray_icon.setToolTip(APP_NAME)

        self._menu = QMenu()
        self._resume_action = self._menu.addAction("Resume Timer", self._on_resume_clicked)
        self._pause_action = self._menu.addAction("Pause Timer", self._timer.pause)
        self._menu.addAction("Skip Break", self._timer.skip_break)
        self._menu.addAction("Take Break Now", self._timer.take_break_now)
        self._menu.addSeparator()
        self._menu.addAction("Settings...", self._make_coming_soon_handler("Settings"))
        self._menu.addAction("Statistics...", self._make_coming_soon_handler("Statistics"))
        self._menu.addAction("About", self._on_about_clicked)
        self._menu.addSeparator()
        self._menu.addAction("Quit", self._on_quit_clicked)

        self._tray_icon.setContextMenu(self._menu)
        self._tray_icon.show()

        # Keep the menu's enabled/disabled state honest as the timer changes
        # state on its own (e.g. a break ending automatically flips us back
        # from "on break" to "working", which should re-enable Pause).
        self._timer.state_changed.connect(self._on_timer_state_changed)
        self._timer.tick_signal.connect(self._on_timer_tick)
        self._update_action_availability(self._timer.state)

    # --- Menu action handlers -------------------------------------------------

    def _on_resume_clicked(self) -> None:
        # "Resume Timer" doubles as "Start Timer" from IDLE — a user
        # shouldn't need to know the internal state name to know which
        # button gets things going.
        if self._timer.state == TimerState.IDLE:
            self._timer.start()
        else:
            self._timer.resume()

    def _make_coming_soon_handler(self, feature_name: str):
        def handler() -> None:
            QMessageBox.information(
                None, feature_name, f"{feature_name} is coming in a later step."
            )
        return handler

    def _on_about_clicked(self) -> None:
        QMessageBox.information(None, "About", f"{APP_NAME}\nVersion {APP_VERSION}")

    def _on_quit_clicked(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    # --- Reacting to timer state (BreakTimer -> tray, one direction only) ------

    def _on_timer_state_changed(self, new_state: TimerState, _old_state: TimerState) -> None:
        self._update_action_availability(new_state)

    def _update_action_availability(self, state: TimerState) -> None:
        self._resume_action.setEnabled(state in (TimerState.IDLE, TimerState.PAUSED))
        self._pause_action.setEnabled(state not in (TimerState.IDLE, TimerState.PAUSED))

    def _on_timer_tick(self, remaining_seconds: int, state: TimerState) -> None:
        minutes, seconds = divmod(remaining_seconds, 60)
        self._tray_icon.setToolTip(f"{APP_NAME} — {state.name} {minutes:02d}:{seconds:02d}")
