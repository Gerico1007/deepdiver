"""
Tests for the studio artifact foundation: registry, resume diffing,
session-tracker truth handling, and the bundled skills subsystem.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import json
import os

import pytest

from deepdiver.studio_artifacts import (
    ARTIFACT_TYPES,
    completed_card_selectors,
    get_artifact_spec,
    list_artifact_type_keys,
    normalize_artifact_format,
    normalize_artifact_type,
)
from deepdiver.session_tracker import SessionTracker, compute_missing_sources
from deepdiver import skills_manager


# ── Artifact registry ────────────────────────────────────────────

def test_registry_covers_full_studio_family():
    expected = {
        'audio_overview', 'slide_deck', 'video_overview', 'mind_map',
        'reports', 'flashcards', 'quiz', 'infographic', 'data_table',
    }
    assert expected == set(list_artifact_type_keys())


def test_normalize_artifact_type_accepts_labels_and_variants():
    assert normalize_artifact_type('slide_deck') == 'slide_deck'
    assert normalize_artifact_type('Slide Deck') == 'slide_deck'
    assert normalize_artifact_type('slide-deck') == 'slide_deck'
    assert normalize_artifact_type('Audio Overview') == 'audio_overview'
    assert normalize_artifact_type('nonsense') is None
    assert normalize_artifact_type('') is None


def test_normalize_artifact_format_maps_to_dialog_labels():
    assert normalize_artifact_format('slide_deck', 'presenter') == 'Presenter Slides'
    assert normalize_artifact_format('slide_deck', 'detailed') == 'Detailed Deck'
    assert normalize_artifact_format('slide_deck', 'Presenter Slides') == 'Presenter Slides'
    assert normalize_artifact_format('audio_overview', 'deep_dive') == 'Deep Dive'
    assert normalize_artifact_format('mind_map', 'anything') is None
    assert normalize_artifact_format('slide_deck', None) is None


def test_completed_card_selectors_carry_drift_tolerant_cues():
    selectors = completed_card_selectors('Audio Overview')
    joined = ' '.join(selectors)
    assert 'aria-description="Audio Overview"' in joined
    assert 'button[aria-label="Play"]' in joined
    assert 'artifact-library-item' in joined
    # Family-specific selectors must come before the generic fallbacks.
    assert 'Audio Overview' in selectors[0]


def test_every_spec_declares_capability_flags():
    for key, spec in ARTIFACT_TYPES.items():
        assert spec['label'], key
        for flag in ('supports_language', 'supports_length',
                     'supports_focus_prompt', 'downloadable', 'playable'):
            assert isinstance(spec[flag], bool), (key, flag)


# ── Resume source diffing ────────────────────────────────────────

def test_compute_missing_sources_diffs_by_basename():
    existing = {'a.md', 'b.pdf'}
    candidates = ['/packet/a.md', '/packet/c.txt', '/other/b.pdf', '/packet/d.md']
    missing = compute_missing_sources(existing, candidates)
    assert missing == ['/packet/c.txt', '/packet/d.md']


def test_compute_missing_sources_handles_empty_inputs():
    assert compute_missing_sources(None, None) == []
    assert compute_missing_sources(set(), ['/x/a.md']) == ['/x/a.md']
    assert compute_missing_sources({'a.md'}, []) == []


# ── Session tracker truth handling ───────────────────────────────

@pytest.fixture
def tracker(tmp_path):
    return SessionTracker({'SESSION_TRACKING': {'session_dir': str(tmp_path)}})


def test_load_current_session_is_explicit(tracker, tmp_path):
    tracker.start_session(ai_assistant='claude')
    session_id = tracker.current_session['session_id']

    fresh = SessionTracker({'SESSION_TRACKING': {'session_dir': str(tmp_path)}})
    # A fresh tracker must NOT be trusted to auto-load...
    assert fresh.current_session is None
    # ...and the public loader restores the active session.
    assert fresh.load_current_session() is True
    assert fresh.current_session['session_id'] == session_id


def test_load_current_session_without_file(tmp_path):
    fresh = SessionTracker({'SESSION_TRACKING': {'session_dir': str(tmp_path / 'empty')}})
    assert fresh.load_current_session() is False


def test_notebook_source_filenames(tracker):
    tracker.start_session()
    tracker.add_notebook({'id': 'nb-1', 'url': 'https://notebooklm.google.com/notebook/nb-1'})
    tracker.add_source_to_notebook('nb-1', {'filename': 'a.md', 'path': '/x/a.md'})
    tracker.add_source_to_notebook('nb-1', {'filename': 'b.md', 'path': '/x/b.md'})
    assert tracker.get_notebook_source_filenames('nb-1') == ['a.md', 'b.md']
    assert tracker.get_notebook_source_filenames('nb-missing') == []


def test_record_artifact_download_updates_matching_artifact(tracker):
    tracker.start_session()
    tracker.add_notebook({'id': 'nb-1', 'url': 'u'})
    tracker.add_artifact_to_notebook('nb-1', {
        'artifact_id': 'art-1', 'type': 'audio_overview', 'status': 'completed',
    })

    assert tracker.record_artifact_download('nb-1', 'art-1', {
        'title': 'EP128 Overview', 'path': '/out/ep128.mp3',
        'size': 1234, 'sha256': 'deadbeef',
    }) is True

    artifacts = tracker.list_notebook_artifacts('nb-1')
    assert artifacts[0]['download_path'] == '/out/ep128.mp3'
    assert artifacts[0]['download_sha256'] == 'deadbeef'
    assert artifacts[0]['download_size'] == 1234


def test_record_artifact_download_appends_untracked_artifact(tracker):
    tracker.start_session()
    tracker.add_notebook({'id': 'nb-1', 'url': 'u'})

    assert tracker.record_artifact_download('nb-1', 'ghost-artifact', {
        'title': 'Recovered', 'path': '/out/recovered.mp3', 'size': 10,
        'sha256': 'abc', 'family_label': 'Audio Overview',
    }) is True

    artifacts = tracker.list_notebook_artifacts('nb-1')
    assert len(artifacts) == 1
    assert artifacts[0]['status'] == 'downloaded'
    assert artifacts[0]['download_path'] == '/out/recovered.mp3'


# ── Bundled skills subsystem ─────────────────────────────────────

def test_bundled_skills_include_notebooklm_automation():
    bundled = skills_manager.list_bundled_skills()
    names = [skill['name'] for skill in bundled]
    assert 'deepdiver-notebooklm-automation' in names
    skill = skills_manager.get_bundled_skill('deepdiver-notebooklm-automation')
    assert skill is not None
    assert 'SKILL.md' in skill['files']
    assert skill['description']


def test_get_bundled_skill_by_dir_name():
    assert skills_manager.get_bundled_skill('notebooklm-automation') is not None
    assert skills_manager.get_bundled_skill('does-not-exist') is None


def test_resolve_install_target(tmp_path):
    explicit = skills_manager.resolve_install_target(target_dir=str(tmp_path / 'sk'))
    assert explicit == (tmp_path / 'sk').resolve()
    preset = skills_manager.resolve_install_target(agent='claude')
    assert str(preset).endswith('.claude/skills')
    # Explicit dir wins over agent preset.
    both = skills_manager.resolve_install_target(agent='claude', target_dir=str(tmp_path))
    assert both == tmp_path.resolve()
    assert skills_manager.resolve_install_target() is None
    assert skills_manager.resolve_install_target(agent='unknown-agent') is None


def test_install_skill_roundtrip(tmp_path):
    target = tmp_path / 'agent-skills'
    result = skills_manager.install_skill('notebooklm-automation', target)
    assert result['installed'] is True
    installed_md = target / 'notebooklm-automation' / 'SKILL.md'
    assert installed_md.is_file()
    assert 'deepdiver' in installed_md.read_text(encoding='utf-8')

    # Second install without force is skipped, with force succeeds.
    again = skills_manager.install_skill('notebooklm-automation', target)
    assert again['installed'] is False and 'skipped' in again
    forced = skills_manager.install_skill('notebooklm-automation', target, force=True)
    assert forced['installed'] is True


def test_install_all_skills(tmp_path):
    results = skills_manager.install_all_skills(tmp_path / 'all')
    assert results
    assert all(r['installed'] for r in results)
