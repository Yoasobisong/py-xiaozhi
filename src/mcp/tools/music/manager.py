"""Music tools manager.

Registers MCP tools for controlling the NetEase Cloud Music desktop client.
Tools: play, search_and_play, play_favorites, pause, stop,
       next_track, previous_track, get_current_track.
"""

from typing import Any, Dict

from src.utils.logging_config import get_logger

from .music_player import get_music_player_instance

logger = get_logger(__name__)


class MusicToolsManager:
    """Music tools manager."""

    def __init__(self):
        self._initialized = False
        self._music_player = None
        logger.info("[MusicManager] Music tools manager initialized")

    def init_tools(self, add_tool, PropertyList, Property, PropertyType):
        """Register all music MCP tools."""
        try:
            logger.info("[MusicManager] Registering music tools")
            self._music_player = get_music_player_instance()

            # --- Play (generic) ---
            async def play_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.play()
                return result.get("message", "播放完成")

            add_tool((
                "music_player.play",
                "Play music. Opens NetEase Cloud Music desktop client and starts "
                "playback. If the app is not running, it will be launched first.\n"
                "Use when user says generic phrases like: '放首歌', '听歌', "
                "'播放音乐', '继续播放', '放个歌', 'play music'.\n"
                "No parameters needed. Plays whatever was last queued.",
                PropertyList(),
                play_wrapper,
            ))

            # --- Search and play ---
            async def search_and_play_wrapper(args: Dict[str, Any]) -> str:
                song_name = args.get("song_name", "")
                result = await self._music_player.search_and_play(song_name)
                return result.get("message", "搜索播放完成")

            add_tool((
                "music_player.search_and_play",
                "Search for a specific song by name and play it in NetEase Cloud "
                "Music desktop client. Uses the NetEase API to find the song.\n"
                "Use when user mentions a specific song or artist: "
                "'播放稻香', '听一下孤勇者', '放周杰伦的歌', "
                "'play Shape of You', '来首Beyond的歌'.\n"
                "Parameter:\n"
                "- song_name: Song name, artist name, or both.",
                PropertyList([Property("song_name", PropertyType.STRING)]),
                search_and_play_wrapper,
            ))

            # --- Play favorites ---
            async def play_favorites_wrapper(args: Dict[str, Any]) -> str:
                shuffle = args.get("shuffle", False)
                result = await self._music_player.play_favorites(shuffle=shuffle)
                return result.get("message", "播放收藏")

            add_tool((
                "music_player.play_favorites",
                "Play the user's 'My Likes' (我喜欢的音乐) playlist in NetEase "
                "Cloud Music. Requires MUSIC_U cookie to be configured.\n"
                "Use when user says: '播放我喜欢的歌', '放我的收藏', "
                "'随机播放我喜欢的音乐', 'play my favorites'.\n"
                "Parameter:\n"
                "- shuffle: true for random order, false for sequential (default).",
                PropertyList([
                    Property("shuffle", PropertyType.BOOLEAN, default_value=False),
                ]),
                play_favorites_wrapper,
            ))

            # --- Pause ---
            async def pause_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.pause()
                return result.get("message", "已暂停")

            add_tool((
                "music_player.pause",
                "Pause the currently playing music.\n"
                "Do NOT call this during TTS speech — TTS automatically pauses music.\n"
                "Only call when user explicitly says: '暂停', '暂停音乐', "
                "'先停一下', 'pause music'.",
                PropertyList(),
                pause_wrapper,
            ))

            # --- Stop ---
            async def stop_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.stop()
                return result.get("message", "已停止")

            add_tool((
                "music_player.stop",
                "Completely stop music playback.\n"
                "Use when user says: '停止音乐', '关闭音乐', '别放了', "
                "'不听了', 'stop music'.",
                PropertyList(),
                stop_wrapper,
            ))

            # --- Next track ---
            async def next_track_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.next_track()
                return result.get("message", "已切换")

            add_tool((
                "music_player.next_track",
                "Skip to the next track.\n"
                "Use when user says: '下一首', '换一首', '切歌', "
                "'next song', 'skip'.",
                PropertyList(),
                next_track_wrapper,
            ))

            # --- Previous track ---
            async def previous_track_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.previous_track()
                return result.get("message", "已切换")

            add_tool((
                "music_player.previous_track",
                "Go back to the previous track.\n"
                "Use when user says: '上一首', '前一首', 'previous song'.",
                PropertyList(),
                previous_track_wrapper,
            ))

            # --- Get current track ---
            async def get_current_track_wrapper(args: Dict[str, Any]) -> str:
                result = await self._music_player.get_current_track()
                return result.get("message", "无法获取")

            add_tool((
                "music_player.get_current_track",
                "Get information about the currently playing track. Reports whether "
                "music is playing and what song it is (from the app window title).\n"
                "Use when user says: '现在放的什么歌', '这首歌叫什么', "
                "'在听什么', 'what song is this', 'what is playing'.",
                PropertyList(),
                get_current_track_wrapper,
            ))

            self._initialized = True
            logger.info("[MusicManager] Music tools registration complete (8 tools)")

        except Exception as e:
            logger.error(
                f"[MusicManager] Music tools registration failed: {e}",
                exc_info=True,
            )
            raise

    def is_initialized(self) -> bool:
        """Check if the manager is initialized."""
        return self._initialized


# Global manager instance
_music_tools_manager = None


def get_music_tools_manager() -> MusicToolsManager:
    """Get the singleton music tools manager."""
    global _music_tools_manager
    if _music_tools_manager is None:
        _music_tools_manager = MusicToolsManager()
        logger.debug("[MusicManager] Created music tools manager instance")
    return _music_tools_manager
