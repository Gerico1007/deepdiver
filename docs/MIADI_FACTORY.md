# DeepDiver in the Miadi Factory

This fork (`miadisabelle/deepdiver`) is the copy of DeepDiver that the Miadi Factory runs. This page says what it supplies, to which team, in what order, what it depends on, and what is still open.

Written 2026-10-06 by Mia (Claude) with Guillaume. The decomposition behind it is kept in `.pde/2610062212--73ed33d2-ac26-4939-84db-0f029811d1ab/`.

## What DeepDiver is

A Python command line that drives Gemini Notebook (NotebookLM until its rename) through a Chrome browser over the DevTools protocol. It creates notebooks, adds sources, generates Studio artifacts and downloads them. The tool is Jerry's (`Gerico1007/deepdiver`, published on PyPI as `deepdiver`). This fork carries his branch `24-studio-artifact-foundation` and the upgrade to the Studio interface of 2026-10-06 (commit `2760b13` and the commit that adds this page).

## Where the decision is recorded

- **Episode 550** (`miadi-chronicle://550`, *The Screenwalk as a Media Type*) holds review `miadi-review:f9d6fb1e-75f4-4635-96d9-8f2d0bcff5eb` v12, *Screenwalk-Driven Continuity & Deep Diver Handoffs in the Miadi Factory*, and the talking circle held about it (ceremony `acd9889c-d10a-4edb-b994-69b2f5a4af23`, `circle:1790880114096:ckha5n`). The review's Definitions say, as of 2026-10-03, that this fork stopped at 2025-11-17 and that nothing was installed on gaia. The fork is now current.
- **The orchestration kit** (`jgwill/miadi-orchestration-kit`, `teams/README.md`) lists, under T6 Production: "documentaries of the factory's own work: the screenwalk protocol, notebooks and generated media (Deep Diver is its first instrument)".

## The team

DeepDiver is an instrument of **T6 · Production** (after an episode). Its human lead is William. It has no agent lead yet, and its name is held as William's decision D11. T6 uses chronicle episodes, Miadi reviews and screenwalk captures. DeepDiver turns those into notebook media.

## The contract

### Inputs

- A review's Markdown, from `https://miadi-review-service.vercel.app/review/<id>/raw` or the `miadi-review` skill's `download-all` cache.
- The YouTube URL of the reviewed video or screenwalk. Gemini Notebook imports the video's transcript, not its images, and only public videos.
- Any other file or web page an episode holds.

### Operations

