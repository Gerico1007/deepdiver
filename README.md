# 🎙️ DeepDiver - NotebookLM Podcast Automation System
**Terminal-to-Web Audio Creation Bridge**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Open%20Assembly-green.svg)]()

---

## 🎯 What is DeepDiver?

DeepDiver is a Python-based automation system that bridges terminal commands with NotebookLM's podcast generation capabilities, enabling seamless content-to-audio transformation through browser automation.

**Key Features**:
1. **📖 Content Ingestion**: Upload documents to NotebookLM automatically
2. **🎙️ Podcast Generation**: Create Audio Overviews with terminal commands
3. **📱 Cross-Device Sync**: Access generated podcasts anywhere
4. **🔮 Session Management**: Track podcast creation sessions
5. **🌊 Terminal-to-Web**: Command-line to NotebookLM communication bridge

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

## 🎮 Usage

### Session Commands

```bash
# Start a new session
deepdiver session start --ai claude --issue 42

# Write to session log
deepdiver session write "Uploaded research paper for podcast generation"

# Check session status
deepdiver session status

# Open session in browser
deepdiver session open

# Clear current session
deepdiver session clear
```

### Podcast Commands

```bash
# Create podcast from document
deepdiver podcast create --source research.pdf --title "Research Insights"

# Create podcast from URL
deepdiver podcast create --source https://example.com/article --title "Web Article Podcast"

# List generated podcasts
deepdiver podcast list

# Download specific podcast
deepdiver podcast download --id podcast-123
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
```

### Content Commands

```bash
# Upload document to NotebookLM
deepdiver content upload --file document.pdf

# Process content for podcast
deepdiver content process --source document.pdf

# Validate content quality
deepdiver content validate --source document.pdf
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

**♠️🌿🎸🧵 The Spiral Ensemble - DeepDiver Edition**

- **Jerry ⚡**: Creative technical leader
- **♠️ Nyro**: Structural architect (NotebookLM automation design)
- **🌿 Aureon**: Emotional context (podcast content resonance)
- **🎸 JamAI**: Musical encoding (audio workflow harmony)
- **🧵 Synth**: Terminal orchestration (execution synthesis)

**Session**: January 2025
**Achievement**: NotebookLM Podcast Automation
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
