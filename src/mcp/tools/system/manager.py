"""系统工具管理器.

负责系统工具的初始化、配置和MCP工具注册
"""

from typing import Any, Dict

from src.utils.logging_config import get_logger

from .app_management.killer import kill_application, list_running_applications
from .app_management.launcher import launch_application
from .app_management.scanner import scan_installed_applications
from .tools import (
    cancel_shutdown,
    get_brightness,
    get_top_processes,
    get_volume,
    lock_screen,
    restart_system,
    set_brightness,
    set_volume,
    shutdown_system,
    sleep_system,
)

logger = get_logger(__name__)


class SystemToolsManager:
    """
    系统工具管理器.
    """

    def __init__(self):
        """
        初始化系统工具管理器.
        """
        self._initialized = False
        logger.info("[SystemManager] 系统工具管理器初始化")

    def init_tools(self, add_tool, PropertyList, Property, PropertyType):
        """
        初始化并注册所有系统工具.
        """
        try:
            logger.info("[SystemManager] 开始注册系统工具")

            # 注册音量控制工具
            self._register_volume_control_tool(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册音量获取工具
            self._register_volume_get_tool(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册应用程序启动工具
            self._register_app_launcher_tool(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册应用程序扫描工具
            self._register_app_scanner_tool(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册应用程序关闭工具
            self._register_app_killer_tools(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册电源管理工具
            self._register_power_management_tools(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册亮度控制工具
            self._register_brightness_tools(
                add_tool, PropertyList, Property, PropertyType
            )

            # 注册进程资源监控工具
            self._register_top_processes_tool(
                add_tool, PropertyList, Property, PropertyType
            )

            self._initialized = True
            logger.info("[SystemManager] 系统工具注册完成")

        except Exception as e:
            logger.error(f"[SystemManager] 系统工具注册失败: {e}", exc_info=True)
            raise

    def _register_volume_control_tool(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        注册音量控制工具.
        """
        volume_props = PropertyList(
            [Property("volume", PropertyType.INTEGER, min_value=0, max_value=100)]
        )
        add_tool(
            (
                "self.audio_speaker.set_volume",
                "Set the system speaker volume to an absolute value (0-100).\n"
                "Use when user mentions: volume, sound, louder, quieter, mute, unmute, adjust volume.\n"
                "Examples: 'set volume to 50', 'turn volume up', 'make it louder', 'mute', "
                "'音量设为50', '调大声音', '声音小一点', '静音'.\n"
                "Parameter:\n"
                "- volume: Integer (0-100) representing the target volume level. Set to 0 for mute.",
                volume_props,
                set_volume,
            )
        )
        logger.debug("[SystemManager] 注册音量控制工具成功")

    def _register_volume_get_tool(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        注册音量获取工具.
        """
        get_volume_props = PropertyList([])
        add_tool(
            (
                "self.audio_speaker.get_volume",
                "Get the current system speaker volume level.\n"
                "Use when user asks about: current volume, volume level, how loud, what's the volume.\n"
                "Examples: 'what is the current volume?', 'how loud is it?', 'check volume level', "
                "'现在音量多少?', '查看音量', '音量是多少'.\n"
                "Returns:\n"
                "- Integer (0-100) representing the current volume level.",
                get_volume_props,
                get_volume,
            )
        )
        logger.debug("[SystemManager] 注册音量获取工具成功")

    def _register_app_launcher_tool(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        注册应用程序启动工具.
        """
        app_props = PropertyList([Property("app_name", PropertyType.STRING)])
        add_tool(
            (
                "self.application.launch",
                "Launch desktop applications and software programs by name. This tool "
                "opens applications installed on the user's computer across Windows, "
                "macOS, and Linux platforms. It automatically detects the operating "
                "system and uses appropriate launch methods.\n"
                "Use this tool when the user wants to:\n"
                "1. Open specific software applications (e.g., 'QQ', 'QQ音乐', 'WeChat', '微信')\n"
                "2. Launch system utilities (e.g., 'Calculator', '计算器', 'Notepad', '记事本')\n"
                "3. Start browsers (e.g., 'Chrome', 'Firefox', 'Safari')\n"
                "4. Open media players (e.g., 'VLC', 'Windows Media Player')\n"
                "5. Launch development tools (e.g., 'VS Code', 'PyCharm')\n"
                "6. Start games or other installed programs\n\n"
                "Examples of valid app names:\n"
                "- Chinese: 'QQ音乐', '微信', '计算器', '记事本', '浏览器'\n"
                "- English: 'QQ', 'WeChat', 'Calculator', 'Notepad', 'Chrome'\n"
                "- Mixed: 'QQ Music', 'Microsoft Word', 'Adobe Photoshop'\n\n"
                "The system will try multiple launch strategies including direct execution, "
                "system commands, and path searching to find and start the application.",
                app_props,
                launch_application,
            )
        )
        logger.debug("[SystemManager] 注册应用程序启动工具成功")

    def _register_app_scanner_tool(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        注册应用程序扫描工具.
        """
        scanner_props = PropertyList(
            [Property("force_refresh", PropertyType.BOOLEAN, default_value=False)]
        )
        add_tool(
            (
                "self.application.scan_installed",
                "Scan and list all installed applications on the system. This tool "
                "provides a comprehensive list of available applications that can be "
                "launched using the launch tool. It scans system directories, registry "
                "(Windows), and application folders to find installed software.\n"
                "Use this tool when:\n"
                "1. User asks what applications are available on the system\n"
                "2. You need to find the correct application name before launching\n"
                "3. User wants to see all installed software\n"
                "4. Application launch fails and you need to check available apps\n\n"
                "The scan results include both system applications (Calculator, Notepad) "
                "and user-installed software (QQ, WeChat, Chrome, etc.). Each application "
                "entry contains the clean name for launching and display name for reference.\n\n"
                "After scanning, use the 'name' field from results with self.application.launch "
                "to start applications. For example, if scan shows {name: 'QQ', display_name: 'QQ音乐'}, "
                "use self.application.launch with app_name='QQ' to launch it.",
                scanner_props,
                scan_installed_applications,
            )
        )
        logger.debug("[SystemManager] 注册应用程序扫描工具成功")

    def _register_app_killer_tools(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        注册应用程序关闭工具.
        """
        # 注册应用程序关闭工具
        killer_props = PropertyList(
            [
                Property("app_name", PropertyType.STRING),
                Property("force", PropertyType.BOOLEAN, default_value=False),
            ]
        )
        add_tool(
            (
                "self.application.kill",
                "Close or terminate running applications by name. This tool can gracefully "
                "close applications or force-kill them if needed. It automatically finds "
                "running processes matching the application name and terminates them.\n"
                "Use this tool when:\n"
                "1. User asks to close, quit, or exit an application\n"
                "2. User wants to stop or terminate a running program\n"
                "3. Application is unresponsive and needs to be force-closed\n"
                "4. User says 'close QQ', 'quit Chrome', 'stop music player', etc.\n\n"
                "Parameters:\n"
                "- app_name: Name of the application to close (e.g., 'QQ', 'Chrome', 'Calculator')\n"
                "- force: Set to true for force-kill unresponsive applications (default: false)\n\n"
                "The tool will find all running processes matching the application name and "
                "attempt to close them gracefully. If force=true, it will use system kill "
                "commands to immediately terminate the processes.",
                killer_props,
                kill_application,
            )
        )

        # 注册运行中应用程序列表工具
        list_props = PropertyList(
            [Property("filter_name", PropertyType.STRING, default_value="")]
        )
        add_tool(
            (
                "self.application.list_running",
                "List all currently running applications and processes. This tool provides "
                "real-time information about active applications on the system, including "
                "process IDs, names, and commands.\n"
                "Use this tool when:\n"
                "1. User asks what applications are currently running\n"
                "2. You need to check if a specific application is running before closing it\n"
                "3. User wants to see active processes or programs\n"
                "4. Troubleshooting application issues\n\n"
                "Parameters:\n"
                "- filter_name: Optional filter to show only applications containing this name\n\n"
                "Returns detailed information about running applications including process IDs "
                "which can be useful for targeted application management.",
                list_props,
                list_running_applications,
            )
        )
        logger.debug("[SystemManager] 注册应用程序关闭工具成功")

    def _register_power_management_tools(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        Register power management tools (shutdown, restart, sleep, cancel).
        """
        # Shutdown
        shutdown_props = PropertyList(
            [Property("delay", PropertyType.INTEGER, default_value=30,
                       min_value=0, max_value=3600)]
        )
        add_tool(
            (
                "system.shutdown",
                "Shutdown the computer. Schedules a system shutdown with a delay.\n"
                "Use when user says: '关机', '关闭电脑', 'shutdown', 'turn off computer'.\n"
                "Parameters:\n"
                "- delay: Seconds before shutdown (default 30, gives time to cancel).\n"
                "The user can cancel with system.cancel_shutdown before the delay expires.",
                shutdown_props,
                shutdown_system,
            )
        )

        # Restart
        restart_props = PropertyList(
            [Property("delay", PropertyType.INTEGER, default_value=30,
                       min_value=0, max_value=3600)]
        )
        add_tool(
            (
                "system.restart",
                "Restart the computer. Schedules a system restart with a delay.\n"
                "Use when user says: '重启', '重启电脑', 'restart', 'reboot'.\n"
                "Parameters:\n"
                "- delay: Seconds before restart (default 30).\n"
                "The user can cancel with system.cancel_shutdown before the delay expires.",
                restart_props,
                restart_system,
            )
        )

        # Sleep
        sleep_props = PropertyList([])
        add_tool(
            (
                "system.sleep",
                "Put the computer to sleep/suspend mode.\n"
                "Use when user says: '休眠', '睡眠', '待机', 'sleep', 'suspend', "
                "'put computer to sleep'.\n"
                "No parameters needed. Takes effect immediately.",
                sleep_props,
                sleep_system,
            )
        )

        # Cancel shutdown
        cancel_props = PropertyList([])
        add_tool(
            (
                "system.cancel_shutdown",
                "Cancel a previously scheduled shutdown or restart.\n"
                "Use when user says: '取消关机', '取消重启', '不要关机了', "
                "'cancel shutdown', 'cancel restart'.\n"
                "Only works if a shutdown/restart was scheduled with a delay.",
                cancel_props,
                cancel_shutdown,
            )
        )

        # Lock screen
        lock_props = PropertyList([])
        add_tool(
            (
                "system.lock_screen",
                "Lock the screen / workstation.\n"
                "Use when user says: '锁屏', '锁定屏幕', '锁定电脑', "
                "'lock screen', 'lock computer', 'lock workstation'.\n"
                "No parameters needed. Takes effect immediately.",
                lock_props,
                lock_screen,
            )
        )
        logger.debug("[SystemManager] 注册电源管理工具成功")

    def _register_brightness_tools(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        Register screen brightness control tools.
        """
        # Set brightness
        brightness_props = PropertyList(
            [Property("brightness", PropertyType.INTEGER,
                       min_value=0, max_value=100)]
        )
        add_tool(
            (
                "system.set_brightness",
                "Set the screen brightness level (0-100).\n"
                "Use when user says: '调亮度', '亮度调到50', '屏幕太亮了', "
                "'屏幕太暗了', 'set brightness', 'make screen brighter/dimmer'.\n"
                "Parameter:\n"
                "- brightness: Integer (0-100), 0 = darkest, 100 = brightest.",
                brightness_props,
                set_brightness,
            )
        )

        # Get brightness
        get_brightness_props = PropertyList([])
        add_tool(
            (
                "system.get_brightness",
                "Get the current screen brightness level.\n"
                "Use when user says: '当前亮度多少', '亮度是多少', "
                "'what is the brightness', 'check brightness'.\n"
                "Returns the current brightness percentage.",
                get_brightness_props,
                get_brightness,
            )
        )
        logger.debug("[SystemManager] 注册亮度控制工具成功")

    def _register_top_processes_tool(
        self, add_tool, PropertyList, Property, PropertyType
    ):
        """
        Register system resource monitoring tool (top processes).
        """
        top_props = PropertyList(
            [
                Property("sort_by", PropertyType.STRING, default_value="cpu"),
                Property("count", PropertyType.INTEGER, default_value=10,
                         min_value=1, max_value=50),
                Property("filter_name", PropertyType.STRING, default_value=""),
            ]
        )
        add_tool(
            (
                "system.top_processes",
                "查看系统资源占用最高的进程。\n"
                "Use when user says: '什么在占CPU', '内存占用', '哪个进程最耗资源', "
                "'电脑怎么这么卡', '卡顿', '系统资源', 'top processes', "
                "'what is using CPU/memory', 'why is my computer slow'.\n"
                "Parameters:\n"
                "- sort_by: 'cpu' or 'memory' (default: 'cpu')\n"
                "- count: Number of processes to return (1-50, default: 10)\n"
                "- filter_name: Optional keyword to filter process names\n\n"
                "Returns system summary (total CPU/memory usage) and top N processes "
                "with CPU%, memory%, memory_mb for each.",
                top_props,
                get_top_processes,
            )
        )
        logger.debug("[SystemManager] 注册进程资源监控工具成功")

    def is_initialized(self) -> bool:
        """
        检查管理器是否已初始化.
        """
        return self._initialized

    def get_status(self) -> Dict[str, Any]:
        """
        获取管理器状态.
        """
        available_tools = [
            "set_volume",
            "get_volume",
            "launch_application",
            "scan_installed_applications",
            "kill_application",
            "list_running_applications",
            "top_processes",
        ]
        return {
            "initialized": self._initialized,
            "tools_count": len(available_tools),
            "available_tools": available_tools,
        }


# 全局管理器实例
_system_tools_manager = None


def get_system_tools_manager() -> SystemToolsManager:
    """
    获取系统工具管理器单例.
    """
    global _system_tools_manager
    if _system_tools_manager is None:
        _system_tools_manager = SystemToolsManager()
        logger.debug("[SystemManager] 创建系统工具管理器实例")
    return _system_tools_manager
