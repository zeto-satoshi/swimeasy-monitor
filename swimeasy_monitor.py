"""
swimeasy_monitor.py
--------------------
Monitors SwimEasy (Wix Bookings) for the June 13 2026 4pm Trial class slot.

Platform confirmed: Wix Bookings (cross-origin iframe — no public API without key)
Strategy: Playwright headless browser scrapes the booking page directly.

SETUP:
  pip install playwright schedule python-dotenv
  playwright install chromium

TELEGRAM BOT SETUP (5 min):
  1. Message @BotFather on Telegram → /newbot → copy token
  2. Message your bot once, then open:
     https://api.telegram.org/bot<TOKEN>/getUpdates
     copy the "id" field from "chat"
  3. Fill in .env file (copy from .env.example)
"""

import os
import time
import logging
import requests
import schedule
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

# Confirmed booking URL (Trial class, Amsterdam location)
BOOKING_URL = (
    "https://www.swimeasy.nl/booking-calendar/trial-class-1"
    "?location=0de8ca4b-540c-4533-b0d3-eccdce9424e2"
)

TARGET_DATE_TEXT = "June 13"      # text shown on calendar
TARGET_TIME_TEXT = "4:00 pm"      # text on the slot button
POLL_INTERVAL_MIN = 5
MAX_RUNTIME_HOURS = 168           # 7 days — covers Jun 6 → Jun 13

# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────

def send_telegram(msg: str) -> bool:
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(f"[TELEGRAM not configured] {msg}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        r.raise_for_status()
        logging.info("Telegram sent OK")
        return True
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return False


# ─────────────────────────────────────────────
# SLOT CHECK  (Playwright)
# ─────────────────────────────────────────────

def check_slot() -> str | None:
    """
    Returns:
      "open"      — slot is bookable (no Waitlist text)
      "waitlist"  — slot exists but is on waitlist
      "not_found" — slot/date not visible
      None        — page error
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            # Go to booking page — domcontentloaded avoids waiting on Wix's
            # perpetual background XHR traffic that blocks networkidle
            page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=60000)

            # Wait for the calendar grid to render before touching anything
            page.wait_for_selector("text='13'", timeout=30000)

            # ── Click June 13 ──
            # Sat column x is ~460 in a 1280-wide viewport; pick the rightmost
            # "13" cell in case other elements also contain that digit
            date_cell = None
            all_cells = page.locator("text='13'").all()
            rightmost_x = -1
            for cell in all_cells:
                bbox = cell.bounding_box()
                if bbox and bbox["x"] > rightmost_x:
                    rightmost_x = bbox["x"]
                    date_cell = cell

            if not date_cell:
                date_cell = page.locator("text='13'").first

            date_cell.click()
            # Wait for the header, then the slot buttons (they render separately)
            page.wait_for_selector("text=/June 13/", timeout=10000)
            page.wait_for_selector(f"text=/{TARGET_TIME_TEXT}/", timeout=10000)

            # ── Check availability area ──
            avail_area = page.locator("text=/June 13/")
            if avail_area.count() == 0:
                logging.warning("June 13 availability section not found after click")
                browser.close()
                return "not_found"

            # ── Find the 4:00 pm slot ──
            slot = page.locator(f"text=/{TARGET_TIME_TEXT}/")
            if slot.count() == 0:
                logging.warning(f"'{TARGET_TIME_TEXT}' slot not visible on June 13")
                browser.close()
                return "not_found"

            # Check parent/sibling text for "Waitlist"
            parent_html = slot.locator("..").inner_text(timeout=3000)
            browser.close()

            if "waitlist" in parent_html.lower():
                return "waitlist"
            else:
                return "open"

    except PWTimeout:
        logging.error("Playwright timed out")
        return None
    except Exception as e:
        logging.error(f"Playwright error: {e}")
        return None


# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────

start_time = datetime.now()
notification_sent = False


def run_check():
    global notification_sent

    now_ams = datetime.now(ZoneInfo("Europe/Amsterdam")).strftime("%Y-%m-%d %H:%M %Z")
    now_det = datetime.now(ZoneInfo("America/Detroit")).strftime("%H:%M %Z")
    logging.info(f"Checking... [{now_ams} | {now_det}]")

    status = check_slot()
    logging.info(f"  Status: {status}")

    if status == "open":
        if not notification_sent:
            msg = (
                "🏊‍♀️ <b>SwimEasy slot OPEN!</b>\n\n"
                f"📅 <b>June 13, 2026</b> at <b>4:00 pm</b>\n"
                f"📍 Trial class · Amsterdam\n"
                f"🕐 Checked: {now_ams}\n\n"
                "👉 Book NOW:\n"
                f"{BOOKING_URL}\n\n"
                "<i>(This alert fires once per opening)</i>"
            )
            send_telegram(msg)
            notification_sent = True
            logging.info("  ✅ OPEN — alert sent!")
        else:
            logging.info("  ✅ OPEN — already alerted")
    elif status == "waitlist":
        notification_sent = False
        logging.info("  ⏳ Still on waitlist")
    elif status == "not_found":
        logging.warning("  ❓ Slot/date not found — layout may have changed")
    else:
        logging.warning("  ❌ Page check failed (timeout or error)")

    # Stop after max runtime
    if (datetime.now() - start_time).total_seconds() / 3600 > MAX_RUNTIME_HOURS:
        logging.info(f"Reached {MAX_RUNTIME_HOURS}h limit. Stopping.")
        raise SystemExit(0)


if __name__ == "__main__":
    import sys

    check_only = "--check" in sys.argv

    # Only mirror to stdout when running interactively — avoids duplicate log
    # lines when nohup redirects stdout into the same file as FileHandler
    handlers: list[logging.Handler] = [logging.FileHandler("swimeasy_monitor.log")]
    if sys.stdout.isatty():
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )

    logging.info("=" * 55)
    logging.info("SwimEasy Slot Monitor")
    logging.info(f"Target: June 13 2026 · 4:00 pm · Trial class")
    logging.info(f"Platform: Wix Bookings (Playwright)")
    logging.info(f"Interval: every {POLL_INTERVAL_MIN} min")
    logging.info("=" * 55)

    if check_only:
        result = check_slot()
        logging.info(f"  --check result: {result}")
        print(result)
        sys.exit(0)

    run_check()
    schedule.every(POLL_INTERVAL_MIN).minutes.do(run_check)

    while True:
        schedule.run_pending()
        time.sleep(30)
