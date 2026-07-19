import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import NotebookLMAutomator


class _Element:
    def __init__(self, click_side_effect=None):
        self.click = AsyncMock(side_effect=click_side_effect)
        self.evaluate = AsyncMock()


class _DownloadWaiter:
    def __init__(self, download):
        async def _resolve_download():
            return download

        self.value = _resolve_download()


class _ExpectDownload:
    def __init__(self, download):
        self._waiter = _DownloadWaiter(download)

    async def __aenter__(self):
        return self._waiter

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_download_audio_uses_menu_download_link_when_direct_control_is_hidden(tmp_path):
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.wait_for_timeout = AsyncMock()

    menu_open = {"value": False}
    menu_button = _Element(click_side_effect=lambda: menu_open.__setitem__("value", True))
    download_link = _Element()
    download = MagicMock()
    download.suggested_filename = "artifact.m4a"

    async def save_as(path):
        Path(path).write_bytes(b"notebooklm-audio")

    download.save_as = AsyncMock(side_effect=save_as)

    async def wait_for_selector(selector, timeout=0, state=None):
        if selector == 'button[aria-label="See more options for audio player"]':
            return menu_button
        if selector == 'a[role="menuitem"][download]' and menu_open["value"]:
            return download_link
        return None

    page.wait_for_selector = AsyncMock(side_effect=wait_for_selector)
    page.expect_download = MagicMock(return_value=_ExpectDownload(download))
    automator.page = page

    output_path = tmp_path / "artifact.m4a"
    result = asyncio.run(automator.download_audio(str(output_path)))

    assert result is True
    menu_button.click.assert_awaited_once()
    download_link.evaluate.assert_awaited_once()
    download_link.click.assert_awaited_once()
    download.save_as.assert_awaited_once_with(str(output_path))
    assert output_path.read_bytes() == b"notebooklm-audio"


def test_close_preserves_shared_cdp_page_context_and_browser():
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.close = AsyncMock()
    context = MagicMock()
    context.close = AsyncMock()
    browser = MagicMock()
    browser.close = AsyncMock()
    playwright = MagicMock()
    playwright.stop = AsyncMock()

    automator.page = page
    automator.context = context
    automator.browser = browser
    automator.playwright = playwright
    automator._connected_over_cdp = True
    automator._owns_page = False
    automator._owns_context = False

    asyncio.run(automator.close())

    page.close.assert_not_called()
    context.close.assert_not_called()
    browser.close.assert_not_called()
    playwright.stop.assert_awaited_once()
    assert automator.page is None
    assert automator.context is None
    assert automator.browser is None


def test_close_releases_owned_resources():
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.close = AsyncMock()
    context = MagicMock()
    context.close = AsyncMock()
    browser = MagicMock()
    browser.close = AsyncMock()
    playwright = MagicMock()
    playwright.stop = AsyncMock()

    automator.page = page
    automator.context = context
    automator.browser = browser
    automator.playwright = playwright
    automator._owns_page = True
    automator._owns_context = True
    automator._connected_over_cdp = False

    asyncio.run(automator.close())

    page.close.assert_awaited_once()
    context.close.assert_awaited_once()
    browser.close.assert_awaited_once()
    playwright.stop.assert_awaited_once()
