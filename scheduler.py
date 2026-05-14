"""
scheduler.py — Run the agent on a cron schedule using APScheduler.

Usage:
    python scheduler.py

The agent will run once immediately, then every 24 hours at the configured time.
Adjust CRON_HOUR / CRON_MINUTE to change the schedule.
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from agent.trigger_logic import run_agent
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CRON_HOUR   = 9     # 9 AM
CRON_MINUTE = 0

def job():
    log.info("Scheduled run starting…")
    summary = run_agent(dry_run_override=(config.EMAIL_MODE == "dry_run"))
    log.info(f"Run complete: {summary}")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(
        job,
        trigger=CronTrigger(hour=CRON_HOUR, minute=CRON_MINUTE),
        id="finance_agent",
        name="Finance Follow-Up Agent",
        replace_existing=True,
    )
    log.info(f"Scheduler started — running daily at {CRON_HOUR:02d}:{CRON_MINUTE:02d}")
    log.info("Press Ctrl+C to exit.")

    # Run once immediately on start
    job()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")
