"""
LinkedIn MCP runner — executed inside a Claude Code session where
the Claude-in-Chrome MCP tools are available.

This script acts as a bridge: it calls scraper_linkedin.py with the
MCP tool callables, then hands the results to main.run_with_mcp().

How to run:
    In a Claude Code session, ask:
    "Run /Users/.../lead_gen/run_linkedin_mcp.py"
    Claude Code will import the Chrome MCP tools automatically.
"""

import sys
import os

# Add the lead_gen directory to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from scraper_linkedin import scrape_linkedin
from main import run_with_mcp, log

# These will be injected by Claude Code's MCP environment
# Import stubs here so the file is valid Python outside MCP context
try:
    from mcp_tools import navigate, get_page_text, find, javascript_tool
except ImportError:
    # When run standalone (testing), provide no-op stubs
    def navigate(url): log(f"[STUB] navigate({url})")
    def get_page_text(): return ""
    def find(selector): return []
    def javascript_tool(script): return None


if __name__ == "__main__":
    log("Starting LinkedIn MCP scrape...")

    linkedin_leads = scrape_linkedin(
        mcp_navigate=navigate,
        mcp_get_page_text=get_page_text,
        mcp_find=find,
        mcp_javascript=javascript_tool,
        log=log,
    )

    log(f"LinkedIn returned {len(linkedin_leads)} leads.")
    output_path = run_with_mcp(linkedin_leads)

    if output_path:
        log(f"All done. File saved at: {output_path}")
