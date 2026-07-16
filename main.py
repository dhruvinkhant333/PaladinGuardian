"""
main.py

Entry point for Paladin Break Guardian.

STEP 1 SCOPE: there is no tray icon, no overlay, and no PySide6 import
here yet — those arrive in later steps (core/tray.py, core/overlay.py,
ui/). What this DOES do is wire the two pieces built so far — ConfigManager
and BreakTimer — into something you can actually run right now and watch
work correctly in a terminal:

    python main.py

It starts a work session using your configured duration, prints every
state transition, and lets you interrupt it with the tray commands the
real app will eventually expose, typed as text for now:

    p  = pause / resume
    b  = take a break now
    s  = skip current break
    q  = quit (saves config)

This keeps every step of the project runnable end-to-end instead of
"trust me, it'll work once the GUI is built" — you can verify the state
machine's timing and transitions today, in real time, with real config
persistence.
"""

import sys
import threading
import time

from config import AppConfig
from constants import APP_NAME, APP_VERSION, TICK_INTERVAL_SECONDS
from core.timer import BreakTimer, TimerState
from utils.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


def _format_mmss(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _run_ticker(timer: BreakTimer, stop_event: threading.Event) -> None:
    """Background thread standing in for the QTimer a later step will add."""
    while not stop_event.is_set():
        time.sleep(TICK_INTERVAL_SECONDS)
        timer.tick()


def main() -> int:
    print(f"{APP_NAME} v{APP_VERSION} — Step 1 core demo (no GUI yet)\n")

    config_manager = ConfigManager()
    app_config: AppConfig = config_manager.load()
    timer = BreakTimer(app_config.timer)

    def on_state_changed(new_state: TimerState, old_state: TimerState) -> None:
        print(f"  [state] {old_state.name} -> {new_state.name}")

    def on_tick(remaining: int, state: TimerState) -> None:
        print(f"\r  [{state.name}] {_format_mmss(remaining)} remaining   ", end="", flush=True)

    def on_break_started(state: TimerState, duration: int) -> None:
        label = "long break" if state == TimerState.LONG_BREAK else "break"
        print(f"\n  >>> Time for a {label}! ({_format_mmss(duration)})")

    def on_session_completed(total: int) -> None:
        print(f"\n  >>> Work session #{total} complete.")

    timer.state_changed.connect(on_state_changed)
    timer.tick_signal.connect(on_tick)
    timer.break_started.connect(on_break_started)
    timer.session_completed.connect(on_session_completed)

    timer.start()

    stop_event = threading.Event()
    ticker_thread = threading.Thread(target=_run_ticker, args=(timer, stop_event), daemon=True)
    ticker_thread.start()

    print("Commands: [p]ause/resume  [b]reak now  [s]kip break  [q]uit\n")

    try:
        while True:
            command = input().strip().lower()
            if command == "p":
                if timer.state == TimerState.PAUSED:
                    timer.resume()
                else:
                    timer.pause()
            elif command == "b":
                timer.take_break_now()
            elif command == "s":
                timer.skip_break()
            elif command == "q":
                break
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        stop_event.set()
        config_manager.save(app_config)
        print("\nConfig saved. Goodbye.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
