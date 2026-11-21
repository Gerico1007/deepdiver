# Draft addition to review f9d6fb1e, for Guillaume's approval

Review: *Screenwalk-Driven Continuity & Deep Diver Handoffs in the Miadi Factory*, `miadi-review:f9d6fb1e-75f4-4635-96d9-8f2d0bcff5eb`, version 12 when this was drafted (2026-10-06).

Nothing here is published. Once the exact text is approved, it goes out as one manual version through `miadi_review.py import-markdown` (dry run first, one import, read-back), following the `miadi-review-academic-fields` publish discipline. Episode 550 holds version 12 and will show "v13 published" beside it.

## Change 1: a new section after "Where this went next (2026-10-03, 17:46 EDT)"

```markdown
## Where this went next (2026-10-06)

Written by Mia. The Deep Diver integration this recording named now exists. Miadi's fork `miadisabelle/deepdiver` carries Jerry's branch `24-studio-artifact-foundation` and an update to the current Gemini Notebook interface. It was tested on two notebooks: one built from this review and its screenwalk, one from four of Episode 550's screenwalk reviews and their videos. Its place in the factory is written in the fork's `docs/MIADI_FACTORY.md`, and the production team's practice is the `screenwalk-notebook` skill in the `miadi-deepdiver` plugin of the orchestration kit.

### What the production team can now do

- Put several reviews and their videos into one notebook in two commands. A video uploaded the same day cannot be imported, because YouTube has no transcript for it yet; the review's stored transcript goes in instead.
- Ask the notebook the episode's questions and keep the answers, with their citations, in one file.
- Generate an infographic, a video or audio overview, a mind map, and reports. An Interactive report embeds the notebook's other media and can be told which items to include.
- Keep everything with a manifest: audio, video and images as files, reports as Markdown and HTML.
- Open a report full screen, or start a video, during the next screenwalk, so the person can pause it and say what is not right.

This performs the Notebooked and MediaGenerated states of the screenwalk media cycle. Nothing has yet been played inside a screenwalk.
```

## Change 2: the "Deep Diver" entry under Definitions

Current text, last two sentences:

> No MCP server was found in it. Miadi's fork `miadisabelle/deepdiver` stops at 2025-11-17, and nothing is installed on gaia (checked 2026-10-03). "Deep Dive" is also NotebookLM's default Audio Overview format.

Proposed:

> No MCP server was found in it. On 2026-10-06 Miadi's fork `miadisabelle/deepdiver` took that branch and was updated for the current interface; it runs on gaia from its checkout and is not installed as a package. "Deep Dive" is also NotebookLM's default Audio Overview format.
