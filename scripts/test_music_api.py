"""Standalone test for NetEase Cloud Music API (pyncm).

Run from project root:
    python -m scripts.test_music_api
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_pyncm_import():
    """Test 1: Can we import pyncm?"""
    print("=" * 60)
    print("[Test 1] Importing pyncm...")
    try:
        import pyncm
        from pyncm.apis import cloudsearch as ncm_search
        from pyncm.apis import login as ncm_login
        from pyncm.apis import user as ncm_user
        print(f"  OK - pyncm version: {pyncm.__version__ if hasattr(pyncm, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"  FAIL - {e}")
        return False


def test_config_load():
    """Test 2: Can we load MUSIC_U from config?"""
    print("=" * 60)
    print("[Test 2] Loading MUSIC_U from config...")
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "config.json"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        music_u = config.get("MUSIC", {}).get("NETEASE_MUSIC_U", "")
        if music_u:
            print(f"  OK - MUSIC_U found ({len(music_u)} chars)")
            print(f"  First 20 chars: {music_u[:20]}...")
            return music_u
        else:
            print("  WARN - MUSIC_U is empty, will use anonymous login")
            return ""
    except Exception as e:
        print(f"  FAIL - {e}")
        return None


def test_login(music_u: str):
    """Test 3: Can we login to NetEase API?"""
    print("=" * 60)
    print("[Test 3] Logging in to NetEase API...")
    import pyncm
    from pyncm.apis import login as ncm_login

    try:
        if music_u:
            pyncm.SetCurrentSession(pyncm.Session())
            pyncm.GetCurrentSession().cookies.set("MUSIC_U", music_u)
            print("  OK - Set MUSIC_U cookie")
        else:
            ncm_login.LoginViaAnonymousAccount()
            print("  OK - Anonymous login")
        return True
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_login_status():
    """Test 4: Check login status and get user ID."""
    print("=" * 60)
    print("[Test 4] Checking login status...")
    from pyncm.apis import login as ncm_login

    try:
        status = ncm_login.GetCurrentLoginStatus()
        print(f"  Raw response keys: {list(status.keys()) if isinstance(status, dict) else type(status)}")

        # Try different response structures
        profile = status.get("profile") or status.get("data", {}).get("profile")
        if profile:
            user_id = profile.get("userId")
            nickname = profile.get("nickname", "unknown")
            print(f"  OK - User: {nickname} (ID: {user_id})")
            return user_id
        else:
            print(f"  WARN - No profile in response")
            print(f"  Full response: {json.dumps(status, indent=2, ensure_ascii=False)[:500]}")
            return None
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_search(keyword: str = "稻香"):
    """Test 5: Search for a song."""
    print("=" * 60)
    print(f"[Test 5] Searching for '{keyword}'...")
    from pyncm.apis import cloudsearch as ncm_search

    try:
        result = ncm_search.GetSearchResult(
            keyword=keyword,
            stype=1,
            limit=5,
        )

        if not result:
            print("  FAIL - Empty response")
            return None

        code = result.get("code")
        print(f"  Response code: {code}")

        if code != 200:
            print(f"  FAIL - Non-200 code")
            print(f"  Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            return None

        songs = result.get("result", {}).get("songs", [])
        if not songs:
            print("  FAIL - No songs found")
            return None

        print(f"  OK - Found {len(songs)} songs:")
        for i, song in enumerate(songs):
            song_id = song.get("id")
            name = song.get("name")
            artists = song.get("ar", []) or song.get("artists", [])
            artist_names = ", ".join(a.get("name", "") for a in artists)
            fee = song.get("fee", 0)
            fee_label = {0: "free", 1: "VIP", 4: "paid album", 8: "free"}.get(fee, f"fee={fee}")
            print(f"    [{i+1}] {name} - {artist_names} (id={song_id}, {fee_label})")

        return songs[0]
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_user_playlists(user_id: int):
    """Test 6: Get user playlists."""
    print("=" * 60)
    print(f"[Test 6] Getting playlists for user {user_id}...")
    from pyncm.apis import user as ncm_user

    try:
        result = ncm_user.GetUserPlaylists(user_id=user_id, limit=5)

        if not result:
            print("  FAIL - Empty response")
            return None

        playlists = result.get("playlist", [])
        if not playlists:
            print("  FAIL - No playlists found")
            print(f"  Response keys: {list(result.keys())}")
            return None

        print(f"  OK - Found {len(playlists)} playlists:")
        for i, pl in enumerate(playlists):
            pl_id = pl.get("id")
            name = pl.get("name")
            count = pl.get("trackCount", 0)
            print(f"    [{i+1}] {name} (id={pl_id}, {count} tracks)")

        likes_id = playlists[0].get("id")
        print(f"  Likes playlist ID: {likes_id}")
        return likes_id
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_orpheus_uri(song_id: int):
    """Test 7: Test opening orpheus:// URI."""
    print("=" * 60)
    print(f"[Test 7] Testing orpheus://song/{song_id} ...")
    try:
        import subprocess
        # Just check if the URI scheme is registered
        result = subprocess.run(
            ["reg", "query", "HKCR\\orpheus"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if "orpheus" in result.stdout.lower() or result.returncode == 0:
            print("  OK - orpheus:// URI scheme is registered")
            return True
        else:
            print("  WARN - orpheus:// URI scheme NOT registered")
            print("  Will fall back to web browser")
            return False
    except Exception as e:
        print(f"  WARN - Could not check registry: {e}")
        return False


def test_pycaw():
    """Test 8: Test pycaw audio session detection."""
    print("=" * 60)
    print("[Test 8] Testing pycaw audio session detection...")
    try:
        from pycaw.pycaw import AudioUtilities
        sessions = AudioUtilities.GetAllSessions()
        print(f"  OK - Found {len(sessions)} audio sessions:")
        for s in sessions:
            if s.Process:
                name = s.Process.name()
                state_map = {0: "Inactive", 1: "Active", 2: "Expired"}
                state = state_map.get(s.State, f"Unknown({s.State})")
                print(f"    - {name}: {state}")

                # Check for volume control
                if name.lower() == "cloudmusic.exe":
                    try:
                        vol = s._ctl.QueryInterface(
                            __import__("comtypes").GUID("{87CE5498-68D6-44E5-9215-6DA47EF883D8}")
                        )
                        print(f"      Volume interface available: YES")
                    except Exception:
                        # Try simpleaudiovolume
                        try:
                            from pycaw.pycaw import ISimpleAudioVolume
                            vol = s._ctl.QueryInterface(ISimpleAudioVolume)
                            current_vol = vol.GetMasterVolume()
                            print(f"      SimpleAudioVolume: {current_vol:.2f}")
                        except Exception as ve:
                            print(f"      Volume control check: {ve}")
        return True
    except ImportError:
        print("  FAIL - pycaw not installed")
        return False
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("NetEase Cloud Music API Test Suite")
    print("=" * 60)

    # Test 1: Import
    if not test_pyncm_import():
        print("\nCANNOT PROCEED: pyncm not available")
        return

    # Test 2: Config
    music_u = test_config_load()
    if music_u is None:
        print("\nCANNOT PROCEED: config load failed")
        return

    # Test 3: Login
    if not test_login(music_u):
        print("\nCANNOT PROCEED: login failed")
        return

    # Test 4: Login status
    user_id = test_login_status()

    # Test 5: Search
    song = test_search("稻香")

    # Test 6: Playlists (only if we have a user ID)
    if user_id:
        test_user_playlists(user_id)
    else:
        print("=" * 60)
        print("[Test 6] SKIPPED - No user ID available")

    # Test 7: orpheus:// URI
    if song:
        test_orpheus_uri(song.get("id"))

    # Test 8: pycaw
    test_pycaw()

    print("=" * 60)
    print("All tests complete!")


if __name__ == "__main__":
    main()
