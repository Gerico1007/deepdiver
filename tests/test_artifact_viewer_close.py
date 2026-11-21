import asyncio
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import NotebookLMAutomator


def _automator_with_buttons(labels_present):
    """A page whose locator(selector) finds a button only for the given selectors."""
    automator = NotebookLMAutomator()
    page = MagicMock()
    clicked = []

    def locator(selector):
        loc = MagicMock()
        present = selector in labels_present
        loc.count = AsyncMock(return_value=1 if present else 0)
        first = MagicMock()

        async def click(timeout=None):
            clicked.append(selector)

        first.click = AsyncMock(side_effect=click)
        loc.first = first
        return loc

    page.locator = MagicMock(side_effect=locator)
    page.wait_for_timeout = AsyncMock()
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    automator.page = page
    return automator, page, clicked


def test_an_open_infographic_viewer_is_closed():
    automator, page, clicked = _automator_with_buttons({'button[aria-label="Close infographic"]'})
    closed = asyncio.run(automator.close_open_artifact_viewer())
    assert closed is True
    assert clicked == ['button[aria-label="Close infographic"]']
    page.keyboard.press.assert_not_called()


def test_no_open_viewer_presses_nothing():
    automator, page, clicked = _automator_with_buttons(set())
    closed = asyncio.run(automator.close_open_artifact_viewer())
    assert closed is False
    assert clicked == []
    page.keyboard.press.assert_not_called()


def test_close_artifact_viewer_still_falls_back_to_escape():
    automator, page, clicked = _automator_with_buttons(set())
    asyncio.run(automator.close_artifact_viewer())
    page.keyboard.press.assert_awaited_once_with('Escape')
