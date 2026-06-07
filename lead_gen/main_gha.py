"""
GitHub Actions entry point — runs Naukri + Instahyre only.
Loads session state from environment variables (GitHub Secrets).
Emails the Excel report when done.

Called by .github/workflows/lead_gen.yml
"""

import os
import json
import base64
import datetime as dt
from typing import List

from playwright.sync_api import sync_playwright

from scraper_naukri import scrape_naukri
from scraper_instahyre import scrape_instahyre
from exporter import export_to_excel
from emailer import send_leads_email
from models import JobLead


def log(msg: str):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def load_state(env_var: str) -> dict | None:
    raw = os.environ.get(env_var, "")
    if not raw:
        log(f"WARNING: {env_var} secret not set — scraper will run without saved session.")
        return None
    try:
        return json.loads(base64.b64decode(raw).decode())
    except Exception as e:
        log(f"WARNING: Failed to decode {env_var}: {e}")
        return None


def run():
    log("=" * 55)
    log("GHA Lead Generation Run — Naukri + Instahyre")
    log("=" * 55)

    naukri_state    = load_state("NAUKRI_STATE")
    instahyre_state = load_state("INSTAHYRE_STATE")

    all_leads: List[JobLead] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ── Naukri ──
        try:
            ctx = browser.new_context(
                storage_state=naukri_state,
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = ctx.new_page()
            leads = scrape_naukri(page, log)
            all_leads.extend(leads)
            ctx.close()
        except Exception as e:
            log(f"[ERROR] Naukri: {e}")

        # ── Instahyre ──
        try:
            ctx = browser.new_context(
                storage_state=instahyre_state,
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = ctx.new_page()
            leads = scrape_instahyre(page, log)
            all_leads.extend(leads)
            ctx.close()
        except Exception as e:
            log(f"[ERROR] Instahyre: {e}")

        browser.close()

    log("=" * 55)
    if all_leads:
        # In GHA, save to /tmp (no Desktop)
        from config import OUTPUT_DIR
        import os
        output_dir = OUTPUT_DIR if OUTPUT_DIR.parent.exists() else __import__('pathlib').Path("/tmp/lead_generation_runs")
        output_dir.mkdir(parents=True, exist_ok=True)

        from exporter import export_to_excel
        output_path = export_to_excel(all_leads, output_dir=output_dir)
        log(f"✓ {len(all_leads)} leads exported → {output_path}")

        send_leads_email(
            excel_path=str(output_path),
            lead_count=len(all_leads),
            platforms=["Naukri", "Instahyre"],
            log=log,
        )
    else:
        log("No leads collected this run.")


if __name__ == "__main__":
    run()
