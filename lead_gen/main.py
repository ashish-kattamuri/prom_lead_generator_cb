"""
Lead Generation Tool — Phase 1
Scrapes LinkedIn, Naukri, and Instahyre for jobs posted in the last 24 hours
using the user's live Chrome session via Claude-in-Chrome MCP.

Run this from a Claude Code session by saying:
    "Run the lead generation scraper"

Claude Code injects the Chrome MCP tool callables automatically.
"""

import sys
import os
from datetime import datetime
from typing import List

from scraper_linkedin import scrape_linkedin
from scraper_naukri import scrape_naukri
from scraper_instahyre import scrape_instahyre
from exporter import export_to_excel
from models import JobLead


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run(mcp_navigate, mcp_javascript, mcp_get_page_text=None, mcp_find=None):
    """
    Main entry point called from a Claude Code session.
    mcp_navigate, mcp_javascript — Chrome MCP tool callables.
    """
    log("=" * 55)
    log("Lead Generation Run Started")
    log("=" * 55)

    all_leads: List[JobLead] = []

    # ── LinkedIn ──
    try:
        linkedin_leads = scrape_linkedin(
            mcp_navigate=mcp_navigate,
            mcp_get_page_text=mcp_get_page_text or (lambda: ""),
            mcp_find=mcp_find or (lambda **kw: []),
            mcp_javascript=mcp_javascript,
            log=log,
        )
        all_leads.extend(linkedin_leads)
    except Exception as e:
        log(f"[ERROR] LinkedIn scraper failed: {e}")

    # ── Naukri ──
    try:
        naukri_leads = scrape_naukri(
            mcp_navigate=mcp_navigate,
            mcp_javascript=mcp_javascript,
            log=log,
        )
        all_leads.extend(naukri_leads)
    except Exception as e:
        log(f"[ERROR] Naukri scraper failed: {e}")

    # ── Instahyre ──
    try:
        instahyre_leads = scrape_instahyre(
            mcp_navigate=mcp_navigate,
            mcp_javascript=mcp_javascript,
            log=log,
        )
        all_leads.extend(instahyre_leads)
    except Exception as e:
        log(f"[ERROR] Instahyre scraper failed: {e}")

    # ── Export ──
    log("=" * 55)
    if all_leads:
        output_path = export_to_excel(all_leads)
        log(f"✓ Exported {len(all_leads)} leads → {output_path}")
        return str(output_path)
    else:
        log("No leads collected this run.")
        return None
