"""
`studio keep`: what an episode commits from a download folder
(miadi-chronicle://251, finding F8 of the first /deepdive run).
"""

import json
import os
import shutil
import subprocess

import pytest

from deepdiver.keep import keep_folder

pytestmark = pytest.mark.skipif(shutil.which('ffmpeg') is None, reason='needs ffmpeg')


def _ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


@pytest.fixture
def download(tmp_path):
    folder = tmp_path / 'notebook-abc'
    folder.mkdir()
    png = folder / 'Diagram-20261010T001522.png'
    mp4 = folder / 'Overview-20261010T001515.mp4'
    m4a = folder / 'Audio-20261010T001530.m4a'
    md = folder / 'Report-20261010T001509.md'
    html = folder / 'Report-20261010T001509.html'
    _ffmpeg('-f', 'lavfi', '-i', 'testsrc=size=320x240:rate=1', '-frames:v', '1', str(png))
    _ffmpeg('-f', 'lavfi', '-i', 'testsrc=size=320x240:rate=5', '-f', 'lavfi',
            '-i', 'sine=frequency=440', '-t', '2', '-c:v', 'libx264', '-c:a', 'aac', str(mp4))
    _ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '2', '-c:a', 'aac', str(m4a))
    md.write_text('# Report\n')
    html.write_text('<p>Report</p>')
    manifest = {'notebook_id': 'abc', 'downloads': [
        {'title': 'Report', 'family_label': 'Reports', 'path': str(md), 'html_path': str(html),
         'size': md.stat().st_size, 'sha256': 'x'},
        {'title': 'Overview', 'family_label': 'Video Overview', 'path': str(mp4),
         'size': mp4.stat().st_size, 'sha256': 'y'},
        {'title': 'Diagram', 'family_label': 'Infographic', 'path': str(png),
         'size': png.stat().st_size, 'sha256': 'z'},
        {'title': 'Audio', 'family_label': 'Audio Overview', 'path': str(m4a),
         'size': m4a.stat().st_size, 'sha256': 'w'},
    ], 'skipped': [], 'failed': []}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    return folder


def _by_title(manifest):
    return {e['title']: e for e in manifest['downloads']}


def test_image_becomes_webp_and_png_is_removed(download):
    entry = _by_title(keep_folder(str(download)))['Diagram']
    assert entry['kept']['path'] == 'Diagram-20261010T001522.webp'
    assert (download / 'Diagram-20261010T001522.webp').exists()
    assert not (download / 'Diagram-20261010T001522.png').exists()
    assert entry['sha256'] == 'z'  # the download's own record stays


def test_video_and_audio_go_to_keep_and_downloads_stay(download):
    entries = _by_title(keep_folder(str(download)))
    assert entries['Overview']['kept']['path'] == os.path.join('keep', 'Overview-20261010T001515.mp4')
    assert entries['Audio']['kept']['path'] == os.path.join('keep', 'Audio-20261010T001530.m4a')
    assert (download / 'Overview-20261010T001515.mp4').exists()
    assert (download / 'keep' / 'Overview-20261010T001515.mp4').exists()
    assert 'CRF 30' in entries['Overview']['kept']['how']


def test_report_is_kept_as_downloaded(download):
    entry = _by_title(keep_folder(str(download)))['Report']
    assert entry['kept']['path'] == 'Report-20261010T001509.md'
    assert entry['kept']['how'] == 'as downloaded'


def test_manifest_is_rewritten_with_relative_kept_paths(download):
    keep_folder(str(download))
    on_disk = json.loads((download / 'manifest.json').read_text())
    for entry in on_disk['downloads']:
        assert not os.path.isabs(entry['kept']['path'])
        assert len(entry['kept']['sha256']) == 64


def test_second_run_changes_nothing(download):
    first = keep_folder(str(download))
    second = keep_folder(str(download))
    assert [e['kept'] for e in first['downloads']] == [e['kept'] for e in second['downloads']]


def test_a_folder_kept_by_hand_is_recorded_not_redone(download):
    # Episode 120, 2026-10-10: the PNG was converted and removed by hand, the
    # video re-encoded into keep/, and manifest.json still named the PNG.
    _ffmpeg('-i', str(download / 'Diagram-20261010T001522.png'), '-c:v', 'libwebp',
            str(download / 'Diagram-20261010T001522.webp'))
    os.remove(download / 'Diagram-20261010T001522.png')
    (download / 'keep').mkdir()
    shutil.copy(download / 'Overview-20261010T001515.mp4', download / 'keep' / 'Overview-20261010T001515.mp4')
    before = (download / 'keep' / 'Overview-20261010T001515.mp4').stat().st_mtime_ns
    entries = _by_title(keep_folder(str(download)))
    assert entries['Diagram']['kept']['path'] == 'Diagram-20261010T001522.webp'
    assert 'made before this run' in entries['Diagram']['kept']['how']
    assert (download / 'keep' / 'Overview-20261010T001515.mp4').stat().st_mtime_ns == before
    assert 'kept_error' not in entries['Diagram']
