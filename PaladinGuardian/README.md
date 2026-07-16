# ⚔️ Paladin Break Guardian

A break-reminder desktop app for Linux (built and tested against Fedora KDE
Plasma / Wayland), inspired by Cat Gatekeeper.

## Status: Step 2 of N — System tray

The app is now a real (if minimal) system tray application: a tray icon
with Resume/Pause/Skip/Take Break Now/Settings/Statistics/About/Quit,
wired directly to the timer built in Step 1. **There is no break overlay
yet** — that's the next step.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

This launches into your system tray (no window, no terminal UI) and starts
a work session immediately using your configured duration. Right-click the
tray icon for the menu. Quit from there to save config and exit cleanly.

Config is read from and written to:

```
~/.config/paladin-guardian/config.json
```

Settings and Statistics menu items currently show a "coming in a later
step" placeholder — they're wired up, just not built yet.

## Run the tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Project layout so far

```
PaladinGuardian/
├── main.py                  # Thin entry point — just calls app.run()
├── app.py                   # QApplication bootstrap: wires config+timer+tray
├── config.py                # AppConfig / TimerConfig dataclasses (the schema)
├── constants.py              # App metadata, XDG paths, factory defaults
├── requirements.txt
├── core/
│   ├── timer.py              # BreakTimer state machine (no Qt dependency)
│   └── tray.py                # QSystemTrayIcon + menu, wired to BreakTimer
├── utils/
│   ├── config_manager.py     # JSON load/save, atomic writes, fail-soft reads
│   ├── helpers.py            # Signal — lightweight Qt-style signal/slot
│   └── logger.py             # Rotating file + console logging
└── tests/
    ├── conftest.py            # Session-scoped offscreen QApplication fixture
    ├── test_timer.py
    └── test_tray.py
```

## Roadmap

- [x] Step 1 — Config system + timer state machine
- [x] Step 2 — System tray (PySide6 `QSystemTrayIcon`) wired to `BreakTimer` (this step)
- [ ] Step 3 — Fullscreen break overlay (with the Wayland always-on-top
      caveat handled explicitly)
- [ ] Step 4 — Settings window
- [ ] Step 5 — Idle detection, statistics, sound, companions...
