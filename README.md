# SwimEasy Slot Monitor

A single-file Python agent that watches a Wix Bookings page for a specific swim class slot to open up, then fires a Telegram push notification the moment it does.

Built and operated entirely with Claude Code as an agentic workflow project.

---

## What It Does

Polls the SwimEasy booking page every 5 minutes using a headless Chromium browser. When the target slot changes from "Waitlist" to bookable, it sends a Telegram alert immediately with a direct booking link.

**Target:** June 13, 2026 · 4:00 pm · Trial class · Amsterdam

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  swimeasy_monitor.py                │
│                                                     │
│  ┌──────────┐    ┌──────────────┐   ┌───────────┐  │
│  │ schedule │───▶│ check_slot() │──▶│run_check()│  │
│  │ (5 min)  │    │  Playwright  │   │           │  │
│  └──────────┘    │  headless    │   │  "open"?  │  │
│                  │  Chromium    │   └─────┬─────┘  │
│                  └──────────────┘         │yes      │
│                                           ▼         │
│                                   send_telegram()   │
│                                   Telegram Bot API  │
└─────────────────────────────────────────────────────┘
         ▲
         │ caffeinate -i (prevents macOS sleep)
         │ nohup (survives terminal close)
```

### Why each piece exists

| Component | Why it's needed |
|-----------|----------------|
| **Playwright** | SwimEasy runs on Wix Bookings — the calendar is rendered by JavaScript inside a widget. No public API exists, so a real browser is required to scrape it. `requests` + `BeautifulSoup` would see an empty page. |
| **Headless Chromium** | Runs without a visible window. Same rendering as real Chrome. Playwright manages the browser lifecycle. |
| **`domcontentloaded` (not `networkidle`)** | Wix pages stream background XHR requests indefinitely. Waiting for `networkidle` causes a 40s+ timeout. `domcontentloaded` fires when the HTML is parsed; we then wait for specific DOM elements to confirm the widget has rendered. |
| **Two-phase wait after click** | After clicking June 13, the availability header (`"Availability for Saturday, June 13"`) loads first, then the slot buttons (`"4:00 pm"`) render separately ~1 second later. A single wait misses the second render. |
| **`schedule` library** | Lightweight cron-like scheduler. Runs `run_check()` every 5 minutes inside a `while True` loop with 30-second sleep ticks. |
| **`notification_sent` flag** | Prevents duplicate alerts. Resets to `False` if the slot goes back to waitlist — so if it opens, fills, then opens again, a fresh alert fires. |
| **Telegram Bot API** | Push notification to phone. Zero-infrastructure: no app, no server, just an HTTP POST to `api.telegram.org`. |
| **`caffeinate -i`** | Prevents macOS idle system sleep. The `-i` flag holds a "user is active" assertion for the lifetime of the wrapped process. Display sleep still works (saves power). |
| **`nohup`** | Detaches the process from the terminal session. Closing the terminal or SSH disconnect doesn't kill it. |
| **`MAX_RUNTIME_HOURS = 168`** | Safety exit after 7 days so the script doesn't run forever if forgotten. Covers the full Jun 6 → Jun 13 window. |

---

## Page Scraping Logic (step by step)

```
1. Navigate to booking URL
   wait_until="domcontentloaded" + timeout=60s

2. Wait for calendar to render
   page.wait_for_selector("text='13'", timeout=30s)

3. Click the June 13 cell
   → Find all elements matching text='13'
   → Pick the one with the rightmost x coordinate (= Sat column)
   → click()

4. Wait for availability panel (two-phase)
   → wait_for_selector("text=/June 13/")    ← header loads first
   → wait_for_selector("text=/4:00 pm/")   ← slot buttons load second

5. Check for "Waitlist" in slot's parent element
   → parent_html = slot.locator("..").inner_text()
   → "waitlist" in parent_html.lower() → return "waitlist"
   → else → return "open"
```

**Returns:**
- `"open"` — slot is bookable → triggers Telegram alert
- `"waitlist"` — slot exists but full → continue polling, reset notification flag
- `"not_found"` — date or time not visible → logs warning, likely layout change
- `None` — Playwright error or timeout → logs error, try again next cycle

---

## Agentic Workflow Layer (Claude Code)

This project uses Claude Code as an AI engineer, not just an editor. The `.claude/` folder configures it:

```
.claude/
├── settings.local.json     ← permission allowlist + deny list
└── commands/
    ├── dryrun.md           ← /dryrun  single check + diagnosis
    ├── start.md            ← /start   launch with caffeinate, verify clean start
    ├── status.md           ← /status  health check + countdown to June 13
    ├── commit.md           ← /commit  safe git commit (never stages .env)
    └── review.md           ← /review  code quality + selector audit
```

**Key pattern — `/loop 5m /dryrun`:**
Instead of just running the script and walking away, you can have Claude Code poll the slot every 5 minutes and react intelligently — surfacing errors, diagnosing `"not_found"`, and alerting if the process dies.

---

## How to Run

```bash
# One-time setup
pip install playwright schedule python-dotenv requests
playwright install chromium
cp .env.example .env        # fill in TELEGRAM_TOKEN and TELEGRAM_CHAT_ID

# Verify everything works (expect "waitlist")
python swimeasy_monitor.py --check   # or use /dryrun in Claude Code

# Start 7-day continuous monitor
nohup caffeinate -i .venv/bin/python swimeasy_monitor.py >> swimeasy_monitor.log 2>&1 &

# Check it's alive
pgrep -f swimeasy_monitor.py
tail -f swimeasy_monitor.log

# Stop it
pkill -f swimeasy_monitor.py
```

---

## Lessons Learned Building This

**1. Wix = JavaScript-rendered, no public API**
The booking page is a Wix widget. `curl` returns a shell with no slot data. The only reliable approach is a real browser.

**2. `networkidle` is a trap for Wix**
Wix keeps background analytics and chat requests alive indefinitely. `networkidle` never fires. Always use `domcontentloaded` + explicit element waits for SPAs.

**3. Selector timing matters more than sleep timers**
Fixed `time.sleep(2.5)` after a click is fragile — sometimes too short, sometimes wasteful. Chaining `wait_for_selector()` calls is deterministic: it fires exactly when the element appears.

**4. Text selectors: exact vs. regex**
Playwright's `text='June 13'` matches elements whose *entire* text is exactly `"June 13"`. The availability header says `"Availability for Saturday, June 13"` — so it never matched. `text=/June 13/` (regex) matches any element *containing* that substring.

**5. Bounding box beats hardcoded coordinates**
The original selector assumed the "13" cell was at x>550 based on a screenshot. The actual x was 460 — wrong on day one. Picking the rightmost bounding box dynamically is robust to layout changes.

---

## File Structure

```
swimeasy-monitor/
├── .env                    ← Telegram secrets (gitignored, never commit)
├── .env.example            ← Template with placeholder values
├── .gitignore
├── .claude/
│   ├── settings.local.json ← Claude Code permissions
│   └── commands/           ← Custom slash commands
├── CLAUDE.md               ← Instructions for Claude Code agent
├── README.md               ← This file
└── swimeasy_monitor.py     ← The entire monitor (222 lines)
```
