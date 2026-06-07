from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobLead:
    platform: str
    company: str
    role: str
    domain: str          # e.g. Engineering, Sales, HR, Finance
    industry: str        # e.g. IT, BFSI, Manufacturing
    contact: str         # email / phone — empty string if not found
    job_url: str
    date_posted: str     # raw string from platform e.g. "2 hours ago"
    location: str = ""
    poster_name: str = ""
    poster_profile_url: str = ""
    mba_relevant: str = ""      # "Yes" / "No" — auto-tagged
    contact_status: str = ""   # "Found" / "Need to Find"
