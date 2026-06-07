"""
LinkedIn scraper — uses the user's live Chrome session via Claude-in-Chrome MCP.
Navigates to LinkedIn Jobs, sorted by most recent (past 24 hours), and extracts leads.

This module is called from main.py which already has the MCP tools available.
It returns a list of JobLead objects.
"""

import time
import random
from typing import List, Callable

from models import JobLead
from utils import extract_contact, infer_domain, infer_industry, is_within_24h, random_delay
from config import LINKEDIN_JOBS_URL, MAX_PAGES_LINKEDIN, LINKEDIN_PAGE_DELAY, LINKEDIN_SCROLL_DELAY


def scrape_linkedin(mcp_navigate, mcp_get_page_text, mcp_find, mcp_javascript,
                    log: Callable = print) -> List[JobLead]:
    """
    Parameters mirror the MCP tool callables injected from main.py.
    Returns a list of JobLead for all jobs posted in the last 24 hours.
    """
    leads: List[JobLead] = []

    log("[LinkedIn] Navigating to Jobs feed (past 24h, most recent)...")
    mcp_navigate(url=LINKEDIN_JOBS_URL)
    random_delay(*LINKEDIN_PAGE_DELAY)

    # Scroll to load jobs and collect job card links
    job_urls = _collect_job_urls(mcp_javascript, mcp_get_page_text, log)
    log(f"[LinkedIn] Found {len(job_urls)} job postings to process.")

    for idx, job_url in enumerate(job_urls, 1):
        try:
            lead = _extract_job_detail(job_url, mcp_navigate, mcp_get_page_text,
                                       mcp_javascript, log)
            if lead:
                leads.append(lead)
                log(f"[LinkedIn] ({idx}/{len(job_urls)}) Scraped: {lead.company} — {lead.role}")
        except Exception as e:
            log(f"[LinkedIn] ({idx}/{len(job_urls)}) Failed for {job_url}: {e}")
        random_delay(*LINKEDIN_PAGE_DELAY)

    log(f"[LinkedIn] Done. {len(leads)} leads collected.")
    return leads


def _collect_job_urls(mcp_javascript, mcp_get_page_text, log) -> List[str]:
    """Scroll the job listing page and collect all job card URLs posted in last 24h."""
    all_urls = []
    stop_early = False

    for scroll_round in range(MAX_PAGES_LINKEDIN):
        # Scroll down to load more results
        mcp_javascript(script="window.scrollBy(0, 1200);")
        random_delay(*LINKEDIN_SCROLL_DELAY)

        # Extract job card links and their posted-time labels via JS
        result = mcp_javascript(script="""
            const cards = Array.from(document.querySelectorAll(
                'a[href*="/jobs/view/"], a.job-card-list__title'
            ));
            return cards.map(a => ({
                url: a.href,
                text: a.innerText.trim()
            })).filter(item => item.url.includes('/jobs/view/'));
        """)

        # Also check time labels to know if we've gone past 24h
        time_labels = mcp_javascript(script="""
            const timeEls = Array.from(document.querySelectorAll(
                '.job-card-container__listed-status, ' +
                '.jobs-unified-top-card__posted-date, ' +
                'time, [class*="posted"]'
            ));
            return timeEls.map(el => el.innerText.trim()).filter(t => t.length > 0);
        """)

        if isinstance(result, list):
            new_urls = [item['url'] for item in result if item.get('url')]
            for url in new_urls:
                if url not in all_urls:
                    all_urls.append(url)

        if isinstance(time_labels, list):
            for label in time_labels:
                if label and not is_within_24h(label):
                    # We've scrolled past the 24h window
                    stop_early = True
                    break

        if stop_early:
            log(f"[LinkedIn] Reached posts older than 24h at scroll round {scroll_round + 1}. Stopping.")
            break

        # Check if "no more results" indicator appeared
        end_check = mcp_javascript(script="""
            const el = document.querySelector('.jobs-search-no-results, .artdeco-empty-state');
            return el ? el.innerText : null;
        """)
        if end_check:
            log("[LinkedIn] Reached end of results.")
            break

    return list(dict.fromkeys(all_urls))  # dedupe preserving order


def _extract_job_detail(job_url: str, mcp_navigate, mcp_get_page_text,
                        mcp_javascript, log) -> JobLead | None:
    """Open an individual job posting and extract structured data."""
    mcp_navigate(url=job_url)
    random_delay(*LINKEDIN_PAGE_DELAY)

    # Extract structured fields via JS
    data = mcp_javascript(script="""
        function getText(sel) {
            const el = document.querySelector(sel);
            return el ? el.innerText.trim() : '';
        }

        const company = getText('.job-details-jobs-unified-top-card__company-name') ||
                        getText('.topcard__org-name-link') ||
                        getText('[class*="company-name"]');

        const role = getText('.job-details-jobs-unified-top-card__job-title') ||
                     getText('.topcard__title') ||
                     getText('h1[class*="title"]');

        const location = getText('.job-details-jobs-unified-top-card__bullet') ||
                         getText('.topcard__flavor--bullet');

        const posted = getText('.job-details-jobs-unified-top-card__posted-date') ||
                       getText('.topcard__flavor--metadata') ||
                       getText('span[class*="posted"]') ||
                       getText('time');

        // Poster info — shown in "Meet the hiring team" section
        const posterName = getText('.hirer-card__hirer-information .artdeco-entity-lockup__title') ||
                           getText('[class*="hirer-card"] .artdeco-entity-lockup__title') || '';

        const posterProfileUrl = (() => {
            const a = document.querySelector('.hirer-card__hirer-information a, [class*="hirer-card"] a');
            return a ? a.href : '';
        })();

        // Full description text (for contact extraction)
        const description = getText('.jobs-description__content') ||
                            getText('.description__text') || '';

        return { company, role, location, posted, posterName, posterProfileUrl, description };
    """)

    if not isinstance(data, dict):
        return None

    company = data.get('company', '').strip()
    role = data.get('role', '').strip()
    posted = data.get('posted', '').strip()
    description = data.get('description', '').strip()

    if not company or not role:
        return None

    # Only keep if within 24 hours
    if posted and not is_within_24h(posted):
        return None

    contact = extract_contact(description)

    return JobLead(
        platform="LinkedIn",
        company=company,
        role=role,
        domain=infer_domain(role),
        industry=infer_industry(company, description),
        contact=contact,
        job_url=job_url,
        date_posted=posted,
        location=data.get('location', ''),
        poster_name=data.get('posterName', ''),
        poster_profile_url=data.get('posterProfileUrl', ''),
    )
