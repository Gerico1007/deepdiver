"""
Regression tests for ♠️ Nyro's structural review of the Studio artifact
foundation — identity over position, intention over repetition.

Covers:
  1. download_all_artifacts must re-locate each card by its stable DOM index,
     never by its ordinal in the visibility-filtered list (wrong-artifact bug).
  4. download_audio must derive the saved extension from the browser's
     suggested filename instead of the hardcoded .mp3.
  5. download_all_artifacts must let each card's own More menu decide: cards
     whose menu offers Download (audio, video, infographic) are downloaded,
     cards without one are skipped as not downloadable, and an attempted
     download that does not land is recorded as failed.
  3. _monitor_artifact_generation must return the NEW card's metadata on a
     repeat generation, resolved by set-difference against a baseline.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from deepdiver.notebooklm_automator import NotebookLMAutomator


# ── Fake DOM primitives ──────────────────────────────────────────

class _Text:
    def __init__(self, text):
        self.inner_text = AsyncMock(return_value=text)


class _Described:
    def __init__(self, aria_description):
        self.get_attribute = AsyncMock(return_value=aria_description)


class _Play:
    def __init__(self):
        self.click = AsyncMock()


class FakeCard:
    """A minimal artifact-library-item stand-in for the automator's DOM reads."""

    def __init__(self, title, family_label, visible=True, playable=True, artifact_id=None):
        self.title = title
        self.family_label = family_label
        self._attrs = {'data-artifact-id': artifact_id or f'id-{title}'}
        self.play = _Play() if playable else None
        self.is_visible = AsyncMock(return_value=visible)

    async def get_attribute(self, attr):
        return self._attrs.get(attr)

    async def query_selector(self, selector):
        if selector == '.timestamp, .created-at, [data-timestamp]':
            return None
        if selector == '.artifact-title, .title-container .artifact-title':
            return _Text(self.title)
        if selector == '.artifact-details':
            return _Text(f'{self.family_label} · details')
        if selector == '[aria-description]':
            return _Described(self.family_label)
        if selector == 'button[aria-label="Play"]':
            return self.play
        return None


def _make_page(cards):
    page = MagicMock()
    page.query_selector_all = AsyncMock(return_value=cards)
    page.wait_for_timeout = AsyncMock()
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    return page


# ── Finding 1 + 5: alignment by DOM index, card menu decides ─────

def test_download_all_aligns_by_dom_index_when_hidden_card_precedes(tmp_path):
    """
    A hidden Audio card sits at DOM index 0; visible cards follow. The filtered
    list drops it, so ordinal indices diverge from DOM indices. Downloads must
    act on the RIGHT card (by DOM index) and never the hidden decoy, the card
    whose menu has no Download is skipped, and a failed attempt is recorded
    as failed rather than silently skipped.
    """
    ghost = FakeCard('Ghost', 'Audio Overview', visible=False, playable=True)   # dom 0 (filtered)
    alpha = FakeCard('Alpha', 'Audio Overview', visible=True, playable=True)    # dom 1
    beta = FakeCard('Beta Map', 'Mind Map', visible=True, playable=False)       # dom 2
    gamma = FakeCard('Gamma Vid', 'Video Overview', visible=True, playable=True)  # dom 3
    delta = FakeCard('Delta', 'Audio Overview', visible=True, playable=True)    # dom 4
    omega = FakeCard('Omega', 'Infographic', visible=True, playable=False)      # dom 5
    cards = [ghost, alpha, beta, gamma, delta, omega]

    automator = NotebookLMAutomator()
    automator.page = _make_page(cards)

    touched = []

    async def fake_card_download(card, output_path, timeout=None):
        touched.append(card)
        if card is beta:
            return None, 'no Download item in card menu'
        if card is omega:
            return None, 'download did not start'
        ext = '.mp4' if card is gamma else '.m4a'
        Path(output_path + ext).write_bytes(b'media-bytes')
        return output_path + ext, None

    automator._download_card_via_menu = fake_card_download

    manifest = asyncio.run(automator.download_all_artifacts(str(tmp_path)))

    titles = [d['title'] for d in manifest['downloads']]
    assert titles == ['Alpha', 'Gamma Vid', 'Delta']

    # Identity, not ordinal position: the hidden decoy is never touched.
    assert touched == [alpha, beta, gamma, delta, omega]
    assert ghost not in touched

    skipped = {s['title']: s['reason'] for s in manifest['skipped']}
    assert skipped == {'Beta Map': 'Mind Map: no Download item in card menu'}
    failed = {f['title']: f['reason'] for f in manifest['failed']}
    assert failed == {'Omega': 'Infographic: download did not start'}

    # Manifest file titles line up with the files actually written.
    written = json.loads((tmp_path / 'manifest.json').read_text())
    assert [d['title'] for d in written['downloads']] == ['Alpha', 'Gamma Vid', 'Delta']
    for entry in written['downloads']:
        assert Path(entry['path']).exists()


