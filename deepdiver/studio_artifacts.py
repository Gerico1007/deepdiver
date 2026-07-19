"""
Studio Artifact Registry
Part of DeepDiver - NotebookLM Podcast Automation System

Shared definitions for every NotebookLM/Gemini Notebook Studio artifact
family, so generation, detection, and session tracking speak one language.

The tile labels and card markers come from live-session observations of the
current Studio panel (Gemini Notebook rebrand era): Audio Overview,
Slide Deck, Video Overview, Mind Map, Reports, Flashcards, Quiz,
Infographic, and Data Table.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

from typing import Any, Dict, List, Optional


# Card completion cues shared by every artifact family. A finished artifact
# renders an <artifact-library-item> card whose aria-description names the
# family; a Play button plus a More/menu button is the strong completion
# signal for playable artifacts, while non-playable ones still expose the
# title + More controls.
ARTIFACT_CARD_SELECTOR = 'artifact-library-item'

ARTIFACT_TYPES: Dict[str, Dict[str, Any]] = {
    'audio_overview': {
        'label': 'Audio Overview',
        'formats': {
            'deep_dive': 'Deep Dive',
            'brief': 'Brief',
            'critique': 'Critique',
            'debate': 'Debate',
        },
        'supports_language': True,
        'supports_length': True,
        'supports_focus_prompt': True,
        'downloadable': True,
        'playable': True,
    },
    'slide_deck': {
        'label': 'Slide Deck',
        'formats': {
            'detailed': 'Detailed Deck',
            'detailed_deck': 'Detailed Deck',
            'presenter': 'Presenter Slides',
            'presenter_slides': 'Presenter Slides',
        },
        'supports_language': True,
        'supports_length': True,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'video_overview': {
        'label': 'Video Overview',
        'formats': {
            'explainer': 'Explainer',
            'brief': 'Brief',
        },
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': True,
        'playable': True,
    },
    'mind_map': {
        'label': 'Mind Map',
        'formats': None,
        'supports_language': False,
        'supports_length': False,
        'supports_focus_prompt': False,
        'downloadable': False,
        'playable': False,
    },
    'reports': {
        'label': 'Reports',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'flashcards': {
        'label': 'Flashcards',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'quiz': {
        'label': 'Quiz',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'infographic': {
        'label': 'Infographic',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'data_table': {
        'label': 'Data Table',
        'formats': None,
        'supports_language': False,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
}

# Artifact families that DeepDiver can substitute when the requested family
# is unavailable in the current UI, recorded so status/result reporting can
# state the fallback honestly instead of failing silently.
ARTIFACT_FALLBACKS: Dict[str, str] = {
    'video_overview': 'audio_overview',
}


def normalize_artifact_type(value: str) -> Optional[str]:
    """Resolve a user-supplied artifact type to a registry key."""
    if not value:
        return None
    key = value.strip().lower().replace('-', '_').replace(' ', '_')
    if key in ARTIFACT_TYPES:
        return key
    # Accept the display label as input too ("Slide Deck" -> slide_deck).
    for type_key, spec in ARTIFACT_TYPES.items():
        if spec['label'].lower() == value.strip().lower():
            return type_key
    return None


def get_artifact_spec(artifact_type: str) -> Optional[Dict[str, Any]]:
    """Return the registry spec for an artifact type (normalized)."""
    key = normalize_artifact_type(artifact_type)
    if key is None:
        return None
    return ARTIFACT_TYPES[key]


def normalize_artifact_format(artifact_type: str, value: Optional[str]) -> Optional[str]:
    """Resolve a user-supplied format to the display label the dialog shows."""
    spec = get_artifact_spec(artifact_type)
    if not spec or not value:
        return None
    formats = spec.get('formats')
    if not formats:
        return None
    key = value.strip().lower().replace('-', '_').replace(' ', '_')
    if key in formats:
        return formats[key]
    # Accept the display label directly ("Presenter Slides").
    for display in formats.values():
        if display.lower() == value.strip().lower():
            return display
    return None


def completed_card_selectors(artifact_label: Optional[str] = None) -> List[str]:
    """
    Drift-tolerant selectors that identify a COMPLETED artifact card.

    These are the durable completion cues observed after NotebookLM UI drift:
    legacy 'Load' buttons disappeared, and the current card exposes
    aria-description + Play/More controls inside <artifact-library-item>.
    """
    selectors = []
    if artifact_label:
        selectors.extend([
            f'{ARTIFACT_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(button[aria-label="Play"])',
            f'{ARTIFACT_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(button[aria-label="More"])',
            f'{ARTIFACT_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(.artifact-title)',
        ])
    selectors.extend([
        f'{ARTIFACT_CARD_SELECTOR}:has(.artifact-title):has(button[aria-label="Play"]):has(button[aria-label="More"])',
        f'{ARTIFACT_CARD_SELECTOR}:has(.artifact-more-button):has(button[aria-label="Play"])',
        # Legacy pre-drift cues kept as last resorts.
        '.studio-artifact:has(button:has-text("Load"))',
        '.artifact-card:has(button:has-text("Load"))',
    ])
    return selectors


def list_artifact_type_keys() -> List[str]:
    """Stable ordering of artifact type keys for CLI help and iteration."""
    return list(ARTIFACT_TYPES.keys())
