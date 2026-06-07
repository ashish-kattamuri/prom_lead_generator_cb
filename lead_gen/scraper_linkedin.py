import re
from typing import List, Optional
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import Page

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, is_within_24h
import time as _time
from config import LINKEDIN_JOBS_URL, MAX_SCRAPE_MINUTES_LINKEDIN, PAGE_LOAD_WAIT, SCROLL_PAUSE


def scrape_linkedin(page: Page, log=print) -> List[JobLead]:
    log("[LinkedIn] Navigating to Jobs feed (past 24h, most recent)...")
    page.goto(LINKEDIN_JOBS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(PAGE_LOAD_WAIT)

    job_urls = _collect_job_urls(page, log)
    log(f"[LinkedIn] Found {len(job_urls)} job postings.")

    leads = []
    for idx, url in enumerate(job_urls, 1):
        try:
            lead = _extract_job(url, page, log)
            if lead:
                leads.append(lead)
                log(f"[LinkedIn] ({idx}/{len(job_urls)}) {lead.company} — {lead.role}")
            else:
                log(f"[LinkedIn] ({idx}/{len(job_urls)}) Skipped.")
        except Exception as e:
            log(f"[LinkedIn] ({idx}/{len(job_urls)}) Error: {e}")
        page.wait_for_timeout(2000)

    log(f"[LinkedIn] Done. {len(leads)} leads.")
    return leads


def _normalise_linkedin_url(url: str) -> Optional[str]:
    """
    Convert any LinkedIn job URL variant to the canonical /jobs/view/{id}/ form.

    Handles:
      - https://www.linkedin.com/jobs/view/3767702526/          → unchanged
      - https://www.linkedin.com/jobs/search/?currentJobId=XYZ  → /jobs/view/XYZ/
      - Any URL with a numeric job ID in the path               → /jobs/view/{id}/
    """
    try:
        parsed = urlparse(url)
        # Already a clean /jobs/view/ URL
        view_match = re.search(r'/jobs/view/(\d+)', parsed.path)
        if view_match:
            return f"https://www.linkedin.com/jobs/view/{view_match.group(1)}/"

        # Search page with currentJobId param
        qs = parse_qs(parsed.query)
        job_id = qs.get("currentJobId", [None])[0]
        if job_id and job_id.isdigit():
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
    except Exception:
        pass
    return None


def _collect_job_urls(page: Page, log) -> List[str]:
    urls = []
    deadline = _time.time() + MAX_SCRAPE_MINUTES_LINKEDIN * 60
    prev_count = -1
    stall_rounds = 0

    while _time.time() < deadline:
        page.evaluate("window.scrollBy(0, 1200)")
        page.wait_for_timeout(SCROLL_PAUSE)

        raw_urls = page.evaluate("""
            () => [...new Set(
                Array.from(document.querySelectorAll(
                    'a[href*="/jobs/view/"], a[href*="currentJobId"]'
                )).map(a => a.href)
            )]
        """)
        for raw in raw_urls:
            clean = _normalise_linkedin_url(raw)
            if clean and clean not in urls:
                urls.append(clean)

        # Stop if we've scrolled past the 24h window
        time_texts = page.evaluate("""
            () => Array.from(document.querySelectorAll(
                '.job-card-container__listed-status, time, [class*="posted"]'
            )).map(el => el.innerText.trim()).filter(t => t)
        """)
        if any(t and not is_within_24h(t) for t in time_texts):
            log(f"[LinkedIn] Reached posts older than 24h. Stopping. ({len(urls)} URLs collected)")
            break

        # Stop if LinkedIn shows end-of-results
        if page.query_selector(".jobs-search-no-results, .artdeco-empty-state__title"):
            log(f"[LinkedIn] End of results. ({len(urls)} URLs collected)")
            break

        # Stop if page hasn't grown in 3 consecutive scrolls (truly no more content)
        if len(urls) == prev_count:
            stall_rounds += 1
            if stall_rounds >= 3:
                log(f"[LinkedIn] No new jobs after 3 scrolls. Stopping. ({len(urls)} URLs collected)")
                break
        else:
            stall_rounds = 0
        prev_count = len(urls)

    return urls


def _extract_job(url: str, page: Page, log) -> Optional[JobLead]:
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(PAGE_LOAD_WAIT)

    def txt(selector: str) -> str:
        el = page.query_selector(selector)
        return el.inner_text().strip() if el else ""

    role = (txt(".job-details-jobs-unified-top-card__job-title") or
            txt(".topcard__title") or txt("h1"))
    company = (txt(".job-details-jobs-unified-top-card__company-name") or
               txt(".topcard__org-name-link") or txt("[class*='company-name']"))
    location = (txt(".job-details-jobs-unified-top-card__bullet") or
                txt(".topcard__flavor--bullet"))
    posted = (txt(".job-details-jobs-unified-top-card__posted-date") or
              txt("span[class*='posted']") or txt("time"))
    description = (txt(".jobs-description__content") or txt(".description__text") or "")
    poster_name = txt(".hirer-card__hirer-information .artdeco-entity-lockup__title")
    poster_url = ""
    poster_el = page.query_selector(".hirer-card__hirer-information a")
    if poster_el:
        poster_url = poster_el.get_attribute("href") or ""

    if not role or not company:
        return None
    if posted and not is_within_24h(posted):
        return None

    return JobLead(
        platform="LinkedIn",
        company=company,
        role=role,
        domain=infer_domain(role),
        industry=infer_industry(company, description),
        contact=extract_contact(description),
        job_url=url,
        date_posted=posted,
        location=location,
        poster_name=poster_name,
        poster_profile_url=poster_url,
    )
