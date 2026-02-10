"""NetEase Cloud Music controller.

Controls the NetEase Cloud Music desktop client via:
- orpheus:// URI scheme (open specific songs/playlists)
- Windows media keys (play/pause/stop/next/prev)
- pyncm API (search songs, get playlists)
- pycaw audio session API (detect real playback state)
"""

import asyncio
import ctypes
import ctypes.wintypes
import os
import platform
import subprocess
from typing import Optional

from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# NetEase Cloud Music API (optional dependency)
try:
    import pyncm
    from pyncm.apis import cloudsearch as ncm_search
    from pyncm.apis import login as ncm_login
    from pyncm.apis import user as ncm_user

    PYNCM_AVAILABLE = True
except ImportError:
    PYNCM_AVAILABLE = False

# Windows media key virtual-key codes
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

# NetEase Cloud Music process name
NETEASE_PROCESS_NAME = "cloudmusic.exe"

# Volume level during TTS playback (0.0 ~ 1.0)
TTS_DUCK_LEVEL = 0.2


class MusicPlayer:
    """Singleton music controller for NetEase Cloud Music desktop client.

    Actual playback state is detected from Windows audio sessions (pycaw)
    to avoid stale state bugs. Volume ducking is used during TTS speech
    instead of pause/resume to keep music playing at lower volume.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # TTS volume ducking
        self._original_volume: Optional[float] = None

        # NetEase Cloud Music API state
        self._ncm_initialized = False
        self._ncm_has_vip_cookie = False
        self._user_id: Optional[int] = None
        self._likes_playlist_id: Optional[int] = None

        # Initialize NetEase API
        self._init_netease_api()
        logger.info("MusicPlayer initialized")

    # ------------------------------------------------------------------
    # NetEase API initialization
    # ------------------------------------------------------------------

    def _init_netease_api(self):
        """Initialize NetEase Cloud Music API session with MUSIC_U cookie."""
        if not PYNCM_AVAILABLE:
            logger.warning("pyncm not installed. Search/favorites unavailable.")
            return

        try:
            config_manager = ConfigManager.get_instance()
            music_u = config_manager.get_config("MUSIC.NETEASE_MUSIC_U") or ""

            if music_u:
                pyncm.SetCurrentSession(pyncm.Session())
                pyncm.GetCurrentSession().cookies.set("MUSIC_U", music_u)
                self._ncm_initialized = True
                self._ncm_has_vip_cookie = True
                logger.info("NetEase Cloud Music: logged in with MUSIC_U cookie")
            else:
                logger.warning(
                    "MUSIC.NETEASE_MUSIC_U not configured, using anonymous login. "
                    "VIP songs will only play ~30s preview."
                )
                ncm_login.LoginViaAnonymousAccount()
                self._ncm_initialized = True
                logger.info("NetEase Cloud Music: anonymous login")

        except Exception as e:
            logger.error(f"NetEase Cloud Music API init failed: {e}")
            self._ncm_initialized = False

    def _ensure_user_id(self):
        """Fetch and cache the current user ID."""
        if self._user_id is not None:
            return
        if not self._ncm_has_vip_cookie:
            return
        try:
            status = ncm_login.GetCurrentLoginStatus()
            profile = status.get("profile", {})
            if profile:
                self._user_id = profile.get("userId")
                logger.info(f"NetEase user ID: {self._user_id}")
        except Exception as e:
            logger.warning(f"Failed to get user ID: {e}")

    def _ensure_likes_playlist_id(self):
        """Fetch and cache the user's 'My Likes' playlist ID."""
        if self._likes_playlist_id is not None:
            return
        self._ensure_user_id()
        if self._user_id is None:
            return
        try:
            result = ncm_user.GetUserPlaylists(user_id=self._user_id, limit=1)
            playlists = result.get("playlist", [])
            if playlists:
                self._likes_playlist_id = playlists[0].get("id")
                logger.info(f"Likes playlist ID: {self._likes_playlist_id}")
        except Exception as e:
            logger.warning(f"Failed to get likes playlist: {e}")

    # ------------------------------------------------------------------
    # Windows media key helper
    # ------------------------------------------------------------------

    def _send_media_key(self, vk_code: int):
        """Send a Windows media key event via user32.keybd_event."""
        if platform.system() != "Windows":
            logger.warning("Media key control only supported on Windows")
            return
        try:
            user32 = ctypes.windll.user32
            user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            user32.keybd_event(
                vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0
            )
        except Exception as e:
            logger.error(f"Failed to send media key: {e}")

    def _open_uri(self, uri: str):
        """Open an orpheus:// URI to control the desktop client."""
        try:
            os.startfile(uri)
            logger.info(f"Opened URI: {uri}")
        except OSError:
            # orpheus:// not registered, fall back to web player
            if uri.startswith("orpheus://song/"):
                song_id = uri.split("/")[-1]
                web_url = f"https://music.163.com/#/song?id={song_id}"
            elif uri.startswith("orpheus://playlist/"):
                playlist_id = uri.split("/")[-1]
                web_url = f"https://music.163.com/#/playlist?id={playlist_id}"
            else:
                logger.error(f"Failed to open URI: {uri}")
                raise

            logger.info(f"Desktop client not found, opening web: {web_url}")
            import webbrowser

            webbrowser.open(web_url)

    # ------------------------------------------------------------------
    # Playback state detection
    # ------------------------------------------------------------------

    def is_music_app_running(self) -> bool:
        """Check if NetEase Cloud Music process is running."""
        if platform.system() != "Windows":
            return False
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {NETEASE_PROCESS_NAME}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return NETEASE_PROCESS_NAME.lower() in result.stdout.lower()
        except Exception as e:
            logger.debug(f"Process check failed: {e}")
            return False

    def is_music_actually_playing(self) -> bool:
        """Check if NetEase Cloud Music is actively outputting audio.

        Uses Windows audio session API (pycaw) to detect real playback state.
        AudioSessionState: 0=Inactive, 1=Active (playing), 2=Expired.
        """
        if platform.system() != "Windows":
            return False
        try:
            from pycaw.pycaw import AudioUtilities

            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if (
                    session.Process
                    and session.Process.name().lower() == NETEASE_PROCESS_NAME
                ):
                    # AudioSessionStateActive = 1
                    if session.State == 1:
                        return True
            return False
        except ImportError:
            logger.warning("pycaw not installed, falling back to process check")
            return self.is_music_app_running()
        except Exception as e:
            logger.debug(f"Audio session check failed: {e}")
            return self.is_music_app_running()

    # ------------------------------------------------------------------
    # Volume ducking for TTS
    # ------------------------------------------------------------------

    def _get_music_session(self):
        """Get the pycaw audio session for cloudmusic.exe."""
        if platform.system() != "Windows":
            return None
        try:
            from pycaw.pycaw import AudioUtilities

            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if (
                    session.Process
                    and session.Process.name().lower() == NETEASE_PROCESS_NAME
                ):
                    return session
        except ImportError:
            logger.debug("pycaw not installed, cannot get music session")
        except Exception as e:
            logger.debug(f"Failed to get music session: {e}")
        return None

    def duck_volume(self):
        """Lower music volume for TTS speech."""
        session = self._get_music_session()
        if not session:
            return False
        try:
            vol = session.SimpleAudioVolume
            current = vol.GetMasterVolume()
            # Skip if already ducked or volume is already low
            if current <= TTS_DUCK_LEVEL:
                logger.debug(f"Volume already low ({current:.2f}), skip duck")
                return False
            self._original_volume = current
            vol.SetMasterVolume(TTS_DUCK_LEVEL, None)
            logger.info(
                f"Music volume ducked: {self._original_volume:.2f} -> {TTS_DUCK_LEVEL}"
            )
            return True
        except Exception as e:
            logger.debug(f"Duck volume failed: {e}")
            return False

    def restore_volume(self):
        """Restore music volume after TTS speech."""
        if self._original_volume is None:
            return False
        session = self._get_music_session()
        if not session:
            self._original_volume = None
            return False
        try:
            vol = session.SimpleAudioVolume
            vol.SetMasterVolume(self._original_volume, None)
            logger.info(f"Music volume restored: {self._original_volume:.2f}")
            self._original_volume = None
            return True
        except Exception as e:
            logger.debug(f"Restore volume failed: {e}")
            self._original_volume = None
            return False

    # ------------------------------------------------------------------
    # Window title detection
    # ------------------------------------------------------------------

    def _get_netease_window_title(self) -> Optional[str]:
        """Get the window title of NetEase Cloud Music main window.

        Enumerates all windows, matches by process ID to find the
        NetEase Cloud Music window, and returns its title.
        The title typically shows 'song_name - artist_name' when playing.
        """
        if platform.system() != "Windows":
            return None
        try:
            user32 = ctypes.windll.user32

            # Get NetEase Cloud Music PIDs
            result = subprocess.run(
                [
                    "tasklist", "/FI",
                    f"IMAGENAME eq {NETEASE_PROCESS_NAME}",
                    "/FO", "CSV", "/NH",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            netease_pids = set()
            for line in result.stdout.strip().split("\n"):
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    try:
                        netease_pids.add(int(parts[1]))
                    except ValueError:
                        pass

            if not netease_pids:
                return None

            # Enumerate windows and find matching title
            best_title = None
            WNDENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.wintypes.BOOL,
                ctypes.wintypes.HWND,
                ctypes.wintypes.LPARAM,
            )

            def _enum_callback(hwnd, _lparam):
                nonlocal best_title
                # Check if window is visible
                if not user32.IsWindowVisible(hwnd):
                    return True

                # Get process ID
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                if pid.value not in netease_pids:
                    return True

                # Get window title
                length = user32.GetWindowTextLengthW(hwnd) + 1
                if length <= 1:
                    return True
                buf = ctypes.create_unicode_buffer(length)
                user32.GetWindowTextW(hwnd, buf, length)
                title = buf.value.strip()

                # Skip generic/empty titles
                if title and title != "网易云音乐":
                    best_title = title

                return True

            user32.EnumWindows(WNDENUMPROC(_enum_callback), 0)
            return best_title

        except Exception as e:
            logger.debug(f"Failed to get window title: {e}")
            return None

    # ------------------------------------------------------------------
    # MCP tool methods
    # ------------------------------------------------------------------

    async def play(self) -> dict:
        """Open NetEase Cloud Music and start playing.

        If the app is not running, launches it first.
        Only sends play/pause media key if music is NOT already playing,
        to avoid toggling an already-playing track to paused.
        """
        try:
            if not await asyncio.to_thread(self.is_music_app_running):
                try:
                    await asyncio.to_thread(self._open_uri, "orpheus://")
                    logger.info("Launching NetEase Cloud Music")
                    await asyncio.sleep(3)
                except Exception as e:
                    logger.error(f"Failed to launch NetEase Cloud Music: {e}")
                    return {
                        "status": "error",
                        "message": f"无法打开网易云音乐: {e}",
                    }

            # Only send toggle key if not already playing
            is_playing = await asyncio.to_thread(self.is_music_actually_playing)
            if not is_playing:
                await asyncio.to_thread(self._send_media_key, VK_MEDIA_PLAY_PAUSE)
                logger.info("Music play command sent (was not playing)")
            else:
                logger.info("Music already playing, no toggle needed")

            return {"status": "success", "message": "已开始播放音乐"}

        except Exception as e:
            logger.error(f"Play failed: {e}", exc_info=True)
            return {"status": "error", "message": f"播放失败: {e}"}

    async def search_and_play(self, song_name: str) -> dict:
        """Search for a song and play it in the desktop client."""
        logger.info(f"search_and_play called: song_name='{song_name}'")

        if not song_name or not song_name.strip():
            return {"status": "error", "message": "歌曲名不能为空"}

        if not PYNCM_AVAILABLE or not self._ncm_initialized:
            return {
                "status": "error",
                "message": "NetEase Cloud Music API not initialized. "
                "Install pyncm: pip install pyncm",
            }

        try:
            # Search
            search_result = await asyncio.to_thread(
                ncm_search.GetSearchResult,
                keyword=song_name,
                stype=1,
                limit=10,
            )

            if not search_result or search_result.get("code") != 200:
                return {"status": "error", "message": f"搜索失败: {song_name}"}

            songs = search_result.get("result", {}).get("songs", [])
            if not songs:
                return {"status": "error", "message": f"没有找到: {song_name}"}

            # Prioritize free songs for anonymous users
            if self._ncm_has_vip_cookie:
                candidates = songs
            else:
                free_songs = [s for s in songs if s.get("fee", 0) != 1]
                vip_songs = [s for s in songs if s.get("fee", 0) == 1]
                candidates = free_songs + vip_songs

            song = candidates[0]
            song_id = song.get("id")
            title = song.get("name", song_name)
            artists = song.get("ar", []) or song.get("artists", [])
            artist = ", ".join(
                [a.get("name", "") for a in artists if a.get("name")]
            )

            display_name = f"{title} - {artist}" if artist else title

            # Open in desktop client
            await asyncio.to_thread(self._open_uri, f"orpheus://song/{song_id}")

            logger.info(f"Playing: {display_name} (id={song_id})")
            return {
                "status": "success",
                "message": f"正在播放: {display_name}",
            }

        except Exception as e:
            logger.error(f"Search and play failed: {e}", exc_info=True)
            return {"status": "error", "message": f"播放失败: {e}"}

    async def play_favorites(self, shuffle: bool = False) -> dict:
        """Play the user's 'My Likes' playlist in the desktop client."""
        logger.info(f"play_favorites called: shuffle={shuffle}, has_cookie={self._ncm_has_vip_cookie}")

        if not self._ncm_has_vip_cookie:
            return {
                "status": "error",
                "message": "需要配置 MUSIC_U cookie 才能播放收藏歌单",
            }

        try:
            await asyncio.to_thread(self._ensure_likes_playlist_id)

            if self._likes_playlist_id is None:
                return {"status": "error", "message": "无法获取「我喜欢的音乐」歌单"}

            await asyncio.to_thread(
                self._open_uri,
                f"orpheus://playlist/{self._likes_playlist_id}",
            )

            # Wait for playlist to load, then start playback
            await asyncio.sleep(1.5)
            await asyncio.to_thread(self._send_media_key, VK_MEDIA_PLAY_PAUSE)

            mode_text = "随机播放" if shuffle else "顺序播放"
            logger.info(f"Playing favorites playlist ({mode_text})")
            return {
                "status": "success",
                "message": f"正在播放「我喜欢的音乐」({mode_text})",
            }

        except Exception as e:
            logger.error(f"Play favorites failed: {e}", exc_info=True)
            return {"status": "error", "message": f"播放收藏失败: {e}"}

    async def pause(self) -> dict:
        """Pause playback via media key."""
        self._send_media_key(VK_MEDIA_PLAY_PAUSE)
        logger.info("Music paused")
        return {"status": "success", "message": "已暂停音乐"}

    async def resume(self) -> dict:
        """Resume playback via media key."""
        self._send_media_key(VK_MEDIA_PLAY_PAUSE)
        logger.info("Music resumed")
        return {"status": "success", "message": "已恢复播放"}

    async def stop(self) -> dict:
        """Stop playback via media key."""
        self._send_media_key(VK_MEDIA_STOP)
        logger.info("Music stopped")
        return {"status": "success", "message": "已停止音乐"}

    async def next_track(self) -> dict:
        """Skip to next track via media key."""
        self._send_media_key(VK_MEDIA_NEXT_TRACK)
        logger.info("Skipped to next track")
        return {"status": "success", "message": "已切换到下一首"}

    async def previous_track(self) -> dict:
        """Go to previous track via media key."""
        self._send_media_key(VK_MEDIA_PREV_TRACK)
        logger.info("Skipped to previous track")
        return {"status": "success", "message": "已切换到上一首"}

    async def get_current_track(self) -> dict:
        """Get info about the currently playing track.

        Combines audio session detection (is it playing?) with
        window title extraction (what song is it?).
        """
        is_playing = await asyncio.to_thread(self.is_music_actually_playing)
        if not is_playing:
            is_running = await asyncio.to_thread(self.is_music_app_running)
            if not is_running:
                return {
                    "status": "success",
                    "message": "网易云音乐未运行",
                    "playing": False,
                }
            return {
                "status": "success",
                "message": "当前没有在播放音乐",
                "playing": False,
            }

        # Try to get song info from window title
        title = await asyncio.to_thread(self._get_netease_window_title)
        if title:
            return {
                "status": "success",
                "message": f"当前正在播放: {title}",
                "playing": True,
                "track": title,
            }

        return {
            "status": "success",
            "message": "正在播放音乐（无法获取歌曲信息）",
            "playing": True,
        }


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------

_music_player_instance: Optional[MusicPlayer] = None


def get_music_player_instance() -> MusicPlayer:
    """Get or create the singleton MusicPlayer instance."""
    global _music_player_instance
    if _music_player_instance is None:
        _music_player_instance = MusicPlayer()
    return _music_player_instance
