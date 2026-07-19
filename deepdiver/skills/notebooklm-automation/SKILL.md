---
name: deepdiver-notebooklm-automation
description: Operate DeepDiver to drive NotebookLM/Gemini Notebook — ingest sources, resume existing notebooks, generate any Studio artifact (audio, slide deck, video, mind map, reports, flashcards, quiz, infographic, data table), download results, and recover from UI drift.
triggers:
  - NotebookLM or Gemini Notebook automation
  - Creating podcasts / Audio Overviews from documents via terminal
  - Resuming or repairing a stuck NotebookLM ingest or generation run
  - Generating Studio artifacts (slide decks, mind maps, reports, quizzes)
---

# DeepDiver NotebookLM automation

DeepDiver is a Python CLI that drives NotebookLM (now presenting as
"Gemini Notebook") through a live Chrome session over CDP. This skill is the
operating manual an agent needs to run it well.

## Setup

1. Chrome must run with remote debugging on port 9222 and a logged-in
   Google account:
   ```bash
   google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-deepdiver &
   ```
   Or let DeepDiver do it (supports cloning an authenticated profile so the
   live profile is never touched):
   ```bash
   deepdiver chrome launch --clone-profile "Profile 3"
   ```
2. Verify real CDP health (`deepdiver status` probes `/json/version` — trust
   its CDP line, not just "config loaded"):
   ```bash
   deepdiver status
   ```

## Core commands

```bash
deepdiver init                                  # config + Chrome setup
deepdiver test                                  # connect → navigate → auth check
deepdiver notebook create --source <url|file>   # new notebook (+ first source)
deepdiver notebook open <id>                    # navigate to existing notebook
deepdiver notebook resume <id> -s a.md -s b.md  # upload ONLY missing sources
deepdiver notebook add-source <id> <url|file>
deepdiver notebook share <email> --role viewer
deepdiver studio audio --format deep_dive --language French --length long \
  --focus "..." --notebook-id <id> --download    # generate + download mp3
deepdiver studio slide-deck --format presenter --focus "..." -n <id>
deepdiver studio generate <type> -n <id>        # any Studio family
deepdiver studio list -n <id>                   # artifact cards currently visible
deepdiver session status                        # session truth
deepdiver skills list                           # skills bundled in this package
```

Artifact types for `studio generate`: `audio_overview`, `slide_deck`,
`video_overview`, `mind_map`, `reports`, `flashcards`, `quiz`,
`infographic`, `data_table`.

## Core principles

1. **Prefer resume over recreate.** If a notebook exists in
   `sessions/current_session.json`, continue from it with
   `deepdiver notebook resume` — it diffs tracked sources against your local
   files and uploads only what's missing.
2. **The session tracker is the source of truth.** Packet `result.json`
   files can lag behind reality after resumed live work; reconcile from the
   tracker, not from stale packet output.
3. **UI drift is expected.** NotebookLM changes labels, tabs, and modal
   flows without notice. DeepDiver layers fallbacks (visible controls, then
   the hidden `input[name="Filedata"]` upload input) — a missing tab
   selector is not proof the flow failed.
4. **A timeout is not a failure verdict.** Generation monitoring ends with
   a final drift-aware sweep for a completed artifact card; if the card
   exists, DeepDiver recovers it (`recovered_after_timeout: true`) instead
   of failing. Prefer download-and-reconcile over regenerating.

## Known pitfalls

- **Rebrand modal blocks everything.** "NotebookLM is now Gemini Notebook"
  (`Let's go`) intercepts pointer events; buttons look clickable but clicks
  time out. DeepDiver dismisses it automatically on navigation; if driving
  the browser directly, dismiss it first.
- **Completion cues post-drift.** A finished artifact is an
  `artifact-library-item` card with `aria-description` naming the family,
  `button[aria-label="Play"]`, and a More button; title/details live in
  `.artifact-title` / `.artifact-details`. Legacy "Load" buttons are gone.
- **"Generating Audio Overview... Come back in a few minutes"** in the UI
  justifies continued waiting even when process logs go quiet.
- **Sharing gate ≠ failure.** A ready Slide Deck can show a disabled
  "Copy link" — the notebook isn't shared broadly enough. Hand off the
  authenticated notebook URL + artifact title instead.
- **Session dir is relative** (`./sessions`) — run from the repo root, or
  point `SESSION_TRACKING.session_dir` at an absolute path.
- **Video Overview fallback.** If a requested family fails in the current
  UI, Audio Overview is the practical fallback; record the substitution in
  your status reporting.

## Verification checklist

- notebook URL opens for the expected `notebook_id`
- tracker source count matches expected uploads (`deepdiver session status`)
- generation actually triggered (Studio panel or logs)
- artifact card visible (`deepdiver studio list`)
- downloaded file exists and is non-empty at the target path
