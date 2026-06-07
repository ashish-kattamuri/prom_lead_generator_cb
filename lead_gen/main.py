"""
Lead Generation Tool — Phase 1
Scrapes LinkedIn (via Chrome MCP), Naukri, and Instahyre for jobs posted
in the last 24 hours and exports a formatted Excel to ~/Desktop/lead_generation_runs/

Usage:
    python main.py                  # run once immediately
    python main.py --schedule       # run once at 9 AM daily (blocking)
"""

import sys
import argparse
import time as _time
from datetime import datetime

from scraper_naukri import scrape_naukri
from scraper_instahyre import scrape_instahyre
from exporter import export_to_excel
from models import JobLead


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_scrape_session():
    log("=" * 55)
    log("Lead Generation Run Started")
    log("=" * 55)

    all_leads: list[JobLead] = []

    # ── 1. LinkedIn (requires Chrome MCP — run via Claude Code session) ──
    log("LinkedIn scraping must be triggered via Claude Code (Chrome MCP).")
    log("Skipping LinkedIn in standalone mode. Use run_with_mcp() instead.")

    # ── 2. Naukri ──
    try:
        naukri_leads = scrape_naukri(log=log)
        all_leads.extend(naukri_leads)
    except Exception as e:
        log(f"[ERROR] Naukri scraper failed: {e}")

    # ── 3. Instahyre ──
    try:
        instahyre_leads = scrape_instahyre(log=log)
        all_leads.extend(instahyre_leads)
    except Exception as e:
        log(f"[ERROR] Instahyre scraper failed: {e}")

    # ── 4. Export ──
    if all_leads:
        output_path = export_to_excel(all_leads)
        log(f"✓ Exported {len(all_leads)} leads → {output_path}")
    else:
        log("No leads collected this run.")

    log("=" * 55)
    return all_leads


def run_with_mcp(linkedin_leads: list[JobLead]):
    """
    Called from a Claude Code session after LinkedIn MCP scraping.
    Merges LinkedIn leads with Naukri + Instahyre and exports.
    """
    all_leads: list[JobLead] = list(linkedin_leads)

    try:
        all_leads.extend(scrape_naukri(log=log))
    except Exception as e:
        log(f"[ERROR] Naukri: {e}")

    try:
        all_leads.extend(scrape_instahyre(log=log))
    except Exception as e:
        log(f"[ERROR] Instahyre: {e}")

    if all_leads:
        output_path = export_to_excel(all_leads)
        log(f"✓ Exported {len(all_leads)} leads → {output_path}")
        return str(output_path)
    else:
        log("No leads collected.")
        return None


def _wait_for_9am():
    """Block until 9:00 AM local time."""
    import datetime as dt
    now = dt.datetime.now()
    target = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now >= target:
        # Already past 9 AM today — schedule for tomorrow
        target = target + dt.timedelta(days=1)
    wait_seconds = (target - now).total_seconds()
    log(f"Scheduled mode: waiting {wait_seconds/3600:.1f}h until 9:00 AM.")
    _time.sleep(wait_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lead Generation Scraper")
    parser.add_argument("--schedule", action="store_true",
                        help="Run once at 9 AM daily (blocking loop)")
    args = parser.parse_args()

    if args.schedule:
        log("Scheduled mode active. Will run every day at 9:00 AM.")
        while True:
            _wait_for_9am()
            run_scrape_session()
    else:
        run_scrape_session()