# ── Finding 4: extension derived from the browser suggestion ─────

class _DownloadWaiter:
    def __init__(self, download):
        async def _resolve():
            return download
        self.value = _resolve()


class _ExpectDownload:
    def __init__(self, download):
        self._waiter = _DownloadWaiter(download)

    async def __aenter__(self):
        return self._waiter

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _MenuElement:
    def __init__(self, click_side_effect=None):
        self.click = AsyncMock(side_effect=click_side_effect)
        self.evaluate = AsyncMock()


def test_download_audio_swaps_extension_to_suggested_container(tmp_path):
    """Caller asks for .mp3; browser hands back .m4a → file is saved as .m4a."""
    automator = NotebookLMAutomator()
    page = MagicMock()
    page.wait_for_timeout = AsyncMock()

    menu_open = {"value": False}
    menu_button = _MenuElement(click_side_effect=lambda: menu_open.__setitem__("value", True))
    download_link = _MenuElement()
    download = MagicMock()
    download.suggested_filename = "notebook-overview.m4a"

    saved = {}

    async def save_as(path):
        saved['path'] = path
        Path(path).write_bytes(b'real-m4a-bytes')

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

    requested = tmp_path / "artifact.mp3"
    expected = tmp_path / "artifact.m4a"
    result = asyncio.run(automator.download_audio(str(requested)))

    assert result == str(expected)
    download.save_as.assert_awaited_once_with(str(expected))
    assert saved['path'] == str(expected)
    assert expected.exists()
    assert not requested.exists()


# ── Finding 3: monitor returns the NEW card on repeat generation ─

def test_resolve_new_artifact_returns_added_card_on_repeat_generation():
    """
    detect_completed_artifact handed back the FIRST-matched (pre-existing) card;
    with a baseline set, resolution must return the ADDED card instead.
    """
    automator = NotebookLMAutomator()

    old_meta = {'card_key': 'k-old', 'artifact_id': 'old', 'title': 'Old Overview'}
    new_meta = {'card_key': 'k-new', 'artifact_id': 'new', 'title': 'New Overview'}

    automator._completed_card_snapshot = AsyncMock(return_value=[dict(old_meta), dict(new_meta)])

    detected = dict(old_meta)  # the stale first-match
    resolved = asyncio.run(
        automator._resolve_new_artifact(detected, 'audio_overview', 1, {'k-old'})
    )

    assert resolved['artifact_id'] == 'new'
    assert resolved['title'] == 'New Overview'
    # The identity key is an internal detail, stripped from the returned card.
    assert 'card_key' not in resolved


def test_resolve_new_artifact_passthrough_on_fresh_notebook():
    """baseline_count == 0 → detected is already the only card; return as-is."""
    automator = NotebookLMAutomator()
    automator._completed_card_snapshot = AsyncMock(return_value=[])
    detected = {'artifact_id': 'first', 'title': 'First'}

    resolved = asyncio.run(
        automator._resolve_new_artifact(detected, 'audio_overview', 0, None)
    )
    assert resolved is detected
    automator._completed_card_snapshot.assert_not_called()


def test_resolve_new_artifact_falls_back_when_nothing_added():
    """If no card is distinguishable as new, fall back to detected (no crash)."""
    automator = NotebookLMAutomator()
    old_meta = {'card_key': 'k-old', 'artifact_id': 'old', 'title': 'Old'}
    automator._completed_card_snapshot = AsyncMock(return_value=[dict(old_meta)])
    detected = dict(old_meta)

    resolved = asyncio.run(
        automator._resolve_new_artifact(detected, 'audio_overview', 1, {'k-old'})
    )
    assert resolved is detected


def test_resolve_new_artifact_diffs_on_first_card_of_a_family():
    """No earlier card of the family: the family's own new card wins over
    whatever the completion selectors matched first (another family's card)."""
    automator = NotebookLMAutomator()
    report = {'artifact_id': 'report-1', 'title': 'Mastering the Miadi Screenwalk', 'card_key': 'artifact:report-1'}
    automator._completed_card_snapshot = AsyncMock(return_value=[report])
    detected = {'artifact_id': 'video-1', 'title': 'How Screenwalks Transform Developer Captures'}

    resolved = asyncio.run(
        automator._resolve_new_artifact(detected, 'reports', 0, set())
    )
    assert resolved['title'] == 'Mastering the Miadi Screenwalk'
    assert 'card_key' not in resolved
