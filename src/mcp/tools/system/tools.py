"""系统工具实现.

提供具体的系统工具功能实现
"""

import asyncio
import subprocess
import sys
from typing import Any, Dict

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def set_volume(args: Dict[str, Any]) -> bool:
    """
    设置音量.
    """
    try:
        volume = args["volume"]
        logger.info(f"[SystemTools] 设置音量到 {volume}")

        # 验证音量范围
        if not (0 <= volume <= 100):
            logger.warning(f"[SystemTools] 音量值超出范围: {volume}")
            return False

        # 直接使用VolumeController设置音量
        from src.utils.volume_controller import VolumeController

        # 检查依赖并创建音量控制器
        if not VolumeController.check_dependencies():
            logger.warning("[SystemTools] 音量控制依赖不完整，无法设置音量")
            return False

        volume_controller = VolumeController()
        await asyncio.to_thread(volume_controller.set_volume, volume)
        logger.info(f"[SystemTools] 音量设置成功: {volume}")
        return True

    except KeyError:
        logger.error("[SystemTools] 缺少volume参数")
        return False
    except Exception as e:
        logger.error(f"[SystemTools] 设置音量失败: {e}", exc_info=True)
        return False


async def get_volume(args: Dict[str, Any]) -> int:
    """
    获取当前音量.
    """
    try:
        logger.info("[SystemTools] 获取当前音量")

        # 直接使用VolumeController获取音量
        from src.utils.volume_controller import VolumeController

        # 检查依赖并创建音量控制器
        if not VolumeController.check_dependencies():
            logger.warning("[SystemTools] 音量控制依赖不完整，返回默认音量")
            return VolumeController.DEFAULT_VOLUME

        volume_controller = VolumeController()
        current_volume = await asyncio.to_thread(volume_controller.get_volume)
        logger.info(f"[SystemTools] 当前音量: {current_volume}")
        return current_volume

    except Exception as e:
        logger.error(f"[SystemTools] 获取音量失败: {e}", exc_info=True)
        from src.utils.volume_controller import VolumeController

        return VolumeController.DEFAULT_VOLUME


async def _get_audio_status() -> Dict[str, Any]:
    """
    获取音频状态.
    """
    try:
        from src.utils.volume_controller import VolumeController

        if VolumeController.check_dependencies():
            volume_controller = VolumeController()
            # 使用线程池获取音量，避免阻塞
            current_volume = await asyncio.to_thread(volume_controller.get_volume)
            return {
                "volume": current_volume,
                "muted": current_volume == 0,
                "available": True,
            }
        else:
            return {
                "volume": 50,
                "muted": False,
                "available": False,
                "reason": "Dependencies not available",
            }

    except Exception as e:
        logger.warning(f"[SystemTools] 获取音频状态失败: {e}")
        return {"volume": 50, "muted": False, "available": False, "error": str(e)}


def _get_application_status() -> Dict[str, Any]:
    """
    获取应用状态信息.
    """
    try:
        from src.application import Application
        from src.iot.thing_manager import ThingManager

        app = Application.get_instance()
        thing_manager = ThingManager.get_instance()

        # DeviceState的值直接是字符串，不需要访问.name属性
        device_state = str(app.get_device_state())
        iot_count = len(thing_manager.things) if thing_manager else 0

        return {
            "device_state": device_state,
            "iot_devices": iot_count,
        }

    except Exception as e:
        logger.warning(f"[SystemTools] 获取应用状态失败: {e}")
        return {"device_state": "unknown", "iot_devices": 0, "error": str(e)}


async def shutdown_system(args: Dict[str, Any]) -> str:
    """
    Shutdown the system with a delay.
    """
    delay = args.get("delay", 30)
    try:
        logger.info(f"[SystemTools] Shutting down system in {delay} seconds")

        if sys.platform == "win32":
            cmd = ["shutdown", "/s", "/t", str(delay)]
        elif sys.platform == "darwin":
            cmd = ["sudo", "shutdown", "-h", f"+{max(1, delay // 60)}"]
        else:
            cmd = ["shutdown", "-h", f"+{max(1, delay // 60)}"]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=10
        )
        logger.info(f"[SystemTools] Shutdown scheduled in {delay} seconds")
        return f"System will shutdown in {delay} seconds. Use 'cancel_shutdown' to abort."

    except Exception as e:
        logger.error(f"[SystemTools] Shutdown failed: {e}", exc_info=True)
        return f"Shutdown failed: {e}"


async def restart_system(args: Dict[str, Any]) -> str:
    """
    Restart the system with a delay.
    """
    delay = args.get("delay", 30)
    try:
        logger.info(f"[SystemTools] Restarting system in {delay} seconds")

        if sys.platform == "win32":
            cmd = ["shutdown", "/r", "/t", str(delay)]
        elif sys.platform == "darwin":
            cmd = ["sudo", "shutdown", "-r", f"+{max(1, delay // 60)}"]
        else:
            cmd = ["shutdown", "-r", f"+{max(1, delay // 60)}"]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=10
        )
        logger.info(f"[SystemTools] Restart scheduled in {delay} seconds")
        return f"System will restart in {delay} seconds. Use 'cancel_shutdown' to abort."

    except Exception as e:
        logger.error(f"[SystemTools] Restart failed: {e}", exc_info=True)
        return f"Restart failed: {e}"


