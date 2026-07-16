"""
utils/helpers.py

Small, generic utilities shared across modules that don't belong to any
one layer.

Signal is the one worth explaining: it's a minimal, dependency-free
stand-in for Qt's signal/slot pattern (`.connect(callback)`, `.emit(*args)`).

WHY not just import PySide6.QtCore.Signal here and be done with it:
Signal is used by core/timer.py, and core/ is the business-logic layer
that later steps (tests, a CLI mode, a future non-Qt frontend) need to
use WITHOUT dragging in a Qt application instance. Real Qt Signals only
work on QObject subclasses inside a running QApplication event loop,
which would force every unit test to boot a GUI framework just to check
"does pausing the timer stop the countdown." This tiny class gives the
same ergonomic API with zero framework coupling. When ui/ wires the
real Qt tray/overlay to core/timer.py in a later step, connecting a
Qt slot to one of these Signals is a one-line adapter, not a rewrite.
"""

from typing import Callable


class Signal:
    """A minimal observer-pattern signal: connect callables, emit to all of them."""

    def __init__(self) -> None:
        self._subscribers: list[Callable] = []

    def connect(self, callback: Callable) -> None:
        self._subscribers.append(callback)

    def disconnect(self, callback: Callable) -> None:
        self._subscribers.remove(callback)

    def emit(self, *args, **kwargs) -> None:
        for callback in list(self._subscribers):
            callback(*args, **kwargs)
