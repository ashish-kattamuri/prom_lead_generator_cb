import os
from pathlib import Path

# Output directory on Desktop
OUTPUT_DIR = Path.home() / "Desktop" / "lead_generation_runs"

# How far back to look (hours)
LOOKBACK_HOURS = 24

# Delays between LinkedIn page loads (seconds) — keep human-like
LINKEDIN_PAGE_DELAY = (2, 4)   # random between 2 and 4 seconds
LINKEDIN_SCROLL_DELAY = (1, 2)

# LinkedIn Jobs URL — sorted by most recent, date posted = past 24 hours
LINKEDIN_JOBS_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?f_TPR=r86400"   # r86400 = past 24 hours (86400 seconds)
    "&sortBy=DD"       # DD = date posted descending (most recent)
)

# Naukri search URL — jobs posted in last 1 day, all India
NAUKRI_JOBS_URL = (
    "https://www.naukri.com/jobs-in-india"
    "?experience=0"
    "&jobAge=1"        # posted in last 1 day
)

# Instahyre search URL
INSTAHYRE_JOBS_URL = "https://www.instahyre.com/search-jobs/?sort=date"

# Request headers to mimic a real browser for HTTP scrapers
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Max pages to scrape per platform (safety cap)
MAX_PAGES_LINKEDIN = 20
MAX_PAGES_NAUKRI = 10
MAX_PAGES_INSTAHYRE = 10
