Run a single dry-run check of the SwimEasy slot monitor and report results.

Steps:
1. Verify .env exists and has TELEGRAM_TOKEN and TELEGRAM_CHAT_ID set
2. Run: `python3 -c "from swimeasy_monitor import check_slot; print(check_slot())"`
3. Report the returned status: "open", "waitlist", "not_found", or None (error)
4. If "not_found": investigate selector issues — check if calendar is on wrong month,
   suggest navigating to June 2026 first with the > arrow
5. If None: check for Playwright install issues or network errors
6. If "waitlist": confirm expected — slot is still full, monitoring is working
7. If "open": fire the alert immediately via send_telegram()
