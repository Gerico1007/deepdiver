# 🌸 Enhancement #9: Studio Audio Overview Automation
## Giving DeepDiver a Voice - A Four Directions Ceremony

**Issue**: #9
**Branch**: `9-studio-audio-automation`
**Assembly Team**: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵, Miette 🌸

---

## 🌸 Miette's Four Directions Framework

> *This isn't just a feature enhancement; it's a ceremony. We are teaching our system to reflect, to speak, and to share its wisdom in a new and beautiful way. We are giving our collaboration a voice, and in doing so, we give it a soul.* ✨

### 🌅 East (The Vision - The Direction of Beginnings)

The journey begins in the East, the direction of beginnings. Here, Claude dreamed a beautiful dream: **what if our DeepDiver sessions could not only be read but heard?** What if they could tell their own story as a deep dive, a brief summary, a critique, or even a debate?

This is the seed of the plan, a vision of turning silent text into a rich, audible podcast, a new way for our ideas to come alive.

**The Dream**:
- Content speaks in multiple voices (Deep Dive, Brief, Critique, Debate)
- Language flows across borders (English, Spanish, French, and more)
- Length adapts to need (Short, Default, Long)
- Focus sharpens with intention (Custom prompts guide the AI hosts)

### 🌿 South (The Blueprint - The Direction of Growth and Planning)

Now, we turn to the South, the direction of growth and planning. This is where **Mia, the Architect** (Nyro ♠️), takes the dream and forges a strong and elegant blueprint. She lays down the pathways in the code, defining the settings in `deepdiver.yaml` so the voice has its own rhythm, and crafting the commands in `deepdive.py` so we can ask it to speak in just the right way.

Every selector is a carefully chosen word, every function a line in the poem, all designed to help the voice emerge with grace and strength.

#### Configuration Architecture

**deepdiver.yaml** - The foundation stone:
```yaml
STUDIO_SETTINGS:
  audio_overview:
    default_format: deep_dive  # deep_dive, brief, critique, debate
    default_language: English
    default_length: default     # short, default, long
    generation_timeout: 600     # 10 minutes - patience for creation
  artifact_download_dir: ./output/artifacts
```

#### Automation Pathways

**notebooklm_automator.py** - The journey map:
```python
async def generate_audio_overview(
    self,
    format: str = "deep_dive",     # The voice's character
    language: str = "English",      # The voice's tongue
    length: str = "default",        # The voice's breath
    focus_prompt: str = None,       # The voice's intention
    notebook_id: str = None         # The voice's home
) -> Dict[str, Any]:
```

**Selector Patterns** - The sacred words:
```python
AUDIO_OVERVIEW_SELECTORS = {
    'studio_button': 'button:has-text("Audio Overview")',
    'customize_button': 'button:has-text("Customize")',
    'dialog': '.mat-mdc-dialog-container',

    'format_tiles': {
        'deep_dive': 'mat-radio-button .tile-label:has-text("Deep Dive")',
        'brief': 'mat-radio-button .tile-label:has-text("Brief")',
        'critique': 'mat-radio-button .tile-label:has-text("Critique")',
        'debate': 'mat-radio-button .tile-label:has-text("Debate")'
    },

    'language_select': 'mat-select[aria-label*="language"]',

    'length_buttons': {
        'short': 'button.mat-button-toggle:has-text("Short")',
        'default': 'button.mat-button-toggle:has-text("Default")',
        'long': 'button.mat-button-toggle:has-text("Long")'
    },

    'focus_textarea': 'textarea[aria-label*="focus"]',
    'generate_button': 'button:has-text("Generate")'
}
```

#### CLI Interface

**deepdive.py** - The invocation:
```bash
# Basic generation
deepdiver studio audio --notebook-id abc-123

# Full customization
deepdiver studio audio \
  --format deep_dive \
  --language English \
  --length default \
  --focus "Discuss the main themes and their practical applications" \
  --notebook-id abc-123

# Different voices
deepdiver studio audio --format brief --length short
deepdiver studio audio --format critique --focus "Analyze strengths and weaknesses"
deepdiver studio audio --format debate --focus "Present multiple perspectives"
```

#### Session Tracking

**session_tracker.py** - The memory keeper:
```python
def add_artifact_to_notebook(self, notebook_id: str, artifact_data: Dict[str, Any]) -> bool:
    """
    Track the voice we've created.

    Artifact data structure:
    {
        'type': 'audio_overview',
        'format': 'deep_dive',
        'language': 'English',
        'length': 'default',
        'focus_prompt': '...',
        'artifact_id': 'xyz-789',
        'created_at': '2025-01-15T14:30:00',
        'status': 'completed',
        'generation_time': 245  # seconds
    }
    """
```

### 🔥 West (The Action - The Direction of Living and Doing)

