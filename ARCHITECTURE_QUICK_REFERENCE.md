# DeepDiver Architecture - Quick Reference Guide

## System Components at a Glance

### Core Modules (5 files, ~3,700 lines)

| Module | Lines | Purpose | Key Classes |
|--------|-------|---------|------------|
| **deepdive.py** | 789 | CLI orchestrator | Click command groups |
| **notebooklm_automator.py** | 1442 | Browser automation | NotebookLMAutomator |
| **session_tracker.py** | 724 | Session management | SessionTracker |
| **content_processor.py** | 344 | File validation | ContentProcessor |
| **podcast_manager.py** | 403 | Audio management | PodcastManager |

---

## Main CLI Commands

```bash
# System
deepdiver init              # Initialize & auto-launch Chrome
deepdiver test              # Test connection
deepdiver status            # Show system status

# Notebooks (PRIMARY INTERFACE)
deepdiver notebook create [--source URL/FILE]
deepdiver notebook list
deepdiver notebook open <id>
deepdiver notebook add-source <id> <source>
deepdiver notebook share <email>
deepdiver notebook url [--notebook-id]

# Sessions
deepdiver session start --ai claude --issue 4
deepdiver session status
deepdiver session close

# Legacy
deepdiver podcast <file.pdf>     # Create podcast (old)
```

---

## Key Architecture Patterns

### 1. Chrome DevTools Protocol (CDP)
- **Reuses authenticated browser**: No re-login needed
- **URL Priority Chain**:
  1. CLI override: `--cdp-url http://...`
  2. Environment: `DEEPDIVER_CDP_URL=http://...`
  3. Config file: `deepdiver.yaml`
  4. Default: `http://localhost:9222`

### 2. Multi-Selector Fallback
- Handles dynamic NotebookLM UI changes
- Try 5-7 selectors per element
- Log first matching selector

### 3. Session Persistence
- JSON files in `./sessions/`
- `current_session.json` for quick access
- `session_{uuid}.json` for history
- Auto-save after changes

### 4. Browser Persistence
- Browser stays open between commands
- Multiple CLI calls share same Chrome instance
- Speeds up workflows

---

## Data Flow: Create Notebook + Add Source

```
deepdiver notebook create --source "https://example.com"
    ↓
1. SessionTracker.start_session()
2. NotebookLMAutomator.connect_to_browser()
3. NotebookLMAutomator.navigate_to_notebooklm()
4. NotebookLMAutomator.create_notebook()
   └─ Returns {id, url, created_at, sources=[]}
5. NotebookLMAutomator.add_source(url)
   └─ Routes to add_url_source() or upload_document()
6. SessionTracker.add_notebook(notebook_data)
7. SessionTracker.add_source_to_notebook(id, source_data)
8. Display results to user
```

---

## Session File Structure

```json
{
  "session_id": "uuid-string",
  "ai_assistant": "claude",
  "status": "active",
  "created_at": "2025-11-13T...",
  "notebooks": [
    {
      "id": "abc-123",
      "url": "https://notebooklm.google.com/notebook/abc-123",
      "title": "Research Paper",
      "active": true,
      "sources": [
        {
          "filename": "paper.pdf",
          "path": "/path/to/paper.pdf",
          "type": "pdf",
          "source_id": "a1b2c3d4",
          "added_at": "2025-11-13T..."
        }
      ]
    }
  ],
  "active_notebook_id": "abc-123",
  "notes": [],
  "podcasts_created": []
}
```

---

## Browser Automation Methods

### Connection
```python
await automator.connect_to_browser()           # Via CDP
await automator.navigate_to_notebooklm()       # Go to NotebookLM
await automator.check_authentication()         # Verify logged in
```

### Notebooks
```python
await automator.create_notebook()              # New notebook
await automator.navigate_to_notebook(id)       # Open existing
await automator.share_notebook(email, role)    # Share with user
```

### Sources (RECOMMENDED: Use add_source())
```python
await automator.add_source(source, notebook_id)  # Smart routing
# Routes to:
await automator.add_url_source(url, notebook_id)
await automator.upload_document(file, notebook_id)
```

### Audio (Planned)
```python
await automator.generate_audio_overview(title)
await automator.download_audio(output_path)
```

---

## Session Tracker Methods

### Lifecycle
```python
tracker.start_session(ai_assistant='claude', issue_number=4)
tracker.end_session()
tracker.load_session(session_id)
tracker._load_current_session()
```

### Notebook Management
```python
tracker.add_notebook(notebook_data)
tracker.list_notebooks()
tracker.get_notebook_by_id(id)
tracker.set_active_notebook(id)
tracker.update_notebook(id, updates)
```

### Source Management
```python
tracker.add_source_to_notebook(notebook_id, source_data)
tracker.list_notebook_sources(notebook_id)
```

### Queries
```python
tracker.get_session_status()
tracker.list_sessions()
tracker.get_active_notebook()
```

