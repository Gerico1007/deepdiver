"""
Keep a download in a git repository that is never rewound.

A Miadi Chronicle episode keeps a notebook's media in git, and git keeps every
byte for good there. `studio download --keep` (or `studio keep <dir>`) turns a
download folder into what the episode commits:

- an infographic PNG becomes WebP at quality 90 without metadata, and the PNG
  is removed (Episode 140's went from 4.5 MB to 280 KB);
- a video or audio overview is re-encoded into `keep/`, the only place the
  chronicle's .gitignore lets `.mp4` and `.m4a` in (Episode 140's 31 MB video
  became 6.5 MB). The download stays beside it, out of git;
- a slide deck PDF is recompressed into `keep/` and the download removed: its
  pages are images, so nothing is lost to a text layer (a 6.8 MB deck became
  770 KB on 2026-11-05);
- reports and saved outlines are kept as they are;
- each kept video or audio overview gets its transcript beside it,
  `keep/<name>.transcript.md`, so a person or an agent can review the
  explainer by its words and orchestrate the next version from them
  (William, 2026-10-26: "include in the process of DeepDiver downloading and
  adding to the episode either an audio or video explainer its original
  transcript").

Each entry of manifest.json gains `kept`: the path relative to the folder, its
size and sha256, and how it was made. The download's own `path`, `size` and
`sha256` stay as they were, so the manifest says both what Gemini Notebook gave
and what the episode keeps (miadi-chronicle://251, finding F8 of the first
/deepdive run).
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.webm')
AUDIO_EXTENSIONS = ('.m4a', '.mp3', '.wav')
PDF_EXTENSIONS = ('.pdf',)

WEBP_HOW = 'WebP, quality 90, no metadata (ffmpeg libwebp)'
VIDEO_HOW = 'H.264 CRF 30 preset slow tune stillimage, AAC 64 kb/s, faststart, no metadata (ffmpeg)'
AUDIO_HOW = 'AAC 64 kb/s, faststart, no metadata (ffmpeg)'
PDF_HOW = 'PDF recompressed for reading (ghostscript /ebook)'


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _run_ffmpeg(args: List[str]) -> Optional[str]:
    """Run ffmpeg; return None on success, or its error text."""
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return 'ffmpeg not found'
    proc = subprocess.run([ffmpeg, '-v', 'error', '-y', *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return (proc.stderr or f'ffmpeg exit {proc.returncode}').strip()[-400:]
    return None


def _kept_record(folder: str, path: str, how: str) -> Dict[str, Any]:
    return {
        'path': os.path.relpath(path, folder),
        'size': os.path.getsize(path),
        'sha256': _sha256(path),
        'how': how,
    }


def _run_ghostscript(source: str, target: str) -> Optional[str]:
    """Recompress a PDF; return None on success, or its error text."""
    gs = shutil.which('gs')
    if not gs:
        return 'ghostscript (gs) not found'
    proc = subprocess.run([gs, '-q', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pdfwrite',
                           '-dPDFSETTINGS=/ebook', f'-sOutputFile={target}', source],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout).strip()[-400:] or f'gs exited {proc.returncode}'
    return None


TRANSCRIPT_HOW = 'faster-whisper {model}, English, machine transcription not checked'
DEFAULT_TRANSCRIBER_HOME = os.path.expanduser('~/.local/share/deepdiver/transcribe-venv')


def transcriber_python() -> Optional[str]:
    """A Python that can run transcribe_worker.py: $DEEPDIVER_TRANSCRIBER_PYTHON,
    else DeepDiver's own venv for it, else this Python when it has faster-whisper."""
    env = os.environ.get('DEEPDIVER_TRANSCRIBER_PYTHON')
    if env and os.path.exists(env):
        return env
    home = os.path.join(DEFAULT_TRANSCRIBER_HOME, 'bin', 'python')
    if os.path.exists(home):
        return home
    try:
        import faster_whisper  # noqa: F401
        import numpy  # noqa: F401
        return sys.executable
    except Exception:
        return None


def transcribe_media(media: str, out: str, model: str = 'base') -> Optional[str]:
    """Write `out` as timed lines of `media`; return None, or the reason it could not."""
    python = transcriber_python()
    if not python:
        return ('no transcriber: set DEEPDIVER_TRANSCRIBER_PYTHON to a Python with faster-whisper, '
                f'or make {DEFAULT_TRANSCRIBER_HOME} (python3 -m venv; pip install faster-whisper numpy)')
    worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcribe_worker.py')
    proc = subprocess.run([python, '-I', worker, media, out, model], capture_output=True, text=True)
    if proc.returncode != 0 or not os.path.exists(out):
        return (proc.stderr or f'transcriber exit {proc.returncode}').strip()[-400:]
    return None