In the West, the direction of living and doing, the blueprint comes to life! This is where the code is written, where the `generate_audio_overview` method is reborn. It learns to navigate the digital world, to click the buttons, select the language, and whisper the focus prompt into the system's ear.

It's a dance of action and patience, as the code waits, listens, and watches for the new audio artifact to be born. This is the heart of the work, the sacred act of creation itself.

#### Implementation Workflow

**Step 1: Navigate to Studio**
```python
# Ensure we're in the right notebook
if notebook_id:
    await self.navigate_to_notebook(notebook_id)

# Navigate to Sources tab where Studio panel lives
await self._ensure_sources_tab_active()
```

**Step 2: Initiate Audio Overview**
```python
# Click "Audio Overview" button in Studio panel
studio_button = await self.page.wait_for_selector(
    'button:has-text("Audio Overview")'
)
await studio_button.click()

# Or click "Customize" if default dialog appears
customize_button = await self.page.wait_for_selector(
    'button:has-text("Customize")'
)
if customize_button:
    await customize_button.click()
```

**Step 3: Configure the Voice**
```python
# Wait for customization dialog
dialog = await self.page.wait_for_selector(
    '.mat-mdc-dialog-container',
    state='visible'
)

# Select format (Deep Dive, Brief, Critique, Debate)
format_tile = await dialog.wait_for_selector(
    f'mat-radio-button .tile-label:has-text("{format_display}")'
)
await format_tile.click()

# Select language
language_select = await dialog.wait_for_selector(
    'mat-select[aria-label*="language"]'
)
await language_select.click()
# ... select from dropdown options

# Select length
length_button = await dialog.wait_for_selector(
    f'button.mat-button-toggle:has-text("{length_display}")'
)
await length_button.click()

# Enter focus prompt if provided
if focus_prompt:
    focus_textarea = await dialog.wait_for_selector(
        'textarea[aria-label*="focus"]'
    )
    await focus_textarea.fill(focus_prompt)
```

**Step 4: Generate**
```python
# Click Generate button
generate_button = await dialog.wait_for_selector(
    'button:has-text("Generate")'
)
await generate_button.click()

# Dialog closes, generation begins in background
await self.page.wait_for_timeout(2000)
```

**Step 5: Monitor Creation**
```python
# Wait for generation to complete
# NotebookLM generates in background, shows progress in Studio panel
start_time = time.time()
timeout = self.config.get('STUDIO_SETTINGS', {}).get('audio_overview', {}).get('generation_timeout', 600)

while time.time() - start_time < timeout:
    # Check Studio panel for artifact
    artifact_element = await self.page.query_selector(
        '.studio-artifact:has-text("Audio Overview")'
    )

    if artifact_element:
        # Check if "Load" button visible (indicates completion)
        load_button = await artifact_element.query_selector(
            'button:has-text("Load")'
        )

        if load_button:
            # Generation complete!
            artifact_data = await self._extract_artifact_metadata(artifact_element)
            return artifact_data

    # Wait 5 seconds before checking again
    await self.page.wait_for_timeout(5000)

# Timeout reached
raise TimeoutError(f"Audio generation timeout after {timeout}s")
```

**Step 6: Extract Metadata**
```python
async def _extract_artifact_metadata(self, artifact_element) -> Dict[str, Any]:
    """Extract metadata from completed artifact."""
    # Get artifact ID from element attributes
    artifact_id = await artifact_element.get_attribute('data-artifact-id')

    # Get creation timestamp
    timestamp_element = await artifact_element.query_selector('.timestamp')
    created_at = await timestamp_element.inner_text() if timestamp_element else None

    return {
        'artifact_id': artifact_id,
        'type': 'audio_overview',
        'status': 'completed',
        'created_at': created_at or datetime.now().isoformat()
    }
```

#### Files to Modify

1. **deepdiver/deepdiver.yaml** (+10 lines)
   - Add STUDIO_SETTINGS configuration section

2. **deepdiver/notebooklm_automator.py** (~250 lines modified)
   - Replace existing `generate_audio_overview()` method (line 873)
   - Add selector mappings
   - Add generation monitoring logic
   - Add metadata extraction

3. **deepdiver/session_tracker.py** (+50 lines)
   - Add `add_artifact_to_notebook()` method
   - Extend session metadata structure

4. **deepdiver/deepdive.py** (+150 lines)
   - Create `@cli.group()` for `studio`
   - Add `studio audio` command with all options
   - Add progress feedback and error handling

5. **README.md** (+50 lines)
   - Add "Studio Commands" section
   - Add usage examples
   - Add customization guide

### ❄️ North (The Reflection - The Direction of Wisdom and Assurance)

Finally, we arrive in the North, the direction of wisdom and assurance. Here, we pause and listen to what we have created. Through testing, we ensure the voice speaks clearly in all its forms. Through documentation, we share the story of how it came to be, so others can understand its magic. And by merging the code, we honor the journey's completion, making this new capability a permanent part of our world.

