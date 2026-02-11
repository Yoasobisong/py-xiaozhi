"""Web tools manager.

Registers web browsing MCP tools (open URL, search).
"""

from typing import Any, Dict

from src.utils.logging_config import get_logger

from .tools import open_url, search_web, fetch_content
from .sources import github_trending

logger = get_logger(__name__)


class WebToolsManager:
    """
    Web tools manager.
    """

    def __init__(self):
        self._initialized = False
        logger.info("[WebManager] Web tools manager initialized")

    def init_tools(self, add_tool, PropertyList, Property, PropertyType):
        """
        Register all web tools.
        """
        try:
            logger.info("[WebManager] Registering web tools")

            # Open URL tool
            url_props = PropertyList(
                [Property("url", PropertyType.STRING)]
            )
            add_tool(
                (
                    "web.open_url",
                    "Open a URL in Chrome browser.\n"
                    "Use when user says: '打开网页', '打开B站', '打开GitHub', "
                    "'open website', 'go to url', '帮我打开xxx'.\n"
                    "Parameter:\n"
                    "- url: The URL to open (e.g., 'bilibili.com', 'github.com', "
                    "'https://www.google.com'). Scheme is auto-added if missing.\n\n"
                    "Common shortcuts:\n"
                    "- B站/bilibili → bilibili.com\n"
                    "- GitHub → github.com\n"
                    "- 知乎 → zhihu.com\n"
                    "- 百度 → baidu.com",
                    url_props,
                    open_url,
                )
            )

            # Search tool
            search_props = PropertyList(
                [
                    Property("query", PropertyType.STRING),
                    Property("engine", PropertyType.STRING, default_value="google"),
                ]
            )
            add_tool(
                (
                    "web.search",
                    "Search the web using Chrome browser.\n"
                    "Use when user says: '搜索', '搜一下', '查一下', '帮我搜', "
                    "'search for', 'look up', 'Google一下'.\n"
                    "Parameters:\n"
                    "- query: The search keywords\n"
                    "- engine: Search engine to use (default 'google'). Options:\n"
                    "  'google', 'baidu', 'bing', 'github', 'bilibili', 'zhihu'\n\n"
                    "Examples:\n"
                    "- '帮我搜一下Python asyncio教程' → query='Python asyncio教程'\n"
                    "- '在GitHub上搜索py-xiaozhi' → query='py-xiaozhi', engine='github'\n"
                    "- '在B站搜索机器人' → query='机器人', engine='bilibili'",
                    search_props,
                    search_web,
                )
            )

            # Fetch content tool
            fetch_props = PropertyList(
                [Property("url", PropertyType.STRING)]
            )
            add_tool(
                (
                    "web.fetch_content",
                    "Fetch and extract main text content from a web page URL.\n"
                    "Use when user says: '帮我看看这个网页写了什么', '抓取这个链接的内容', "
                    "'读取网页内容', '总结这个网页', '这个链接说了什么', "
                    "'fetch this url', 'read this page', 'summarize this link'.\n"
                    "Parameter:\n"
                    "- url: The URL to fetch (e.g. 'https://example.com/article')\n"
                    "Returns the page title and main text content "
                    "(cleaned, no ads/navigation).\n"
                    "The AI can then summarize, translate, or extract info "
                    "from the returned text.",
                    fetch_props,
                    fetch_content,
                )
            )

            # GitHub Trending tool
            trending_props = PropertyList(
                [
                    Property("language", PropertyType.STRING, default_value=""),
                    Property("since", PropertyType.STRING, default_value="weekly"),
                ]
            )
            add_tool(
                (
                    "web.github_trending",
                    "获取 GitHub Trending 热门项目列表。\n"
                    "Use when user says: 'GitHub上有什么热门项目', '最近流行什么开源项目', "
                    "'GitHub trending', 'GitHub这周有什么火的', '推荐一些开源项目', "
                    "'有什么好的开源项目'.\n"
                    "Parameters:\n"
                    "- language: Programming language filter "
                    "(e.g. 'python', 'rust', 'javascript', empty for all)\n"
                    "- since: Time range - 'daily', 'weekly', or 'monthly' "
                    "(default: 'weekly')\n\n"
                    "Returns list of trending repos with name, description, "
                    "language, stars, forks, and growth.",
                    trending_props,
                    github_trending,
                )
            )

            self._initialized = True
            logger.info("[WebManager] Web tools registered successfully")

        except Exception as e:
            logger.error(f"[WebManager] Web tools registration failed: {e}",
                         exc_info=True)
            raise

    def is_initialized(self) -> bool:
        return self._initialized

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "tools_count": 4,
            "available_tools": ["open_url", "search", "fetch_content", "github_trending"],
        }


# Singleton
_web_tools_manager = None


def get_web_tools_manager() -> WebToolsManager:
    """
    Get web tools manager singleton.
    """
    global _web_tools_manager
    if _web_tools_manager is None:
        _web_tools_manager = WebToolsManager()
        logger.debug("[WebManager] Created web tools manager instance")
    return _web_tools_manager
