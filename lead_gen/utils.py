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
    # Indian mobile: optional +91 / 91, then 10 digits starting with 6-9
    phone = re.search(r"(?:\+91|91)?[\s\-]?[6-9]\d{9}", text)
    if phone:
        return phone.group().strip()
    return ""


# Rough domain classifier based on job title keywords
_DOMAIN_MAP = {
    "engineering": ["engineer", "developer", "sde", "software", "devops", "data scientist",
                    "ml", "machine learning", "backend", "frontend", "fullstack"],
    "hr & talent": ["hr", "human resource", "talent", "recruiter", "people ops",
                    "hrbp", "learning & development", "l&d"],
    "sales & business dev": ["sales", "business development", "bd", "account executive",
                              "account manager", "revenue"],
    "marketing": ["marketing", "growth", "brand", "content", "seo", "performance marketing",
                  "digital marketing"],
    "finance": ["finance", "financial", "chartered accountant", "ca ", "cfo", "accounting",
                "controller", "fp&a"],
    "operations": ["operations", "supply chain", "logistics", "procurement", "scm"],
    "product": ["product manager", "product owner", "pm ", "product lead"],
    "consulting": ["consultant", "associate consultant", "strategy", "management consulting"],
}

_INDUSTRY_MAP = {
    "IT & Software": ["software", "saas", "technology", "tech", "it ", "information technology",
                      "cloud", "cybersecurity", "fintech", "edtech", "healthtech"],
    "BFSI": ["bank", "banking", "insurance", "nbfc", "financial services", "asset management",
             "wealth management", "brokerage"],
    "Manufacturing": ["manufacturing", "auto", "automobile", "fmcg", "consumer goods",
                      "chemical", "pharma", "industrial"],
    "Consulting": ["consulting", "advisory", "big 4", "mckinsey", "bcg", "bain", "deloitte",
                   "pwc", "ey ", "kpmg", "accenture"],
    "E-commerce & Retail": ["ecommerce", "e-commerce", "retail", "d2c", "marketplace"],
    "Healthcare": ["hospital", "healthcare", "health care", "pharma", "biotech", "medtech",
                   "diagnostics"],
    "Education": ["education", "edtech", "school", "university", "institute", "learning"],
    "Logistics": ["logistics", "supply chain", "shipping", "freight", "warehouse"],
}


def infer_domain(title: str) -> str:
    title_lower = title.lower()
    for domain, keywords in _DOMAIN_MAP.items():
        if any(kw in title_lower for kw in keywords):
            return domain.title()
    return "Other"


def infer_industry(company: str, description: str = "") -> str:
    text = (company + " " + description).lower()
    for industry, keywords in _INDUSTRY_MAP.items():
        if any(kw in text for kw in keywords):
            return industry
    return "Other"


def is_within_24h(posted_text: str) -> bool:
    """Return True if the posted_text string suggests the job was posted within 24 hours."""
    t = posted_text.lower()
    if "just now" in t or "moments ago" in t:
        return True
    # "X minutes ago" / "X hours ago"
    match = re.search(r"(\d+)\s*(minute|hour|min|hr)", t)
    if match:
        return True
    # "1 day ago" is borderline — include it; "2 days ago" exclude
    match_days = re.search(r"(\d+)\s*day", t)
    if match_days and int(match_days.group(1)) <= 1:
        return True
    return False
