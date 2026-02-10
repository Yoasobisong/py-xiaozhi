"""
Clipboard tools for MCP.
"""

from .manager import ClipboardToolsManager, get_clipboard_tools_manager
from .tools import read_clipboard, write_clipboard

__all__ = [
    "ClipboardToolsManager",
    "get_clipboard_tools_manager",
    "read_clipboard",
    "write_clipboard",
]
