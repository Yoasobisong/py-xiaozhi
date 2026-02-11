"""
Web tools for MCP.
"""

from .manager import WebToolsManager, get_web_tools_manager
from .tools import fetch_content, open_url, search_web

__all__ = [
    "WebToolsManager",
    "get_web_tools_manager",
    "open_url",
    "search_web",
    "fetch_content",
]
