"""
Instahyre scraper — pure HTTP requests + BeautifulSoup.
Instahyre exposes job listings as JSON in a script tag / API endpoint.
"""

import requests
import json
from bs4 import BeautifulSoup
from typing import List, Callable
from datetime import datetime, timedelta, timezone

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, random_delay
from config import HTTP_HEADERS, MAX_PAGES_INSTAHYRE


INSTAHYRE_API = "https://www.instahyre.com/api/v1/opportunity/?format=json&ordering=-created&page={page}"


def scrape_instahyre(log: Callable = print) -> List[JobLead]:
    leads: List[JobLead] = []
    session = requests.Session()
    session.headers.update(HTTP_HEADERS)
    # Instahyre needs an Accept: application/json header for the API endpoint
    session.headers["Accept"] = "application/json"

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    for page in range(1, MAX_PAGES_INSTAHYRE + 1):
        url = INSTAHYRE_API.format(page=page)
        log(f"[Instahyre] Fetching page {page}...")

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log(f"[Instahyre] Failed on page {page}: {e}")
            break

        results = data.get("results", [])
        if not results:
            log(f"[Instahyre] No results on page {page}. Stopping.")
            break

        page_leads = 0
        stop = False
        for item in results:
            lead = _parse_instahyre_item(item, cutoff)
            if lead is None:
                # None means older than 24h — stop paginating
                stop = True
                break
            if lead:
                leads.append(lead)
                page_leads += 1

        log(f"[Instahyre] Page {page}: {page_leads} leads added, {len(leads)} total.")

        if stop:
            log("[Instahyre] Reached posts older than 24h. Stopping.")
            break

        random_delay(1.5, 2.5)

    log(f"[Instahyre] Done. {len(leads)} leads collected.")
    return leads


def _parse_instahyre_item(item: dict, cutoff: datetime) -> JobLead | None | bool:
    """
    Returns:
      JobLead  — valid lead within 24h
      False    — item within 24h but incomplete (skip, continue)
      None     — item older than 24h (stop pagination)
    """
    try:
        created_str = item.get("created", "")
        if created_str:
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            if created < cutoff:
                return None  # signal to stop

        company_data = item.get("employer", {}) or item.get("company", {})
        company = (
            company_data.get("name", "") or
            item.get("company_name", "") or
            item.get("employer_name", "")
        ).strip()

        role = (item.get("designation", "") or item.get("title", "")).strip()

        if not company or not role:
            return False

        location_list = item.get("locations", [])
        location = ", ".join(
            loc.get("name", loc) if isinstance(loc, dict) else str(loc)
            for loc in location_list
        )

        description = item.get("description", "") or item.get("job_description", "") or ""
        contact = extract_contact(description)

        job_id = item.get("id", "")
        job_url = f"https://www.instahyre.com/jobs/{job_id}/" if job_id else "https://www.instahyre.com"

        posted = created_str[:10] if created_str else ""

        return JobLead(
            platform="Instahyre",
            company=company,
            role=role,
            domain=infer_domain(role),
            industry=infer_industry(company, description),
            contact=contact,
            job_url=job_url,
            date_posted=posted,
            location=location,
        )
    except Exception:
        return False