---

## Configuration System

**File**: `deepdiver/deepdiver.yaml`

### Key Sections
- **BROWSER_SETTINGS**: CDP URL, timeouts, headless mode
- **NOTEBOOKLM_SETTINGS**: Base URL, operation timeouts
- **CONTENT_SETTINGS**: File formats, max size, temp directory
- **SESSION_TRACKING**: Session directory, auto-save, metadata format
- **AUDIO_SETTINGS**: Output directory, naming pattern, quality checks

### Override Hierarchy
```
1. CLI argument (--cdp-url)
2. Environment variable (DEEPDIVER_CDP_URL)
3. YAML config file
4. Hardcoded defaults
```

---

## Implementation Status

### ✅ Fully Implemented
- Browser connection & navigation (CDP)
- Notebook creation & management
- Source uploading (PDF, DOCX, TXT, HTML, MD)
- URL sources (websites, YouTube, SimExp)
- Notebook sharing
- Session tracking & persistence
- CLI interface
- Configuration system

### 🚧 Partially Implemented
- Audio generation/download (methods exist, needs testing)
- Content processor (validation working, integration incomplete)
- Podcast manager (file organization ready, metadata embedding incomplete)

### ❌ Not Implemented
- Batch processing
- Retry logic
- Cloud storage integration
- REST API
- Progress indicators

---

## Common Patterns in Code

### 1. Multi-Selector Fallback
```python
selectors = [
    'button[primary-attr]',      # Most specific
    'button[aria-label="..."]',
    'button:has-text("...")',    # Most generic
]
for selector in selectors:
    try:
        element = await page.wait_for_selector(selector, timeout=2000)
        if element:
            break
    except:
        continue
```

### 2. Screenshot on Error
```python
try:
    # automation code
except Exception as e:
    await page.screenshot(path=f"debug/operation_error.png")
    logger.error(f"Error: {e}")
    raise
```

### 3. Session Auto-Save
```python
if self.auto_save:
    self._save_current_session()  # Auto-persists to JSON
```

### 4. Async Browser Operations
```python
async def some_operation(self):
    if not self.page:
        return False
    await self.page.goto(url)
    await self.page.wait_for_selector(selector, timeout=5000)
    return True
```

---

## Directory Structure

```
/home/gmusic/workspace/deepdiver/
├── deepdiver/                   # Main package
│   ├── __init__.py
│   ├── deepdive.py              # CLI (789 lines)
│   ├── notebooklm_automator.py  # Automation (1442 lines)
│   ├── session_tracker.py       # Sessions (724 lines)
│   ├── content_processor.py     # Content (344 lines)
│   ├── podcast_manager.py       # Podcasts (403 lines)
│   └── deepdiver.yaml           # Config (80 lines)
├── tests/                       # Test directory
├── sessions/                    # Session JSON files
├── output/                      # Generated podcasts
├── debug/                       # Error screenshots
├── setup.py
├── README.md
├── ROADMAP.md
├── CLAUDE.md
└── ARCHITECTURE_ANALYSIS.md     # This project's full analysis
```

---

## Entry Points

### CLI
```python
# setup.py
entry_points={
    "console_scripts": [
        "deepdiver=deepdiver.deepdive:main",
    ],
}

# Run with: deepdiver <command> [options]
```

### Programmatic
```python
from deepdiver import NotebookLMAutomator, SessionTracker

automator = NotebookLMAutomator(config_path="deepdiver/deepdiver.yaml")
tracker = SessionTracker()

await automator.connect_to_browser()
tracker.start_session()
```

---

## Key Concepts

### Notebook
- Created in NotebookLM
- Contains sources (PDFs, URLs, etc.)
- Can generate Audio Overviews
- Shareable with collaborators
- Tracked in session

### Source
- Document or URL added to notebook
- Can be: PDF, DOCX, TXT, MD, HTML, or URL
- YouTube videos supported
- SimExp notes supported
- Generates source_id hash

### Session
- Grouping of work (per issue/feature)
- Contains multiple notebooks
- Persisted as JSON file
- Tracks notebooks, sources, podcasts, notes

### Audio Overview
- Podcast generated by NotebookLM
- Created from notebook sources
- Downloaded as MP3
- Tracked in session/notebook

---

## Quick Debug Checklist

- [ ] Chrome running with `--remote-debugging-port=9222`?
- [ ] Logged into Google account in Chrome?
- [ ] CDP URL correct? (check `deepdiver init`)
- [ ] Valid session exists? (check `deepdiver session status`)
- [ ] Check debug screenshots in `debug/` directory
- [ ] Enable logging: Set LOGGING level to DEBUG in config
- [ ] Verify file path exists: `ls -la <filepath>`
- [ ] Check selector changed: Run `deepdiver get-html` and inspect

---

**For detailed information, see ARCHITECTURE_ANALYSIS.md**
