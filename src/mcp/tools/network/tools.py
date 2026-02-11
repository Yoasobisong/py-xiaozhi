"""Network diagnostic tools.

Ping hosts, simple download speed test, and local/public IP lookup.
"""

import asyncio
import json
import platform
import re
import socket
import subprocess
import time

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def ping_host(arguments: dict) -> str:
    """Ping a host and return latency / packet loss stats."""
    host = arguments.get("host", "").strip()
    count = arguments.get("count", 4)

    if not host:
        return '{"success": false, "message": "请提供要 ping 的主机地址"}'

    # Sanitize: only allow hostname/IP characters
    if not re.match(r'^[\w.\-]+$', host):
        return '{"success": false, "message": "无效的主机地址"}'

    count = max(1, min(count, 20))

    try:
        logger.info(f"[NetworkTools] Pinging {host} x{count}")

        is_win = platform.system() == "Windows"
        cmd = ["ping", "-n" if is_win else "-c", str(count), host]

        proc = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if is_win else 0,
        )

        output = proc.stdout + proc.stderr

        # Parse average latency
        avg_ms = None
        if is_win:
            # "Average = 12ms" or "平均 = 12ms"
            m = re.search(r'(?:Average|平均)\s*=\s*(\d+)ms', output)
            if m:
                avg_ms = int(m.group(1))
        else:
            # "min/avg/max/mdev = 10.1/12.3/15.0/1.2 ms"
            m = re.search(r'[\d.]+/([\d.]+)/[\d.]+/[\d.]+\s*ms', output)
            if m:
                avg_ms = float(m.group(1))

        # Parse packet loss
        loss_match = re.search(r'(\d+)%', output)
        packet_loss = f"{loss_match.group(1)}%" if loss_match else "unknown"

        result = {
            "success": True,
            "host": host,
            "avg_ms": avg_ms,
            "packet_loss": packet_loss,
            "message": (
                f"Ping {host}: 平均延迟 {avg_ms}ms, 丢包率 {packet_loss}"
                if avg_ms is not None
                else f"Ping {host}: 丢包率 {packet_loss}"
            ),
        }

        if proc.returncode != 0 and avg_ms is None:
            result["success"] = False
            result["message"] = f"Ping {host} 失败: 主机不可达或域名无法解析"

        logger.info(f"[NetworkTools] Ping result: {result['message']}")
        return json.dumps(result, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        return json.dumps(
            {"success": False, "message": f"Ping {host} 超时"},
            ensure_ascii=False,
        )
    except Exception as e:
        logger.error(f"[NetworkTools] Ping failed: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"Ping 失败: {e}"},
            ensure_ascii=False,
        )


async def speedtest(arguments: dict) -> str:
    """Simple download speed test using a public test file."""
    try:
        logger.info("[NetworkTools] Starting speed test")

        import requests

        # Use multiple test URLs as fallback
        test_urls = [
            ("https://speed.cloudflare.com/__down?bytes=5000000", 5_000_000),
            ("https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm", None),
        ]

        for url, expected_size in test_urls:
            try:
                start = time.monotonic()
                resp = await asyncio.to_thread(
                    lambda u=url: requests.get(u, timeout=15, stream=True)
                )
                # Read all content
                data = await asyncio.to_thread(lambda r=resp: r.content)
                elapsed = time.monotonic() - start

                actual_size = len(data)
                if actual_size < 10000:
                    # Too small, probably an error page
                    continue

                speed_bps = actual_size * 8 / elapsed
                speed_mbps = round(speed_bps / 1_000_000, 2)

                result = {
                    "success": True,
                    "download_mbps": speed_mbps,
                    "downloaded_mb": round(actual_size / 1_000_000, 2),
                    "elapsed_seconds": round(elapsed, 2),
                    "message": f"下载速度: {speed_mbps} Mbps",
                }
                logger.info(f"[NetworkTools] Speed test: {speed_mbps} Mbps")
                return json.dumps(result, ensure_ascii=False)

            except Exception as e:
                logger.debug(f"[NetworkTools] Test URL failed ({url}): {e}")
                continue

        return json.dumps(
            {"success": False, "message": "测速失败: 所有测试服务器均不可达"},
            ensure_ascii=False,
        )

    except Exception as e:
        logger.error(f"[NetworkTools] Speed test failed: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"测速失败: {e}"},
            ensure_ascii=False,
        )


async def get_ip(arguments: dict) -> str:
    """Get local (LAN) and public IP addresses."""
    try:
        logger.info("[NetworkTools] Getting IP addresses")

        # Get local IP via UDP socket (no actual data sent)
        local_ip = "unknown"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception as e:
            logger.debug(f"[NetworkTools] Local IP detection failed: {e}")
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                pass

        # Get public IP
        public_ip = "unknown"
        ip_apis = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
        ]

        import requests

        for api_url in ip_apis:
            try:
                resp = await asyncio.to_thread(
                    lambda u=api_url: requests.get(u, timeout=5)
                )
                data = resp.json()
                # ipify returns {"ip": "..."}, httpbin returns {"origin": "..."}
                public_ip = data.get("ip") or data.get("origin", "unknown")
                if public_ip != "unknown":
                    break
            except Exception as e:
                logger.debug(f"[NetworkTools] Public IP API failed ({api_url}): {e}")
                continue

        result = {
            "success": True,
            "local_ip": local_ip,
            "public_ip": public_ip,
            "message": f"局域网 IP: {local_ip}, 公网 IP: {public_ip}",
        }
        logger.info(f"[NetworkTools] IP: local={local_ip}, public={public_ip}")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[NetworkTools] Get IP failed: {e}", exc_info=True)
        return json.dumps(
            {"success": False, "message": f"获取 IP 失败: {e}"},
            ensure_ascii=False,
        )
