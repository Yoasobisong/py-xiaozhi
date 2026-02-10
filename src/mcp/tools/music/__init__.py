"""音乐播放器工具包.

提供基础的音乐播放控制功能：播放、暂停、停止。
"""

from .manager import MusicToolsManager, get_music_tools_manager
from .music_player import get_music_player_instance

__all__ = [
    "MusicToolsManager",
    "get_music_tools_manager",
    "get_music_player_instance",
]
