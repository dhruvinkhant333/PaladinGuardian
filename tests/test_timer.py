"""
tests/test_timer.py

Unit tests for core/timer.py. None of these tests sleep or wait on a
real clock — that's exactly what the tick()-driven design in the
core/timer.py docstring is for: a "20 minute" work session is simulated
by calling tick() 1200 times, which runs in milliseconds.
"""

import sys
from pathlib import Path

# Allow running `pytest` from the project root without an install step.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TimerConfig
from core.timer import BreakTimer, TimerState


def make_timer(**overrides) -> BreakTimer:
    """Small work/break durations keep test loops short and readable."""
    config = TimerConfig(
        work_duration_minutes=1,          # 60 ticks
        break_duration_seconds=10,
        long_break_duration_seconds=20,
        sessions_before_long_break=2,
        **overrides,
    )
    return BreakTimer(config)


def tick_n(timer: BreakTimer, n: int) -> None:
    for _ in range(n):
        timer.tick()


def test_starts_idle():
    timer = make_timer()
    assert timer.state == TimerState.IDLE
    assert timer.remaining_seconds == 0


def test_start_enters_working_state():
    timer = make_timer()
    timer.start()
    assert timer.state == TimerState.WORKING
    assert timer.remaining_seconds == 60


def test_tick_counts_down():
    timer = make_timer()
    timer.start()
    timer.tick()
    assert timer.remaining_seconds == 59


def test_tick_while_idle_does_nothing():
    timer = make_timer()
    timer.tick()
    assert timer.state == TimerState.IDLE
    assert timer.remaining_seconds == 0


def test_work_session_transitions_to_short_break():
    timer = make_timer()
    timer.start()
    tick_n(timer, 60)  # exhaust the 60-second work session
    assert timer.state == TimerState.SHORT_BREAK
    assert timer.remaining_seconds == 10
    assert timer.completed_sessions == 1


def test_every_nth_session_is_a_long_break():
    timer = make_timer()  # already configured with sessions_before_long_break=2
    timer.start()
    tick_n(timer, 60)                    # session 1 -> short break
    assert timer.state == TimerState.SHORT_BREAK
    tick_n(timer, 10)                    # break ends -> back to work
    assert timer.state == TimerState.WORKING
    tick_n(timer, 60)                    # session 2 -> long break
    assert timer.state == TimerState.LONG_BREAK
    assert timer.remaining_seconds == 20
    assert timer.completed_sessions == 2


def test_break_ends_and_returns_to_working():
    timer = make_timer()
    timer.start()
    tick_n(timer, 60)          # -> SHORT_BREAK
    tick_n(timer, 10)          # exhaust break
    assert timer.state == TimerState.WORKING
    assert timer.remaining_seconds == 60


def test_pause_and_resume_preserve_remaining_time():
    timer = make_timer()
    timer.start()
    tick_n(timer, 15)
    assert timer.remaining_seconds == 45

    timer.pause()
    assert timer.state == TimerState.PAUSED
    timer.tick()  # ticking while paused must be a no-op
    assert timer.remaining_seconds == 45

    timer.resume()
    assert timer.state == TimerState.WORKING
    assert timer.remaining_seconds == 45


def test_skip_break_returns_to_work_immediately():
    timer = make_timer()
    timer.start()
    tick_n(timer, 60)  # -> SHORT_BREAK
    assert timer.state == TimerState.SHORT_BREAK

    timer.skip_break()
    assert timer.state == TimerState.WORKING
    assert timer.remaining_seconds == 60


def test_skip_break_while_working_is_ignored():
    timer = make_timer()
    timer.start()
    timer.skip_break()
    assert timer.state == TimerState.WORKING  # unchanged


def test_take_break_now_interrupts_work_session():
    timer = make_timer()
    timer.start()
    tick_n(timer, 5)  # 55 seconds still left in the work session
    timer.take_break_now()
    assert timer.state == TimerState.SHORT_BREAK
    assert timer.remaining_seconds == 10
    # An early break should not count as a completed work session.
    assert timer.completed_sessions == 0


def test_reset_returns_to_idle():
    timer = make_timer()
    timer.start()
    tick_n(timer, 10)
    timer.reset()
    assert timer.state == TimerState.IDLE
    assert timer.remaining_seconds == 0


def test_state_changed_signal_fires_on_transitions():
    timer = make_timer()
    transitions = []
    timer.state_changed.connect(lambda new, old: transitions.append((old, new)))

    timer.start()
    tick_n(timer, 60)

    assert transitions == [
        (TimerState.IDLE, TimerState.WORKING),
        (TimerState.WORKING, TimerState.SHORT_BREAK),
    ]
