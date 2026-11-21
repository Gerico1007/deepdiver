"""
K5 (William, 2026-10-26): kept explainers carry their transcript, and an
explainer gets a new version through NotebookLM's Iterate. The browser part
runs against pages built like the Studio panel, never a real notebook.
"""

import asyncio
import json
import os

import pytest
from playwright.async_api import async_playwright

from deepdiver import keep
from deepdiver.notebooklm_automator import NotebookLMAutomator, match_studio_cards


# ── transcripts in keep ──────────────────────────────────────────

def _folder(tmp_path):
    folder = tmp_path / 'notebook-abc'
    (folder / 'keep').mkdir(parents=True)
    (folder / 'keep' / 'Session-Continuity-1.mp4').write_bytes(b'video')
    (folder / 'Session-Continuity-1.mp4').write_bytes(b'download')
    (folder / 'Report-1.md').write_text('# Report\n')
    manifest = {'downloads': [
        {'title': 'Session Continuity', 'family_label': 'Video Overview', 'path': '/elsewhere/Session-Continuity-1.mp4',
         'kept': {'path': 'keep/Session-Continuity-1.mp4', 'size': 5, 'sha256': 'x', 'how': 'H.264'}},
        {'title': 'Report', 'family_label': 'Reports', 'path': '/elsewhere/Report-1.md',
         'kept': {'path': 'Report-1.md', 'size': 9, 'sha256': 'y', 'how': 'as downloaded'}},
    ]}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    return folder


def _fake_transcriber(calls):
    def run(media, out, model='base'):
        calls.append(media)
        with open(out, 'w') as fh:
            fh.write('[00:00] Welcome back.\n[00:04] Today we look at session continuity.\n')
        return None
    return run


def test_a_kept_video_gets_its_transcript_beside_it_and_in_the_manifest(tmp_path, monkeypatch):
    folder = _folder(tmp_path)
    calls = []
    monkeypatch.setattr(keep, 'transcribe_media', _fake_transcriber(calls))
    manifest = keep.keep_folder(str(folder))
    video = manifest['downloads'][0]['kept']
    assert video['transcript']['path'] == os.path.join('keep', 'Session-Continuity-1.transcript.md')
    text = (folder / 'keep' / 'Session-Continuity-1.transcript.md').read_text()
    assert text.startswith('# Transcript: Session Continuity')
    assert '[00:04] Today we look at session continuity.' in text
    assert 'not checked' in text
    assert calls == [str(folder / 'keep' / 'Session-Continuity-1.mp4')]
    assert 'transcript' not in manifest['downloads'][1]['kept']
    on_disk = json.loads((folder / 'manifest.json').read_text())
    assert on_disk['downloads'][0]['kept']['transcript']['sha256'] == video['transcript']['sha256']


def test_a_transcript_already_there_is_recorded_not_redone(tmp_path, monkeypatch):
    folder = _folder(tmp_path)
    (folder / 'keep' / 'Session-Continuity-1.transcript.md').write_text('# Transcript: earlier\n')
    calls = []
    monkeypatch.setattr(keep, 'transcribe_media', _fake_transcriber(calls))
    manifest = keep.keep_folder(str(folder))
    assert calls == []
    assert manifest['downloads'][0]['kept']['transcript']['path'].endswith('.transcript.md')


def test_without_a_transcriber_the_manifest_says_why(tmp_path, monkeypatch):
    folder = _folder(tmp_path)
    monkeypatch.setattr(keep, 'transcriber_python', lambda: None)
    manifest = keep.keep_folder(str(folder))
    assert 'no transcriber' in manifest['downloads'][0]['kept']['transcript_error']
    assert not (folder / 'keep' / 'Session-Continuity-1.transcript.md').exists()


def test_no_transcript_when_asked(tmp_path, monkeypatch):
    folder = _folder(tmp_path)
    calls = []
    monkeypatch.setattr(keep, 'transcribe_media', _fake_transcriber(calls))
    manifest = keep.keep_folder(str(folder), transcripts=False)
    assert calls == [] and 'transcript' not in manifest['downloads'][0]['kept']


