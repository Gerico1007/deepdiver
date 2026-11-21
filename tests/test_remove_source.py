"""
notebook remove-source: a revised source replaces its old copy (screenwalk
2610221013, 07:22-08:44). The browser part runs against a page built like the
Sources panel (a row's More menu, a Remove item, a confirm dialog), never
against a real notebook.
"""

import asyncio
import json

import pytest
from playwright.async_api import async_playwright

from deepdiver.notebooklm_automator import NotebookLMAutomator, match_source_titles
from deepdiver.session_tracker import SessionTracker

PANEL = """
<div id="sources">
  <div class="single-source-container"><span class="source-title">spec-v1.md</span>
    <button aria-label="More"><mat-icon>more_vert</mat-icon></button></div>
  <div class="single-source-container"><span class="source-title">https://www.youtube.com/watch?v=gloSM0SIgPI</span>
    <button aria-label="More"><mat-icon>more_vert</mat-icon></button></div>
  <div class="single-source-container"><span class="source-title">twin.md</span>
    <button aria-label="More"><mat-icon>more_vert</mat-icon></button></div>
  <div class="single-source-container"><span class="source-title">twin.md</span>
    <button aria-label="More"><mat-icon>more_vert</mat-icon></button></div>
</div>
<script>
  let target = null;
  document.querySelectorAll('button[aria-label="More"]').forEach((b) => b.addEventListener('click', () => {
    target = b.closest('.single-source-container');
    const menu = document.createElement('div');
    menu.id = 'menu';
    menu.innerHTML = '<div role="menuitem">Rename source</div><div role="menuitem">Remove source</div>';
    document.body.appendChild(menu);
    menu.children[1].addEventListener('click', () => {
      menu.remove();
      const dialog = document.createElement('mat-dialog-container');
      dialog.setAttribute('role', 'dialog');
      dialog.innerHTML = '<p>Delete this source?</p><button>Cancel</button><button>Delete</button>';
      document.body.appendChild(dialog);
      dialog.querySelectorAll('button')[1].addEventListener('click', () => { target.remove(); dialog.remove(); });
    });
  }));
</script>
"""


def run(coro):
    return asyncio.run(coro)


async def _with_panel(action):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(PANEL)
        automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
        automator.page = page
        automator.logger = __import__('logging').getLogger('test')
        try:
            return await action(automator, page)
        finally:
            await browser.close()


def test_matching_is_exact_first_then_by_video_id():
    titles = ['spec-v1.md', 'https://www.youtube.com/watch?v=gloSM0SIgPI', 'twin.md', 'twin.md']
    assert match_source_titles(titles, 'spec-v1.md') == [0]
    assert match_source_titles(titles, 'https://youtu.be/gloSM0SIgPI') == [1]
    assert match_source_titles(titles, 'twin.md') == [2, 3]
    assert match_source_titles(titles, 'spec-v2.md') == []
    assert match_source_titles(titles, 'spec') == []


def test_removes_the_named_row_through_more_remove_delete():
    async def act(automator, page):
        result = await automator.remove_source('spec-v1.md')
        return result, await automator.list_source_titles()
    result, left = run(_with_panel(act))
    assert result == {'removed': True, 'title': 'spec-v1.md', 'reason': ''}
    assert 'spec-v1.md' not in left and len(left) == 3


def test_removes_a_video_named_by_its_short_url():
    async def act(automator, page):
        return await automator.remove_source('https://youtu.be/gloSM0SIgPI'), await automator.list_source_titles()
    result, left = run(_with_panel(act))
    assert result['removed'] and not any('gloSM0SIgPI' in t for t in left)


def test_refuses_a_title_two_rows_share_and_removes_nothing():
    async def act(automator, page):
        return await automator.remove_source('twin.md'), await automator.list_source_titles()
    result, left = run(_with_panel(act))
    assert not result['removed'] and 'nothing removed' in result['reason']
    assert left.count('twin.md') == 2 and len(left) == 4


def test_an_unknown_title_is_not_removed():
    async def act(automator, page):
        return await automator.remove_source('spec-v2.md'), await automator.list_source_titles()
    result, left = run(_with_panel(act))
    assert not result['removed'] and result['reason'] == 'no source has this title' and len(left) == 4


