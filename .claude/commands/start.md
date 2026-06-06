Launch the SwimEasy monitor in the background and tail the log.
Prevents macOS system sleep for the full duration via caffeinate.

Steps:
1. Check if the script is already running:
   `pgrep -f swimeasy_monitor.py`
   If a PID is found, report it and stop — do not start a second instance.

2. Confirm .env has real credentials (not placeholder values):
   `grep -c "YOUR_BOT_TOKEN_HERE" .env` should return 0.
   If placeholders are found, warn and stop.

3. Launch in background with sleep prevention:
   `nohup caffeinate -i .venv/bin/python swimeasy_monitor.py >> swimeasy_monitor.log 2>&1 &`
   Report the PID.

4. Tail the log for 15 seconds to confirm it started cleanly:
   `tail -f swimeasy_monitor.log`
   Look for the "SwimEasy Slot Monitor" header and first "Checking..." line.
   Report whether the first check returned "waitlist", "open", "not_found", or an error.

5. If the first check returns "not_found" or None, flag it immediately —
   do not leave a broken process running in the background.
