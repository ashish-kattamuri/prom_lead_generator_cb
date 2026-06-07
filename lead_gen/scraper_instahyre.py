"""
Instahyre scraper — uses Chrome MCP with the user's live browser session.
Navigates to Instahyre job search sorted by date, extracts jobs from last 24h.
"""

from typing import List, Callable, Optional

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, random_delay, is_within_24h
from config import LINKEDIN_PAGE_DELAY, LINKEDIN_SCROLL_DELAY, MAX_PAGES_INSTAHYRE


INSTAHYRE_URL = "https://www.instahyre.com/search-jobs/?sort=date"


def scrape_instahyre(mcp_navigate, mcp_javascript, log: Callable = print) -> List[JobLead]:
    leads: List[JobLead] = []

    log("[Instahyre] Navigating to Instahyre jobs (sorted by date)...")
    mcp_navigate(url=INSTAHYRE_URL)
    random_delay(3, 5)

    job_urls = _collect_job_urls(mcp_javascript, log)
    log(f"[Instahyre] Found {len(job_urls)} job postings to process.")

    for idx, job_url in enumerate(job_urls, 1):
        try:
            lead = _extract_job_detail(job_url, mcp_navigate, mcp_javascript, log)
            if lead:
                leads.append(lead)
                log(f"[Instahyre] ({idx}/{len(job_urls)}) Scraped: {lead.company} — {lead.role}")
            else:
                log(f"[Instahyre] ({idx}/{len(job_urls)}) Skipped (older than 24h or incomplete).")
        except Exception as e:
            log(f"[Instahyre] ({idx}/{len(job_urls)}) Failed for {job_url}: {e}")
        random_delay(*LINKEDIN_PAGE_DELAY)

    log(f"[Instahyre] Done. {len(leads)} leads collected.")
    return leads


def _collect_job_urls(mcp_javascript, log) -> List[str]:
    all_urls = []
    stop_early = False

    for scroll_round in range(MAX_PAGES_INSTAHYRE):
        mcp_javascript(script="window.scrollBy(0, 1500);")
        random_delay(*LINKEDIN_SCROLL_DELAY)

        result = mcp_javascript(script="""
            const links = Array.from(document.querySelectorAll(
                'a[href*="/job/"], a[href*="/jobs/"], ' +
                '.job-card a, .opportunity-card a, [class*="job-title"] a'
            ));
            return [...new Set(
                links.map(a => a.href).filter(h => h.includes('instahyre.com'))
            )];
        """)

        # Check posted times to know if we've scrolled past 24h
        time_labels = mcp_javascript(script="""
            const els = Array.from(document.querySelectorAll(
                '[class*="posted"], [class*="date"], time, [class*="age"]'
            ));
            return els.map(el => el.innerText.trim()).filter(t => t.length > 0);
        """)

        if isinstance(result, list):
            for url in result:
                if url not in all_urls:
                    all_urls.append(url)

        if isinstance(time_labels, list):
            for label in time_labels:
                if label and not is_within_24h(label):
                    stop_early = True
                    break

        if stop_early:
            log(f"[Instahyre] Reached posts older than 24h at scroll {scroll_round + 1}.")
            break

        end = mcp_javascript(script="""
            const el = document.querySelector('[class*="no-result"], [class*="empty-state"]');
            return el ? el.innerText : null;
        """)
        if end:
            log("[Instahyre] End of results.")
            break

    return list(dict.fromkeys(all_urls))


def _extract_job_detail(job_url: str, mcp_navigate, mcp_javascript, log) -> Optional[JobLead]:
    mcp_navigate(url=job_url)
    random_delay(*LINKEDIN_PAGE_DELAY)

    data = mcp_javascript(script="""
        function getText(sel) {
            const el = document.querySelector(sel);
            return el ? el.innerText.trim() : '';
        }

        const role = getText('h1[class*="title"], h1[class*="designation"], h1') || '';
        const company = getText('[class*="company-name"], [class*="companyName"], .company a') || '';
        const location = getText('[class*="location"], [class*="city"]') || '';
        const posted = getText('[class*="posted"], [class*="date"], time') || '';
        const description = getText('[class*="description"], [class*="job-detail"], .jd-content') || '';

        return { role, company, location, posted, description };
    """)

    if not isinstance(data, dict):
        return None

    company = data.get('company', '').strip()
    role = data.get('role', '').strip()
    posted = data.get('posted', '').strip()
    description = data.get('description', '').strip()

    if not company or not role:
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
        job_url=job_url,
        date_posted=posted,
        location=data.get('location', ''),
    )
