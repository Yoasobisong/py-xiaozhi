"""Network tools manager.

Registers network diagnostic MCP tools (ping, speedtest, get_ip).
"""

from typing import Any, Dict

from src.utils.logging_config import get_logger

from .tools import get_ip, ping_host, speedtest

logger = get_logger(__name__)


class NetworkToolsManager:
    """Network tools manager."""

    def __init__(self):
        self._initialized = False
        logger.info("[NetworkManager] Network tools manager initialized")

    def init_tools(self, add_tool, PropertyList, Property, PropertyType):
        """Register all network tools."""
        try:
            logger.info("[NetworkManager] Registering network tools")

            # Ping
            ping_props = PropertyList(
                [
                    Property("host", PropertyType.STRING),
                    Property(
                        "count", PropertyType.INTEGER,
                        default_value=4, min_value=1, max_value=20,
                    ),
                ]
            )
            add_tool(
                (
                    "network.ping",
                    "Ping a host to check connectivity and measure latency.\n"
                    "Use when user says: 'ping百度', 'ping一下谷歌', '测试网络连通性', "
                    "'ping baidu.com', 'check if server is reachable'.\n"
                    "Parameters:\n"
                    "- host: Hostname or IP address to ping (e.g. 'baidu.com', '8.8.8.8')\n"
                    "- count: Number of ping packets (default 4, max 20)\n"
                    "Returns: average latency in ms and packet loss percentage.",
                    ping_props,
                    ping_host,
                )
            )

            # Speed test
            speedtest_props = PropertyList([])
            add_tool(
                (
                    "network.speedtest",
                    "Run a simple download speed test.\n"
                    "Use when user says: '测速', '测一下网速', '网速多少', "
                    "'speed test', 'check internet speed', '下载速度'.\n"
                    "No parameters needed. Downloads a test file and measures speed.\n"
                    "Returns: download speed in Mbps.",
                    speedtest_props,
                    speedtest,
                )
            )

            # Get IP
            ip_props = PropertyList([])
            add_tool(
                (
                    "network.get_ip",
                    "Get the local (LAN) and public IP addresses.\n"
                    "Use when user says: '我的IP是多少', '查看IP地址', '本机IP', "
                    "'what is my IP', 'show IP address', '公网IP', '局域网IP'.\n"
                    "No parameters needed.\n"
                    "Returns: local (LAN) IP and public (WAN) IP.",
                    ip_props,
                    get_ip,
                )
            )

            self._initialized = True
            logger.info("[NetworkManager] Network tools registered successfully")

        except Exception as e:
            logger.error(
                f"[NetworkManager] Network tools registration failed: {e}",
                exc_info=True,
            )
            raise

    def is_initialized(self) -> bool:
        return self._initialized

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "tools_count": 3,
            "available_tools": ["ping", "speedtest", "get_ip"],
        }


# Singleton
_network_tools_manager = None


def get_network_tools_manager() -> NetworkToolsManager:
    """Get network tools manager singleton."""
    global _network_tools_manager
    if _network_tools_manager is None:
        _network_tools_manager = NetworkToolsManager()
        logger.debug("[NetworkManager] Created network tools manager instance")
    return _network_tools_manager
