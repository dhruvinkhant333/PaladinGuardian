"""
tests/conftest.py

QApplication must exist before any QWidget/QSystemTrayIcon is
constructed, and Qt only tolerates ONE QApplication per process — so
this fixture is session-scoped, not per-test.

QT_QPA_PLATFORM=offscreen must be set BEFORE Qt initializes a display
connection, which is why it's set at import time here rather than
inside the fixture function body. This lets the full test suite run
in CI / this sandbox / any machine with no real X11 or Wayland session.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
