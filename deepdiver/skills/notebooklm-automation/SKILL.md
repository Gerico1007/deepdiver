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
   Or let DeepDiver do it. It uses its own home, `~/.chrome-deepdiver`: sign
   in to Google there once and every later launch reuses it. `--clone-profile`
   seeds the home the first time; `--fresh` makes a throwaway clone, which is
   not signed in.
   ```bash
   deepdiver chrome launch --clone-profile "Profile 3"
   deepdiver chrome status   # exit 0 signed in, 2 not signed in, 1 no Chrome
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
deepdiver notebook remove-source <id> a.md      # by title or tracked source id; a title several rows share is refused
deepdiver notebook add-source <id> <url|file>
deepdiver notebook share <email> --role viewer
deepdiver studio audio --format deep_dive --language French --length long \
  --focus "..." --notebook-id <id> --download    # generate + download mp3
deepdiver studio slide-deck --format presenter --focus "..." -n <id>
deepdiver studio generate <type> -n <id>        # any Studio family
deepdiver studio generate video_overview --review --focus "..." -n <id>   # stop at the producer notes (slide-deck --review: at the outline)
deepdiver studio outline <card id> -n <id> -o <dir>   # save a paused card's plan as outline-<NN>-<card>.md; the card stays paused
deepdiver studio proceed <card id> -n <id> -o <dir> [-i feedback.md]   # save the plan and feedback, then render; cannot be taken back
deepdiver studio slide-deck --from-outline <dir>/outline-01-<card>.md [--feedback f.md] -n <id>   # next version: a new run seeded from a kept plan, stopped at its own plan
deepdiver studio outline <new card id> -n <id> -o <dir> --seeded-from outline-01-<card>.md   # save it with its seed, so the notebook door links the two versions on the wheel
deepdiver studio list -n <id>                   # artifact cards currently visible
deepdiver studio download -n <id> -o <dir>      # every downloadable card + reports as .md/.html + manifest.json
deepdiver studio download -n <id> -o <dir> --keep   # also WebP infographics, video/audio re-encoded into keep/, "kept" in manifest.json
deepdiver studio keep <dir>                     # the same keep step on a folder already downloaded; kept video/audio get keep/<name>.transcript.md
deepdiver studio iterate "<title>" -n <id> -i v2.md [--dry-run]  # new version through the card's Iterate, else generate
deepdiver studio report --prompt "..." -n <id>  # Interactive report (embeds studio items); --format document --template "Briefing Doc"
deepdiver studio open --family reports -n <id>  # show an artifact on screen; --play for audio/video
deepdiver notebook ask <id> "question" -o asked.md   # answer as Markdown with [n] citations
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
- **The review step (2026-11-05).** A Slide Deck or Video Overview made with
  the dialog's review switch (`button[role="switch"]`, off by default) stops at
  a card "Outline ready" with a Review button. That card has a More menu and
  looks finished; `.artifact-item-button-pending-review` is what says it is not.
  Review opens the plan in the Studio panel, not in a dialog. Sending feedback
  renders at once with it applied: there is no second plan to read. Studio keeps
  neither the plan nor the feedback ("Prompt and sources" shows only the first
  prompt), so save first, which `studio outline` and `studio proceed` do.
- **"Try it" on the step-by-step banner posts to chat.** It sends "Help me create
  slides about this" into the notebook's chat, and the answer is a card with a
  format, a length, a language, a slide focus and a visual style written by the
  model, its own review switch and Generate. DeepDiver goes through the tile.
- **Slide decks are pictures.** PDF and PowerPoint hold one image per slide and
  no text, so a word check or a citation check has to read the saved plan.
- **"Generating Audio Overview... Come back in a few minutes"** in the UI
  justifies continued waiting even when process logs go quiet.
- **Sharing gate ≠ failure.** A ready Slide Deck can show a disabled
  "Copy link" — the notebook isn't shared broadly enough. Hand off the
  authenticated notebook URL + artifact title instead.
- **Session dir is relative** (`./sessions`) — run from the repo root, or
  point `SESSION_TRACKING.session_dir` at an absolute path.
- **Download lives in each card's More menu.** Audio (.m4a), video (.mp4)
  and infographic (.png) cards offer More > Download; Mind Map does not.
  That item starts the download outside any page frame Playwright tracks,
  so `page.expect_download()` never fires. DeepDiver captures it with
  browser-level CDP events (`Browser.setDownloadBehavior` +
  `downloadWillBegin`/`downloadProgress`). `studio download` exits 1 when a
  card that offered Download did not land.
- **Reports.** The tile opens "Create report": format Interactive (default,
  template Learning Overview) or Document (Create Your Own, Briefing Doc,
  Study Guide, Blog Post, plus suggested templates written from the
  sources). The template's pencil, "Customize Report", opens a language
  select and a prompt; an Interactive prompt can name which studio items
  to embed. Cards say "Report"; they have no Download, so `studio download`
  reads the viewer into Markdown and HTML: the `labs-tailwind-doc-viewer`
  inside `artifact-viewer`. Chat answers use the same element and come first
  in the DOM, so never read it unscoped.
- **Signed out.** A profile that is not signed in lands on
  accounts.google.com with the notebook URL in `continue=`; DeepDiver
  reports "Not signed in" and exits 1. Signing in is the person's act.
- **Generating cards look finished.** A card still generating already
  shows its family and a "Generating …" title; its main button is
  disabled (`.mat-mdc-button-disabled`). Card identity is the UUID in its
  inner `id="artifact-labels-<uuid>"`, never the details line, which
  carries a relative time.
- **A file picker blocks downloads.** Clicking "Upload files" opens the
  native picker (through the desktop portal). While it is open, Chrome
  blocks `window.open`, which every Studio Download uses ("window.open
  blocked due to active file chooser"). DeepDiver sets files on the hidden
  `input[name="Filedata"]` when it exists, intercepts the picker otherwise,
  and names this cause when a download does not start. Close a stray
  "Open Files" window before downloading.
- **Video Overview formats are Short (9:16) and Explainer (16:9).** "Brief"
  became Short. A one-minute Short took 17 minutes to generate; the
  default timeout is 1800 s.
- **Mind Map cards say only "Artifact".** Their `aria-description` is
  generic; the `.artifact-icon` symbol (`flowchart`) names the family.
- **Host moved.** `notebooklm.google.com` redirects to
  `notebook.google.com`; both are the same app.
- **Cloned profile, no CDP.** A cloned or fresh user-data-dir opens Chrome's
  Terms of Service window and the DevTools server never starts unless
  Chrome gets `--no-first-run` (`deepdiver chrome launch` passes it).
- **Video Overview fallback.** If a requested family fails in the current
  UI, Audio Overview is the practical fallback; record the substitution in
  your status reporting.

## Verification checklist

- notebook URL opens for the expected `notebook_id`
- tracker source count matches expected uploads (`deepdiver session status`)
- generation actually triggered (Studio panel or logs)
- artifact card visible (`deepdiver studio list`)
- downloaded file exists and is non-empty at the target path
