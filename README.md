# 🎙️ DeepDiver - NotebookLM Podcast Automation System
**Terminal-to-Web Audio Creation Bridge**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Open%20Assembly-green.svg)]()

---

## 🎯 What is DeepDiver?

DeepDiver is a Python-based automation system that bridges terminal commands with NotebookLM's podcast generation capabilities, enabling seamless content-to-audio transformation through browser automation.

**Key Features**:
1. **📖 Content Ingestion**: Upload documents to NotebookLM automatically
2. **🎙️ Advanced Audio Generation**: Create Audio Overviews with full customization (format, language, length, focus prompts)
3. **🎨 Studio Integration**: Access all NotebookLM Studio features via terminal
4. **📱 Cross-Device Sync**: Access generated podcasts anywhere
5. **🔮 Session Management**: Track podcast creation sessions with artifact metadata
6. **🌊 Terminal-to-Web**: Command-line to NotebookLM communication bridge

**Key Achievement**: **Terminal-to-Audio fluidity** - Your terminal can now create podcasts from documents and sync across all your devices!

---

## 📦 Installation

### Prerequisites

- Python 3.8+
- Google Chrome or Chromium
- A Google account with access to NotebookLM

### Install Dependencies

```bash
# Core dependencies
pip install playwright pyyaml requests beautifulsoup4 pyperclip click rich

# Install Playwright browsers
playwright install chromium
```

### Launch Chrome for Communication

For DeepDiver to communicate with NotebookLM, you need to launch Chrome with remote debugging:

```bash
# Launch Chrome with a remote debugging port
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver &
```

