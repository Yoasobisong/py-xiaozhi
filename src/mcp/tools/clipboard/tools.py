"""Clipboard tools implementation.

Read/write system clipboard text content.
"""

import asyncio
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
            return '{"success": true, "content": "", "message": "Clipboard is empty or contains non-text data"}'

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
