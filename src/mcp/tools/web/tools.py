"""Web tools implementation.

Provides web browsing tools: open URLs and search via Chrome.
"""

import shutil
import subprocess
import sys
from typing import Any, Dict
from urllib.parse import quote_plus

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _find_chrome() -> str:
    """
    Find Chrome executable path on the current platform.
    Returns the path or empty string if not found.
    """
    if sys.platform == "win32":
        # Common Chrome paths on Windows
        import os

        candidates = [
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
            ),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return ""
    elif sys.platform == "darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        import os

        return chrome_path if os.path.isfile(chrome_path) else ""
    else:
        # Linux: check common names
        for name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            path = shutil.which(name)
            if path:
                return path
        return ""


def open_url(arguments: dict) -> str:
    """
    Open a URL in Chrome browser.
    """
    url = arguments.get("url", "")
    if not url:
        return '{"success": false, "message": "No URL provided"}'

    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://", "file://")):
        url = "https://" + url

    try:
        chrome_path = _find_chrome()
        if chrome_path:
            logger.info(f"[WebTools] Opening URL in Chrome: {url}")
            subprocess.Popen([chrome_path, url])
            return f'{{"success": true, "message": "Opened {url} in Chrome"}}'
        else:
            # Fallback to default browser
            import webbrowser

            logger.info(f"[WebTools] Chrome not found, opening in default browser: {url}")
            webbrowser.open(url)
            return f'{{"success": true, "message": "Opened {url} in default browser"}}'

    except Exception as e:
        logger.error(f"[WebTools] Failed to open URL: {e}", exc_info=True)
        return f'{{"success": false, "message": "Failed to open URL: {e}"}}'


def search_web(arguments: dict) -> str:
    """
    Search the web using Chrome browser.
    """
    query = arguments.get("query", "")
    engine = arguments.get("engine", "google")

    if not query:
        return '{"success": false, "message": "No search query provided"}'

    # Build search URL
    encoded_query = quote_plus(query)
    search_urls = {
        "google": f"https://www.google.com/search?q={encoded_query}",
        "baidu": f"https://www.baidu.com/s?wd={encoded_query}",
        "bing": f"https://www.bing.com/search?q={encoded_query}",
        "github": f"https://github.com/search?q={encoded_query}",
        "bilibili": f"https://search.bilibili.com/all?keyword={encoded_query}",
        "zhihu": f"https://www.zhihu.com/search?type=content&q={encoded_query}",
    }

    url = search_urls.get(engine, search_urls["google"])

    try:
        chrome_path = _find_chrome()
        if chrome_path:
            logger.info(f"[WebTools] Searching '{query}' via {engine} in Chrome")
            subprocess.Popen([chrome_path, url])
            return f'{{"success": true, "message": "Searching \\"{query}\\" via {engine}"}}'
        else:
            import webbrowser

            logger.info(f"[WebTools] Searching '{query}' in default browser")
            webbrowser.open(url)
            return f'{{"success": true, "message": "Searching \\"{query}\\" via {engine}"}}'

    except Exception as e:
        logger.error(f"[WebTools] Search failed: {e}", exc_info=True)
        return f'{{"success": false, "message": "Search failed: {e}"}}'
