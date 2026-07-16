"""
main.py

Entry point for Paladin Break Guardian.

All actual wiring (QApplication, config, timer, tray) lives in app.py —
this file's only job is to be the thing `python main.py` runs, and to
translate a normal Ctrl+C in a terminal into a clean exit instead of a
stack trace.
"""

import sys

from app import run


if __name__ == "__main__":
    try:
        sys.exit(run())
    except KeyboardInterrupt:
        sys.exit(0)
