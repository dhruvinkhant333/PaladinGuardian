"""
tests/test_tray.py

These tests run against the real QSystemTrayIcon/QMenu objects using
Qt's offscreen platform plugin (see conftest.py) — no real desktop or
tray is needed. What's verified here is the WIRING: that each menu
action calls the right BreakTimer method, and that Resume/Pause enable
state tracks the timer's actual state rather than drifting out of sync.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TimerConfig
from core.timer import BreakTimer, TimerState
from core.tray import TrayController


def make_timer() -> BreakTimer:
    return BreakTimer(TimerConfig(work_duration_minutes=1, break_duration_seconds=5))


def test_tray_constructs_without_error(qapp):
    timer = make_timer()
    tray = TrayController(timer)
    assert tray is not None


def test_menu_has_expected_actions(qapp):
    timer = make_timer()
    tray = TrayController(timer)
    action_texts = [a.text() for a in tray._menu.actions() if not a.isSeparator()]
    assert action_texts == [
        "Resume Timer",
        "Pause Timer",
        "Skip Break",
        "Take Break Now",
        "Settings...",
        "Statistics...",
        "About",
        "Quit",
    ]


def test_resume_action_starts_timer_from_idle(qapp):
    timer = make_timer()
    tray = TrayController(timer)
    assert timer.state == TimerState.IDLE

    tray._on_resume_clicked()
    assert timer.state == TimerState.WORKING


def test_pause_action_disabled_while_idle(qapp):
    timer = make_timer()
    tray = TrayController(timer)
    assert not tray._pause_action.isEnabled()
    assert tray._resume_action.isEnabled()


def test_action_availability_flips_after_start(qapp):
    timer = make_timer()
    tray = TrayController(timer)

    timer.start()

    assert tray._pause_action.isEnabled()
    assert not tray._resume_action.isEnabled()


def test_pause_then_resume_via_tray_actions(qapp):
    timer = make_timer()
    tray = TrayController(timer)

    timer.start()
    timer.pause()
    assert tray._resume_action.isEnabled()

    tray._on_resume_clicked()
    assert timer.state == TimerState.WORKING
