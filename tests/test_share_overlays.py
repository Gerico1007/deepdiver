import asyncio
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import NotebookLMAutomator


class _VisibleElement:
    def __init__(self, visible=True):
        self.is_visible = AsyncMock(return_value=visible)
        self.click = AsyncMock()


def _make_automator_with_page(query_selector_impl):
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.query_selector = AsyncMock(side_effect=query_selector_impl)
    page.wait_for_timeout = AsyncMock()
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    automator.page = page
    return automator, page


def test_dismiss_preexisting_dialog_uses_escape_when_overlay_is_visible():
    async def query_selector(selector):
        if selector == '.cdk-overlay-backdrop':
            return _VisibleElement(True)
        return None

    automator, page = _make_automator_with_page(query_selector)

    dismissed = asyncio.run(automator._dismiss_preexisting_dialogs())

    assert dismissed is True
    page.keyboard.press.assert_awaited_once_with('Escape')
    page.wait_for_timeout.assert_awaited_once_with(500)


def test_dismiss_preexisting_dialog_does_nothing_when_no_overlay_is_visible():
    async def query_selector(_selector):
        return None

    automator, page = _make_automator_with_page(query_selector)

    dismissed = asyncio.run(automator._dismiss_preexisting_dialogs())

    assert dismissed is False
    page.keyboard.press.assert_not_called()
    page.wait_for_timeout.assert_not_called()
