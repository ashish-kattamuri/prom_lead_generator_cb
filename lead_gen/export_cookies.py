"""
One-time script: exports Naukri and Instahyre session cookies from your
saved Playwright session into base64 strings ready to paste as GitHub Secrets.

Run AFTER setup_session.py:
    python3 export_cookies.py

Then follow the printed instructions to add the secrets to GitHub.
"""

import json
import base64
from playwright.sync_api import sync_playwright
from config import SESSION_DIR


SITES = {
    "NAUKRI_STATE":    "https://www.naukri.com",
    "INSTAHYRE_STATE": "https://www.instahyre.com",
}


def main():
    if not SESSION_DIR.exists():
        print("ERROR: No saved session found. Run setup_session.py first.")
        return

    print("\nExporting session cookies...\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=True,
        )

        for secret_name, url in SITES.items():
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)

            state = ctx.storage_state()
            encoded = base64.b64encode(json.dumps(state).encode()).decode()

            print(f"{'='*60}")
            print(f"GitHub Secret name : {secret_name}")
            print(f"GitHub Secret value:")
            print(encoded)
            print()
            page.close()

        ctx.close()

    print("="*60)
    print("\nHow to add these to GitHub:")
    print("1. Go to your repo → Settings → Secrets and variables → Actions")
    print("2. Click 'New repository secret'")
    print("3. Paste each name + value above")
    print("\nAlso add these secrets for email delivery:")
    print("  GMAIL_APP_PASSWORD  → your Gmail app password (see README)")
    print("  RECIPIENT_EMAIL     → steve.jobbs786@gmail.com (already set in code)")


if __name__ == "__main__":
    main()
