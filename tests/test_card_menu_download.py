"""
Tests for the Studio card-menu download path and the Gemini Notebook host.

Observed live on 2026-10-06 (notebook.google.com, Chrome 154):
  - every downloadable card offers More > Download; Mind Map does not;
  - that menu item starts the download outside any frame Playwright tracks,
    so only browser-level CDP download events see it;
  - a Mind Map card carries the generic aria-description "Artifact" and is
    named only by its icon;
  - notebooklm.google.com redirects to notebook.google.com.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import (
    NotebookLMAutomator,
    _is_notebook_url,
    _is_notebooklm_host,
)
from deepdiver.studio_artifacts import ARTIFACT_TYPES, family_label_from_icon


# ── Registry: icon → family ──────────────────────────────────────

def test_every_family_resolves_from_its_icon():
    for spec in ARTIFACT_TYPES.values():
        assert family_label_from_icon(spec['icon']) == spec['label']


def test_unknown_icon_resolves_to_none():
    assert family_label_from_icon('sparkle') is None
    assert family_label_from_icon(None) is None


# ── Host checks ──────────────────────────────────────────────────

def test_both_notebook_hosts_are_recognised():
    assert _is_notebooklm_host('https://notebooklm.google.com/')
    assert _is_notebooklm_host('https://notebook.google.com/notebook/abc')
    assert _is_notebook_url('https://notebook.google.com/notebook/abc')
    assert not _is_notebook_url('https://notebook.google.com/')
    assert not _is_notebooklm_host('https://evil.example/notebook.google.com/notebook/x')


# ── list_studio_artifacts: icon fallback ─────────────────────────

class _Text:
    def __init__(self, text):
        self.inner_text = AsyncMock(return_value=text)


class _Described:
    def __init__(self, value):
        self.get_attribute = AsyncMock(return_value=value)


class _IconCard:
    def __init__(self, title, aria_description, icon):
        self.title = title
        self.aria_description = aria_description
        self.icon = icon
        self.is_visible = AsyncMock(return_value=True)

    async def get_attribute(self, attr):
        return f'id-{self.title}' if attr == 'data-artifact-id' else None

    async def query_selector(self, selector):
        if selector == '.artifact-title, .title-container .artifact-title':
            return _Text(self.title)
        if selector == '[aria-description]':
            return _Described(self.aria_description)
        if selector == '.artifact-icon':
            return _Text(self.icon)
        return None


def test_generic_artifact_card_is_named_by_its_icon():
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.query_selector_all = AsyncMock(return_value=[
        _IconCard('IAIP map', 'Artifact', 'flowchart'),
        _IconCard('Episode audio', 'Audio Overview', 'audio_spark'),
    ])
    automator.page = page

    artifacts = asyncio.run(automator.list_studio_artifacts())

    assert [a['family_label'] for a in artifacts] == ['Mind Map', 'Audio Overview']


# ── _capture_download: CDP events + rename ───────────────────────

class _FakeCDPSession:
    """Emits downloadWillBegin/downloadProgress when the trigger fires."""

    def __init__(self, out_bytes=b'media', suggested='Episode_Audio.m4a', start=True):
        self.handlers = {}
        self.sent = []
        self.out_bytes = out_bytes
        self.suggested = suggested
        self.start = start
        self.detach = AsyncMock()
        self.download_path = None

    def on(self, event, handler):
        self.handlers[event] = handler

    async def send(self, method, params=None):
        self.sent.append((method, params))
        if method == 'Browser.setDownloadBehavior':
            self.download_path = params['downloadPath']

    def fire(self):
        if not self.start:
            return
        guid = 'guid-1'
        Path(self.download_path, guid).write_bytes(self.out_bytes)
        self.handlers['Browser.downloadWillBegin']({
            'guid': guid, 'suggestedFilename': self.suggested, 'url': 'https://x/download'})
        self.handlers['Browser.downloadProgress']({'guid': guid, 'state': 'inProgress'})
        self.handlers['Browser.downloadProgress']({
            'guid': guid, 'state': 'completed',
            'filePath': str(Path(self.download_path, guid))})


def _automator_with(session):
    automator = NotebookLMAutomator()
    automator.browser = MagicMock()
    automator.browser.new_browser_cdp_session = AsyncMock(return_value=session)
    return automator


def test_capture_download_saves_under_stem_with_suggested_extension(tmp_path):
    session = _FakeCDPSession(suggested='Treating_AI_as_a_Relative.m4a')
    automator = _automator_with(session)

    async def trigger():
        session.fire()

    requested = tmp_path / 'treating-ai.mp3'
    saved, reason = asyncio.run(automator._capture_download(trigger, str(requested)))

    assert reason is None
    assert saved == str(tmp_path / 'treating-ai.m4a')
    assert Path(saved).read_bytes() == b'media'
    assert not (tmp_path / 'guid-1').exists()
    method, params = session.sent[0]
    assert method == 'Browser.setDownloadBehavior'
    assert params == {'behavior': 'allowAndName', 'downloadPath': str(tmp_path),
                      'eventsEnabled': True}
    session.detach.assert_awaited_once()


def test_capture_download_appends_extension_to_bare_stem(tmp_path):
    session = _FakeCDPSession(suggested='Decolonizing_Code_Infographic.png')
    automator = _automator_with(session)

    async def trigger():
        session.fire()

    saved, reason = asyncio.run(
        automator._capture_download(trigger, str(tmp_path / 'infographic-20261006T2206')))

    assert reason is None
    assert saved == str(tmp_path / 'infographic-20261006T2206.png')


def test_capture_download_reports_a_download_that_never_starts(tmp_path):
    session = _FakeCDPSession(start=False)
    automator = _automator_with(session)

    async def trigger():
        session.fire()

    saved, reason = asyncio.run(automator._capture_download(
        trigger, str(tmp_path / 'x.m4a'), start_timeout=0.05))

    assert saved is None
    assert reason == 'download did not start'
    session.detach.assert_awaited_once()


# ── _download_card_via_menu ──────────────────────────────────────

def test_card_without_download_item_is_reported_and_menu_closed():
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.wait_for_selector = AsyncMock(side_effect=Exception('timeout'))
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    automator.page = page

    more = MagicMock()
    more.click = AsyncMock()
    card = MagicMock()
    card.query_selector = AsyncMock(return_value=more)

    saved, reason = asyncio.run(automator._download_card_via_menu(card, '/tmp/unused'))

    assert saved is None
    assert reason == 'no Download item in card menu'
    card.query_selector.assert_awaited_once_with('button[aria-label="More"]')
    more.click.assert_awaited_once()
    page.keyboard.press.assert_awaited_once_with('Escape')


# ── Completion detection ─────────────────────────────────────────

def test_completion_selectors_never_match_a_generating_card():
    from deepdiver.studio_artifacts import GENERATING_CARD_MARKER, completed_card_selectors
    for selector in completed_card_selectors('Infographic'):
        if selector.startswith('artifact-library-item'):
            assert f':not(:has({GENERATING_CARD_MARKER}))' in selector, selector


def test_mind_map_completion_is_matched_by_its_icon():
    from deepdiver.studio_artifacts import completed_card_selectors
    selectors = completed_card_selectors('Mind Map')
    assert any('.artifact-icon:text-is("flowchart")' in s for s in selectors)


# ── Reports ──────────────────────────────────────────────────────

def test_report_card_label_and_templates_resolve():
    from deepdiver.studio_artifacts import (
        normalize_artifact_format, normalize_artifact_type, normalize_report_template,
    )
    assert normalize_artifact_type('Report') == 'reports'
    assert normalize_artifact_format('reports', 'interactive') == 'Interactive'
    assert normalize_artifact_format('reports', 'document') == 'Document'
    assert normalize_report_template('briefing-doc') == 'Briefing Doc'
    assert normalize_report_template('learning_overview') == 'Learning Overview'
    # Suggested templates are written from the sources and pass through.
    assert normalize_report_template('Architecture Specification') == 'Architecture Specification'


def test_report_card_family_is_the_canonical_label():
    automator = NotebookLMAutomator()
    card = _IconCard('Executive Briefing', 'Report', 'auto_tab_group')
    assert asyncio.run(automator._card_family_label(card)) == 'Reports'


# ── Report save reads the artifact viewer, never the chat ────────

class _FakeViewer:
    def __init__(self, markdown, html):
        self._markdown, self._html = markdown, html
        self.first = self

    async def wait_for(self, state=None, timeout=None):
        return None

    async def evaluate(self, script):
        return self._markdown

    async def inner_html(self):
        return self._html


def test_save_report_card_reads_the_artifact_viewer_not_a_chat_answer(tmp_path):
    """Chat answers render in the same doc-viewer element as reports and come
    first in the DOM; the saved report must be the one in the artifact viewer."""
    chat = _FakeViewer('In the sources, Guillaume corrects agents aloud ...\n', '<div>Thoughts</div>')
    report = _FakeViewer('# Mastering the Miadi Screenwalk\n\n## Introduction\n', '<div>report</div>')
    page = MagicMock()
    page.locator = MagicMock(side_effect=lambda sel: report if sel.startswith('artifact-viewer ') else chat)

    automator = NotebookLMAutomator()
    automator.page = page
    automator.open_artifact_card = AsyncMock(return_value=True)
    automator.close_artifact_viewer = AsyncMock()

    saved, reason = asyncio.run(automator.save_report_card(
        MagicMock(), str(tmp_path / 'report'), title='Mastering the Miadi Screenwalk'))

    assert reason is None
    text = Path(saved['path']).read_text()
    assert text.startswith('# Mastering the Miadi Screenwalk')
    assert 'corrects agents aloud' not in text
    assert 'Thoughts' not in Path(saved['html_path']).read_text()
    automator.close_artifact_viewer.assert_awaited_once()


def test_signin_redirect_is_not_a_notebook():
    from deepdiver.notebooklm_automator import _is_google_signin_url
    signin = ('https://accounts.google.com/v3/signin/identifier?continue='
              'https://notebook.google.com/login?continue%3Dhttps://notebook.google.com/notebook/0ae51b4c')
    assert _is_google_signin_url(signin)
    assert not _is_notebook_url(signin)
    assert _is_notebook_url('https://notebook.google.com/notebook/0ae51b4c-8ed2-4ee2-a641-2c7e88b7e2ea')
