"""系统工具包.

提供完整的系统管理功能，包括设备状态查询、音频控制等操作。
"""

from .manager import SystemToolsManager, get_system_tools_manager
from .tools import (
    cancel_shutdown,
    get_brightness,
    get_volume,
    lock_screen,
    restart_system,
    set_brightness,
    set_volume,
    shutdown_system,
    sleep_system,
)

__all__ = [
    "SystemToolsManager",
    "get_system_tools_manager",
    "set_volume",
    "get_volume",
    "shutdown_system",
    "restart_system",
    "sleep_system",
    "lock_screen",
    "cancel_shutdown",
    "set_brightness",
    "get_brightness",
]