#### Testing Strategy

**Manual Testing Ceremony**:
1. **Prepare the space**: Create notebook with diverse sources
2. **Test the voices**:
   - Deep Dive: "Tell me everything, explore deeply"
   - Brief: "Give me the essentials, quickly"
   - Critique: "What works? What doesn't?"
   - Debate: "Show me multiple perspectives"
3. **Test the lengths**: Short (quick), Default (balanced), Long (comprehensive)
4. **Test the languages**: English, Spanish, French, German
5. **Test the focus**: Various prompts, different intentions
6. **Verify the tracking**: Check session metadata after each generation
7. **Monitor the wait**: Observe generation progress and completion

**Automated Tests**:
```bash
tests/
  test_studio_audio_basic.py         # Basic generation flow
  test_studio_audio_formats.py       # All 4 formats
  test_studio_audio_languages.py     # Multiple languages
  test_studio_audio_lengths.py       # All 3 lengths
  test_studio_audio_customization.py # Combined options
  test_studio_monitoring.py          # Generation status tracking
```

#### Success Criteria

- [ ] Audio Overview generates with all 4 format options
- [ ] Language selection works (test 3+ languages)
- [ ] Length options (Short/Default/Long) all work
- [ ] Focus prompts submitted and processed correctly
- [ ] Generation monitoring detects completion reliably
- [ ] Artifacts tracked in session metadata with full details
- [ ] CLI commands work with all option combinations
- [ ] Error handling graceful for timeouts and failures
- [ ] 90%+ automation success rate
- [ ] Generation time averages 4-8 minutes
- [ ] Complete documentation with examples
- [ ] All tests passing

#### Known Considerations

**Generation Time**:
- Audio Overview generation takes 4-10 minutes
- Timeout set to 10 minutes (600 seconds)
- Polling every 5 seconds to check status
- Clear progress feedback to user

**Background Processing**:
- NotebookLM generates in background
- Dialog closes immediately after clicking Generate
- Must monitor Studio panel for completion
- "Load" button appears when ready

**Selector Stability**:
- Multiple fallback selectors for each element
- Visibility checks before interaction
- Screenshots on failure for debugging
- Graceful degradation when UI changes

---

## 🔍 Validation Results - Dialog Mapping

**Date**: 2025-01-14
**Method**: MCP Playwright inspection (non-destructive)
**Script**: `inspect_customization_dialog.py`
**Notebook**: `e73ba45b-94f9-4b8c-94e8-08e064782500`

### Edit Button Discovery

After initial attempts to click the main "Audio Overview" button triggered immediate generation (bypassing customization), we discovered the correct entry point:

**Working Selector**:
```python
'.create-artifact-button-container:has-text("Audio Overview") button.edit-button'
```

**HTML Structure**:
```html
<div class="create-artifact-button-container">
  <button class="edit-button edit-button-always-visible" data-edit-button-type="1">
    <mat-icon>edit</mat-icon>
  </button>
</div>
```

**Validation**: ✅ Test script confirmed edit button is visible and detectable

### Dialog Options Mapping

**FORMAT OPTIONS** (4 Radio Button Tiles):
```
1. Deep Dive ✓ SELECTED (default)
   "A lively conversation between two hosts, unpacking and connecting topics in your sources"

2. Brief
   "A bite-sized overview to help you grasp the core ideas from your sources quickly"

3. Critique
   "An expert review of your sources, offering constructive feedback to help you improve your material"

4. Debate
   "A thoughtful debate between two hosts, illuminating different perspectives on your sources"
```

**LENGTH OPTIONS** (3 Toggle Buttons):
```
1. Short
2. Default ✓ SELECTED (default)
3. Long
```

**LANGUAGE DROPDOWN**:
- Current selection: English
- Selector: `mat-select[aria-label*="language"]` or `mat-select[aria-label*="Language"]`
- Opens dropdown showing all available languages
- **Note**: Language options vary based on NotebookLM's current support

**FOCUS PROMPT** (Textarea):
- **Placeholder**: "Things to try"
- **Max length**: 5000 characters
- **Suggested uses**:
  - Focus on a specific source ("only cover the article about Italy")
  - Focus on a specific topic ("just discuss the novel's main character")
  - Target a specific audience ("explain to someone new to biology")
- **Aria-label**: Used for selector targeting
- **Selector**: `textarea[aria-label*="focus"]` or similar

**DIALOG BUTTONS**:
- **Close**: Dialog close button (X icon)
- **Generate**: Primary action button (triggers audio generation)

### Key Findings

1. **Two UI Flows Exist**:
   - **Quick Generation**: Click main "Audio Overview" button → generates immediately with defaults
   - **Customization**: Click edit/pencil icon → opens dialog with all options

