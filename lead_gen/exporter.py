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


COLUMNS = [
    ("Platform",            "platform"),
    ("Company",             "company"),
    ("Role / Designation",  "role"),
    ("Domain",              "domain"),
    ("Industry",            "industry"),
    ("Contact",             "contact"),
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
    platform_col_idx = 1  # "Platform" is column A

    for row_idx, (row, lead) in enumerate(zip(ws.iter_rows(min_row=2), leads), start=2):
        bg = "F5F7FA" if row_idx % 2 == 0 else "FFFFFF"
        for cell in row:
            cell.fill = PatternFill("solid", fgColor=bg)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=False)

        # Colour the Platform cell
        platform_cell = ws.cell(row=row_idx, column=platform_col_idx)
        color = PLATFORM_COLORS.get(lead.platform, DEFAULT_COLOR)
        platform_cell.font = Font(bold=True, color="FFFFFF")
        platform_cell.fill = PatternFill("solid", fgColor=color)
        platform_cell.alignment = Alignment(horizontal="center", vertical="center")

    # --- Column widths ---
    col_widths = {
        "Platform": 12,
        "Company": 28,
        "Role / Designation": 35,
        "Domain": 20,
        "Industry": 22,
        "Contact": 28,
        "Poster Name": 22,
        "Poster Profile": 35,
        "Location": 20,
        "Date Posted": 16,
        "Job URL": 40,
    }
    for col_idx, (col_label, _) in enumerate(
        [("Platform", ""), ("Company", ""), ("Role / Designation", ""), ("Domain", ""),
         ("Industry", ""), ("Contact", ""), ("Poster Name", ""), ("Poster Profile", ""),
         ("Location", ""), ("Date Posted", ""), ("Job URL", "")],
        start=1
    ):
        ws.column_dimensions[get_column_letter(col_idx)].width = list(col_widths.values())[col_idx - 1]

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-filter
    ws.auto_filter.ref = ws.dimensions
