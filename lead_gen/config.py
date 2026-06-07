from pathlib import Path

# Output directory on Desktop
OUTPUT_DIR = Path.home() / "Desktop" / "lead_generation_runs"

# Persistent browser session storage (keeps you logged in across runs)
SESSION_DIR = Path.home() / ".lead_gen_session"

# How far back to look (hours)
LOOKBACK_HOURS = 24

# Delays between page loads (seconds)
PAGE_LOAD_WAIT = 4000       # ms — wait after navigation
SCROLL_PAUSE = 2000         # ms — wait after each scroll

# LinkedIn Jobs URL — past 24 hours, sorted most recent
LINKEDIN_JOBS_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?f_TPR=r86400"
    "&sortBy=DD"
)

# Naukri — last 1 day, sorted by date
NAUKRI_JOBS_URL = "https://www.naukri.com/jobs-in-india?jobAge=1&sortType=1"

# Instahyre — sorted by date
INSTAHYRE_JOBS_URL = "https://www.instahyre.com/search-jobs/?sort=date"

# Max scroll rounds per platform (each round scrolls ~1 screen)
MAX_SCROLLS_LINKEDIN = 20
MAX_SCROLLS_NAUKRI = 15
MAX_SCROLLS_INSTAHYRE = 15

# Run headless (True = no visible browser window, False = visible)
HEADLESS = False