def test_tracker_finds_by_source_id_and_forgets_the_removed_source(tmp_path, monkeypatch):
    tracker = SessionTracker.__new__(SessionTracker)
    tracker.logger = __import__('logging').getLogger('test')
    tracker.current_session = {'notebooks': [{'id': 'nb1', 'sources': [
        {'filename': 'spec-v1.md', 'source_id': 'a1b2c3d4', 'type': 'md'},
        {'filename': 'notes.md', 'source_id': 'e5f6a7b8', 'type': 'md'},
    ]}]}
    saved = []
    monkeypatch.setattr(tracker, 'update_notebook',
                        lambda nid, upd: saved.append(upd) or tracker.current_session['notebooks'][0].update(upd) or True,
                        raising=False)
    monkeypatch.setattr(tracker, 'get_notebook_by_id',
                        lambda nid: next((n for n in tracker.current_session['notebooks'] if n['id'] == nid), None),
                        raising=False)
    assert tracker.find_source('nb1', 'a1b2c3d4')['filename'] == 'spec-v1.md'
    assert tracker.find_source('nb1', 'notes.md')['source_id'] == 'e5f6a7b8'
    assert tracker.find_source('nb1', 'nothing') is None
    assert tracker.remove_source_from_notebook('nb1', 'a1b2c3d4')
    assert [s['filename'] for s in tracker.current_session['notebooks'][0]['sources']] == ['notes.md']
    assert not tracker.remove_source_from_notebook('nb1', 'a1b2c3d4')


# The "Delete <title>?" dialog renders after the menu closes (Episode 297, 2026-10-25).
LATE = PANEL.replace(
    "document.body.appendChild(dialog);\n      dialog.querySelectorAll('button')[1]",
    "setTimeout(() => document.body.appendChild(dialog), 1500);\n      dialog.querySelectorAll('button')[1]")

# A dialog that never offers Delete: it must be closed, or its backdrop blocks the next removal.
NO_DELETE = PANEL.replace(
    "dialog.innerHTML = '<p>Delete this source?</p><button>Cancel</button><button>Delete</button>';",
    "dialog.innerHTML = '<p>Something else</p><button>Cancel</button><button>Later</button>';"
    " dialog.querySelectorAll('button')[0].addEventListener('click', () => dialog.remove());")


async def _with(html, action):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)
        automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
        automator.page = page
        automator.logger = __import__('logging').getLogger('test')
        try:
            return await action(automator, page)
        finally:
            await browser.close()


def test_waits_for_a_confirm_dialog_that_renders_late():
    assert LATE != PANEL

    async def act(automator, page):
        first = await automator.remove_source('spec-v1.md')
        second = await automator.remove_source('https://youtu.be/gloSM0SIgPI')
        return first, second, await automator.list_source_titles()
    first, second, left = run(_with(LATE, act))
    assert first['removed'] and second['removed'], (first, second)
    assert left == ['twin.md', 'twin.md']


def test_a_dialog_without_delete_is_closed_and_reported():
    assert NO_DELETE != PANEL

    async def act(automator, page):
        result = await automator.remove_source('spec-v1.md')
        open_dialogs = await page.locator('mat-dialog-container').count()
        return result, open_dialogs, await automator.list_source_titles()
    result, open_dialogs, left = run(_with(NO_DELETE, act))
    assert not result['removed'] and 'no Delete button' in result['reason']
    assert open_dialogs == 0
    assert 'spec-v1.md' in left


def test_a_keyring_prompt_is_named_instead_of_a_hung_tab():
    from deepdiver.notebooklm_automator import keyring_prompt_message
    msg = keyring_prompt_message([(1, 'systemd'), (1373509, 'gcr-prompter')], ['Gemini Notebook - Google Chrome'])
    assert 'gcr-prompter, pid 1373509' in msg and 'only a person can unlock it' in msg
    msg2 = keyring_prompt_message([(1, 'systemd')], ['Unlock Login Keyring'])
    assert 'Unlock Login Keyring' in msg2
    assert keyring_prompt_message([(1, 'systemd'), (2, 'chrome')], ['New Tab - Google Chrome']) is None


def test_attach_timeout_names_the_keyring_prompt_first(monkeypatch):
    from deepdiver import notebooklm_automator as na
    monkeypatch.setattr(na, 'find_keyring_prompt', lambda: 'A GNOME keyring prompt is open (gcr-prompter, pid 7).')
    monkeypatch.setattr(na.requests, 'get', lambda *a, **k: (_ for _ in ()).throw(AssertionError('tabs not read')))
    assert 'gcr-prompter, pid 7' in na.describe_attach_timeout('http://127.0.0.1:9222')
