Check whether the SwimEasy monitor is alive and report its current state.

Steps:
1. Check if the process is running:
   `pgrep -f swimeasy_monitor.py`
   Report PID if found; report "not running" if not.

2. If running, show how long it has been alive:
   `ps -o etime= -p <PID>`

3. Show the last 20 lines of the log:
   `tail -20 swimeasy_monitor.log`
   Summarize: last check time, last status ("waitlist" / "open" / "not_found" / error),
   and whether a Telegram alert has been sent.

4. Report how much time remains until June 13, 2026 at 4:00 pm CEST
   (the target slot). Calculate from current time.

5. If the process is NOT running:
   - Check if the log shows a clean exit (MAX_RUNTIME_HOURS reached) or a crash.
   - Recommend running /start if it crashed unexpectedly.
