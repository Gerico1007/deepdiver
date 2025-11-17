# **DeepDiver NotebookLM Studio Artifacts Implementation Guide**

> **Status**: Future Implementation Roadmap
> **Current Phase**: Phase 1 (Audio Overview) ✅ Completed in PR #10
> **Next Phase**: Phase 2 (Video Overview) - Ready for implementation

## **Complete Artifact Customization Reference**

Based on the successful Audio Overview implementation in PR #10, this guide provides comprehensive implementation details for all remaining NotebookLM Studio artifact types using Playwright Python automation.

This document serves as a **blueprint for future development phases**, providing:
- Detailed customization options for each artifact type
- Playwright implementation patterns
- CLI command structures
- Testing strategies
- Session integration approaches

## **Implementation Status**

| Phase | Artifact Type | Status | Priority | PR/Issue |
|-------|---------------|--------|----------|----------|
| Phase 1 | Audio Overview | ✅ Completed | - | PR #10 |
| Phase 2 | Video Overview | 📋 Planned | ⭐ Next | - |
| Phase 3 | Mind Map | 📋 Planned | Medium | - |
| Phase 4 | Study Guides & Reports | 📋 Planned | Medium | - |
| Phase 5 | Flashcards | 📋 Planned | Low | - |
| Phase 6 | Quizzes | 📋 Planned | Low | - |

## **Table of Contents**