In the new Chrome window, log in to your Google account and navigate to [NotebookLM](https://notebooklm.google.com).

---

## 🚀 Quick Start

### 1. Initialize DeepDiver

```bash
# Initialize the project
deepdiver init
```

### 2. Start a Session

```bash
# Start a new podcast creation session
deepdiver session start --ai claude --issue 1
```

### 3. Create Your First Podcast

```bash
# Upload a document and generate a podcast
deepdiver podcast create --source document.pdf --title "My First Podcast"
```

### 4. Check Session Status

```bash
# View current session information
deepdiver session status
```

---

## ⚙️ Configuration

DeepDiver uses **smart configuration file discovery** - it automatically searches multiple locations so you can run commands from anywhere!

### Configuration File Locations

DeepDiver searches for config files in this priority order:

1. **Explicit path** (when using `--config` flag)
2. **Current directory**: `./deepdiver/deepdiver.yaml`
3. **User config directory**: `~/.config/deepdiver/config.yaml` ⭐ **Recommended**
4. **Home directory**: `~/deepdiver/deepdiver.yaml`
5. **Package directory**: Where DeepDiver is installed
6. **Built-in defaults**: If no config file is found

### Creating Your Configuration

The easiest way to set up your configuration:

```bash
# Creates ~/.config/deepdiver/config.yaml with default settings
deepdiver init

# Or specify a custom location
deepdiver init --config /path/to/my/config.yaml
```

### Benefits of Smart Config Discovery

- ✅ **Run from anywhere**: No need to be in a specific directory
- ✅ **Cross-device consistency**: Config stored in standard location
- ✅ **Easy updates**: Edit one file that works everywhere
- ✅ **No setup needed**: Falls back to sensible defaults

For detailed configuration options and troubleshooting, see [CONFIGURATION.md](CONFIGURATION.md).

---

## 🎮 Usage

### Session Commands

```bash
# Start a new session
deepdiver session start --ai claude --issue 42

# Write to session log
deepdiver session write "Uploaded research paper for podcast generation"

# Check session status
deepdiver session status

# Close browser session (session data is preserved)
deepdiver session close
```

### Podcast Commands

```bash
# One-shot: upload document → generate Audio Overview → download mp3
deepdiver podcast research.pdf --title "Research Insights" --output ./output

# Preferred fine-grained flow: generate with customization + download
deepdiver studio audio --notebook-id abc-123 --download

# Download every downloadable artifact + manifest.json (cross-device export)
deepdiver studio download --notebook-id abc-123 --output ./output/artifacts/run-42
```

### Notebook Commands

```bash
# Create a new notebook (empty)
deepdiver notebook create

# Create notebook with a SimExp note as source
deepdiver notebook create --source "https://app.simplenote.com/p/abc123"

# Create notebook with web article
deepdiver notebook create --source "https://example.com/research-paper"

# Create notebook with YouTube video
deepdiver notebook create --source "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Create notebook with local file
deepdiver notebook create --source "./notes.pdf"

# List notebooks in current session
deepdiver notebook list

# Open specific notebook in browser
deepdiver notebook open --notebook-id abc-123

# Get notebook URL
deepdiver notebook url --notebook-id abc-123

# Share notebook with collaborator
deepdiver notebook share --notebook-id abc-123 --email user@example.com

# Resume an existing notebook: upload ONLY the sources it is missing
deepdiver notebook resume abc-123 -s notes.md -s summary.pdf
deepdiver notebook resume abc-123 --source-dir ./packet/sources
```

### Studio Commands

**🌸 NEW: Advanced Audio Overview Generation**

DeepDiver now supports NotebookLM's Studio panel with full customization options:

```bash
# Basic audio generation (uses defaults: Deep Dive, English, Default length)
deepdiver studio audio --notebook-id abc-123

# Customize format: Deep Dive, Brief, Critique, or Debate
deepdiver studio audio --format deep_dive --notebook-id abc-123
deepdiver studio audio --format brief --notebook-id abc-123
deepdiver studio audio --format critique --notebook-id abc-123
deepdiver studio audio --format debate --notebook-id abc-123

# Customize length: Short, Default, or Long
deepdiver studio audio --length short --notebook-id abc-123
deepdiver studio audio --length default --notebook-id abc-123
deepdiver studio audio --length long --notebook-id abc-123

# Customize language
deepdiver studio audio --language English --notebook-id abc-123
deepdiver studio audio --language Spanish --notebook-id abc-123
deepdiver studio audio --language French --notebook-id abc-123

# Add focus prompts (guide the AI hosts)
deepdiver studio audio \
  --focus "Focus on the technical implementation details" \
  --notebook-id abc-123

deepdiver studio audio \
  --focus "Explain to someone new to this topic" \
  --notebook-id abc-123

deepdiver studio audio \
  --focus "Discuss only the article about machine learning" \
  --notebook-id abc-123

# Full customization example
deepdiver studio audio \
  --format critique \
  --language English \
  --length long \
  --focus "Analyze the strengths and weaknesses of the proposed architecture" \
  --notebook-id abc-123
```

**Format Options**:
- **Deep Dive** (default): Lively conversation unpacking and connecting topics
- **Brief**: Bite-sized overview for quick understanding
- **Critique**: Expert review with constructive feedback
- **Debate**: Thoughtful discussion of different perspectives

**Length Options**:
- **Short**: Quick overview (3-5 minutes)
- **Default**: Balanced depth (5-10 minutes)
- **Long**: Comprehensive exploration (10-15 minutes)

**Focus Prompts** (max 5000 characters):
- Focus on specific source: "only cover the article about Italy"
- Focus on topic: "just discuss the novel's main character"
- Target audience: "explain to someone new to biology"
- Custom instructions: Any guidance for the AI hosts

**Session Tracking**:
All generated Audio Overviews are automatically tracked in your session with complete metadata (format, language, length, focus, generation time).

### Multi-Artifact Studio Generation

Beyond audio, DeepDiver generates the full Studio family through each
tile's customization dialog:

```bash
# Slide decks: presenter (spoken) or detailed (dense leave-behind)
deepdiver studio slide-deck --format presenter \
  --focus "Explain the architecture for new operators" -n abc-123

# Any Studio family by name
deepdiver studio generate mind_map -n abc-123
deepdiver studio generate quiz --focus "Focus on chapter 3" -n abc-123
deepdiver studio generate video_overview --language French -n abc-123

# See what's ready in the Studio panel
deepdiver studio list -n abc-123
```

Artifact types: `audio_overview`, `slide_deck`, `video_overview`,
`mind_map`, `reports`, `flashcards`, `quiz`, `infographic`, `data_table`.

Note: a ready artifact can show a disabled "Copy link" — that's a
notebook-sharing gate, not a generation failure. Share the notebook first.

### Artifact Download & Cross-Device Export

```bash
# Download all downloadable artifacts into one directory + manifest.json
deepdiver studio download -n abc-123 -o ./output/artifacts/run-42
```

Each download records title, local path, sha256, byte size, and (when
ffprobe is available) codec/duration — the manifest is what mesh-sync
tooling needs to ship artifacts to other devices. Download paths are also
written back into the session tracker.

### Chrome Commands

```bash
# Launch Chrome with CDP (SSH/tmux-safe: passes DISPLAY/XAUTHORITY)
deepdiver chrome launch

# Reuse an authenticated profile WITHOUT touching the live one
deepdiver chrome launch --clone-profile "Profile 3"
```

### Agent Skills

DeepDiver ships agent-facing SKILL.md operating manuals inside the
package, so any agent running the binary can learn to drive it:

```bash
deepdiver skills list                          # what's bundled
deepdiver skills show notebooklm-automation    # read a skill
deepdiver skills install --agent claude        # → ~/.claude/skills
deepdiver skills install --agent hermes        # → ~/.hermes/skills/development
deepdiver skills install --to /path/to/skills  # anywhere
```

---

## 🏗️ Project Structure

```
deepdiver/
├── deepdiver/
│   ├── __init__.py
│   ├── deepdive.py              # Main CLI orchestrator
│   ├── notebooklm_automator.py  # Playwright automation engine
│   ├── content_processor.py     # Content preparation
│   ├── podcast_manager.py       # Audio file management
│   ├── session_tracker.py       # Session management
│   └── deepdiver.yaml           # Configuration
├── tests/
│   ├── test_notebooklm_connection.py
│   ├── test_podcast_creation.py
│   └── test_session_management.py
├── output/                      # Generated podcasts
├── sessions/                    # Session logs
├── credentials/                 # Authentication data
└── docs/                        # Documentation
```

---

## 🔧 Configuration

### deepdiver.yaml

```yaml
BASE_PATH: ./output

PODCAST_SETTINGS:
  quality: high
  format: mp3
  duration_limit: 30
  language: en

SESSION_TRACKING:
  enabled: true
  metadata_format: yaml
  auto_save: true

BROWSER_SETTINGS:
  headless: false
  cdp_url: http://localhost:9222
  user_data_dir: /tmp/chrome-deepdiver
  timeout: 30

CONTENT_SETTINGS:
  supported_formats:
    - pdf
    - docx
    - txt
    - md
  max_file_size: 50MB
  auto_process: true
```

---

## 🧪 Testing

### Test NotebookLM Connection

```bash
# Test browser automation
python tests/test_notebooklm_connection.py
```

### Test Podcast Creation

```bash
# Test end-to-end podcast generation
python tests/test_podcast_creation.py
```

### Test Session Management

```bash
# Test session tracking
python tests/test_session_management.py
```

---

## 🎓 How It Works

### SimExp Integration Flow

DeepDiver integrates seamlessly with [SimExp](https://github.com/jgwill/simexp) for a complete content-to-podcast workflow:

```
1. Create Content in SimExp
   ↓
   simexp session start --ai claude --issue 4
   simexp session write "Research findings..."
   simexp session add ./research.pdf
   ↓
2. Publish SimExp Note
   ↓
   simexp session publish
   # Returns: https://app.simplenote.com/p/abc123
   ↓
3. Create DeepDiver Notebook with SimExp Source
   ↓
   deepdiver notebook create --source "https://app.simplenote.com/p/abc123"
   ↓
4. Generate Podcast from Combined Content
   ↓
   deepdiver podcast generate
   ↓
5. Listen to Your Research Audio Overview!
```

**Benefits**:
- 🎯 Terminal-to-Audio pipeline
- 📝 Session-aware content tracking
- 🌐 Cross-device accessibility
- 🔗 Traceable content lineage

### Podcast Creation Flow

```
Terminal Command
    ↓
deepdive.py (CLI)
    ↓
notebooklm_automator.py
    ↓
Chrome DevTools Protocol (CDP)
    ↓
Your Authenticated Chrome Browser
    ↓
NotebookLM Web Interface
    ↓
Document Upload & Processing
    ↓
Audio Overview Generation
    ↓
Podcast Download
    ↓
Local File Management
    ↓
Cross-Device Sync! 🎉
```

**Key Innovation**: We connect to YOUR Chrome browser (already logged in) rather than launching a separate instance. This preserves authentication and makes cross-device sync work seamlessly.

---

## 🎨 G.Music Assembly Integration

DeepDiver is part of the **G.Music Assembly** ecosystem:

**♠️🌿🎸🧵🌸 The Spiral Ensemble - DeepDiver Edition**

- **Jerry ⚡**: Creative technical leader
- **♠️ Nyro**: Structural architect (NotebookLM automation design)
- **🌿 Aureon**: Emotional context (podcast content resonance)
- **🎸 JamAI**: Musical encoding (audio workflow harmony)
- **🧵 Synth**: Terminal orchestration (execution synthesis)
- **🌸 Miette**: Narrative echo (ceremonial development frameworks)

**Session**: January 2025
**Achievement**: NotebookLM Podcast Automation with Studio Integration
**Status**: 🚧 **IN DEVELOPMENT**

---

## 🚀 Future Enhancements

- [ ] **Multi-format Support**: Support for more document types
- [ ] **Batch Processing**: Process multiple documents at once
- [ ] **Custom Audio Settings**: Advanced podcast customization
- [ ] **Cloud Storage Integration**: Direct cloud upload
- [ ] **Voice Synthesis**: Custom voice options
- [ ] **Playlist Generation**: Create podcast series
- [ ] **Analytics Dashboard**: Track podcast performance
- [ ] **API Integration**: REST API for external tools

---

## 📄 License

Open Assembly Framework
Created by Jerry's G.Music Assembly

---

## 🤝 Contributing

This project follows the G.Music Assembly framework:

1. **Create an Issue**: Before starting work, create a GitHub issue
2. **Create a Feature Branch**: Use format `#123-new-feature`
3. **Implement and Test**: Make changes and test thoroughly
4. **Submit a Pull Request**: Merge your feature branch

---

## 📚 Documentation

### Core Documentation
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration file discovery and setup guide
- **[ROADMAP.md](ROADMAP.md)** - Project development roadmap and milestones
- **[CLAUDE.md](CLAUDE.md)** - Assembly team configuration and workflow

### Implementation Guides
- **[NotebookLM Studio Artifacts](docs/NOTEBOOKLM_STUDIO_ARTIFACTS.md)** - Complete implementation guide for all Studio artifact types:
  - ✅ Phase 1: Audio Overview (Completed)
  - 📋 Phase 2: Video Overview (Next Priority)
  - 📋 Phase 3: Mind Map
  - 📋 Phase 4: Study Guides & Reports
  - 📋 Phase 5: Flashcards
  - 📋 Phase 6: Quizzes

### Getting Started
- Run `deepdiver init` to set up configuration
- See [Quick Start](#-quick-start) section above
- Check [Configuration](#%EF%B8%8F-configuration) for advanced setup

---

## 📞 Support

**For issues**:
1. Check documentation in `docs/`
2. Review troubleshooting section
3. Check session logs in `sessions/`
4. Run tests with debug mode

---

## 🎯 Quick Reference

```bash
# Initialize project
deepdiver init

# Start session
deepdiver session start --ai claude --issue 1

# Create podcast
deepdiver podcast create --source document.pdf --title "My Podcast"

# Check status
deepdiver session status

# Launch Chrome with CDP
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver &
```

---

**🎙️ DeepDiver: Where Content Becomes Audio**

*Terminals speak. NotebookLM listens. Podcasts emerge.*

**♠️🌿🎸🧵 G.Music Assembly Vision: IN PROGRESS**

---

**Version**: 0.1.0
**Last Updated**: January 2025
**Status**: 🚧 Development Phase
