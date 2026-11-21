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
#
# 'icon' is the Material Symbols name shared by the Studio tile and the card's
# .artifact-icon. Some cards (Mind Map, observed 2026-10-06) carry only the
# generic aria-description "Artifact", so the icon is the fallback family key.
ARTIFACT_CARD_SELECTOR = 'artifact-library-item'

# A card still generating already carries the family label and a title
# ("Generating Infographic... based on 2 sources"); what it lacks is an
# enabled main button and a More menu. Its main button is disabled
# (observed 2026-10-06), so every completion selector excludes that.
GENERATING_CARD_MARKER = '.mat-mdc-button-disabled'

# A Slide Deck or Video Overview made with the review switch stops at a plan
# (observed 2026-11-05): the card says "Outline ready", its main button is
# enabled and it has a More menu, so it looks finished to everything above. It
# is not. Nothing is rendered until someone presses Review, then Proceed.
PENDING_REVIEW_MARKER = '.artifact-item-button-pending-review'
REVIEW_BUTTON_SELECTOR = '.review-plan-button button'
# Review opens the plan in the Studio panel, not in a dialog. A chat answer can
# carry an a2ui card too, so the plan is read only inside this viewer.
PLAN_SELECTOR = '.plan-viewer-container .a2ui-plan-container'
READY_CARD_SELECTOR = (
    f'{ARTIFACT_CARD_SELECTOR}:not(:has({GENERATING_CARD_MARKER})):not(:has({PENDING_REVIEW_MARKER}))'
)

ARTIFACT_TYPES: Dict[str, Dict[str, Any]] = {
    'audio_overview': {
        'label': 'Audio Overview',
        'icon': 'audio_spark',
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
        'icon': 'tablet',
        'formats': {
            'detailed': 'Detailed Deck',
            'detailed_deck': 'Detailed Deck',
            'presenter': 'Presenter Slides',
            'presenter_slides': 'Presenter Slides',
        },
        'supports_language': True,
        'supports_length': True,
        'supports_focus_prompt': True,
        # The card's menu offers PDF and PowerPoint (2026-11-05). Every slide of
        # either is one image, so neither carries selectable text.
        'downloadable': True,
        'playable': False,
        'review_switch': 'Review slide outline',
    },
    'video_overview': {
        'label': 'Video Overview',
        'icon': 'videocam',
        # Observed 2026-10-06: Short (9:16, "a bite-sized overview") and
        # Explainer (16:9). "Brief" was the earlier name of the short one.
        'formats': {
            'explainer': 'Explainer',
            'short': 'Short',
            'brief': 'Short',
        },
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': True,
        'playable': True,
        'review_switch': 'Review producer notes',
    },
    'mind_map': {
        'label': 'Mind Map',
        'icon': 'flowchart',
        'formats': None,
        'supports_language': False,
        'supports_length': False,
        'supports_focus_prompt': False,
        'downloadable': False,
        'playable': False,
    },
    'reports': {
        'label': 'Reports',
        'icon': 'auto_tab_group',
        # Cards say "Report"; the dialog is titled "Create report".
        'card_label': 'Report',
        'dialog_title': 'Create report',
        'formats': {
            'interactive': 'Interactive',
            'document': 'Document',
        },
        # Fixed templates (observed 2026-10-06). Document also lists
        # "Suggested Template" cards written from the sources; any of
        # those can be named by its visible title.
        'templates': {
            'learning_overview': 'Learning Overview',
            'create_your_own': 'Create Your Own',
            'briefing_doc': 'Briefing Doc',
            'study_guide': 'Study Guide',
            'blog_post': 'Blog Post',
        },
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        # Interactive reports have no Download or export; Document reports
        # export to Docs/Sheets only.
        'downloadable': False,
        'playable': False,
    },
    'flashcards': {
        'label': 'Flashcards',
        'icon': 'copy',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'quiz': {
        'label': 'Quiz',
        'icon': 'quiz',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': False,
        'playable': False,
    },
    'infographic': {
        'label': 'Infographic',
        'icon': 'stacked_bar_chart',
        'formats': None,
        'supports_language': True,
        'supports_length': False,
        'supports_focus_prompt': True,
        'downloadable': True,
        'playable': False,
    },
    'data_table': {
        'label': 'Data Table',
        'icon': 'format_list_bulleted',
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
    # Accept the display label, or the label a card shows ("Report"), too.
    for type_key, spec in ARTIFACT_TYPES.items():
        if value.strip().lower() in (spec['label'].lower(), spec.get('card_label', '').lower()):
            return type_key
    return None


def family_label_from_icon(icon: Optional[str]) -> Optional[str]:
    """Resolve a card's .artifact-icon symbol name to its family label."""
    if not icon:
        return None
    icon = icon.strip()
    for spec in ARTIFACT_TYPES.values():
        if spec.get('icon') == icon:
            return spec['label']
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
    A card whose main button is disabled is still generating and never
    matches.
    """
    selectors = []
    if artifact_label:
        selectors.extend([
            f'{READY_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(button[aria-label="Play"])',
            f'{READY_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(button[aria-label="More"])',
            f'{READY_CARD_SELECTOR}:has([aria-description="{artifact_label}"]):has(.artifact-title)',
        ])
        # Mind Map cards say only "Artifact"; their icon names the family.
        # :text-is() is a Playwright pseudo-class, fine for query_selector.
        spec = get_artifact_spec(artifact_label)
        if spec and spec.get('icon'):
            selectors.append(
                f'{READY_CARD_SELECTOR}:has(.artifact-icon:text-is("{spec["icon"]}"))'
                f':has(button[aria-label="More"])'
            )
    selectors.extend([
        f'{READY_CARD_SELECTOR}:has(.artifact-title):has(button[aria-label="Play"]):has(button[aria-label="More"])',
        f'{READY_CARD_SELECTOR}:has(.artifact-more-button):has(button[aria-label="Play"])',
        # Legacy pre-drift cues kept as last resorts.
        '.studio-artifact:has(button:has-text("Load"))',
        '.artifact-card:has(button:has-text("Load"))',
    ])
    return selectors


def normalize_report_template(value: Optional[str]) -> Optional[str]:
    """Resolve a template key or title; unknown titles pass through as given."""
    if not value:
        return None
    templates = ARTIFACT_TYPES['reports']['templates']
    key = value.strip().lower().replace('-', '_').replace(' ', '_')
    if key in templates:
        return templates[key]
    return value.strip()


def list_artifact_type_keys() -> List[str]:
    """Stable ordering of artifact type keys for CLI help and iteration."""
    return list(ARTIFACT_TYPES.keys())