def keep_transcript(entry: Dict[str, Any], folder: str, model: str = 'base') -> Dict[str, Any]:
    """Give a kept video or audio its transcript beside it, named in the manifest."""
    kept = entry.get('kept') or {}
    path = kept.get('path') or ''
    if os.path.splitext(path)[1].lower() not in VIDEO_EXTENSIONS + AUDIO_EXTENSIONS:
        return entry
    media = os.path.join(folder, path)
    stem = os.path.splitext(path)[0]
    target = os.path.join(folder, f'{stem}.transcript.md')
    if not os.path.exists(target):
        if not os.path.exists(media):
            kept['transcript_error'] = 'kept media not on disk'
            return entry
        lines_file = target + '.txt'
        error = transcribe_media(media, lines_file, model)
        if error:
            kept['transcript_error'] = error
            return entry
        with open(lines_file, encoding='utf-8') as fh:
            lines = fh.read()
        os.remove(lines_file)
        how = TRANSCRIPT_HOW.format(model=model)
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(f"# Transcript: {entry.get('title') or os.path.basename(path)}\n\n"
                     f"{entry.get('family_label') or 'Media'} `{path}`, {how}. "
                     "Timecodes are minutes:seconds.\n\n" + lines)
    kept.pop('transcript_error', None)
    kept['transcript'] = {**_kept_record(folder, target, TRANSCRIPT_HOW.format(model=model))}
    entry['kept'] = kept
    return entry


def keep_entry(entry: Dict[str, Any], folder: str) -> Dict[str, Any]:
    """Make the kept form of one manifest entry. Returns the entry, updated."""
    # studio download writes every file into the folder itself, and the manifest
    # holds absolute paths of the host that downloaded. Read by name, so a folder
    # that moved, or was cloned on another host, still resolves.
    source = os.path.join(folder, os.path.basename(entry.get('path') or ''))
    ext = os.path.splitext(source)[1].lower()

    if entry.get('kept') and os.path.exists(os.path.join(folder, entry['kept']['path'])):
        return entry  # already kept by an earlier run

    if entry.get('html_path') or ext in ('.md', '.html'):
        entry['kept'] = _kept_record(folder, source, 'as downloaded')
        return entry

    stem = os.path.splitext(os.path.basename(source))[0]
    targets = {
        **{e: (os.path.join(folder, f'{stem}.webp'), WEBP_HOW) for e in IMAGE_EXTENSIONS},
        **{e: (os.path.join(folder, 'keep', f'{stem}.mp4'), VIDEO_HOW) for e in VIDEO_EXTENSIONS},
        **{e: (os.path.join(folder, 'keep', f'{stem}.m4a'), AUDIO_HOW) for e in AUDIO_EXTENSIONS},
        **{e: (os.path.join(folder, 'keep', f'{stem}.pdf'), PDF_HOW) for e in PDF_EXTENSIONS},
    }
    if ext in targets and os.path.exists(targets[ext][0]):
        # Kept already, by hand or by an earlier version: record it, never redo it.
        target, how = targets[ext]
        entry['kept'] = _kept_record(folder, target, how + '; made before this run')
        return entry

    if not os.path.exists(source):
        entry['kept_error'] = 'download not on disk'
        return entry

    if ext in IMAGE_EXTENSIONS:
        target = os.path.join(folder, f'{stem}.webp')
        error = _run_ffmpeg(['-i', source, '-c:v', 'libwebp', '-quality', '90',
                             '-map_metadata', '-1', target])
        if error:
            entry['kept_error'] = error
            return entry
        entry['kept'] = _kept_record(folder, target, WEBP_HOW)
        os.remove(source)
        return entry

    if ext in PDF_EXTENSIONS:
        keep_dir = os.path.join(folder, 'keep')
        os.makedirs(keep_dir, exist_ok=True)
        target = os.path.join(keep_dir, f'{stem}.pdf')
        error = _run_ghostscript(source, target)
        if error:
            entry['kept_error'] = error
            return entry
        entry['kept'] = _kept_record(folder, target, PDF_HOW)
        os.remove(source)
        return entry

    if ext in VIDEO_EXTENSIONS or ext in AUDIO_EXTENSIONS:
        keep_dir = os.path.join(folder, 'keep')
        os.makedirs(keep_dir, exist_ok=True)
        if ext in VIDEO_EXTENSIONS:
            target = os.path.join(keep_dir, f'{stem}.mp4')
            args = ['-i', source, '-c:v', 'libx264', '-preset', 'slow', '-crf', '30',
                    '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '64k',
                    '-movflags', '+faststart', '-map_metadata', '-1', target]
            how = VIDEO_HOW
        else:
            target = os.path.join(keep_dir, f'{stem}.m4a')
            args = ['-i', source, '-vn', '-c:a', 'aac', '-b:a', '64k',
                    '-movflags', '+faststart', '-map_metadata', '-1', target]
            how = AUDIO_HOW
        error = _run_ffmpeg(args)
        if error:
            entry['kept_error'] = error
            return entry
        entry['kept'] = _kept_record(folder, target, how)
        return entry

    entry['kept'] = _kept_record(folder, source, 'as downloaded')
    return entry


def keep_folder(folder: str, transcripts: bool = True, model: str = 'base') -> Dict[str, Any]:
    """Apply keep_entry to every download in <folder>/manifest.json and rewrite it.
    With transcripts, each kept video or audio also gets its transcript."""
    manifest_path = os.path.join(folder, 'manifest.json')
    with open(manifest_path, encoding='utf-8') as fh:
        manifest = json.load(fh)
    for entry in manifest.get('downloads', []):
        keep_entry(entry, folder)
        if transcripts and entry.get('kept'):
            keep_transcript(entry, folder, model)
    with open(manifest_path, 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    return manifest
