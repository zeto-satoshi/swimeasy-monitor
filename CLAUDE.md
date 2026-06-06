# CLAUDE.md — swimeasy-monitor

## Project Context

Single-script Python monitor that watches the SwimEasy Wix Bookings page for an open
slot on **June 13, 2026 at 4:00 pm** (Trial class, Amsterdam location).
When the slot opens, it fires a Telegram push notification immediately.

- **Platform:** Wix Bookings (cross-origin iframe — no public API without a key)
- **Strategy:** Playwright headless Chromium scrapes the booking page directly
- **Scheduler:** `schedule` library polls every 5 minutes
- **Alert:** Telegram Bot API

**Target URL:**
```
https://www.swimeasy.nl/booking-calendar/trial-class-1?location=0de8ca4b-540c-4533-b0d3-eccdce9424e2
```

---

## Communication Rules

**Rule 01 — Language: English or Chinese**
I am a native Mandarin speaker. Explanations and plans can be in Chinese.
Code, variable names, and file content stay in English.

**Rule 02 — Start every reply with my name**
Begin each response with "Zhi，" — this helps me track context window health.

---

## Before Writing Any Code

**Rule 03 — Describe the plan first, wait for approval**
Before touching any file, write out:
- What you're going to do
- Which files will be affected
- Any risks or tradeoffs

Wait for "go ahead" before writing code.

**Rule 04 — Modern Python only**
Python 3.11+. No legacy fallbacks, no over-engineering for unasked edge cases.

---

## While Writing Code

**Rule 05 — After writing code, surface edge cases**
Call out what could break, list 2-3 test cases, and note assumptions baked in.

---

## When Things Break

**Rule 06 — Reproduce before fixing**
Write a minimal repro first, confirm it fails, then fix cleanly. No trial and error.

---

## Project Structure

```
swimeasy-monitor/
├── .env                    ← Telegram secrets — NEVER commit
├── .env.example            ← Template (safe to commit)
├── .gitignore
├── CLAUDE.md               ← this file
├── swimeasy_monitor.py     ← main script (Playwright + schedule + Telegram)
└── swimeasy_monitor.log    ← runtime log (gitignored)
```

---

## Running the Script

```bash
# One-time setup
pip install playwright schedule python-dotenv requests
playwright install chromium

# Dry run (single check)
python swimeasy_monitor.py

# Continuous monitoring (logs to swimeasy_monitor.log)
python swimeasy_monitor.py
```

---

## Key Script Internals

| Symbol | Purpose |
|--------|---------|
| `check_slot()` | Returns `"open"`, `"waitlist"`, `"not_found"`, or `None` |
| `run_check()` | Calls `check_slot()`, logs result, fires Telegram if open |
| `send_telegram()` | Posts alert via Bot API; no-ops if token not configured |
| `POLL_INTERVAL_MIN` | Default 5 min; adjust at top of script |
| `MAX_RUNTIME_HOURS` | Default 120 h (5 days); script self-stops after that |

## Page Behavior Notes

- Calendar loads on June 2026 by default, auto-selects nearest available date (Jun 11)
- Clicking "13" in the Sat column loads "Availability for Saturday, June 13"
- The 4pm slot shows `"Waitlist"` below the time when full
- Right panel shows `"Join Waitlist"` when full; `"Next"` when open
- The "13" cell is at roughly x=624 in the calendar grid (Sat column, rightmost)
- If `not_found` fires repeatedly: navigate with the `>` arrow to June 2026 first

---

## Timezone Reference

- my partner is in **Amsterdam (CEST, UTC+2)**
- Zhi is in **Michigan (EDT, UTC−4)**
- Telegram alert already shows both timezones

---

## Privacy Rules

- `.env` is gitignored. Never hardcode tokens.
- Never commit `swimeasy_monitor.log` (gitignored).

---

## Lessons Learned
_(Claude will append lessons here as the project evolves)_
