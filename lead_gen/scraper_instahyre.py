from typing import List, Optional
from playwright.sync_api import Page

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, is_within_24h
import time as _time
from config import INSTAHYRE_JOBS_URL, MAX_SCRAPE_MINUTES_INSTAHYRE, PAGE_LOAD_WAIT, SCROLL_PAUSE


def scrape_instahyre(page: Page, log=print) -> List[JobLead]:
    log("[Instahyre] Navigating to Instahyre (sorted by date)...")
    page.goto(INSTAHYRE_JOBS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(PAGE_LOAD_WAIT)

    job_urls = _collect_job_urls(page, log)
    log(f"[Instahyre] Found {len(job_urls)} job postings.")

    leads = []
    for idx, url in enumerate(job_urls, 1):
        try:
            lead = _extract_job(url, page, log)
            if lead:
                leads.append(lead)
                log(f"[Instahyre] ({idx}/{len(job_urls)}) {lead.company} — {lead.role}")
            else:
                log(f"[Instahyre] ({idx}/{len(job_urls)}) Skipped (>24h or incomplete).")
        except Exception as e:
            log(f"[Instahyre] ({idx}/{len(job_urls)}) Error: {e}")
        page.wait_for_timeout(2000)

    log(f"[Instahyre] Done. {len(leads)} leads.")
    return leads


def _collect_job_urls(page: Page, log) -> List[str]:
    urls = []
    deadline = _time.time() + MAX_SCRAPE_MINUTES_INSTAHYRE * 60
    prev_count = -1
    stall_rounds = 0

    while _time.time() < deadline:
        page.evaluate("window.scrollBy(0, 1500)")
        page.wait_for_timeout(SCROLL_PAUSE)

        new_urls = page.evaluate("""
            () => [...new Set(
                Array.from(document.querySelectorAll(
                    'a[href*="/job/"], a[href*="/jobs/"], ' +
                    '.job-card a, .opportunity-card a, [class*="job-title"] a'
                )).map(a => a.href).filter(h => h.includes('instahyre.com'))
            )]
        """)
        for u in new_urls:
            if u not in urls:
                urls.append(u)

        time_texts = page.evaluate("""
            () => Array.from(document.querySelectorAll(
                '[class*="posted"], [class*="date"], time, [class*="age"]'
            )).map(el => el.innerText.trim()).filter(t => t)
        """)
        if any(t and not is_within_24h(t) for t in time_texts):
            log(f"[Instahyre] Reached posts older than 24h. Stopping. ({len(urls)} URLs collected)")
            break

        if page.query_selector('[class*="no-result"], [class*="empty-state"]'):
            log(f"[Instahyre] End of results. ({len(urls)} URLs collected)")
            break

        if len(urls) == prev_count:
            stall_rounds += 1
            if stall_rounds >= 3:
                log(f"[Instahyre] No new jobs after 3 scrolls. Stopping. ({len(urls)} URLs collected)")
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

    role = txt("h1[class*='title'], h1[class*='designation']") or txt("h1")
    company = txt("[class*='company-name'], [class*='companyName'], .company a")
    location = txt("[class*='location'], [class*='city']")
    posted = txt("[class*='posted'], [class*='date'], time")
    description = txt("[class*='description'], [class*='job-detail'], .jd-content")

    if not role or not company:
        return None
    if posted and not is_within_24h(posted):
        return None

    return JobLead(
        platform="Instahyre",
        company=company,
        role=role,
        domain=infer_domain(role),
        industry=infer_industry(company, description),
        contact=extract_contact(description),
        job_url=url,
        date_posted=posted,
        location=location,
    )
