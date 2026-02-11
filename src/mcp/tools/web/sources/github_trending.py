"""GitHub Trending scraper.

Fetches and parses GitHub Trending page to extract popular repositories.
"""

import asyncio
import json
import re

import requests
from bs4 import BeautifulSoup

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

_GITHUB_TRENDING_URL = "https://github.com/trending"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_number(text: str) -> int:
    """Parse a number string like '1,234' or '1.2k' into an integer."""
    text = text.strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _parse_trending_page(html: str) -> list:
    """Parse GitHub Trending HTML and extract repository data.

    Returns list of repo dicts.
    """
    soup = BeautifulSoup(html, "html.parser")
    repos = []

    # Each trending repo is in an <article> with class "Box-row"
    articles = soup.select("article.Box-row")

    for rank, article in enumerate(articles, start=1):
        try:
            # Repo name: h2 > a (href like /owner/repo)
            name_tag = article.select_one("h2 a")
            if not name_tag:
                continue
            repo_path = name_tag.get("href", "").strip("/")
            if not repo_path:
                continue

            # Description: p tag
            desc_tag = article.select_one("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # Language
            lang_tag = article.select_one("span[itemprop='programmingLanguage']")
            language = lang_tag.get_text(strip=True) if lang_tag else ""

            # Stars and forks: look for links containing /stargazers and /forks
            stars = 0
            forks = 0
            for link in article.select("a"):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if "/stargazers" in href:
                    stars = _parse_number(text)
                elif "/forks" in href:
                    forks = _parse_number(text)

            # Stars this period: last span containing "stars"
            stars_since = ""
            for span in article.select("span"):
                text = span.get_text(strip=True)
                if "stars" in text.lower() and ("today" in text.lower()
                        or "this week" in text.lower()
                        or "this month" in text.lower()):
                    stars_since = text
                    break

            repos.append({
                "rank": rank,
                "name": repo_path,
                "url": f"https://github.com/{repo_path}",
                "description": description,
                "language": language,
                "stars": stars,
                "forks": forks,
                "stars_since": stars_since,
            })

        except Exception as e:
            logger.warning(f"[GitHubTrending] Failed to parse repo #{rank}: {e}")
            continue

    return repos


async def github_trending(arguments: dict) -> str:
    """Fetch GitHub trending repositories."""
    language = arguments.get("language", "").strip().lower()
    since = arguments.get("since", "weekly").strip().lower()

    # Validate since parameter
    if since not in ("daily", "weekly", "monthly"):
        since = "weekly"

    try:
        # Build URL
        url = _GITHUB_TRENDING_URL
        if language:
            url = f"{url}/{language}"
        url = f"{url}?since={since}"

        logger.info(f"[GitHubTrending] Fetching: {url}")

        # Fetch page
        resp = await asyncio.to_thread(
            lambda: requests.get(url, headers=_HEADERS, timeout=15)
        )
        resp.raise_for_status()

        # Parse
        repos = await asyncio.to_thread(_parse_trending_page, resp.text)

        if not repos:
            return json.dumps(
                {"success": False, "message": "未找到 Trending 项目，请稍后重试"},
                ensure_ascii=False,
            )

        logger.info(
            f"[GitHubTrending] Found {len(repos)} repos "
            f"(language={language or 'all'}, since={since})"
        )

        return json.dumps({
            "success": True,
            "language": language or "all",
            "since": since,
            "count": len(repos),
            "repos": repos,
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[GitHubTrending] Fetch failed: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"获取 GitHub Trending 失败: {e}"},
            ensure_ascii=False,
        )
