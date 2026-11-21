"""A generation that never starts, or is refused by the daily limit, ends early.

2026-10-29, notebook 01726e76: an Infographic waited 902 s and a Video
Overview 1802 s with no card ever started, and the next Video Overview was
refused with "You have reached your daily Video Overview and Infographic
limit". The monitor now says so within its start timeout.
"""

import asyncio
import logging
import time

from playwright.async_api import async_playwright

from deepdiver.notebooklm_automator import NotebookLMAutomator

EMPTY_PANEL = '<div class="studio"></div>'
GENERATING_PANEL = (
    '<div class="studio"><artifact-library-item>'
    '<button class="mat-mdc-button-disabled" disabled>Generating Video Overview...</button>'
    '</artifact-library-item></div>'
)
LIMIT = 'You have reached your daily Video Overview and Infographic limit.'


async def _monitor(html, **kwargs):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
        automator.page = page
        automator.logger = logging.getLogger('test')
        try:
            began = time.time()
            result = await automator._monitor_artifact_generation(
                began, kwargs.pop('timeout', 30), 1, artifact_type=kwargs.pop('artifact_type', 'video_overview'),
                **kwargs,
            )
            return result, automator.last_generation_refusal, time.time() - began
        finally:
            await browser.close()


def test_daily_limit_after_generate_ends_the_watch_with_its_words():
    result, refusal, spent = asyncio.run(_monitor(EMPTY_PANEL + f'<div role="alert">{LIMIT}</div>'))
    assert result is None
    assert refusal == 'You have reached your daily Video Overview and Infographic limit'
    assert spent < 5


def test_nothing_generating_ends_at_the_start_timeout():
    result, refusal, spent = asyncio.run(_monitor(EMPTY_PANEL, start_timeout=2))
    assert result is None
    assert refusal == 'did not start'
    assert spent < 6


def test_a_generating_card_is_watched_past_the_start_timeout():
    result, refusal, spent = asyncio.run(_monitor(GENERATING_PANEL, start_timeout=1, timeout=4))
    assert result is None
    assert refusal is None
    assert spent >= 4


def test_a_limit_naming_other_families_does_not_stop_a_report():
    result, refusal, _ = asyncio.run(
        _monitor(EMPTY_PANEL + f'<div role="alert">{LIMIT}</div>', artifact_type='reports', start_timeout=1)
    )
    assert result is None
    assert refusal == 'did not start'