async def sleep_system(args: Dict[str, Any]) -> str:
    """
    Put the system to sleep/suspend.
    """
    try:
        logger.info("[SystemTools] Putting system to sleep")

        if sys.platform == "win32":
            # Use rundll32 to trigger sleep (not hibernate)
            cmd = [
                "rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"
            ]
        elif sys.platform == "darwin":
            cmd = ["pmset", "sleepnow"]
        else:
            cmd = ["systemctl", "suspend"]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=10
        )
        logger.info("[SystemTools] Sleep command executed")
        return "System is going to sleep."

    except Exception as e:
        logger.error(f"[SystemTools] Sleep failed: {e}", exc_info=True)
        return f"Sleep failed: {e}"


async def lock_screen(args: Dict[str, Any]) -> str:
    """
    Lock the screen / workstation.
    """
    try:
        logger.info("[SystemTools] Locking screen")

        if sys.platform == "win32":
            cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
        elif sys.platform == "darwin":
            cmd = [
                "/System/Library/CoreServices/Menu Extras/User.menu/"
                "Contents/Resources/CGSession", "-suspend"
            ]
        else:
            cmd = ["loginctl", "lock-session"]

        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=10
        )
        logger.info("[SystemTools] Screen locked")
        return "Screen locked."

    except Exception as e:
        logger.error(f"[SystemTools] Lock screen failed: {e}", exc_info=True)
        return f"Lock screen failed: {e}"


async def cancel_shutdown(args: Dict[str, Any]) -> str:
    """
    Cancel a scheduled shutdown or restart.
    """
    try:
        logger.info("[SystemTools] Cancelling scheduled shutdown/restart")

        if sys.platform == "win32":
            cmd = ["shutdown", "/a"]
        else:
            cmd = ["shutdown", "-c"]

        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            logger.info("[SystemTools] Shutdown cancelled successfully")
            return "Scheduled shutdown/restart has been cancelled."
        else:
            return f"No scheduled shutdown to cancel, or cancel failed: {result.stderr}"

    except Exception as e:
        logger.error(f"[SystemTools] Cancel shutdown failed: {e}", exc_info=True)
        return f"Cancel shutdown failed: {e}"


async def set_brightness(args: Dict[str, Any]) -> str:
    """
    Set screen brightness level.
    """
    brightness = args["brightness"]
    try:
        logger.info(f"[SystemTools] Setting brightness to {brightness}")

        if sys.platform == "win32":
            try:
                import screen_brightness_control as sbc

                await asyncio.to_thread(sbc.set_brightness, brightness)
                logger.info(f"[SystemTools] Brightness set to {brightness}")
                return f"Brightness set to {brightness}%"
            except ImportError:
                # Fallback: use WMI via PowerShell
                cmd = [
                    "powershell", "-Command",
                    f"(Get-WmiObject -Namespace root/WMI "
                    f"-Class WmiMonitorBrightnessMethods)"
                    f".WmiSetBrightness(1,{brightness})"
                ]
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return f"Brightness set to {brightness}%"
                return f"Failed to set brightness: {result.stderr}"
        elif sys.platform == "darwin":
            # macOS: use brightness command if available
            cmd = ["brightness", str(brightness / 100.0)]
            await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=10
            )
            return f"Brightness set to {brightness}%"
        else:
            # Linux: use xrandr or brightnessctl
            cmd = ["brightnessctl", "set", f"{brightness}%"]
            await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=10
            )
            return f"Brightness set to {brightness}%"

    except Exception as e:
        logger.error(f"[SystemTools] Set brightness failed: {e}", exc_info=True)
        return f"Set brightness failed: {e}"


async def get_brightness(args: Dict[str, Any]) -> str:
    """
    Get current screen brightness level.
    """
    try:
        logger.info("[SystemTools] Getting current brightness")

        if sys.platform == "win32":
            try:
                import screen_brightness_control as sbc

                brightness = await asyncio.to_thread(sbc.get_brightness)
                # sbc.get_brightness returns a list of brightness values
                current = brightness[0] if isinstance(brightness, list) else brightness
                logger.info(f"[SystemTools] Current brightness: {current}")
                return f"Current brightness: {current}%"
            except ImportError:
                cmd = [
                    "powershell", "-Command",
                    "(Get-WmiObject -Namespace root/WMI "
                    "-Class WmiMonitorBrightness).CurrentBrightness"
                ]
                result = await asyncio.to_thread(
                    subprocess.run, cmd, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return f"Current brightness: {result.stdout.strip()}%"
                return "Failed to get brightness"
        elif sys.platform == "darwin":
            cmd = ["brightness", "-l"]
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=10
            )
            return f"Brightness info: {result.stdout}"
        else:
            cmd = ["brightnessctl", "get"]
            result = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, text=True, timeout=10
            )
            return f"Current brightness: {result.stdout.strip()}"

    except Exception as e:
        logger.error(f"[SystemTools] Get brightness failed: {e}", exc_info=True)
        return f"Get brightness failed: {e}"

