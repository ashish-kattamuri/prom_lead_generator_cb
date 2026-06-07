"""
Exports a list of JobLead objects to a timestamped Excel file.
Saves to ~/Desktop/lead_generation_runs/
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models import JobLead
from config import OUTPUT_DIR
from utils import is_mba_relevant


COLUMNS = [
    ("MBA Relevant",        "mba_relevant"),
    ("Platform",            "platform"),
    ("Company",             "company"),
    ("Role / Designation",  "role"),
    ("Domain",              "domain"),
    ("Industry",            "industry"),
    ("Contact",             "contact"),
    ("Contact Status",      "contact_status"),
    ("Poster Name",         "poster_name"),
    ("Poster Profile",      "poster_profile_url"),
    ("Location",            "location"),
    ("Date Posted",         "date_posted"),
    ("Job URL",             "job_url"),
]

# Per-platform accent colours (header fill)
PLATFORM_COLORS = {
    "LinkedIn":  "0A66C2",
    "Naukri":    "FF7555",
    "Instahyre": "2DC3A5",
}
DEFAULT_COLOR = "4A4A4A"


def export_to_excel(leads: List[JobLead], output_dir: Path = None) -> Path:
    # Tag MBA relevance and contact status before export
    for lead in leads:
        lead.mba_relevant = "Yes" if is_mba_relevant(lead.role) else "No"
        lead.contact_status = "Found" if lead.contact.strip() else "Need to Find"

    # Sort: MBA-relevant first, then by platform
    leads.sort(key=lambda l: (0 if l.mba_relevant == "Yes" else 1, l.platform))

    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"leads_{timestamp}.xlsx"
    filepath = out / filename

    # Build DataFrame
    rows = []
    for lead in leads:
        rows.append({col_label: getattr(lead, attr, "") for col_label, attr in COLUMNS})
    df = pd.DataFrame(rows, columns=[c[0] for c in COLUMNS])

    # Write with openpyxl for styling
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
        wb = writer.book
        ws = writer.sheets["Leads"]

        _style_sheet(ws, leads)

    return filepath


def _style_sheet(ws, leads: List[JobLead]):
    # --- Header row styling ---
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="1E3A5F")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin", color="D0D0D0"),
        right=Side(style="thin", color="D0D0D0"),
        top=Side(style="thin", color="D0D0D0"),
        bottom=Side(style="thin", color="D0D0D0"),
    )

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin_border

    ws.row_dimensions[1].height = 30

    # --- Data rows: zebra striping + platform colour on Platform column ---
    platform_col_idx = 2  # "Platform" is column B (MBA Relevant is column A)

    for row_idx, (row, lead) in enumerate(zip(ws.iter_rows(min_row=2), leads), start=2):
        is_mba = lead.mba_relevant == "Yes"
        # MBA rows: normal white/light; non-MBA rows: dimmed grey
        bg = ("F0FFF4" if row_idx % 2 == 0 else "FFFFFF") if is_mba else "F0F0F0"
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=bg)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=False)
            if not is_mba:
                cell.font = Font(color="999999")  # grey out non-MBA rows

        # MBA Relevant badge (column 1)
        mba_cell = ws.cell(row=row_idx, column=1)
        if is_mba:
            mba_cell.font = Font(bold=True, color="276221")
            mba_cell.fill = PatternFill("solid", fgColor="C6EFCE")
        else:
            mba_cell.font = Font(color="9C0006")
            mba_cell.fill = PatternFill("solid", fgColor="FFC7CE")
        mba_cell.alignment = Alignment(horizontal="center", vertical="center")

        # Contact Status badge (column 8 — "Contact Status")
        contact_status_col = next(
            i for i, (lbl, _) in enumerate(COLUMNS, 1) if lbl == "Contact Status"
        )
        cs_cell = ws.cell(row=row_idx, column=contact_status_col)
        if lead.contact_status == "Found":
            cs_cell.font = Font(bold=True, color="276221")
            cs_cell.fill = PatternFill("solid", fgColor="C6EFCE")
        else:
            cs_cell.font = Font(bold=True, color="974706")
            cs_cell.fill = PatternFill("solid", fgColor="FFEB9C")
        cs_cell.alignment = Alignment(horizontal="center", vertical="center")

        # Colour the Platform cell
        platform_cell = ws.cell(row=row_idx, column=platform_col_idx)
        color = PLATFORM_COLORS.get(lead.platform, DEFAULT_COLOR)
        platform_cell.font = Font(bold=True, color="FFFFFF")
        platform_cell.fill = PatternFill("solid", fgColor=color)
        platform_cell.alignment = Alignment(horizontal="center", vertical="center")

    # --- Column widths ---
    col_widths = {
        "MBA Relevant": 14,
        "Platform": 12,
        "Company": 28,
        "Role / Designation": 35,
        "Domain": 22,
        "Industry": 22,
        "Contact": 28,
        "Contact Status": 18,
        "Poster Name": 22,
        "Poster Profile": 35,
        "Location": 20,
        "Date Posted": 16,
        "Job URL": 40,
    }
    for col_idx, (col_label, _) in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = col_widths.get(col_label, 18)

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-filter
    ws.auto_filter.ref = ws.dimensions
