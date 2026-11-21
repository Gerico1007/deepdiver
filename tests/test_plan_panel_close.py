"""A paused plan left open hides the Studio panel; arriving at the notebook closes it.

2026-11-10, notebook 7bf33cea: after `studio outline`, the plan's panel ("Video
Overview: …", Producer notes, Proceed) covered the Studio tiles, and two
generations ended "No customization dialog opened". Its header button is "Close".
"""

import asyncio
import logging

from playwright.async_api import async_playwright

from deepdiver.notebooklm_automator import NotebookLMAutomator

PLAN_OPEN = """
<section class="studio-panel"><div class="panel-header"><span>Video Overview: A plan</span>
<button aria-label="Close" onclick="document.body.dataset.closed='yes'">collapse_content</button></div>
<div>Producer notes</div><button>Proceed</button></section>
"""
STUDIO_ONLY = """
<section class="studio-panel"><div class="panel-header"><span>Studio</span>
<button aria-label="Close" onclick="document.body.dataset.closed='yes'">collapse_content</button></div>
<button>Video Overview</button></section>
"""


async def _close(html):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
        automator.page = page
        automator.logger = logging.getLogger('test')
        try:
            closed = await automator.close_open_artifact_viewer()
            return closed, await page.evaluate("document.body.dataset.closed || ''")
        finally:
            await browser.close()


def test_an_open_plan_is_closed():
    closed, clicked = asyncio.run(_close(PLAN_OPEN))
    assert closed is True and clicked == 'yes'


def test_the_studio_panel_alone_is_left_open():
    closed, clicked = asyncio.run(_close(STUDIO_ONLY))
    assert closed is False and clicked == ''
