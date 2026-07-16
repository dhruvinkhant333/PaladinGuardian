"""
core/timer.py

The break-timer state machine. This is the single source of truth for
"what phase are we in and how much time is left" — nothing else in the
app is allowed to duplicate that state.

Architectural decision worth calling out explicitly: this class has NO
PySide6 import and no real clock (no threading.Timer, no QTimer). It
exposes a `tick()` method that the CALLER is expected to invoke once per
second. The real app will drive that with a QTimer in a later step; a
unit test drives it by calling tick() in a loop; a future CLI mode could
drive it with plain time.sleep(1).

Why this matters: business logic that owns its own clock is notoriously
hard to test (you either sleep() in your test suite, or mock time
itself). Business logic that just reacts to "one second passed" is
trivial to test — call tick() 1200 times and assert the phase changed,
in milliseconds, with no sleeping and no mocking.
"""

from enum import Enum, auto

from config import TimerConfig
from utils.helpers import Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class TimerState(Enum):
    IDLE = auto()          # app running, timer not started yet
    WORKING = auto()       # counting down a work session
    SHORT_BREAK = auto()   # counting down a regular break
    LONG_BREAK = auto()    # counting down a long break (every N sessions)
    PAUSED = auto()        # counting suspended; remembers what it was paused from


class BreakTimer:
    """
    Drives the work/break cycle described in the spec:
    work_duration -> break_duration -> repeat, with a long break every
    `sessions_before_long_break` work sessions.

    Public signals (connect a callable to any of these):
        state_changed(new_state: TimerState, old_state: TimerState)
        tick(remaining_seconds: int, state: TimerState)
        break_started(state: TimerState, duration_seconds: int)
        session_completed(total_sessions: int)
    """

    def __init__(self, config: TimerConfig) -> None:
        self._config = config

        self.state_changed = Signal()
        self.tick_signal = Signal()
        self.break_started = Signal()
        self.session_completed = Signal()

        self._state = TimerState.IDLE
        self._remaining_seconds = 0
        self._completed_sessions = 0
        self._state_before_pause: TimerState | None = None

    # --- Read-only properties -------------------------------------------------

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def remaining_seconds(self) -> int:
        return self._remaining_seconds

    @property
    def completed_sessions(self) -> int:
        return self._completed_sessions

    # --- Commands (tray menu / UI calls these) ---------------------------------

    def start(self) -> None:
        """Begin (or restart from IDLE) the work/break cycle."""
        if self._state != TimerState.IDLE:
            logger.debug("start() called while state=%s — ignoring.", self._state)
            return
        self._enter_state(TimerState.WORKING, self._config.work_duration_minutes * 60)

    def pause(self) -> None:
        """Suspend counting. No-op if already paused or idle."""
        if self._state in (TimerState.PAUSED, TimerState.IDLE):
            return
        self._state_before_pause = self._state
        self._enter_state(TimerState.PAUSED, self._remaining_seconds)

    def resume(self) -> None:
        """Resume counting after pause(), continuing the same countdown."""
        if self._state != TimerState.PAUSED or self._state_before_pause is None:
            return
        restored_state = self._state_before_pause
        self._state_before_pause = None
        self._enter_state(restored_state, self._remaining_seconds)

    def skip_break(self) -> None:
        """If currently on a break, end it immediately and start work again."""
        if self._state not in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            logger.debug("skip_break() called while state=%s — ignoring.", self._state)
            return
        self._enter_state(TimerState.WORKING, self._config.work_duration_minutes * 60)

    def take_break_now(self) -> None:
        """Force an immediate short break, interrupting a work session early."""
        if self._state != TimerState.WORKING:
            logger.debug("take_break_now() called while state=%s — ignoring.", self._state)
            return
        self._start_break(is_long_break=False)

    def reset(self) -> None:
        """Return to IDLE, clearing the current countdown (stats are untouched)."""
        self._state_before_pause = None
        self._enter_state(TimerState.IDLE, 0)

    # --- The one method the caller's clock drives -------------------------------

    def tick(self) -> None:
        """Advance the countdown by one second. Call this once per second."""
        if self._state in (TimerState.IDLE, TimerState.PAUSED):
            return

        self._remaining_seconds = max(0, self._remaining_seconds - 1)
        self.tick_signal.emit(self._remaining_seconds, self._state)

        if self._remaining_seconds == 0:
            self._on_phase_complete()

    # --- Internal transition logic -----------------------------------------------

    def _on_phase_complete(self) -> None:
        if self._state == TimerState.WORKING:
            self._completed_sessions += 1
            self.session_completed.emit(self._completed_sessions)
            is_long = (
                self._completed_sessions % self._config.sessions_before_long_break == 0
            )
            self._start_break(is_long_break=is_long)

        elif self._state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self._enter_state(TimerState.WORKING, self._config.work_duration_minutes * 60)

    def _start_break(self, is_long_break: bool) -> None:
        if is_long_break:
            duration = self._config.long_break_duration_seconds
            new_state = TimerState.LONG_BREAK
        else:
            duration = self._config.break_duration_seconds
            new_state = TimerState.SHORT_BREAK

        self._enter_state(new_state, duration)
        self.break_started.emit(new_state, duration)

    def _enter_state(self, new_state: TimerState, remaining_seconds: int) -> None:
        old_state = self._state
        self._state = new_state
        self._remaining_seconds = remaining_seconds
        logger.info(
            "State transition: %s -> %s (remaining=%ss)",
            old_state.name, new_state.name, remaining_seconds,
        )
        self.state_changed.emit(new_state, old_state)
