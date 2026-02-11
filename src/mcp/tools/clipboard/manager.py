"""Clipboard tools manager.

Registers clipboard MCP tools (read/write text, analyze image).
"""

from typing import Any, Dict

from src.utils.logging_config import get_logger

from .tools import read_clipboard, write_clipboard, analyze_clipboard_image

logger = get_logger(__name__)


class ClipboardToolsManager:
    """
    Clipboard tools manager.
    """

    def __init__(self):
        self._initialized = False
        logger.info("[ClipboardManager] Clipboard tools manager initialized")

    def init_tools(self, add_tool, PropertyList, Property, PropertyType):
        """
        Register all clipboard tools.
        """
        try:
            logger.info("[ClipboardManager] Registering clipboard tools")

            # Read clipboard
            read_props = PropertyList([])
            add_tool(
                (
                    "clipboard.read_text",
                    "Read text content from the system clipboard.\n"
                    "IMPORTANT: Clipboard content changes frequently. You MUST call this "
                    "tool EVERY TIME the user mentions clipboard, even if you read it before. "
                    "NEVER reuse previous clipboard content — always fetch fresh data.\n\n"
                    "Translation rule: When user asks to translate clipboard content, "
                    "auto-detect the language. If it is Chinese, translate to English. "
                    "If it is any other language (English, Japanese, Korean, etc.), "
                    "translate to Chinese. No need to ask the user which language.\n\n"
                    "Use when user says: '读剪贴板', '剪贴板里有什么', '看看我复制的内容', "
                    "'帮我翻译剪贴板', '总结一下我复制的内容', '再帮我看看剪贴板', "
                    "'read clipboard', 'what did I copy', 'paste content'.\n"
                    "Returns the current clipboard text content.\n"
                    "Useful for: translating copied text, summarizing copied content, "
                    "reformatting text, spell-checking, etc.",
                    read_props,
                    read_clipboard,
                )
            )

            # Write clipboard
            write_props = PropertyList(
                [Property("text", PropertyType.STRING)]
            )
            add_tool(
                (
                    "clipboard.write_text",
                    "Write text content to the system clipboard.\n"
                    "Use when user says: '写入剪贴板', '复制到剪贴板', '帮我复制这段话', "
                    "'put this in clipboard', 'copy to clipboard'.\n"
                    "Parameter:\n"
                    "- text: The text to write to clipboard.\n"
                    "Use after processing clipboard content (e.g., after translating "
                    "or summarizing) to put the result back into the clipboard.",
                    write_props,
                    write_clipboard,
                )
            )

            # Analyze clipboard image
            analyze_props = PropertyList(
                [Property("question", PropertyType.STRING, default_value="")]
            )
            add_tool(
                (
                    "clipboard.analyze_image",
                    "Analyze an image from the system clipboard using AI vision.\n"
                    "Use when user says: '分析剪贴板图片', '看看我截的图', '剪贴板里的图片是什么', "
                    "'识别剪贴板图片', '帮我看看复制的图', 'OCR剪贴板', '翻译截图', "
                    "'analyze clipboard image', 'what is in my clipboard image'.\n"
                    "Supports: Win+Shift+S screenshots, copied images, "
                    "image files copied from Explorer.\n"
                    "Parameter:\n"
                    "- question: (optional) Specific question about the image. "
                    "If empty, describes the image content.\n"
                    "Use cases: OCR text extraction, translate text in image, "
                    "analyze code screenshots, identify objects, read error messages.",
                    analyze_props,
                    analyze_clipboard_image,
                )
            )

            self._initialized = True
            logger.info("[ClipboardManager] Clipboard tools registered successfully")

        except Exception as e:
            logger.error(
                f"[ClipboardManager] Clipboard tools registration failed: {e}",
                exc_info=True,
            )
            raise

    def is_initialized(self) -> bool:
        return self._initialized

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "tools_count": 3,
            "available_tools": ["read_text", "write_text", "analyze_image"],
        }


# Singleton
_clipboard_tools_manager = None


def get_clipboard_tools_manager() -> ClipboardToolsManager:
    """
    Get clipboard tools manager singleton.
    """
    global _clipboard_tools_manager
    if _clipboard_tools_manager is None:
        _clipboard_tools_manager = ClipboardToolsManager()
        logger.debug("[ClipboardManager] Created clipboard tools manager instance")
    return _clipboard_tools_manager
