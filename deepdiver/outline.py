"""
What a Studio plan leaves behind: the outline or producer notes a person or an
agent read, and the feedback they gave, kept beside the notebook's media.

A Slide Deck or Video Overview made with the review switch stops at a plan
(observed 2026-11-05, miadi-chronicle://251). Pressing Proceed, or sending
feedback, renders the deck at once, on the same card. Studio keeps no copy of
the plan or of the feedback: "Prompt and sources" then shows only the first
prompt. So the plan is saved before anything is pressed, and each saved plan is
a numbered file: a new version is a new run seeded from a kept one
(`studio generate --from-outline`), which stops at its own plan.

Entries go in manifest.json under `downloads`, where the episode room reads
what a notebook keeps. They carry `outline_of` instead of `artifact_id`: the
card keeps its id through the render, and `studio download` skips a card whose
id it finds there, so an `artifact_id` here would hide the finished deck.
"""

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .keep import _kept_record

SAVED_HOW = 'read from the Studio review panel, before Proceed'
FEEDBACK_HOW = 'the exact feedback sent to Studio; Studio keeps no copy of it'
FRONT_MATTER_RE = re.compile(r'\A---\n.*?\n---\n+', re.S)


def _manifest_path(folder: str) -> str:
    return os.path.join(folder, 'manifest.json')


def read_manifest(folder: str, notebook_id: Optional[str] = None) -> Dict[str, Any]:
    """The folder's manifest.json, or a new one in the shape `studio download` writes."""
    path = _manifest_path(folder)
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            manifest = json.load(fh)
        if isinstance(manifest, dict):
            manifest.setdefault('downloads', [])
            return manifest
    return {'notebook_id': notebook_id, 'created_at': datetime.now().isoformat(),
            'downloads': [], 'skipped': [], 'failed': []}


def write_manifest(folder: str, manifest: Dict[str, Any]) -> None:
    with open(_manifest_path(folder), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write('\n')


def outline_entries(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The saved plans of a folder, oldest first."""
    return [e for e in manifest.get('downloads', []) if e.get('outline_version')]


def render_outline(plan: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """A plan as Markdown: where it came from, then its items as Studio showed them."""
    lines = ['---',
             f"notebook_id: {meta.get('notebook_id')}",
             f"artifact_id: {meta.get('artifact_id')}",
             f"family: {meta.get('family')}",
             f"plan: {plan.get('step') or 'plan'}",
             f"version: {meta.get('version')}",
             f"saved_at: {meta.get('saved_at')}"]
    if meta.get('seeded_from'):
        lines.append(f"seeded_from: {meta['seeded_from']}")
    lines += ['---', '', f"# {plan.get('title') or 'Untitled plan'}", '']
    items = plan.get('items') or []
    if items:
        lines += [f"{number}. {text}" for number, text in enumerate(items, 1)]
    else:
        lines.append(plan.get('text') or '')
    return '\n'.join(lines).rstrip() + '\n'


def plan_is_empty(plan: Optional[Dict[str, Any]]) -> bool:
    return not plan or not (plan.get('items') or (plan.get('text') or '').strip())


def save_outline(folder: str, plan: Dict[str, Any], artifact_id: str, family: str,
                 notebook_id: Optional[str] = None, seeded_from: Optional[str] = None) -> Dict[str, Any]:
    """Save a plan as the folder's next version, or return the entry already holding it."""
    os.makedirs(folder, exist_ok=True)
    manifest = read_manifest(folder, notebook_id)
    entries = outline_entries(manifest)
    fingerprint = hashlib.sha256(json.dumps(
        {'title': plan.get('title'), 'items': plan.get('items'), 'text': plan.get('text')},
        sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    for entry in entries:
        if entry.get('outline_of') == artifact_id and entry.get('plan_sha256') == fingerprint:
            return entry

    version = len(entries) + 1
    saved_at = datetime.now().isoformat(timespec='seconds')
    path = os.path.join(folder, f'outline-{version:02d}-{(artifact_id or "card")[:8]}.md')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(render_outline(plan, {'notebook_id': notebook_id, 'artifact_id': artifact_id,
                                       'family': family, 'version': version, 'saved_at': saved_at,
                                       'seeded_from': seeded_from}))
    entry = {
        'title': f"{plan.get('step') or 'Plan'} v{version}: {plan.get('title') or family}",
        'family_label': 'Outline',
        'outline_of': artifact_id,
        'outline_version': version,
        'outline_family': family,
        'plan_sha256': fingerprint,
        'item_count': len(plan.get('items') or []),
        'path': path,
        'size': os.path.getsize(path),
        'saved_at': saved_at,
        'kept': _kept_record(folder, path, SAVED_HOW),
    }
    if seeded_from:
        entry['seeded_from'] = seeded_from
    manifest['downloads'].append(entry)
    write_manifest(folder, manifest)
    return entry


def save_feedback(folder: str, outline: Dict[str, Any], feedback: str) -> Dict[str, Any]:
    """Save the feedback beside its plan, before it is sent."""
    manifest = read_manifest(folder)
    stem = os.path.splitext(os.path.basename(outline['path']))[0]
    path = os.path.join(folder, f'{stem}.feedback.md')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(feedback.rstrip() + '\n')
    version = outline['outline_version']
    entry = {
        'title': f'Feedback on plan v{version}',
        'family_label': 'Outline feedback',
        'outline_of': outline.get('outline_of'),
        'feedback_on_version': version,
        'path': path,
        'size': os.path.getsize(path),
        'saved_at': datetime.now().isoformat(timespec='seconds'),
        'kept': _kept_record(folder, path, FEEDBACK_HOW),
    }
    manifest['downloads'] = [e for e in manifest.get('downloads', [])
                             if e.get('feedback_on_version') != version] + [entry]
    write_manifest(folder, manifest)
    return entry


def record_proceed(folder: str, outline: Dict[str, Any], **fields: Any) -> None:
    """Note on the plan's entry that it was sent on to render, and what came of it."""
    manifest = read_manifest(folder)
    for entry in manifest.get('downloads', []):
        if entry.get('outline_version') == outline.get('outline_version'):
            entry.update(fields)
    write_manifest(folder, manifest)


def outline_body(path: str) -> str:
    """A kept plan's text, without the lines saying where it came from."""
    with open(path, encoding='utf-8') as fh:
        return FRONT_MATTER_RE.sub('', fh.read()).strip()


def compose_seed(outline_path: str, focus: Optional[str] = None, feedback: Optional[str] = None) -> str:
    """The description for a new run: the brief, the kept plan, the feedback on it."""
    parts = []
    if focus and focus.strip():
        parts.append(focus.strip())
    parts.append('Use this outline as the plan:\n\n' + outline_body(outline_path))
    if feedback and feedback.strip():
        parts.append('Change it as follows:\n\n' + feedback.strip())
    return '\n\n'.join(parts)
