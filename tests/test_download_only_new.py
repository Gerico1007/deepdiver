"""studio download takes only what a folder's manifest does not hold yet.

2026-10-30 and 2026-11-03: every run fetched and re-encoded each artifact of the
notebook under a new name and overwrote the manifest, so a seat had to download
into a scratchpad to keep one new video.
"""

import asyncio
import json
from pathlib import Path

from deepdiver.notebooklm_automator import NotebookLMAutomator, card_is_held
from tests.test_studio_download_alignment import FakeCard, _make_page


def _automator(cards, touched):
    automator = NotebookLMAutomator()
    automator.page = _make_page(cards)

    async def fake_card_download(card, output_path, timeout=None):
        touched.append(card.title)
        Path(output_path + '.mp4').write_bytes(b'media-bytes')
        return output_path + '.mp4', None

    automator._download_card_via_menu = fake_card_download
    return automator


def test_a_held_card_is_left_and_a_new_one_joins_the_manifest(tmp_path):
    prior = {
        'notebook_id': 'n', 'created_at': '2026-10-29T22:00:00',
        'downloads': [{'title': 'Old', 'artifact_id': 'id-Old', 'path': 'Old.mp4', 'size': 1,
                       'kept': {'path': 'keep/Old.mp4'}}],
        'skipped': [{'title': 'stale', 'reason': 'last run'}], 'failed': [],
    }
    (tmp_path / 'manifest.json').write_text(json.dumps(prior))
    touched = []
    cards = [FakeCard('New', 'Video Overview'), FakeCard('Old', 'Video Overview')]

    manifest = asyncio.run(_automator(cards, touched).download_all_artifacts(str(tmp_path)))

    assert touched == ['New']
    assert [e['title'] for e in manifest['fresh']] == ['New']
    assert manifest['already'] == ['Old']
    written = json.loads((tmp_path / 'manifest.json').read_text())
    assert [e['title'] for e in written['downloads']] == ['Old', 'New']
    assert written['downloads'][0]['kept'] == {'path': 'keep/Old.mp4'}
    assert written['created_at'] == '2026-10-29T22:00:00'
    assert written['skipped'] == []
    assert 'fresh' not in written and 'already' not in written


def test_a_new_folder_gets_everything(tmp_path):
    touched = []
    cards = [FakeCard('A', 'Video Overview'), FakeCard('B', 'Video Overview')]
    manifest = asyncio.run(_automator(cards, touched).download_all_artifacts(str(tmp_path)))
    assert touched == ['A', 'B']
    assert manifest['already'] == []


def test_two_cards_with_one_title_are_told_apart_by_id(tmp_path):
    entries = [{'title': 'Same', 'artifact_id': 'one'}]
    assert card_is_held({'title': 'Same', 'artifact_id': 'one'}, entries)
    assert not card_is_held({'title': 'Same', 'artifact_id': 'two'}, entries)


def test_a_card_without_an_id_falls_back_to_its_title():
    assert card_is_held({'title': 'Same', 'artifact_id': None}, [{'title': 'Same', 'artifact_id': 'one'}])
    assert card_is_held({'title': 'Same', 'artifact_id': 'two'}, [{'title': 'Same'}])
    assert not card_is_held({'title': 'Other', 'artifact_id': None}, [{'title': 'Same', 'artifact_id': 'one'}])
