import asyncio
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import NotebookLMAutomator


class _Element:
    def __init__(self, visible=True, disabled=False, click_side_effect=None):
        self.is_visible = AsyncMock(return_value=visible)
        self.click = AsyncMock(side_effect=click_side_effect)
        self._disabled = disabled

    async def get_attribute(self, name):
        if name == 'disabled':
            return '' if self._disabled else None
        return None


async def _return_none(*_args, **_kwargs):
    return None


def _make_automator_with_page(query_selector_impl=None, wait_for_selector_impl=None):
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.query_selector = AsyncMock(side_effect=query_selector_impl or _return_none)
    page.wait_for_selector = AsyncMock(side_effect=wait_for_selector_impl or _return_none)
    page.wait_for_timeout = AsyncMock()
    page.screenshot = AsyncMock()
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    page.keyboard.type = AsyncMock()
    automator.page = page
    return automator, page


def test_dismiss_preexisting_dialog_uses_escape_when_overlay_is_visible():
    async def query_selector(selector):
        if selector == '.cdk-overlay-backdrop':
            return _Element(True)
        return None

    automator, page = _make_automator_with_page(query_selector_impl=query_selector)

    dismissed = asyncio.run(automator._dismiss_preexisting_dialogs())

    assert dismissed is True
    page.keyboard.press.assert_awaited_once_with('Escape')
    page.wait_for_timeout.assert_awaited_once_with(500)


def test_dismiss_preexisting_dialog_does_nothing_when_no_overlay_is_visible():
    automator, page = _make_automator_with_page()

    dismissed = asyncio.run(automator._dismiss_preexisting_dialogs())

    assert dismissed is False
    page.keyboard.press.assert_not_called()
    page.wait_for_timeout.assert_not_called()


def test_share_notebook_prefers_dialog_scoped_save_button_over_background_share_button():
    page_share_button = _Element(click_side_effect=[None, RuntimeError('background share button should not be reused')])
    share_dialog = _Element()
    email_input = _Element()
    dialog_save_button = _Element()

    async def wait_for_selector(selector, timeout=0):
        if selector in {
            'button[aria-label="Share"]',
            'button:has-text("Share")',
            'button[title="Share"]',
            '[data-testid="share-button"]',
            'button.share-button',
        }:
            return page_share_button
        if selector in {
            'div[role="dialog"]',
            '.share-dialog',
            '[data-testid="share-dialog"]',
            'div.modal',
        }:
            return share_dialog
        if selector in {
            'mat-dialog-container input#mat-input-1',
            'mat-dialog-container input[peoplekitautocomplete]',
            'input[type="email"]',
            'input[aria-label*="email"]',
            'input[aria-label*="Add people"]',
            'input[aria-label*="people and groups"]',
            'input[placeholder*="email"]',
            'input.share-email-input',
            'mat-dialog-container input',
            'div[role="dialog"] input',
            'div[role="dialog"] [role="combobox"]',
            'div[role="dialog"] [contenteditable="true"]',
            'label:has-text("Add people and groups") + div input',
            'label:has-text("Add people and groups") + div [role="combobox"]',
        }:
            return email_input
        if selector == 'mat-dialog-container button:has-text("Save")':
            return dialog_save_button
        return None

    automator, page = _make_automator_with_page(wait_for_selector_impl=wait_for_selector)

    shared = asyncio.run(automator.share_notebook('person@example.com'))

    assert shared is True
    assert page_share_button.click.await_count == 1
    dialog_save_button.click.assert_awaited_once()


def test_share_notebook_retries_save_after_dismissing_nested_backdrop():
    page_share_button = _Element()
    share_dialog = _Element()
    email_input = _Element()
    dialog_save_button = _Element(click_side_effect=[RuntimeError('intercepts pointer events'), None])

    async def query_selector(selector):
        if selector == '.cdk-overlay-backdrop':
            return _Element(True)
        return None

    async def wait_for_selector(selector, timeout=0):
        if selector in {
            'button[aria-label="Share"]',
            'button:has-text("Share")',
            'button[title="Share"]',
            '[data-testid="share-button"]',
            'button.share-button',
        }:
            return page_share_button
        if selector in {
            'div[role="dialog"]',
            '.share-dialog',
            '[data-testid="share-dialog"]',
            'div.modal',
        }:
            return share_dialog
        if selector in {
            'mat-dialog-container input#mat-input-1',
            'mat-dialog-container input[peoplekitautocomplete]',
            'input[type="email"]',
            'input[aria-label*="email"]',
            'input[aria-label*="Add people"]',
            'input[aria-label*="people and groups"]',
            'input[placeholder*="email"]',
            'input.share-email-input',
            'mat-dialog-container input',
            'div[role="dialog"] input',
            'div[role="dialog"] [role="combobox"]',
            'div[role="dialog"] [contenteditable="true"]',
            'label:has-text("Add people and groups") + div input',
            'label:has-text("Add people and groups") + div [role="combobox"]',
        }:
            return email_input
        if selector == 'mat-dialog-container button:has-text("Save")':
            return dialog_save_button
        return None

    automator, page = _make_automator_with_page(
        query_selector_impl=query_selector,
        wait_for_selector_impl=wait_for_selector,
    )

    shared = asyncio.run(automator.share_notebook('person@example.com'))

    assert shared is True
    assert dialog_save_button.click.await_count == 2
    page.keyboard.press.assert_any_await('Escape')
