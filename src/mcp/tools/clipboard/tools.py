"""Clipboard tools implementation.

Read/write system clipboard text content and analyze clipboard images.
"""

import asyncio
import io
import sys
from typing import Any, Dict

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def read_clipboard(arguments: dict) -> str:
    """
    Read text content from the system clipboard.
    """
    try:
        logger.info("[ClipboardTools] Reading clipboard text")

        import pyperclip

        text = await asyncio.to_thread(pyperclip.paste)

        if not text:
            # Check if clipboard has an image instead
            has_image = await asyncio.to_thread(_check_clipboard_has_image)
            if has_image:
                return (
                    '{"success": true, "content": "", '
                    '"message": "剪贴板中没有文本，但检测到图片内容。'
                    '请使用 clipboard.analyze_image 工具来分析剪贴板中的图片。"}'
                )
            return '{"success": true, "content": "", "message": "Clipboard is empty"}'

        # Truncate very long clipboard content for the response
        display_text = text if len(text) <= 2000 else text[:2000] + "...(truncated)"
        logger.info(f"[ClipboardTools] Clipboard text length: {len(text)}")
        return (
            '{"success": true, '
            f'"content": {_json_escape(display_text)}, '
            f'"length": {len(text)}}}'
        )

    except Exception as e:
        logger.error(f"[ClipboardTools] Read clipboard failed: {e}", exc_info=True)
        return f'{{"success": false, "message": "Read clipboard failed: {e}"}}'


async def write_clipboard(arguments: dict) -> str:
    """
    Write text content to the system clipboard.
    """
    text = arguments.get("text", "")
    try:
        logger.info(f"[ClipboardTools] Writing to clipboard, length: {len(text)}")

        import pyperclip

        await asyncio.to_thread(pyperclip.copy, text)
        logger.info("[ClipboardTools] Clipboard write successful")
        return f'{{"success": true, "message": "Text written to clipboard ({len(text)} chars)"}}'

    except Exception as e:
        logger.error(f"[ClipboardTools] Write clipboard failed: {e}", exc_info=True)
        return f'{{"success": false, "message": "Write clipboard failed: {e}"}}'


def _json_escape(s: str) -> str:
    """
    Escape a string for safe JSON embedding.
    """
    import json

    return json.dumps(s, ensure_ascii=False)


def _check_clipboard_has_image() -> bool:
    """Check if the system clipboard contains an image."""
    try:
        from PIL import ImageGrab

        img = ImageGrab.grabclipboard()
        if img is None:
            return False
        # PIL Image or list of file paths (copied files from Explorer)
        if isinstance(img, list):
            IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
            return bool(img and img[0].lower().endswith(IMAGE_EXTS))
        return True
    except Exception:
        return False


async def analyze_clipboard_image(arguments: dict) -> str:
    """Grab image from clipboard and analyze it with VL API."""
    question = arguments.get("question", "")

    try:
        logger.info("[ClipboardTools] Analyzing clipboard image")

        # Grab image from clipboard
        from PIL import ImageGrab

        image = await asyncio.to_thread(ImageGrab.grabclipboard)

        if image is None:
            return '{"success": false, "message": "剪贴板中没有图片"}'

        # Handle file list (e.g. copied file from Explorer)
        if isinstance(image, list):
            from PIL import Image

            IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
            if image and image[0].lower().endswith(IMAGE_EXTS):
                image = await asyncio.to_thread(Image.open, image[0])
            else:
                return '{"success": false, "message": "剪贴板中没有图片"}'

        # Convert RGBA to RGB with white background
        if image.mode == "RGBA":
            from PIL import Image as PILImage

            bg = PILImage.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Resize: longest edge -> 320px (match VLCamera.capture behavior)
        w, h = image.size
        max_dim = max(w, h)
        if max_dim > 320:
            scale = 320 / max_dim
            from PIL import Image as PILImage

            image = image.resize(
                (int(w * scale), int(h * scale)), PILImage.LANCZOS
            )

        # Encode to JPEG bytes
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        jpeg_bytes = buf.getvalue()
        logger.info(
            f"[ClipboardTools] Clipboard image: {w}x{h}, "
            f"JPEG size: {len(jpeg_bytes)} bytes"
        )

        # Reuse VLCamera analyze (same pattern as screenshot_camera.py)
        from src.mcp.tools.camera import get_camera_instance

        camera = get_camera_instance()
        original_data = camera.get_jpeg_data()
        camera.set_jpeg_data(jpeg_bytes)
        try:
            result = camera.analyze(
                question if question else "请描述这张图片的内容"
            )
        finally:
            # Restore original camera data
            camera.set_jpeg_data(original_data["buf"])

        logger.info("[ClipboardTools] Clipboard image analysis completed")
        return result

    except ImportError as e:
        logger.error(f"[ClipboardTools] Missing dependency: {e}")
        return f'{{"success": false, "message": "缺少依赖: {e}"}}'
    except Exception as e:
        logger.error(
            f"[ClipboardTools] Analyze clipboard image failed: {e}",
            exc_info=True,
        )
        return f'{{"success": false, "message": "分析剪贴板图片失败: {e}"}}'
