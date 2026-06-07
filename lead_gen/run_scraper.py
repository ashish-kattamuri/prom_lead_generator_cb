"""
Entry point for running the full scraper from a Claude Code session.

Claude Code reads this file and calls run() with the live Chrome MCP tools.
The user's Chrome browser (logged into LinkedIn, Naukri, Instahyre) does the work.

To trigger: open this Claude Code session and say "Run the lead generation scraper"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import run, log

# ── Chrome MCP tool callables are injected by Claude Code at runtime ──
# These stubs make the file valid Python when imported outside MCP context.
try:
    from mcp_tools import navigate, javascript_tool, get_page_text, find
except ImportError:
    def navigate(url): log(f"[STUB] navigate({url})")
    def javascript_tool(script): return None
    def get_page_text(): return ""
    def find(**kwargs): return []


if __name__ == "__main__":
    output_path = run(
        mcp_navigate=navigate,
        mcp_javascript=javascript_tool,
        mcp_get_page_text=get_page_text,
        mcp_find=find,
    )
    if output_path:
        log(f"Done. Open your file at: {output_path}")