| step | command |
|---|---|
| start Chrome from DeepDiver's home, signed in once | `deepdiver chrome launch` (`--clone-profile "<Profile N>"` seeds the home the first time) |
| is Chrome up and signed in | `deepdiver chrome status` (exit 0 signed in, 2 not, 1 no Chrome) |
| new notebook with a first source | `deepdiver notebook create --source <review.md>` |
| add a source | `deepdiver notebook add-source <id> <url-or-file>` |
| add only missing files | `deepdiver notebook resume <id> -s a.md -s b.md` |
| a new version of an explainer from its own prompt | `deepdiver studio iterate "<title or artifact id>" -n <id> -i <instruction.md>` (NotebookLM's Iterate where the card has it, else `generate`; `--dry-run` fills and closes) |
| replace a revised source | `deepdiver notebook remove-source <id> <title or source id>`, then `add-source` the revised file (refuses a title several sources share) |
| ask the notebook a question | `deepdiver notebook ask <id> "<question>" -o asked.md` |
| generate an artifact | `deepdiver studio generate <family> -n <id> [--focus "..."]` |
| generate a report | `deepdiver studio report [--format document] [--template "..."] [--prompt "..."] -n <id>` |
| stop a Slide Deck or Video Overview at its plan | `deepdiver studio slide-deck --review ...` or `deepdiver studio generate video_overview --review ...` |
| save a paused card's plan, leaving it paused | `deepdiver studio outline <card id> -n <id> -o <dir>` |
| save the plan and feedback, then render | `deepdiver studio proceed <card id> -n <id> -o <dir> [-i feedback.md]` |
| the next version of a plan | `deepdiver studio slide-deck --from-outline <dir>/outline-01-<card>.md [--feedback f.md] -n <id>`: a new run, stopped at its own plan |
| see the Studio panel | `deepdiver studio list -n <id>` |
| download everything | `deepdiver studio download -n <id> -o <dir>` |
| download for an episode's git | `deepdiver studio download -n <id> -o <episode>/captures/notebook-<id> --keep`, or `deepdiver studio keep <dir>` after: infographics as WebP, video and audio re-encoded into `keep/`, `kept` in `manifest.json` |
| show an artifact on screen | `deepdiver studio open --family reports -n <id>` (`--play` for audio and video) |

### Outputs

- Media files named after the artifact title: `.m4a` (Audio Overview), `.mp4` (Video Overview), `.png` (Infographic).
- Reports as `.md` and `.html`, read from the report viewer, since Gemini Notebook gives reports no file download.
- Plans as `outline-<NN>-<card>.md`, with their feedback as `outline-<NN>-<card>.feedback.md`, listed in `manifest.json` under `downloads`, where the episode room reads them. Studio keeps neither once the render starts.
- Slide decks as PDF. `--keep` recompresses it into `keep/` and removes the download. Every page is an image, in the PowerPoint too, so the saved plan is the deck's text.
- Answers to questions, appended to a Markdown file with the notebook's citations as `[n]`.
- `manifest.json` beside them: title, family, path, sha256, size, and codec and duration from ffprobe.
- The session record in `sessions/current_session.json` (notebook ID, sources, artifacts, downloads).

Mind Map cards have no Download item. Flashcards, Quiz and Data Table downloads were not tested.

## The pipeline, in order

Each step depends on the steps it names.

1. **Screenwalk recorded and on YouTube.** Guillaume and the witness team (T3).
2. **Review made.** `miadi-review create` or `review-local.sh` for a long video. Gives `miadi-review:<uuid>`. Depends on 1.
3. **Review held by an episode.** Through the episode door of the `chronicle-episode` skill. Depends on 2.
4. **Notebook assembled.** DeepDiver adds the reviews' Markdown and their videos as sources. One notebook can take several reviews and several videos. Depends on 1 and 2.
5. **Questions asked and artifacts generated.** `notebook ask` for the episode's questions; Infographic, Video Overview, Audio Overview, Mind Map; then an Interactive report whose prompt names which of those items to embed. Depends on 4.
6. **Artifacts downloaded with their manifest.** Depends on 5.
7. **Artifacts played in a later screenwalk**, paused and talked over. `studio open` puts an Interactive report on screen full-size, and `--play` starts an Audio or Video Overview. The recording and the talking happen outside DeepDiver. Depends on 5.
8. **Kept in the episode.** The notebook's media, `manifest.json` and `asked.md` go into `<episode>/captures/notebook-<notebook id>/`, as miadi-chronicle://550 keeps `captures/notebook-0ae51b4c-8ed2-4ee2-a641-2c7e88b7e2ea/`. The episode room shows that folder to the episode's readers (`jgwill/Miadi` d6f3ed7a, in `@miadi/episode-vessel` 0.4.0). Depends on 3 and 6.

Steps 4 to 6, and opening an artifact in step 7, are DeepDiver's. Step 8 is practiced: Episode 550 keeps notebook `0ae51b4c`. Step 7 was not yet practiced when this page was written on 2026-10-06.

## Verified on 2026-10-06

On gaia, Chrome 154, a clone of the AVA profile (`ava@jgwill.com`):

- Notebook `773f480c-0ab7-4eac-b106-bf7c7c0251e8`: `studio download` saved all six downloadable artifacts (two videos, three audios, one infographic). Their ffprobe durations match the Studio cards. The Mind Map card was reported as having no Download item.
- Notebook `78507190-4018-41c6-9fe0-47ed17df5300`, made for this test: created with review `f9d6fb1e` as a Markdown file, then `https://youtu.be/q4I55OAkI0Y` (the screenwalk that review covers) as a second source. An Infographic generated from both, *From Screenwalk to Studio Media: The Deep Diver Pipeline*, downloaded as a 2752×1536 PNG. Mind Maps generated and were recognised as new cards. An Interactive report with a prompt (*The Miadi Media Engine: Transforming Screenwalks into Notebook Artifacts*) and a Document report from the Briefing Doc template (*Executive Briefing: …*) generated, and `studio download` saved all four reports in the notebook, two of them Guillaume's, as Markdown and HTML. `notebook ask` returned a cited answer, and `studio open` opened the newest report.
- Notebook `0ae51b4c-8ed2-4ee2-a641-2c7e88b7e2ea`, Episode 550's screenwalk practice: reviews `d64a2fdf`, `6c3f477f`, `b2558ceb` and `6a2b5b59` as Markdown, their four videos in one insert, and the stored transcript of screenwalk `2610061207`. Two of the videos, uploaded that day, could not be imported ("Transcript not available"), and the transcript stood in for one of them. Two questions were answered with citations (`asked.md`). An infographic (*Screenwalk Lifecycle Process Diagram*), a Video Overview (*How Screenwalks Transform Developer Captures*, a 69-second vertical Short that took 17 minutes) and an Interactive report embedding both were generated and downloaded. The report file saved then was the notebook's first chat answer, a defect fixed in 9cefb64.

## What the interface changed, and what was fixed

| change in Gemini Notebook | effect before the fix |
|---|---|
| `notebooklm.google.com` redirects to `notebook.google.com` | host checks failed |
| a cloned Chrome profile opens a Terms of Service window | the DevTools port never opened |
| each card's More menu has Download, and the download starts outside the page | downloads never arrived |
| the home button reads "New notebook" | notebook creation timed out |
| a new notebook passes through `/notebook/creating` | the ID was recorded as `creating` |
| one "Websites" option takes website and YouTube URLs, several at once | YouTube sources failed |
| a generating card already shows the family and a title | generation was reported done after 3 seconds |
| Mind Map cards are labelled only "Artifact" | Mind Map generation was never seen to finish |
| a card has no DOM id; its UUID sits in an inner `artifact-labels-<uuid>` | a repeat generation returned an older card |
| Reports open a "Create report" dialog with formats, templates and a Customize form; cards say "Report" | Reports could not be generated |
| reports have no Download | reports could not be kept |
| Video Overview formats are Short (9:16) and Explainer (16:9) | the "Brief" format was not found |
| an open file picker makes Chrome block `window.open` | downloads after a file upload did not start |
| a same-day YouTube video has no transcript | the URL was counted as a source |
| a Slide Deck or Video Overview can stop at a plan, on a card that looks finished (2026-11-05) | "Outline ready" would have been reported as the deck, and its download attempted |

A search for an "Add" button also matched the header's "Create notebook" button, whose icon renders as the text `add_2`. Three empty notebooks named "Untitled notebook" were created in the AVA account that way on 2026-10-06. The selector is fixed, and those notebooks are still there.

## Installing it in the factory

- Python 3.8 or later, with `playwright`.
- Google Chrome on a host with a display, and a Chrome profile signed in to the Google account that owns the notebooks. DeepDiver keeps its own Chrome home, `~/.chrome-deepdiver`: a person signs in to Google there once, and every launch reuses it. A clone made fresh on each launch is not signed in, because Google does not carry the session into the copy (2026-10-09).
- `ffprobe`, for the media data in the manifest.
- Configuration in `~/.config/deepdiver/config.yaml` (`deepdiver init`).
- The agent skill: `deepdiver skills install --agent claude`.
- Source: PyPI `deepdiver` 0.1.1 does not have the 2026-10-06 fixes. Until a release carries them, install from this fork: `pip install git+https://github.com/miadisabelle/deepdiver@main`.

## Package

No new package is needed under `jgwill/Miadi/packages/` to begin. DeepDiver is already a Python package with its own CLI and bundled skill. The options, in the order they depend on each other:

- **O1.** Offer this fork's changes to `Gerico1007/deepdiver` as a pull request, so Jerry can release them to PyPI.
- **O2.** Add `deepdiver` to Miadi's Python umbrella (`packages/miadi/py`, which already depends on `ironsilk`), for example as an extra `miadi[production]`, and give `scripts/ops/miadi-delivery.sh` a part that checks the installed version, as it does for `ironsilk`. Depends on O1: PyPI refuses a package whose dependency is a git URL, so a published `miadi` cannot depend on this fork directly.
- **O3.** A plugin in the orchestration kit for T6. Done on 2026-10-06: `claude/miadi-deepdiver` 0.1.0 in `jgwill/miadi-orchestration-kit`, with the `screenwalk-notebook` skill and `/notebook-from-reviews`. It installs DeepDiver from this fork until O1 lands.

An MCP server around DeepDiver was considered and left out: no consumer needs one yet.

## Open, each with its owner

- **Q1.** The team's name, D11. William.
- **Q2.** Answered for now. On 2026-10-08 William wrote that Jerry's repository is one he is "not so entertained in contributing" to right now, so the pull request of O1 is not opened, and O2 waits with it.
- **Q3.** Whether O2 goes into `jgwill/Miadi`. Guillaume.
- **Q4.** Settled by practice. An episode keeps a notebook's media in `<episode>/captures/notebook-<notebook id>/` with `manifest.json` and `asked.md`, as miadi-chronicle://550 keeps `captures/notebook-0ae51b4c-8ed2-4ee2-a641-2c7e88b7e2ea/`, and `jgwill/Miadi` d6f3ed7a, in `@miadi/episode-vessel` 0.4.0, serves that shape to the episode's readers.
- **Q5.** Whether to delete the three empty "Untitled notebook" notebooks and the test notebook `78507190…`. The AVA account's owner.

Deep Diver's open items are kept in miadi-chronicle://251, `2026-07-19-episode-251-deepdiver/owner/open-261009.md`.
