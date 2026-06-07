"""
Naukri.com scraper — pure HTTP requests + BeautifulSoup.
Scrapes jobs posted in the last 1 day (Naukri's ?jobAge=1 filter).
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Callable
import time
import random

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, random_delay
from config import HTTP_HEADERS, MAX_PAGES_NAUKRI


NAUKRI_BASE = "https://www.naukri.com"
NAUKRI_SEARCH = (
    "https://www.naukri.com/jobs-in-india"
    "?jobAge=1"       # posted in last 1 day
    "&pageNo={page}"
)


def scrape_naukri(log: Callable = print) -> List[JobLead]:
    leads: List[JobLead] = []
    session = requests.Session()
    session.headers.update(HTTP_HEADERS)

    for page in range(1, MAX_PAGES_NAUKRI + 1):
        url = NAUKRI_SEARCH.format(page=page)
        log(f"[Naukri] Scraping page {page}...")

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            log(f"[Naukri] Request failed on page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        job_cards = soup.select("article.jobTuple, div.jobTupleHeader, div[class*='srp-jobtuple']")

        if not job_cards:
            log(f"[Naukri] No job cards found on page {page}. Stopping.")
            break

        for card in job_cards:
            lead = _parse_naukri_card(card)
            if lead:
                leads.append(lead)

        log(f"[Naukri] Page {page}: {len(job_cards)} cards, {len(leads)} total leads so far.")
        random_delay(1.5, 3.0)

    log(f"[Naukri] Done. {len(leads)} leads collected.")
    return leads


def _parse_naukri_card(card) -> JobLead | None:
    try:
        # Job title + URL
        title_el = card.select_one("a.title, a[class*='title'], a[href*='naukri.com']")
        role = title_el.get_text(strip=True) if title_el else ""
        job_url = title_el["href"] if title_el and title_el.get("href") else ""
        if not job_url.startswith("http"):
            job_url = NAUKRI_BASE + job_url

        # Company
        company_el = card.select_one("a.subTitle, a[class*='comp-name'], span[class*='comp-name']")
        company = company_el.get_text(strip=True) if company_el else ""

        # Location
        location_el = card.select_one("span[class*='location'], li[class*='location']")
        location = location_el.get_text(strip=True) if location_el else ""

        # Posted time
        posted_el = card.select_one("span[class*='date'], span.freshness, span[class*='age']")
        posted = posted_el.get_text(strip=True) if posted_el else ""

        # Contact — rarely in card but try description snippet
        desc_el = card.select_one("span[class*='job-description'], div[class*='job-desc']")
        description = desc_el.get_text(" ", strip=True) if desc_el else ""
        contact = extract_contact(description)

        if not role or not company:
            return None

        return JobLead(
            platform="Naukri",
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
        return None
