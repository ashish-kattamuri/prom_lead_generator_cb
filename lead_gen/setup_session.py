"""
One-time setup: opens a real browser window so you can log into
LinkedIn, Naukri, and Instahyre. Your session is saved to disk —
future runs reuse it automatically without re-logging in.

Run this ONCE:
    python3 setup_session.py
"""

from playwright.sync_api import sync_playwright
from config import SESSION_DIR


SITES = [
    ("LinkedIn",   "https://www.linkedin.com/login"),
    ("Naukri",     "https://www.naukri.com/nlogin/login"),
    ("Instahyre",  "https://www.instahyre.com/login/"),
]


def main():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nSession will be saved to: {SESSION_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            args=["--start-maximized"],
            viewport=None,
        )
        page = browser.new_page()

        for name, url in SITES:
            print(f"→ Opening {name} login page...")
            page.goto(url)
            input(f"  Log into {name} in the browser, then press ENTER here to continue...")
            print(f"  ✓ {name} session saved.\n")

        browser.close()

    print("All sessions saved. You can now run: python3 main.py")


if __name__ == "__main__":
    main()
