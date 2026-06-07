"""
Local LinkedIn-only runner.
Runs at 10 AM daily via launchd, or manually:

    python3 main_linkedin.py

Output saved to ~/Desktop/lead_generation_runs/
"""

import datetime as dt
from typing import List

from playwright.sync_api import sync_playwright

from scraper_linkedin import scrape_linkedin
from exporter import export_to_excel
from models import JobLead
from config import SESSION_DIR, HEADLESS


def log(msg: str):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run():
    log("=" * 55)
    log("LinkedIn Lead Generation Run")
    log("=" * 55)

    if not SESSION_DIR.exists():
        log("ERROR: No saved session. Run setup_session.py first.")
        return

    leads: List[JobLead] = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=HEADLESS,
            args=["--start-maximized"],
            viewport=None,
        )
        page = browser.new_page()

        try:
            leads = scrape_linkedin(page, log)
        except Exception as e:
            log(f"[ERROR] LinkedIn: {e}")

        browser.close()

    log("=" * 55)
    if leads:
        output_path = export_to_excel(leads)
        log(f"✓ {len(leads)} LinkedIn leads → {output_path}")
    else:
        log("No LinkedIn leads collected.")


if __name__ == "__main__":
    run()