# ── studio iterate ───────────────────────────────────────────────

def test_cards_are_named_by_id_first_then_exact_title():
    cards = [{'artifact_id': '919ca278', 'title': 'Session Continuity'},
             {'artifact_id': 'aa11', 'title': 'Twin'}, {'artifact_id': 'bb22', 'title': 'Twin'}]
    assert match_studio_cards(cards, '919ca278') == [cards[0]]
    assert match_studio_cards(cards, 'Session Continuity') == [cards[0]]
    assert match_studio_cards(cards, 'Twin') == cards[1:]
    assert match_studio_cards(cards, 'Session') == []


STUDIO = """
<artifact-library-item id="card">
  <span class="title">Session Continuity</span>
  <button aria-label="More"><mat-icon>more_vert</mat-icon></button>
</artifact-library-item>
<script>
  window.generated = 0;
  const ITERATE = %s;
  document.querySelector('#card button').addEventListener('click', () => {
    const menu = document.createElement('div');
    menu.innerHTML = '<div role="menuitem">Rename</div><div role="menuitem">View prompt and sources</div>';
    document.body.appendChild(menu);
    menu.children[1].addEventListener('click', () => {
      menu.remove();
      const d = document.createElement('mat-dialog-container');
      d.id = 'prompt';
      d.innerHTML = '<p>Prompt and sources</p><p>Explain session continuity for T1.</p>'
        + (ITERATE ? '<button aria-label="Iterate" class="iterate-button"><mat-icon>restart_alt</mat-icon></button>' : '')
        + '<button aria-label="Close"><mat-icon>close</mat-icon></button>';
      setTimeout(() => document.body.appendChild(d), 400);
      d.querySelector('[aria-label="Close"]').addEventListener('click', () => d.remove());
      const it = d.querySelector('[aria-label="Iterate"]');
      if (it) it.addEventListener('click', () => {
        d.remove();
        const c = document.createElement('mat-dialog-container');
        c.id = 'customize';
        c.innerHTML = '<p>Customize Video Overview</p><textarea>Explain session continuity for T1.</textarea>'
          + '<button aria-label="Close"><mat-icon>close</mat-icon></button><button>Generate</button>';
        setTimeout(() => document.body.appendChild(c), 400);
        c.querySelector('[aria-label="Close"]').addEventListener('click', () => c.remove());
        c.querySelectorAll('button')[1].addEventListener('click', () => { window.generated += 1; c.remove(); });
      });
    });
  });
</script>
"""


async def _studio(iterate, action):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(STUDIO % ('true' if iterate else 'false'))
        automator = NotebookLMAutomator.__new__(NotebookLMAutomator)
        automator.page = page
        automator.logger = __import__('logging').getLogger('test')
        try:
            return await action(automator, page)
        finally:
            await browser.close()


def test_iterate_opens_the_cards_customize_dialog_with_its_own_prompt():
    async def act(automator, page):
        opened = await automator._open_iterate_dialog(page.locator('artifact-library-item').first)
        filled = None
        if opened['dialog'] is not None:
            await opened['dialog'].locator('textarea').fill('Explain it again, naming what exists and what is proposed.')
            filled = await opened['dialog'].locator('textarea').input_value()
            await automator._close_dialog(page.locator('mat-dialog-container'))
        return opened, filled, await page.evaluate('window.generated'), await page.locator('mat-dialog-container').count()
    opened, filled, generated, left = asyncio.run(_studio(True, act))
    assert opened['dialog'] is not None
    assert opened['previous_prompt'] == 'Explain session continuity for T1.'
    assert filled.startswith('Explain it again')
    assert generated == 0 and left == 0


def test_a_card_without_iterate_is_reported_and_its_dialog_closed():
    async def act(automator, page):
        opened = await automator._open_iterate_dialog(page.locator('artifact-library-item').first)
        return opened, await page.locator('mat-dialog-container').count()
    opened, left = asyncio.run(_studio(False, act))
    assert opened['dialog'] is None
    assert 'Explain session continuity for T1.' in opened['previous_prompt']
    assert left == 0
