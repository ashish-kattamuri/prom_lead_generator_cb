import re
import time
import random
from typing import Optional


def random_delay(low: float, high: float):
    time.sleep(random.uniform(low, high))


def extract_contact(text: str) -> str:
    """Pull email or Indian phone number out of any text blob."""
    email = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    if email:
        return email.group()
    phone = re.search(r"(?:\+91|91)?[\s\-]?[6-9]\d{9}", text)
    if phone:
        return phone.group().strip()
    return ""


# ── Domain classifier ────────────────────────────────────────────────────────
_DOMAIN_MAP = [
    ("Management Consulting", [
        "consultant", "consulting", "associate consultant", "strategy consultant",
        "management consultant", "engagement manager", "principal consultant",
    ]),
    ("Strategy & Corp Dev", [
        "strategy", "strategic planning", "corporate strategy", "corporate development",
        "chief of staff", "head of strategy", "business development",
    ]),
    ("Investment Banking & PE", [
        "investment banking", "investment banker", "private equity", "pe associate",
        "venture capital", "vc associate", "m&a", "mergers and acquisitions",
        "equity research", "fund manager", "portfolio manager", "asset management",
        "hedge fund",
    ]),
    ("Finance & FP&A", [
        "financial analyst", "fp&a", "finance manager", "cfo", "treasury",
        "corporate finance", "credit analyst", "controller", "chartered accountant",
        "ca ", "financial planning",
    ]),
    ("Product Management", [
        "product manager", "senior product manager", "product lead", "product owner",
        "associate product manager", "apm", "group product manager", "director of product",
    ]),
    ("Marketing & Brand", [
        "marketing manager", "brand manager", "category manager", "growth manager",
        "product marketing", "cmo", "marketing director", "digital marketing",
        "marketing lead", "vp marketing",
    ]),
    ("Sales & Revenue", [
        "sales manager", "regional sales", "national sales", "key account",
        "account director", "vp sales", "head of sales", "revenue manager",
        "b2b sales", "enterprise sales", "commercial manager", "business development",
    ]),
    ("Operations & Supply Chain", [
        "operations manager", "supply chain", "logistics manager", "procurement",
        "sourcing manager", "scm", "coo", "vp operations", "head of operations",
        "project manager", "program manager", "pmo",
    ]),
    ("General Management", [
        "general manager", " gm ", "business unit head", "country manager",
        "regional manager", "p&l", "managing director", " md ", "ceo", "president",
        "dgm", " agm ", " avp ", " vp ", "svp", "executive director",
        "deputy general manager",
    ]),
    ("HR & People", [
        "hr manager", "hrbp", "hr business partner", "talent acquisition",
        "talent management", "people manager", "chief people officer", "vp hr",
        "head of hr", "learning and development", "l&d", "organizational development",
        "human resource",
    ]),
    ("Technology & Digital", [
        "technology manager", "it manager", "digital transformation", "analytics manager",
        "data science manager", "ai strategist", "it consultant", "cto",
        "chief digital officer", "tech lead", "engineering manager",
    ]),
    ("Data & Analytics", [
        "data analyst", "business analyst", "analytics", "data scientist",
        "insights manager", "bi manager", "reporting analyst",
    ]),
    ("Healthcare Management", [
        "hospital administrator", "healthcare manager", "health services",
        "pharmaceutical manager", "medical sales", "pharma",
    ]),
    ("Real Estate & Infra", [
        "real estate manager", "project director", "infrastructure manager",
        "construction manager", "facility manager",
    ]),
    ("Social Impact / NGO", [
        "program director", "ngo", "csr manager", "social impact", "development sector",
        "non-profit", "nonprofit",
    ]),
]

# ── Industry classifier ──────────────────────────────────────────────────────
_INDUSTRY_MAP = [
    ("IT & Software",        ["software", "saas", "technology", "tech", " it ", "information technology",
                               "cloud", "cybersecurity", "fintech", "edtech", "healthtech", "startup"]),
    ("BFSI",                 ["bank", "banking", "insurance", "nbfc", "financial services",
                               "asset management", "wealth", "brokerage", "capital markets"]),
    ("Management Consulting",["consulting", "advisory", "mckinsey", "bcg", "bain", "deloitte",
                               "pwc", " ey ", "kpmg", "accenture", "strategy&"]),
    ("E-commerce & Retail",  ["ecommerce", "e-commerce", "retail", "d2c", "marketplace", "quick commerce"]),
    ("Manufacturing",        ["manufacturing", "auto", "automobile", "fmcg", "consumer goods",
                               "chemical", "industrial", "engineering products"]),
    ("Pharma & Healthcare",  ["pharma", "pharmaceutical", "biotech", "hospital", "healthcare",
                               "health care", "medtech", "diagnostics", "life sciences"]),
    ("Education",            ["education", "edtech", "school", "university", "institute", "learning"]),
    ("Logistics",            ["logistics", "supply chain", "shipping", "freight", "warehouse", "last mile"]),
    ("Real Estate",          ["real estate", "realty", "property", "construction", "infrastructure"]),
    ("Media & Entertainment",["media", "entertainment", "ott", "gaming", "content", "advertising", "agency"]),
    ("Energy & Utilities",   ["energy", "oil", "gas", "power", "utilities", "renewable", "solar", "ev"]),
    ("Social Impact",        ["ngo", "non-profit", "nonprofit", "development", "csr", "social impact"]),
]


def infer_domain(title: str) -> str:
    t = title.lower()
    for domain, keywords in _DOMAIN_MAP:
        if any(kw in t for kw in keywords):
            return domain
    return "Other"


def infer_industry(company: str, description: str = "") -> str:
    text = (company + " " + description).lower()
    for industry, keywords in _INDUSTRY_MAP:
        if any(kw in text for kw in keywords):
            return industry
    return "Other"


def is_within_24h(posted_text: str) -> bool:
    t = posted_text.lower()
    if any(x in t for x in ["just now", "moments ago", "today"]):
        return True
    match = re.search(r"(\d+)\s*(minute|hour|min|hr)", t)
    if match:
        return True
    match_days = re.search(r"(\d+)\s*day", t)
    if match_days and int(match_days.group(1)) <= 1:
        return True
    return False


def is_mba_relevant(title: str) -> bool:
    """Returns True if the job title matches any known post-MBA role."""
    from config import MBA_JOB_KEYWORDS
    t = " " + title.lower() + " "   # pad so word-boundary checks work on edges
    for kw in MBA_JOB_KEYWORDS:
        # Keywords that are abbreviations (all caps or short) need word boundaries
        pattern = r'\b' + re.escape(kw.strip()) + r'\b'
        if re.search(pattern, t):
            return True
    return False