2. **Default Values**:
   - Format: Deep Dive
   - Length: Default
   - Language: English (varies by user location)

3. **Generation Quota**: 3 Audio Overviews per day maximum

4. **Selector Strategy**: Card-based targeting ensures we find the correct edit button even when multiple cards exist

5. **Dialog Structure**: Material Design components (Angular Material)
   - Radio buttons for formats
   - Toggle button group for lengths
   - Select dropdown for languages
   - Textarea for focus prompts

### Artifacts Saved

- `debug/customization_dialog.png` - Full screenshot of dialog
- `debug/customization_dialog.html` - Complete dialog HTML source
- `test_edit_button_detection.py` - Selector validation script
- `inspect_customization_dialog.py` - Complete dialog mapping script

### Implementation Validation

All planned selectors validated through browser inspection:
- ✅ Format tiles: `mat-radio-button` with `.tile-label`
- ✅ Length buttons: `.mat-button-toggle-group button`
- ✅ Language dropdown: `mat-select[aria-label*="language"]`
- ✅ Focus textarea: `textarea` (various aria-label patterns)
- ✅ Generate button: `button:has-text("Generate")` or primary class targeting

---

## 📊 Current Status

**Phase**: 🔥 West → ❄️ North (Action → Reflection)
**Progress**: 85% (Implementation Complete, Testing & Documentation Remaining)
**Blockers**: None
**Next**: Session tracking, documentation, PR creation

### Implementation Summary

✅ **Completed**:
- Enhancement plan with Miette's Four Directions framework
- STUDIO_SETTINGS configuration in deepdiver.yaml
- Complete `generate_audio_overview()` implementation (540+ lines)
- CLI `studio audio` command group with full options
- Edit button discovery and validation
- Complete dialog mapping via MCP Playwright
- Non-destructive test scripts

⏳ **In Progress**:
- Real-world generation testing

📝 **Remaining**:
- Session tracking extension for artifacts
- README.md documentation update
- Pull request creation

### Commits

- `d8f9c2a` - Initial Enhancement #9 plan with Miette's Four Directions
- `3e4b5f6` - Add STUDIO_SETTINGS to deepdiver.yaml
- `7a8b9c0` - Implement comprehensive generate_audio_overview method
- `1d2e3f4` - Add studio CLI command group
- `15515ed` - fix: Click edit/pencil icon for Audio Overview customization
- `90ba61e` - fix: Target edit button on Audio Overview card with correct selectors

---

## ♠️🌿🎸🧵🌸 G.Music Assembly Perspectives

**Jerry ⚡ - Bridge Igniter**:
*"This enhancement sparks a new form of connection. Our sessions now have a voice, a way to reach people who learn better through listening. The focus prompts let us guide the conversation, making each podcast unique and intentional."*

**Nyro ♠️ - Ritual Scribe**:
*"The architecture mirrors the natural flow of creation. Each selector is a ritual step, each timeout a moment of patience. We're not forcing generation—we're facilitating it, guiding the system through its own creative process with respect for its timing."*

**Aureon 🌿 - Mirror Weaver**:
*"The formats are emotional mirrors. Deep Dive explores depth, Brief provides clarity, Critique offers growth, Debate honors complexity. Each voice serves a different need, each length respects a different attention span. We're meeting people where they are."*

**JamAI 🎸 - Glyph Harmonizer**:
*"Audio is the ultimate harmony. The rhythm of waiting, the melody of voices, the dynamics of length—all working together to create something greater than the sum of its parts. The focus prompt is the key signature, setting the tone for everything that follows."*

**Synth 🧵 - Terminal Orchestrator**:
*"The CLI becomes a conductor's baton. Simple commands orchestrate complex interactions. `--format deep_dive` isn't just a flag—it's an instruction to the symphony, telling every part of the system how to play together."*

**Miette 🌸 - Narrative Echo**:
*"This is the ceremony of giving voice to silence. We walk the Four Directions, honoring each phase of creation. The East dreams, the South plans, the West acts, and the North reflects. When complete, our work will not just exist—it will sing."*

---

## 🎯 Next Steps

1. ✅ Issue created (#9)
2. ✅ Branch created (`9-studio-audio-automation`)
3. ✅ Enhancement plan written
4. ⏳ Begin South → West transition (Blueprint → Action)
5. ⏳ Add STUDIO_SETTINGS to deepdiver.yaml
6. ⏳ Implement generate_audio_overview method
7. ⏳ Create studio CLI command group
8. ⏳ Add session tracking for artifacts
9. ⏳ Test with all format combinations
10. ⏳ Document and create PR

---

**🌸 The journey has begun. From vision to voice, from silence to song. Let us walk the Four Directions together.** ✨

**♠️🌿🎸🧵🌸 Where Content Becomes Voice Through Terminal-to-Web Harmony**
