"""
Naukri scraper — uses Chrome MCP with the user's live browser session.
Navigates to Naukri jobs filtered to last 1 day, extracts job cards.
"""

from typing import List, Callable, Optional

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, random_delay, is_within_24h
from config import LINKEDIN_PAGE_DELAY, LINKEDIN_SCROLL_DELAY, MAX_PAGES_NAUKRI


NAUKRI_URL = "https://www.naukri.com/jobs-in-india?jobAge=1&sortType=1"  # sortType=1 = most recent


def scrape_naukri(mcp_navigate, mcp_javascript, log: Callable = print) -> List[JobLead]:
    leads: List[JobLead] = []

    log("[Naukri] Navigating to Naukri jobs (last 1 day, most recent)...")
    mcp_navigate(url=NAUKRI_URL)
    random_delay(3, 5)  # Naukri is JS-heavy, give it time to render

    job_urls = _collect_job_urls(mcp_javascript, log)
    log(f"[Naukri] Found {len(job_urls)} job postings to process.")

    for idx, job_url in enumerate(job_urls, 1):
        try:
            lead = _extract_job_detail(job_url, mcp_navigate, mcp_javascript, log)
            if lead:
                leads.append(lead)
                log(f"[Naukri] ({idx}/{len(job_urls)}) Scraped: {lead.company} — {lead.role}")
        except Exception as e:
            log(f"[Naukri] ({idx}/{len(job_urls)}) Failed for {job_url}: {e}")
        random_delay(*LINKEDIN_PAGE_DELAY)

    log(f"[Naukri] Done. {len(leads)} leads collected.")
    return leads


def _collect_job_urls(mcp_javascript, log) -> List[str]:
    all_urls = []

    for scroll_round in range(MAX_PAGES_NAUKRI):
        mcp_javascript(script="window.scrollBy(0, 1500);")
        random_delay(*LINKEDIN_SCROLL_DELAY)

        result = mcp_javascript(script="""
            const links = Array.from(document.querySelectorAll(
                'a.title, a[class*="title"][href*="naukri.com"], ' +
                '.jobTupleHeader a, article a[href*="-jobs-"], ' +
                'a[href*="naukri.com/job-listings"]'
            ));
            return [...new Set(links.map(a => a.href).filter(h =>
                h.includes('naukri.com') && (h.includes('-jobs-') || h.includes('job-listings'))
            ))];
        """)

        if isinstance(result, list):
            for url in result:
                if url not in all_urls:
                    all_urls.append(url)

        # Check for "load more" button and click it
        mcp_javascript(script="""
            const btn = document.querySelector('button[class*="load-more"], a[class*="loadMore"]');
            if (btn) btn.click();
        """)

        # Check if we've reached end of results
        end = mcp_javascript(script="""
            const el = document.querySelector('.no-jobs, [class*="no-result"], [class*="noResult"]');
            return el ? el.innerText : null;
        """)
        if end:
            log(f"[Naukri] End of results at scroll {scroll_round + 1}.")
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

        const role = getText('h1.jd-header-title, h1[class*="title"], .jd-header h1') ||
                     getText('h1');

        const company = getText('a.jd-header-comp-name, [class*="comp-name"] a, .jd-header-comp-name') ||
                        getText('[class*="companyName"]');

        const location = getText('.location, [class*="location"] span, .loc span');

        const posted = getText('.posted-date, [class*="posted"], .date-text');

        const description = getText('#job_description, .job-desc, [class*="job-description"]');

        // Recruiter contact info
        const recruiterSection = getText('.recruiterDetails, [class*="recruiter"], .apply-button-container');
        const fullText = description + ' ' + recruiterSection;

        return { role, company, location, posted, description: fullText };
    """)

    if not isinstance(data, dict):
        return None

    company = data.get('company', '').strip()
    role = data.get('role', '').strip()
    posted = data.get('posted', '').strip()
    description = data.get('description', '').strip()

    if not company or not role:
        return None

    return JobLead(
        platform="Naukri",
        company=company,
        role=role,
        domain=infer_domain(role),
        industry=infer_industry(company, description),
        contact=extract_contact(description),
        job_url=job_url,
        date_posted=posted,
        location=data.get('location', ''),
    )
