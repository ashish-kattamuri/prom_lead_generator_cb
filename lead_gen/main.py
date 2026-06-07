"""
Lead Generation Tool — Phase 1
Scrapes LinkedIn, Naukri, and Instahyre for jobs posted in the last 24 hours.
Uses Playwright with a persistent browser session (stays logged in).

Usage:
    python3 main.py                 # run once immediately
    python3 main.py --schedule      # run daily at 9 AM (blocking)

First-time setup (run once to log in):
    python3 setup_session.py
"""

import argparse
import time as _time
import datetime as dt
from typing import List

from playwright.sync_api import sync_playwright

from scraper_linkedin import scrape_linkedin
from scraper_naukri import scrape_naukri
from scraper_instahyre import scrape_instahyre
from exporter import export_to_excel
from models import JobLead
from config import SESSION_DIR, HEADLESS


def log(msg: str):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_once():
    log("=" * 55)
    log("Lead Generation Run Started")
    log("=" * 55)

    if not SESSION_DIR.exists():
        log("ERROR: No saved session found. Run setup_session.py first.")
        return None

    all_leads: List[JobLead] = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=HEADLESS,
            args=["--start-maximized"],
            viewport=None,
        )
        page = browser.new_page()

        try:
            all_leads.extend(scrape_linkedin(page, log))
        except Exception as e:
            log(f"[ERROR] LinkedIn: {e}")

        try:
            all_leads.extend(scrape_naukri(page, log))
        except Exception as e:
            log(f"[ERROR] Naukri: {e}")

        try:
            all_leads.extend(scrape_instahyre(page, log))
        except Exception as e:
            log(f"[ERROR] Instahyre: {e}")

        browser.close()

    log("=" * 55)
    if all_leads:
        output_path = export_to_excel(all_leads)
        log(f"✓ {len(all_leads)} leads exported → {output_path}")
        return str(output_path)
    else:
        log("No leads collected this run.")
        return None


def _wait_until_9am():
    now = dt.datetime.now()
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target:
        target += dt.timedelta(days=1)
    secs = (target - now).total_seconds()
    log(f"Scheduled mode: next run in {secs/3600:.1f}h at 09:00.")
    _time.sleep(secs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", action="store_true",
                        help="Run daily at 9 AM (blocking loop)")
    args = parser.parse_args()

    if args.schedule:
        log("Scheduled mode active — runs every day at 09:00.")
        while True:
            _wait_until_9am()
            run_once()
    else:
        run_once()
