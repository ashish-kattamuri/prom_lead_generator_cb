"""
Sends the daily leads Excel as an email attachment via Gmail SMTP.
Requires a Gmail App Password (not your regular Gmail password).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from datetime import datetime


SENDER        = "steve.jobbs786@gmail.com"
RECIPIENT     = "steve.jobbs786@gmail.com"
GMAIL_APP_PWD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_leads_email(excel_path: str, lead_count: int, platforms: list[str], log=print):
    if not GMAIL_APP_PWD:
        log("[Email] GMAIL_APP_PASSWORD not set — skipping email.")
        return

    date_str = datetime.now().strftime("%d %b %Y")
    subject  = f"Daily Leads Report — {date_str} ({lead_count} leads)"
    body = (
        f"Hi,\n\n"
        f"Your daily lead generation run is complete.\n\n"
        f"  Date      : {date_str}\n"
        f"  Platforms : {', '.join(platforms)}\n"
        f"  Leads     : {lead_count}\n\n"
        f"Find the full report attached.\n\n"
        f"— Lead Gen Bot"
    )

    msg = MIMEMultipart()
    msg["From"]    = SENDER
    msg["To"]      = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(excel_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={Path(excel_path).name}"
        )
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, GMAIL_APP_PWD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
        log(f"[Email] Report sent to {RECIPIENT}.")
    except Exception as e:
        log(f"[Email] Failed to send: {e}")
