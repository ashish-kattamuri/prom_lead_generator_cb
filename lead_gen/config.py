from pathlib import Path

# Output directory on Desktop
OUTPUT_DIR = Path.home() / "Desktop" / "lead_generation_runs"

# Persistent browser session storage (keeps you logged in across runs)
SESSION_DIR = Path.home() / ".lead_gen_session"

# How far back to look (hours)
LOOKBACK_HOURS = 24

# Delays between page loads (ms)
PAGE_LOAD_WAIT = 4000
SCROLL_PAUSE   = 2000

# ── LinkedIn ────────────────────────────────────────────────────────────────
# f_TPR=r86400  → posted in last 24 hours
# f_JT=F        → Full-time only
# sortBy=DD     → Most recent first
LINKEDIN_JOBS_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?f_TPR=r86400"
    "&f_JT=F"
    "&sortBy=DD"
)

# ── Naukri ───────────────────────────────────────────────────────────────────
# jobAge=1      → posted in last 1 day
# sortType=1    → Most recent first
# jobType=1     → Full-time (Naukri jobType param)
NAUKRI_JOBS_URL = "https://www.naukri.com/jobs-in-india?jobAge=1&sortType=1&jobType=1"

# ── Instahyre ────────────────────────────────────────────────────────────────
INSTAHYRE_JOBS_URL = "https://www.instahyre.com/search-jobs/?sort=date&job_type=full_time"

# Safety timeout per platform (minutes) — scraper stops after this even if
# no end-of-results signal received. Set high so nothing gets missed.
MAX_SCRAPE_MINUTES_LINKEDIN  = 120
MAX_SCRAPE_MINUTES_NAUKRI    = 60
MAX_SCRAPE_MINUTES_INSTAHYRE = 60

# Run headless (True = no visible browser window, False = visible)
HEADLESS = False

# ── MBA Job Keywords ─────────────────────────────────────────────────────────
# Used to tag Domain more accurately for post-MBA roles.
# Also used by scrapers to confirm a job is MBA-relevant when needed.
MBA_JOB_KEYWORDS = [
    # Management Consulting
    "consultant", "associate consultant", "strategy consultant",
    "management consultant", "business analyst", "senior analyst",
    "associate", "engagement manager", "principal",

    # Strategy & Corporate Development
    "strategy", "strategic planning", "corporate strategy",
    "corporate development", "business development", "bd manager",
    "chief of staff", "head of strategy",

    # Finance & Investment
    "investment banking", "investment banker", "associate ib",
    "private equity", "venture capital", "vc associate",
    "financial analyst", "fp&a", "finance manager", "cfo",
    "treasury", "corporate finance", "credit analyst",
    "fund manager", "asset management", "portfolio manager",
    "equity research", "m&a", "mergers and acquisitions",

    # Product Management
    "product manager", "senior product manager", "product lead",
    "associate product manager", "apm", "product owner",
    "group product manager", "director of product",

    # Marketing & Brand
    "marketing manager", "brand manager", "category manager",
    "growth manager", "product marketing", "marketing lead",
    "chief marketing officer", "cmo", "vp marketing",
    "marketing director", "digital marketing manager",

    # Sales & Business Development
    "sales manager", "regional sales manager", "national sales manager",
    "key account manager", "kam", "account director",
    "vp sales", "head of sales", "revenue manager",
    "b2b sales", "enterprise sales", "commercial manager",

    # Operations & Supply Chain
    "operations manager", "supply chain manager", "scm",
    "logistics manager", "procurement manager", "sourcing manager",
    "project manager", "program manager", "pmo",
    "vp operations", "head of operations", "chief operating officer", "coo",

    # General Management & Leadership
    "general manager", "gm", "business unit head",
    "country manager", "regional manager", "p&l manager",
    "managing director", "md", "ceo", "president",
    "deputy general manager", "dgm", "agm", "avp", "vp",
    "senior vice president", "svp", "executive director",

    # Human Resources
    "hr manager", "hrbp", "hr business partner",
    "talent acquisition", "talent management", "people manager",
    "chief people officer", "vp hr", "head of hr",
    "learning and development", "l&d manager", "organizational development",

    # Technology & Digital (MBA + Tech)
    "technology manager", "it manager", "digital transformation",
    "data analyst", "business analyst", "analytics manager",
    "data science manager", "ai strategist", "it consultant",
    "cto", "chief digital officer", "cdo",

    # Entrepreneurship & Startups
    "founder", "co-founder", "cxo", "startup founder",

    # Healthcare Management
    "hospital administrator", "healthcare manager", "health services manager",
    "pharmaceutical manager", "medical sales",

    # Real Estate & Infrastructure
    "real estate manager", "project director", "infrastructure manager",

    # Social Impact / Development Sector
    "program director", "ngo manager", "csr manager",
    "social impact manager", "development sector",
]
