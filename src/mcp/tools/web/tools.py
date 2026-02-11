"""Web tools implementation.

Provides web browsing tools: open URLs, search via Chrome, and fetch page content.
"""

import asyncio
import json
import re
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


# Max content length returned to avoid oversized MCP responses
_MAX_CONTENT_CHARS = 4000

# Tags to remove before extracting text
_REMOVE_TAGS = [
    "script", "style", "nav", "footer", "header", "aside",
    "iframe", "form", "noscript", "svg", "canvas",
]


def _extract_main_text(html: str) -> tuple:
    """Extract main text content and title from HTML.

    Returns (title, content_text).
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Remove unwanted tags
    for tag_name in _REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Try to find main content area (priority: article > main > body)
    content_root = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
        or soup.find("body")
        or soup
    )

    # Extract text, preserving paragraph structure
    lines = []
    for element in content_root.stripped_strings:
        text = element.strip()
        if text:
            lines.append(text)

    content = "\n".join(lines)

    # Collapse multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return title, content.strip()


async def fetch_content(arguments: dict) -> str:
    """Fetch a URL and extract main text content."""
    url = arguments.get("url", "").strip()

    if not url:
        return '{"success": false, "message": "请提供要抓取的 URL"}'

    # Auto-add scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        logger.info(f"[WebTools] Fetching content from: {url}")

        import requests

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        resp = await asyncio.to_thread(
            lambda: requests.get(
                url, headers=headers, timeout=10,
                allow_redirects=True, stream=True,
            )
        )

        # Check content type
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return json.dumps(
                {"success": False, "message": f"不支持的内容类型: {content_type}"},
                ensure_ascii=False,
            )

        # Limit download size (500KB)
        content_length = int(resp.headers.get("Content-Length", 0))
        if content_length > 500_000:
            return json.dumps(
                {"success": False, "message": "页面内容过大 (>500KB)"},
                ensure_ascii=False,
            )

        # Read content with size limit
        html = resp.text[:500_000]

        resp.raise_for_status()

        # Extract main text
        title, content = await asyncio.to_thread(_extract_main_text, html)

        if not content:
            return json.dumps(
                {"success": False, "message": "无法提取页面正文内容"},
                ensure_ascii=False,
            )

        # Truncate to max chars
        truncated = False
        if len(content) > _MAX_CONTENT_CHARS:
            content = content[:_MAX_CONTENT_CHARS] + "\n\n...(内容已截断)"
            truncated = True

        result = {
            "success": True,
            "url": url,
            "title": title,
            "content": content,
            "length": len(content),
            "truncated": truncated,
        }
        logger.info(
            f"[WebTools] Fetched: title='{title}', "
            f"content_len={len(content)}, truncated={truncated}"
        )
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[WebTools] Fetch content failed: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"抓取网页失败: {e}"},
            ensure_ascii=False,
        )