- [Phase 2: Video Overview Implementation](#phase-2-video-overview-implementation-)
- [Phase 3: Mind Map Implementation](#phase-3-mind-map-implementation-)
- [Phase 4: Study Guides & Reports Implementation](#phase-4-study-guides--reports-implementation-)
- [Phase 5: Flashcards Implementation](#phase-5-flashcards-implementation-)
- [Phase 6: Quizzes Implementation](#phase-6-quizzes-implementation-)
- [Technical Implementation Patterns](#technical-implementation-patterns)
- [CLI Structure Overview](#cli-structure-overview)
- [Session Integration](#session-integration)
- [Testing Framework](#testing-framework)

---

## **Phase 2: Video Overview Implementation** ✅ **NEXT PRIORITY**

### **Customization Options**

#### **1. Format Selection**
- **Explainer** (default): Comprehensive, structured video for in-depth understanding[1][2][3][4]
- **Brief**: Bite-sized 1-2 minute video covering key points only[3][4]

**UI Pattern**: Radio button tiles (Material Design)

#### **2. Visual Styles** (Powered by Nano Banana)[5][6][4]
Available styles:
- **Auto-select** (let AI choose)[2][1]
- **Classic** (original default style)[6]
- **Whiteboard**[2][5][6]
- **Watercolor**[5][6]
- **Retro Print**[6][2][5]
- **Heritage**[5][6]
- **Paper-craft**[6][5]
- **Kawaii**[2]
- **Anime**[2][5][6]
- **Custom** (text description input)[2]

**UI Pattern**: Dropdown/selection tiles (for 18+ users only)[2]

#### **3. Language Selection**
- 80+ supported languages[7][8]
- **UI Pattern**: Dropdown in CDK overlay[7][2]

#### **4. Steering Prompt**
- Freeform text input (similar to Audio Overview)[9][10][2]
- 5000 character limit (inferred from audio pattern)
- Use cases: Focus on specific sources, target audience, emphasize topics[10][9][2]

### **Playwright Implementation Pattern**

```python
async def generate_video_overview(self, format_type="explainer", visual_style="auto-select",
                                   language="English", steering_prompt="", length=None):
    """
    Generate customized Video Overview

    Args:
        format_type: "explainer" or "brief"
        visual_style: "auto-select", "classic", "whiteboard", "watercolor",
                      "retro-print", "heritage", "paper-craft", "kawaii", "anime", or custom text
        language: Language name (e.g., "English", "French")
        steering_prompt: Custom instructions for focus/audience
        length: Not currently available for video (only audio has this)
    """

    # Click edit button on Video Overview tile
    await self.page.click('.create-artifact-button-container:has-text("Video Overview") button.edit-button')

    # Wait for Material Design dialog (CDK overlay)
    await self.page.wait_for_selector('.mat-mdc-dialog-component-host')

    # Select format (radio button)
    if format_type == "brief":
        await self.page.click('mat-radio-button:has-text("Brief")')
    else:
        await self.page.click('mat-radio-button:has-text("Explainer")')

    # Select visual style
    if visual_style != "auto-select":
        # Open visual style dropdown
        await self.page.click('mat-select[formcontrolname="visualStyle"]')
        await self.page.click(f'mat-option:has-text("{visual_style.title()}")')

    # Select language if not English
    if language != "English":
        await self.page.click('mat-select[formcontrolname="language"]')
        await self.page.click(f'mat-option:has-text("{language}")')

    # Fill steering prompt
    if steering_prompt:
        await self.page.fill('textarea[formcontrolname="steeringPrompt"]', steering_prompt)

    # Click Generate button
    await self.page.click('button:has-text("Generate")')

    # Monitor generation (background polling every 5 seconds)
    await self._monitor_artifact_generation("Video Overview", timeout=600)
```

### **Generation Monitoring**
- **Pattern**: Background polling every 5 seconds[8][9]
- **Completion indicator**: "Load" button appears[8]
- **Timeout**: 600 seconds (10 minutes)[9]
- Concurrent generation supported (can generate multiple artifacts simultaneously)[8][2]

### **CLI Command Structure**

```bash
# Basic video overview
deepdiver studio video

# Customized video
deepdiver studio video \
  --format brief \
  --style anime \
  --language French \
  --prompt "Focus on cost analysis sections only"

# From specific notebook
deepdiver studio video --notebook-id abc-123 --format explainer --style whiteboard
```

---

## **Phase 3: Mind Map Implementation** 🗺️

### **Customization Options**

#### **Generation Method**
Mind Maps are generated via chat chip interaction, not customization dialog[11][12][13]

**UI Pattern**:
1. Click "Mind Map" chip in chat interface[13][11]
2. Generation occurs automatically
3. Appears as new Note in Studio Panel[11][13]

#### **Interaction Features**
- **Zoom/Scroll**: Pan and navigate the map[11]
- **Expand/Collapse**: Click branches to show/hide sub-nodes[12][11]
- **Query Nodes**: Click statement boxes to ask AI questions about that topic[12]
- **Source-grounded**: All nodes linked to original sources[12]

#### **No Direct Customization**
Unlike Audio/Video Overviews, Mind Maps don't have format/language/style options. To "customize":[13][11]
- Delete existing mind map via three-dot menu[13]
- Ask specific chat query before generating
- Select specific sources before generation[12]

### **Playwright Implementation Pattern**

```python
async def generate_mind_map(self, focus_query=None, source_ids=None):
    """
    Generate Mind Map from sources

    Args:
        focus_query: Optional chat query to focus the mind map
        source_ids: Optional list of source IDs to include (default: all)
    """

    # Select specific sources if provided
    if source_ids:
        await self._select_sources(source_ids)

    # If focus query provided, send it to chat first
    if focus_query:
        await self.page.fill('textarea[aria-label="Ask a question"]', focus_query)
        await self.page.press('textarea[aria-label="Ask a question"]', 'Enter')
        await self.page.wait_for_selector('.response-complete')

    # Click Mind Map chip in chat interface
    await self.page.click('.suggested-chip:has-text("Mind Map")')

    # Wait for mind map to appear in Studio panel
    await self.page.wait_for_selector('.studio-artifact:has-text("Mind Map")')

    # Monitor generation completion
    await self._monitor_artifact_generation("Mind Map", timeout=300)

    return await self._get_artifact_metadata("Mind Map")

async def interact_with_mind_map_node(self, node_text):
    """
    Click a mind map node to query about it

    Args:
        node_text: Text content of the node to click
    """
    # Click on the node statement box
    await self.page.click(f'.mind-map-node:has-text("{node_text}")')

    # Wait for AI response
    await self.page.wait_for_selector('.response-complete')

async def export_mind_map(self, format_type="png"):
    """
    Export mind map (if supported)

    Note: Export functionality may be limited in NotebookLM
    """
    # Check if download option exists
    download_button = await self.page.query_selector('button:has-text("Download")')
    if download_button:
        async with self.page.expect_download() as download_info:
            await download_button.click()
        download = await download_info.value
        return await download.path()
```

### **CLI Command Structure**

```bash
# Basic mind map
deepdiver studio mindmap

# Mind map with focus query
deepdiver studio mindmap --query "Focus on machine learning algorithms"

# Mind map from specific sources
deepdiver studio mindmap --sources "source-1,source-2,source-3"

# Query a mind map node
deepdiver studio mindmap-query --node "Neural Networks"
```

---

## **Phase 4: Study Guides & Reports Implementation** 📚

### **Report Types**

#### **Fixed Format Reports**[14][15][16][17][7]
1. **Briefing Doc**: Detailed executive summary in outline format[16][17]
2. **Study Guide**: Includes outline, quiz with answer key, essay questions, glossary[17][14]
3. **Blog Post**: Article format with engaging structure[18][7]
4. **Create Your Own**: Custom format with user-defined prompt[15][19][16][7]

#### **Dynamic Suggested Reports**[16][18][7]
NotebookLM analyzes uploaded sources and suggests 4 additional report formats:
- **Scientific papers** → White paper, Glossary of terms, Magazine-style explainer[18][7]
- **News articles** → Explainer, Timeline[7]
- **Fiction writing** → Character analysis, Plot critique[18]
- **Business docs** → FAQ, Timeline, Competitive analysis[17]

**Note**: FAQ and Timeline were removed as default options but can be requested via "Create Your Own"[7]

### **Customization Options**

#### **1. Language Selection**
- 80+ supported languages[7]
- **UI Pattern**: Dropdown selector

#### **2. Custom Prompt/Instructions**[19][15][7]
- Freeform text input
- Specify: structure, style, tone, focus areas, target audience
- Examples:
  - "Create a critique with expert feedback on what's missing"[15]
  - "Focus only on chapter 5"[20]
  - "Write in the style of [author]"[21]

#### **3. Source Selection**
- Can limit to specific sources or chapters[20]
- Workaround: Split large PDFs or specify page ranges in prompt[20]

### **Playwright Implementation Pattern**

```python
async def generate_report(self, report_type="study-guide", language="English",
                         custom_prompt="", source_ids=None):
    """
    Generate customized report

    Args:
        report_type: "briefing-doc", "study-guide", "blog-post", "custom", or dynamic type
        language: Language name
        custom_prompt: Custom instructions for report generation
        source_ids: Optional list of specific sources to include
    """

    # Click Reports button in Studio panel
    await self.page.click('.create-artifact-button-container:has-text("Reports")')

    # Wait for report selection dialog
    await self.page.wait_for_selector('.report-format-selector')

    # Select report format
    if report_type == "custom":
        await self.page.click('button:has-text("Create your own")')
    elif report_type in ["briefing-doc", "study-guide", "blog-post"]:
        formatted_name = report_type.replace("-", " ").title()
        await self.page.click(f'button:has-text("{formatted_name}")')
    else:
        # Dynamic suggested format
        await self.page.click(f'button:has-text("{report_type}")')

    # Wait for customization dialog
    await self.page.wait_for_selector('.mat-mdc-dialog-component-host')

    # Select language if not English
    if language != "English":
        await self.page.click('mat-select[aria-label="Language"]')
        await self.page.click(f'mat-option:has-text("{language}")')

    # Fill custom instructions
    if custom_prompt or report_type == "custom":
        prompt_text = custom_prompt if custom_prompt else "Describe the report format and content you want"
        await self.page.fill('textarea[placeholder="Describe the report..."]', prompt_text)

    # Click Generate
    await self.page.click('button:has-text("Generate")')

    # Monitor generation
    await self._monitor_artifact_generation(f"Report: {report_type}", timeout=300)

async def list_dynamic_report_suggestions(self):
    """
    Get AI-suggested report formats based on uploaded sources

    Returns:
        List of suggested report type names
    """
    await self.page.click('.create-artifact-button-container:has-text("Reports")')
    await self.page.wait_for_selector('.dynamic-suggestions')

    suggestions = await self.page.query_selector_all('.suggested-format-button')
    return [await s.text_content() for s in suggestions]
```

### **CLI Command Structure**

```bash
# Fixed format reports
deepdiver studio report --type study-guide
deepdiver studio report --type briefing-doc --language Spanish
deepdiver studio report --type blog-post

# Custom report
deepdiver studio report --type custom \
  --prompt "Create a technical white paper focusing on methodology and results"

# Dynamic suggestion (query first)
deepdiver studio report --list-suggestions
deepdiver studio report --type "Glossary of Terms"

# Source-specific report
deepdiver studio report --type study-guide \
  --prompt "Focus only on Chapter 5: Neural Networks" \
  --sources "textbook.pdf"
```

---

## **Phase 5: Flashcards Implementation** 🎴

### **Customization Options**

#### **1. Number of Cards**[22][23][14]
- **Fewer**: ~15-20 cards[23]
- **Standard** (default): ~28-35 cards[23]
- **More**: ~50-60 cards[23]

**UI Pattern**: Button toggle group (3 options)

#### **2. Difficulty Level**[22][14][23]
- **Easy**
- **Medium** (default)
- **Hard**

**UI Pattern**: Button toggle group (3 options)

#### **3. Custom Focus Prompt**[15][23]
- Freeform text input[23]
- Examples:
  - "Focus on chapter one"[23]
  - "Key terms only"[23]
  - "Include definitions and examples"[15]
  - "Make front of cards shorter for memorization"[14]

#### **4. Source Selection**
- Can specify chapters or specific sources[23]

### **Interaction Features**[24][14][23]
- **Flip cards**: Click to reveal answer
- **Explain button**: Get detailed explanation for any card[24][22][14]
- **Navigate**: Scroll through cards (e.g., "1 of 28")[23]
- **Expand view**: Full-screen card display option[23]

### **Playwright Implementation Pattern**

```python
async def generate_flashcards(self, number="standard", difficulty="medium",
                              custom_prompt="", source_ids=None):
    """
    Generate customized flashcards

    Args:
        number: "fewer", "standard", or "more"
        difficulty: "easy", "medium", or "hard"
        custom_prompt: Custom instructions for flashcard content
        source_ids: Optional list of specific sources
    """

    # Click Flashcards button in Studio panel
    await self.page.click('.create-artifact-button-container:has-text("Flashcards")')

    # Wait for customization dialog
    await self.page.wait_for_selector('.mat-mdc-dialog-component-host')

    # Select number of cards (button toggle group)
    await self.page.click(f'button.toggle-option:has-text("{number.title()}")')

    # Select difficulty level
    await self.page.click(f'button.difficulty-option:has-text("{difficulty.title()}")')

    # Fill custom prompt if provided
    if custom_prompt:
        await self.page.fill('textarea[placeholder="What should the AI focus on?"]', custom_prompt)

    # Click Generate
    await self.page.click('button:has-text("Generate")')

    # Monitor generation
    await self._monitor_artifact_generation("Flashcards", timeout=300)

async def interact_with_flashcard(self, card_number, action="flip"):
    """
    Interact with a specific flashcard

    Args:
        card_number: Card index (1-based)
        action: "flip" to reveal answer, "explain" to get explanation
    """
    # Navigate to card
    if card_number > 1:
        for _ in range(card_number - 1):
            await self.page.click('button.next-card')

    if action == "flip":
        await self.page.click('.flashcard-container .card-face')
    elif action == "explain":
        await self.page.click('button:has-text("Explain")')
        await self.page.wait_for_selector('.explanation-panel')

async def export_flashcards(self, format_type="anki"):
    """
    Export flashcards (if supported)

    Note: Direct Anki/Quizlet export may not be available
    """
    # Check for export options
    menu_button = await self.page.query_selector('.flashcard-menu button[aria-label="More options"]')
    if menu_button:
        await menu_button.click()
        await self.page.click(f'button:has-text("Export to {format_type.title()}")')
```

### **CLI Command Structure**

```bash
# Basic flashcards
deepdiver studio flashcards

# Customized flashcards
deepdiver studio flashcards \
  --number more \
  --difficulty hard \
  --prompt "Focus on key terms and definitions only"

# Chapter-specific flashcards
deepdiver studio flashcards \
  --number standard \
  --prompt "Focus on Chapter 3: Machine Learning Algorithms"

# Interact with flashcard
deepdiver studio flashcard-flip --card-number 5
deepdiver studio flashcard-explain --card-number 12

# Export flashcards
deepdiver studio flashcards-export --format anki
```

---

## **Phase 6: Quizzes Implementation** ❓

### **Customization Options**

#### **1. Number of Questions**[22][14][23]
- **Fewer**: ~5-8 questions
- **Standard** (default): ~10-15 questions
- **More**: ~20-25 questions

**UI Pattern**: Button toggle group (3 options)

#### **2. Difficulty Level**[14][22][23]
- **Easy**
- **Medium** (default)
- **Hard**

**UI Pattern**: Button toggle group (3 options)

#### **3. Custom Focus Prompt**[15]
- Freeform text input
- Examples:
  - "Focus on chapter two"[23]
  - "Create questions about tradeoffs and decisions"[15]
  - "Test application of concepts, not just definitions"[15]
  - "Include scenario-based questions"[15]

#### **4. Source Selection**
- Can specify chapters or topics[23]

### **Quiz Features**[24][14]
- **Multiple choice format**: Questions with 4 options typically
- **Instant scoring**: Get your score after completion[14]
- **Review mode**: Review questions and see correct answers[24][14]
- **Explain button**: Get detailed explanation for any answer[22][14][24]
- **Score overview**: See percentage and which questions were correct[14]

### **Playwright Implementation Pattern**

```python
async def generate_quiz(self, number="standard", difficulty="medium",
                       custom_prompt="", source_ids=None):
    """
    Generate customized quiz

    Args:
        number: "fewer", "standard", or "more"
        difficulty: "easy", "medium", or "hard"
        custom_prompt: Custom instructions for quiz content
        source_ids: Optional list of specific sources
    """

    # Click Quiz button in Studio panel
    await self.page.click('.create-artifact-button-container:has-text("Quiz")')

    # Wait for customization dialog (same pattern as flashcards)
    await self.page.wait_for_selector('.mat-mdc-dialog-component-host')

    # Select number of questions
    await self.page.click(f'button.toggle-option:has-text("{number.title()}")')

    # Select difficulty
    await self.page.click(f'button.difficulty-option:has-text("{difficulty.title()}")')

    # Fill custom prompt
    if custom_prompt:
        await self.page.fill('textarea[placeholder="What should the AI focus on?"]', custom_prompt)

    # Click Generate
    await self.page.click('button:has-text("Generate")')

    # Monitor generation
    await self._monitor_artifact_generation("Quiz", timeout=300)

async def take_quiz(self, answers=None):
    """
    Automate taking a quiz

    Args:
        answers: Optional list of answer indices (0-based) for each question
                If None, just navigates through the quiz

    Returns:
        dict: Quiz results with score and question details
    """
    questions_count = await self._get_quiz_question_count()
    results = {"questions": [], "score": None}

    for i in range(questions_count):
        # Get question text
        question_text = await self.page.text_content(f'.quiz-question-{i+1} .question-text')

        # Select answer if provided
        if answers and i < len(answers):
            await self.page.click(f'.quiz-question-{i+1} .answer-option-{answers[i]}')

        results["questions"].append({
            "number": i+1,
            "question": question_text,
            "selected_answer": answers[i] if answers else None
        })

        # Move to next question
        if i < questions_count - 1:
            await self.page.click('button:has-text("Next")')

    # Submit quiz
    await self.page.click('button:has-text("Submit")')

    # Wait for results
    await self.page.wait_for_selector('.quiz-results')

    # Get score
    score_text = await self.page.text_content('.quiz-score')
    results["score"] = score_text

    return results

async def review_quiz_question(self, question_number, action="explain"):
    """
    Review a quiz question after completion

    Args:
        question_number: Question index (1-based)
        action: "explain" to get explanation, "view" to see answer
    """
    # Navigate to review mode
    await self.page.click('button:has-text("Review")')

    # Navigate to specific question
    if question_number > 1:
        for _ in range(question_number - 1):
            await self.page.click('button.next-question')

    if action == "explain":
        await self.page.click(f'.quiz-question-{question_number} button:has-text("Explain")')
        await self.page.wait_for_selector('.explanation-panel')
```

### **CLI Command Structure**

```bash
# Basic quiz
deepdiver studio quiz

# Customized quiz
deepdiver studio quiz \
  --number more \
  --difficulty hard \
  --prompt "Focus on application and tradeoff scenarios"

# Auto-take quiz (for testing)
deepdiver studio quiz-take \
  --answers "0,2,1,3,2" \
  --review

# Review quiz results
deepdiver studio quiz-review --question-number 5
deepdiver studio quiz-explain --question-number 3
```

---

## **Technical Implementation Patterns**

### **Common UI Patterns Across All Artifacts**

#### **1. Edit Button Pattern**[25][26]
```python
# Selector pattern for opening customization dialog
selector = '.create-artifact-button-container:has-text("{artifact_name}") button.edit-button'

# Alternative: Three-dot menu approach
selector = '.artifact-tile:has-text("{artifact_name}") button[aria-label="More options"]'
# Then click "Customize" in dropdown
```

#### **2. Material Design Dialog Structure**[27][28][25]
All customization dialogs use Angular Material CDK with:
- `.mat-mdc-dialog-component-host` - Main dialog container
- `.cdk-overlay-backdrop` - Background overlay
- `.cdk-overlay-pane` - Dialog content pane

```python
# Wait for dialog to appear
await self.page.wait_for_selector('.mat-mdc-dialog-component-host')

# Dismiss dialog (if needed)
await self.page.click('.cdk-overlay-backdrop')
```

#### **3. Form Control Patterns**[29][30][31]

**Radio Buttons (Format selection):**
```python
await self.page.click('mat-radio-button:has-text("Option Name")')
```

**Dropdowns (Language/Style selection):**
```python
# Open dropdown
await self.page.click('mat-select[formcontrolname="fieldName"]')
# Select option
await self.page.click('mat-option:has-text("Option Name")')
```

**Toggle Button Groups (Number/Difficulty):**
```python
await self.page.click('button.toggle-option:has-text("Option")')
```

**Text Areas (Prompts):**
```python
await self.page.fill('textarea[placeholder="Placeholder text..."]', 'Your content')
```

#### **4. Generation Monitoring Pattern**[25][9][8]

```python
async def _monitor_artifact_generation(self, artifact_name, timeout=600):
    """
    Monitor artifact generation with background polling

    Pattern learned from Audio Overview implementation:
    - Poll every 5 seconds
    - Check for "Load" button (completion indicator)
    - Support concurrent generation
    - Timeout after specified seconds
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if artifact has "Load" button (indicates completion)
        load_button = await self.page.query_selector(
            f'.studio-artifact:has-text("{artifact_name}") button:has-text("Load")'
        )

        if load_button:
            logger.info(f"{artifact_name} generation complete")
            return True

        # Check for error state
        error_indicator = await self.page.query_selector(
            f'.studio-artifact:has-text("{artifact_name}") .error-state'
        )

        if error_indicator:
            error_msg = await error_indicator.text_content()
            raise Exception(f"{artifact_name} generation failed: {error_msg}")

        # Wait before next poll
        await asyncio.sleep(5)

    raise TimeoutError(f"{artifact_name} generation timed out after {timeout} seconds")
```

#### **5. Artifact Metadata Tracking**

```python
async def add_artifact_to_notebook(self, artifact_type, customization_params):
    """
    Store complete artifact metadata for session tracking

    Metadata to capture:
    - Artifact type
    - Generation timestamp
    - Customization parameters
    - Artifact ID/URL
    - Thumbnail (if applicable)
    - Duration (for audio/video)
    - Source IDs used
    """
    metadata = {
        "type": artifact_type,
        "timestamp": datetime.now().isoformat(),
        "customization": customization_params,
        "artifact_id": await self._get_artifact_id(artifact_type),
        "url": await self._get_artifact_url(artifact_type),
        "status": "completed"
    }

    # Add type-specific metadata
    if artifact_type in ["Audio Overview", "Video Overview"]:
        metadata["duration"] = await self._get_artifact_duration(artifact_type)
        metadata["format"] = customization_params.get("format")

    if artifact_type == "Video Overview":
        metadata["visual_style"] = customization_params.get("visual_style")
        metadata["thumbnail_url"] = await self._get_video_thumbnail()

    if artifact_type in ["Flashcards", "Quiz"]:
        metadata["count"] = await self._get_item_count(artifact_type)
        metadata["difficulty"] = customization_params.get("difficulty")

    # Store in session
    session_tracker.add_artifact(metadata)

    return metadata
```

### **CSS Selectors Reference**[26][32][25]

```python
# Studio panel selectors
STUDIO_PANEL = ".studio-panel"
STUDIO_HEADER = ".studio-panel-header"
ARTIFACT_CONTAINER = ".create-artifact-button-container"
ARTIFACT_TILE = ".artifact-tile"

# Button selectors
EDIT_BUTTON = "button.edit-button"
CUSTOMIZE_BUTTON = "button:has-text('Customize')"
GENERATE_BUTTON = "button:has-text('Generate')"
LOAD_BUTTON = "button:has-text('Load')"

# Dialog selectors
DIALOG_HOST = ".mat-mdc-dialog-component-host"
DIALOG_CONTENT = ".mat-dialog-content"
OVERLAY_BACKDROP = ".cdk-overlay-backdrop"

# Form control selectors
RADIO_BUTTON = "mat-radio-button"
MAT_SELECT = "mat-select"
MAT_OPTION = "mat-option"
TOGGLE_BUTTON = "button.toggle-option"
TEXTAREA = "textarea"

# Artifact-specific selectors
AUDIO_TILE = '.create-artifact-button-container:has-text("Audio Overview")'
VIDEO_TILE = '.create-artifact-button-container:has-text("Video Overview")'
MINDMAP_CHIP = '.suggested-chip:has-text("Mind Map")'
REPORTS_TILE = '.create-artifact-button-container:has-text("Reports")'
FLASHCARDS_TILE = '.create-artifact-button-container:has-text("Flashcards")'
QUIZ_TILE = '.create-artifact-button-container:has-text("Quiz")'
```

### **Error Handling Patterns**

```python
async def _handle_generation_errors(self, artifact_type):
    """
    Common error scenarios and handling strategies
    """

    # Check for insufficient sources
    if await self.page.query_selector('.error-message:has-text("No sources")'):
        raise ValueError(f"Cannot generate {artifact_type}: No sources uploaded")

    # Check for usage limits
    if await self.page.query_selector('.error-message:has-text("limit reached")'):
        raise Exception(f"Usage limit reached for {artifact_type}")

    # Check for network errors
    if await self.page.query_selector('.error-message:has-text("network")'):
        raise ConnectionError(f"Network error generating {artifact_type}")

    # Check for disabled features
    disabled_tile = await self.page.query_selector(
        f'{ARTIFACT_CONTAINER}:has-text("{artifact_type}").disabled-tile'
    )
    if disabled_tile:
        raise Exception(f"{artifact_type} feature is not available")
```

---

## **CLI Structure Overview**

```bash
# Studio command group
deepdiver studio [artifact-type] [options]

# Artifact types:
#   audio      - Audio Overview
#   video      - Video Overview
#   mindmap    - Mind Map
#   report     - Study Guides / Reports
#   flashcards - Flashcards
#   quiz       - Quiz

# Common options:
#   --notebook-id ID       Target notebook
#   --prompt TEXT          Custom steering/focus prompt
#   --language LANG        Output language
#   --sources IDS          Comma-separated source IDs

# Type-specific options:
#   Audio/Video:
#     --format TYPE        Format selection
#     --length TYPE        Length (audio only)
#     --style STYLE        Visual style (video only)
#
#   Flashcards/Quiz:
#     --number TYPE        Number of items (fewer/standard/more)
#     --difficulty LEVEL   Difficulty level (easy/medium/hard)
#
#   Reports:
#     --type TYPE          Report type (briefing-doc, study-guide, etc.)
#     --list-suggestions   Show dynamic suggestions

# Management commands:
deepdiver studio list                    # List all artifacts in notebook
deepdiver studio status --artifact-id ID # Check generation status
deepdiver studio delete --artifact-id ID # Delete artifact
```

---

## **Session Integration**

### **Artifact Tracking in Sessions**

```python
# Session metadata structure
session_artifacts = {
    "session_id": "session-123",
    "notebook_id": "notebook-abc",
    "artifacts": [
        {
            "id": "artifact-1",
            "type": "Audio Overview",
            "format": "deep-dive",
            "length": "longer",
            "duration_seconds": 1245,
            "created_at": "2025-01-15T14:30:00Z",
            "url": "https://notebooklm.google.com/...",
            "prompt": "Focus on machine learning algorithms"
        },
        {
            "id": "artifact-2",
            "type": "Video Overview",
            "format": "brief",
            "visual_style": "anime",
            "language": "English",
            "duration_seconds": 120,
            "created_at": "2025-01-15T14:35:00Z",
            "thumbnail": "https://...",
            "prompt": "Quick overview for beginners"
        },
        {
            "id": "artifact-3",
            "type": "Flashcards",
            "count": 28,
            "difficulty": "medium",
            "number_setting": "standard",
            "created_at": "2025-01-15T14:40:00Z",
            "prompt": "Focus on key terminology"
        }
    ]
}
```

### **Session Commands Integration**

```bash
# Track artifact generation in session
deepdiver session write "Generated anime-style video overview for chapter 3"

# View all artifacts in current session
deepdiver session artifacts

# Export session with all artifacts
deepdiver session export --include-artifacts
```

---

## **Testing Strategy**

### **Test Suite Structure**

```python
# tests/test_studio_artifacts.py

class TestVideoOverview:
    async def test_basic_video_generation(self):
        """Test default video overview generation"""

    async def test_video_format_options(self):
        """Test explainer vs brief formats"""

    async def test_visual_styles(self):
        """Test all visual style options"""

    async def test_video_with_prompt(self):
        """Test custom steering prompt"""

class TestMindMap:
    async def test_basic_mindmap_generation(self):
        """Test mind map generation via chat chip"""

    async def test_mindmap_node_interaction(self):
        """Test clicking nodes and querying"""

    async def test_source_specific_mindmap(self):
        """Test mind map from selected sources"""

class TestReports:
    async def test_study_guide_generation(self):
        """Test study guide report"""

    async def test_custom_report(self):
        """Test custom report with prompt"""

    async def test_dynamic_suggestions(self):
        """Test AI-suggested report formats"""

class TestFlashcards:
    async def test_flashcard_customization(self):
        """Test number and difficulty options"""

    async def test_flashcard_interaction(self):
        """Test flipping and explaining cards"""

class TestQuiz:
    async def test_quiz_generation(self):
        """Test quiz customization options"""

    async def test_quiz_taking(self):
        """Test automated quiz completion"""

    async def test_quiz_review(self):
        """Test review mode and explanations"""
```

---

## **Configuration Updates**

```yaml
# deepdiver.yaml additions

STUDIO_ARTIFACTS:
  enabled: true

  VIDEO_OVERVIEW:
    default_format: "explainer"  # explainer | brief
    default_style: "auto-select"  # auto-select | classic | whiteboard | etc.
    default_language: "English"
    timeout: 600

  MIND_MAP:
    default_sources: "all"
    interaction_enabled: true
    timeout: 300

  REPORTS:
    default_type: "study-guide"  # briefing-doc | study-guide | blog-post | custom
    default_language: "English"
    timeout: 300

  FLASHCARDS:
    default_number: "standard"  # fewer | standard | more
    default_difficulty: "medium"  # easy | medium | hard
    timeout: 300

  QUIZ:
    default_number: "standard"  # fewer | standard | more
    default_difficulty: "medium"  # easy | medium | hard
    auto_review: true
    timeout: 300

CONCURRENT_GENERATION:
  enabled: true
  max_simultaneous: 3
```

---

## **Implementation Checklist**

### **Phase 2: Video Overview** ✅
- [ ] Research Video Overview UI and DOM structure
- [ ] Map all customization options (format, style, language, prompt)
- [ ] Implement `generate_video_overview()` method
- [ ] Add CLI command: `deepdiver studio video`
- [ ] Handle video-specific metadata (thumbnail, duration, visual style)
- [ ] Test all visual styles (Classic, Anime, Whiteboard, etc.)
- [ ] Test Brief vs Explainer formats
- [ ] Implement generation monitoring with timeout
- [ ] Add session tracking for video artifacts
- [ ] Write comprehensive tests

### **Phase 3: Mind Map** 🗺️
- [ ] Research Mind Map generation via chat chip
- [ ] Implement chat interaction for mind map trigger
- [ ] Implement `generate_mind_map()` method
- [ ] Add node interaction methods
- [ ] Add CLI command: `deepdiver studio mindmap`
- [ ] Test source-specific mind maps
- [ ] Test node querying functionality
- [ ] Implement export functionality (if available)
- [ ] Write tests for all mind map features

### **Phase 4: Study Guides / Reports** 📚
- [ ] Map all report types (fixed + dynamic)
- [ ] Implement `generate_report()` method
- [ ] Implement dynamic suggestion detection
- [ ] Add CLI command: `deepdiver studio report`
- [ ] Test all fixed report formats
- [ ] Test custom report generation
- [ ] Test language selection
- [ ] Test source-specific reports
- [ ] Write comprehensive tests

### **Phase 5: Flashcards** 🎴
- [ ] Map customization options (number, difficulty, prompt)
- [ ] Implement `generate_flashcards()` method
- [ ] Implement card interaction methods (flip, explain)
- [ ] Add CLI command: `deepdiver studio flashcards`
- [ ] Test all number/difficulty combinations
- [ ] Test card navigation and interaction
- [ ] Implement export functionality (if available)
- [ ] Write comprehensive tests

### **Phase 6: Quizzes** ❓
- [ ] Map customization options (number, difficulty, prompt)
- [ ] Implement `generate_quiz()` method
- [ ] Implement quiz-taking automation
- [ ] Implement review mode functionality
- [ ] Add CLI command: `deepdiver studio quiz`
- [ ] Test all number/difficulty combinations
- [ ] Test quiz submission and scoring
- [ ] Test review and explain features
- [ ] Write comprehensive tests

---

## **Key Achievements & Innovations**

### **From Audio Overview Implementation (PR #10)**
✅ **Terminal-to-NotebookLM automation bridge**
✅ **Edit button pattern** for customization dialogs
✅ **Material Design dialog handling** with CDK overlays
✅ **Background polling** for generation monitoring
✅ **Complete metadata tracking** in session system
✅ **5-second polling interval** with 600s timeout

### **Patterns Applicable to All Artifacts**
- Edit pencil icon → Customization dialog
- Material Design components with Angular CDK
- Radio buttons for format selection
- Dropdowns for language/style
- Toggle groups for number/difficulty
- Text areas for custom prompts
- Background generation with polling
- "Load" button as completion indicator
- Comprehensive metadata storage

---

## **Next Steps**

1. **Start with Video Overview** (Phase 2) - Second most requested feature, builds on Audio Overview patterns
2. **Use DeepDiver's existing infrastructure**:
   - `notebooklm_automator.py` - Playwright automation engine
   - `session_tracker.py` - Metadata and session management
   - `deepdive.py` - CLI orchestration
3. **Follow Audio Overview implementation pattern** from PR #10
4. **Test thoroughly** with different customization combinations
5. **Document edge cases** and limitations
6. **Iterate based on user feedback**

---

## **Contributing to Artifact Implementation**

Interested in implementing one of these artifact types? Here's how to get started:

1. **Review this guide** for the artifact type you want to implement
2. **Check the ROADMAP.md** for current project status and priorities
3. **Create a GitHub issue** using the enhancement workflow (see CLAUDE.md)
4. **Follow the Audio Overview pattern** from PR #10 as a reference
5. **Test thoroughly** with the validation scripts approach
6. **Document your implementation** with examples and edge cases

For questions or collaboration, see the main project [README.md](../README.md).

---

## **Related Documentation**

- [ROADMAP.md](../ROADMAP.md) - Overall project development plan
- [CONFIGURATION.md](../CONFIGURATION.md) - Configuration guide
- [CLAUDE.md](../CLAUDE.md) - Assembly team and workflow
- [README.md](../README.md) - Getting started guide

---

**🎙️ DeepDiver: Where Content Becomes Every Type of Artifact**

*♠️🌿🎸🧵 G.Music Assembly - NotebookLM Studio Mastery*
