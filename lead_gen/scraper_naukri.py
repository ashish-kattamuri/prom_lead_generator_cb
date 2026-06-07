from typing import List, Optional
from playwright.sync_api import Page

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, is_within_24h
import time as _time
from config import NAUKRI_JOBS_URL, MAX_SCRAPE_MINUTES_NAUKRI, PAGE_LOAD_WAIT, SCROLL_PAUSE


def scrape_naukri(page: Page, log=print) -> List[JobLead]:
    log("[Naukri] Navigating to Naukri (last 1 day, most recent)...")
    page.goto(NAUKRI_JOBS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(PAGE_LOAD_WAIT + 2000)  # Naukri is JS-heavy

    job_urls = _collect_job_urls(page, log)
    log(f"[Naukri] Found {len(job_urls)} job postings.")

    leads = []
    for idx, url in enumerate(job_urls, 1):
        try:
            lead = _extract_job(url, page, log)
            if lead:
                leads.append(lead)
                log(f"[Naukri] ({idx}/{len(job_urls)}) {lead.company} — {lead.role}")
            else:
                log(f"[Naukri] ({idx}/{len(job_urls)}) Skipped.")
        except Exception as e:
            log(f"[Naukri] ({idx}/{len(job_urls)}) Error: {e}")
        page.wait_for_timeout(2000)

    log(f"[Naukri] Done. {len(leads)} leads.")
    return leads


def _collect_job_urls(page: Page, log) -> List[str]:
    urls = []
    deadline = _time.time() + MAX_SCRAPE_MINUTES_NAUKRI * 60
    prev_count = -1
    stall_rounds = 0

    while _time.time() < deadline:
        page.evaluate("window.scrollBy(0, 1500)")
        page.wait_for_timeout(SCROLL_PAUSE)

        new_urls = page.evaluate("""
            () => [...new Set(
                Array.from(document.querySelectorAll(
                    'a.title, a[class*="title"][href*="naukri.com"], ' +
                    'article a[href*="-jobs-"], a[href*="job-listings"]'
                )).map(a => a.href).filter(h =>
                    h.includes('naukri.com') &&
                    (h.includes('-jobs-') || h.includes('job-listings'))
                )
            )]
        """)
        for u in new_urls:
            if u not in urls:
                urls.append(u)

        # Click "Load more" if present
        load_more = page.query_selector('button[class*="load-more"], a[class*="loadMore"]')
        if load_more:
            load_more.click()
            page.wait_for_timeout(SCROLL_PAUSE)

        if page.query_selector('.no-jobs, [class*="no-result"], [class*="noResult"]'):
            log(f"[Naukri] End of results. ({len(urls)} URLs collected)")
            break

        if len(urls) == prev_count:
            stall_rounds += 1
            if stall_rounds >= 3:
                log(f"[Naukri] No new jobs after 3 scrolls. Stopping. ({len(urls)} URLs collected)")
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

    role = txt("h1.jd-header-title, h1[class*='title'], .jd-header h1") or txt("h1")
    company = (txt("a.jd-header-comp-name, [class*='comp-name'] a") or
               txt("[class*='companyName']"))
    location = txt(".location span, [class*='location'] span, .loc span")
    posted = txt(".posted-date, [class*='posted'], .date-text")
    description = txt("#job_description, .job-desc, [class*='job-description']")
    recruiter = txt(".recruiterDetails, [class*='recruiter']")
    full_text = description + " " + recruiter

    if not role or not company:
        return None

    return JobLead(
        platform="Naukri",
        company=company,
        role=role,
        domain=infer_domain(role),
        industry=infer_industry(company, full_text),
        contact=extract_contact(full_text),
        job_url=url,
        date_posted=posted,
        location=location,
    )
