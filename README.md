# ⚔️ Paladin Break Guardian

A break-reminder desktop app for Linux (built and tested against Fedora KDE
Plasma / Wayland), inspired by Cat Gatekeeper.

## Status: Step 1 of N — Core foundation

This step builds the framework-independent core: configuration persistence
and the work/break timer state machine. **There is no tray icon or overlay
yet** — those are coming in later steps. What's here is fully functional
and tested on its own.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

You'll get a terminal-based demo of the real timer logic: it counts down a
work session, automatically starts a break, cycles a long break in every
`sessions_before_long_break` sessions, and responds to `p` (pause/resume),
`b` (break now), `s` (skip break), `q` (quit — saves config).

Config is read from and written to:

```
~/.config/paladin-guardian/config.json
```

## Run the tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Project layout so far

```
PaladinGuardian/
├── main.py                  # CLI wiring of ConfigManager + BreakTimer
├── config.py                # AppConfig / TimerConfig dataclasses (the schema)
├── constants.py              # App metadata, XDG paths, factory defaults
├── requirements.txt
├── core/
│   └── timer.py              # BreakTimer state machine (no Qt dependency)
├── utils/
│   ├── config_manager.py     # JSON load/save, atomic writes, fail-soft reads
│   ├── helpers.py            # Signal — lightweight Qt-style signal/slot
│   └── logger.py             # Rotating file + console logging
└── tests/
    └── test_timer.py
```

## Roadmap

- [x] Step 1 — Config system + timer state machine (this step)
- [ ] Step 2 — System tray (PySide6 `QSystemTrayIcon`) wired to `BreakTimer`
- [ ] Step 3 — Fullscreen break overlay (with the Wayland always-on-top
      caveat handled explicitly)
- [ ] Step 4 — Settings window
- [ ] Step 5 — Idle detection, statistics, sound, companions...
