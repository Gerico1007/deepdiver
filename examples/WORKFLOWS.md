# DeepDiver + Langfuse Integration Workflows

**♠️🌿🎸🧵 G.Music Assembly Team - Example Workflows**

This guide provides practical examples of using DeepDiver with Langfuse integration.

---

## Table of Contents

1. [Basic Session with Langfuse Tracing](#basic-session-with-langfuse-tracing)
2. [Multi-Notebook Research Session](#multi-notebook-research-session)
3. [Assembly Team Prompt Usage](#assembly-team-prompt-usage)
4. [Querying Session History](#querying-session-history)
5. [Collaborative Session Workflow](#collaborative-session-workflow)
6. [Programmatic Integration](#programmatic-integration)
7. [Debugging with Traces](#debugging-with-traces)

---

## Basic Session with Langfuse Tracing

### Scenario
Create a podcast from a README file with full Langfuse observability.

### Prerequisites
```bash
# Set Langfuse credentials
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Enable Langfuse in config
# Edit deepdiver/deepdiver.yaml:
# LANGFUSE_SETTINGS:
#   enabled: true
#   verbosity: standard
```

### Workflow

**Step 1: Start Session**
```bash
$ deepdiver session start --ai claude --issue 101

✅ Session started: e24667a8-4cef-4146-9226-55731a9d5804
✅ Langfuse trace created: e24667a8-4cef-4146-9226-55731a9d5804
♠️🌿🎸🧵 Assembly Team activated
```

**What happened**:
- Session JSON created in `./sessions/current_session.json`
- Langfuse TRACE created with session metadata
- Assembly Team agents loaded

**Step 2: Create Notebook with Source**
```bash
$ deepdiver notebook create --source ./README.md

✅ Notebook created: nb-abc-123
✅ Langfuse observation added: nb-abc-123 (SPAN)
✅ Source uploaded: README.md
✅ Langfuse observation added: src-def-456 (EVENT)
```

**What happened**:
- Notebook created in NotebookLM
- SPAN observation created (notebook level)
- Source uploaded
- EVENT observation created (nested under notebook)

**Step 3: View Trace Tree**
```bash
$ deepdiver session view-trace

📊 Langfuse Trace Tree

[TRACE] Session e24667a8-4cef-4146-9226-55731a9d5804
├─ input_data:
│   ├─ session_type: deepdiver_podcast_automation
│   ├─ ai_assistant: claude
│   ├─ agents: [Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵]
│   └─ issue_number: 101
│
├─ [SPAN] Notebook: Untitled Notebook (nb-abc-123)
│   ├─ input_data:
│   │   ├─ notebook_id: nb-abc-123
│   │   ├─ notebook_url: https://notebooklm.google.com/notebook/nb-abc-123
│   │   └─ title: Untitled Notebook
│   │
│   ├─ output_data:
│   │   ├─ notebooklm_url: https://notebooklm.google.com/notebook/nb-abc-123
│   │   ├─ sources_count: 1
│   │   └─ creation_status: success
│   │
│   └─ [EVENT] Source Upload: README.md (src-def-456)
│       ├─ input_data:
│       │   ├─ filename: README.md
│       │   ├─ path: ./README.md
│       │   ├─ type: md
│       │   └─ size: 9608
│       │
│       └─ output_data:
│           ├─ source_id: src-def-456
│           ├─ upload_status: success
│           └─ added_at: 2025-11-16T10:30:45
│
└─ metadata:
    ├─ assembly_team: {leader: Jerry ⚡, ...}
    ├─ status: active
    └─ environment: notebooklm

Duration: 2.5 minutes
Notebooks: 1
Sources: 1
Status: active
```

**Step 4: End Session**
```bash
$ deepdiver session close

✅ Session ended: e24667a8-4cef-4146-9226-55731a9d5804
✅ Langfuse trace finalized with output data
```

**What happened**:
- Session status set to "ended"
- Langfuse trace updated with `output_data`:
  - Duration: 2.5 minutes
  - Notebooks created: 1
  - Sources processed: 1
  - Podcasts created: 0

---

## Multi-Notebook Research Session

### Scenario
Research project with multiple notebooks, different source types, tracked as a cohesive Langfuse trace tree.

### Workflow

**Step 1: Start Research Session**
```bash
$ deepdiver session start --ai claude --issue 202

✅ Session started: research-session-xyz
✅ Langfuse trace created: research-session-xyz
```

**Step 2: Create Topic-Specific Notebooks**

```bash
# Notebook 1: Academic Papers
$ deepdiver notebook create --title "AI Research Papers"
✅ Notebook created: nb-papers-001
✅ Langfuse observation added: nb-papers-001

$ deepdiver notebook add-source nb-papers-001 ./papers/transformer.pdf
✅ Source added: transformer.pdf
✅ Langfuse observation added: src-paper-001 (parent: nb-papers-001)

$ deepdiver notebook add-source nb-papers-001 ./papers/attention.pdf
✅ Source added: attention.pdf
✅ Langfuse observation added: src-paper-002 (parent: nb-papers-001)

# Notebook 2: Video Lectures
$ deepdiver notebook create --title "ML Lectures"
✅ Notebook created: nb-lectures-002
✅ Langfuse observation added: nb-lectures-002

$ deepdiver notebook add-source nb-lectures-002 "https://youtube.com/watch?v=..."
✅ Source added: youtube-vid
✅ Langfuse observation added: src-video-001 (parent: nb-lectures-002)

# Notebook 3: Documentation
$ deepdiver notebook create --title "Framework Docs"
✅ Notebook created: nb-docs-003
✅ Langfuse observation added: nb-docs-003

$ deepdiver notebook add-source nb-docs-003 "https://pytorch.org/docs"
✅ Source added: pytorch-docs
✅ Langfuse observation added: src-url-001 (parent: nb-docs-003)
```

**Step 3: View Comprehensive Trace**

```bash
$ deepdiver session view-trace

📊 Langfuse Trace Tree

[TRACE] Session research-session-xyz
│
├─ [SPAN] Notebook: AI Research Papers (nb-papers-001)
│   ├─ [EVENT] Source: transformer.pdf (src-paper-001)
│   └─ [EVENT] Source: attention.pdf (src-paper-002)
│
├─ [SPAN] Notebook: ML Lectures (nb-lectures-002)
│   └─ [EVENT] Source: youtube.com/... (src-video-001)
│
└─ [SPAN] Notebook: Framework Docs (nb-docs-003)
    └─ [EVENT] Source: pytorch.org/docs (src-url-001)

Duration: 15.3 minutes
Notebooks: 3
Sources: 4 (2 PDF, 1 YouTube, 1 URL)
Status: active
```

**Step 4: Query in Langfuse Dashboard**

Navigate to Langfuse web interface:
```
https://cloud.langfuse.com/traces/research-session-xyz
```

Filter observations:
- **By type**: Show only PDF sources → `metadata.source_type = "pdf"`
- **By notebook**: Show sources in "ML Lectures" → `parent_id = "nb-lectures-002"`
- **By timing**: Show operations > 5 seconds → `duration > 5000`

---

## Assembly Team Prompt Usage

### Scenario
Use Assembly Team personas to guide different aspects of the project.

### Workflow

**Step 1: Initialize Assembly Team Prompts**

```bash
# Create default prompts if not already present
$ deepdiver assembly init-prompts

✅ Created default prompt: jerry.md
✅ Created default prompt: nyro.md
✅ Created default prompt: aureon.md
✅ Created default prompt: jamai.md
✅ Created default prompt: synth.md
```

**Step 2: Get Persona Guidance**

```bash
# Consult Nyro for architectural advice
$ deepdiver assembly prompt-get nyro

♠️ Nyro - Structural Architect

Prompt Version: v1.0.0
Last Updated: 2025-11-16

You are Nyro, the Structural Architect of the Assembly Team.
Your role is to analyze technical patterns, recursive loops,
and architectural frameworks in the DeepDiver system...

[Full prompt content displayed]
```

**Step 3: Update Persona Prompt**

```bash
# Edit jerry.md with your creative direction
$ vim ./prompts/jerry.md

# (Make changes, increment version to 1.1.0)

# Sync updated prompt to Langfuse
$ deepdiver assembly prompt-sync jerry

📤 Syncing prompt to Langfuse: deepdiver-jerry (v1.1.0)
✅ Prompt synced successfully
```

**Step 4: Use Personas in Session Notes**

```bash
$ deepdiver session start --ai claude

# Add notes with persona perspectives
$ deepdiver session note "♠️ Nyro: The trace structure reveals recursive patterns in source processing"

$ deepdiver session note "🌿 Aureon: This notebook combination creates emotional resonance through contrasting sources"

$ deepdiver session note "🎸 JamAI: The workflow has a 4/4 rhythm - create, upload, process, review"
```

These notes are stored in session JSON and could be added as observations in Langfuse for full traceability.

---

## Querying Session History

### Scenario
Find all sessions where specific source types were used.

### Workflow

**Using Langfuse Web Interface**:

1. Navigate to **Traces** tab
2. Filter by metadata:
   ```
   metadata.environment = "notebooklm"
   AND metadata.deepdiver_version = "0.1.0"
   ```

3. Search observations:
   ```
   observation_type = "EVENT"
   AND metadata.source_type = "pdf"
   ```

4. Sort by:
   - Duration (longest sessions first)
   - Source count (most productive sessions)
   - Creation date (recent sessions)

**Using CLI** (future implementation):

```bash
# List all sessions with YouTube sources
$ deepdiver session query --source-type=youtube

Found 3 sessions:
1. research-session-xyz (3 YouTube sources)
2. tutorial-session-abc (1 YouTube source)
3. lecture-session-def (2 YouTube sources)

# List sessions with >5 sources
$ deepdiver session query --min-sources=5

Found 2 sessions:
1. comprehensive-project-123 (8 sources)
2. research-deep-dive-456 (12 sources)

# Find sessions by issue number
$ deepdiver session query --issue=42

Found 1 session:
1. feature-implementation-42 (Issue #42)
```

---

## Collaborative Session Workflow

### Scenario
Multiple team members contribute to the same DeepDiver session via Langfuse cloud.

### Workflow

**Team Member A (Creator)**:

```bash
# Start session
$ deepdiver session start --ai claude --issue 303
✅ Session started: collab-session-abc
✅ Langfuse trace created: collab-session-abc

# Create initial notebooks
$ deepdiver notebook create --source ./requirements.md
✅ Notebook created: nb-req-001

# Share session ID with team
$ echo "Session ID: collab-session-abc"
```

**Team Member B (Contributor)**:

```bash
# Load existing session by ID
$ deepdiver session load collab-session-abc
✅ Session loaded from Langfuse
✅ Found 1 notebook with 1 source

# Add more sources
$ deepdiver notebook add-source nb-req-001 ./architecture.md
✅ Source added: architecture.md
✅ Langfuse observation added (visible to all team members)
```

**Team Member C (Reviewer)**:

```bash
# View session trace from any device
$ deepdiver session view-trace collab-session-abc

📊 Langfuse Trace Tree

[TRACE] Session collab-session-abc
├─ [SPAN] Notebook: Requirements (nb-req-001)
│   ├─ [EVENT] Source: requirements.md (added by: Team Member A)
│   └─ [EVENT] Source: architecture.md (added by: Team Member B)
└─ metadata:
    └─ collaborators: [Team Member A, Team Member B, Team Member C]

# Add review notes
$ deepdiver session note "🌿 Aureon: The source combination creates good narrative flow"
```

**Benefits**:
- ✅ Real-time collaboration via Langfuse cloud
- ✅ All contributions tracked in trace tree
- ✅ Session accessible from any device
- ✅ Full audit trail of who added what

---

## Programmatic Integration

### Scenario
Use DeepDiver + Langfuse integration in a Python script or automated pipeline.

### Example Script: `examples/programmatic_session.py`

```python
#!/usr/bin/env python3
"""
Programmatic DeepDiver + Langfuse Integration Example
Demonstrates creating sessions, notebooks, and sources via API
"""

import asyncio
import yaml
from pathlib import Path

from deepdiver.session_tracker import SessionTracker
from deepdiver.langfuse_tracer import LangfuseTracer
from deepdiver.assembly_prompts import AssemblyPromptManager


async def main():
    """Run automated DeepDiver session with Langfuse tracing."""

    # Load configuration
    config_path = Path(__file__).parent.parent / "deepdiver" / "deepdiver.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Enable Langfuse for this session
    config['LANGFUSE_SETTINGS']['enabled'] = True
    config['LANGFUSE_SETTINGS']['verbosity'] = 'standard'

    print("♠️🌿🎸🧵 DeepDiver Programmatic Session Starting...")

    # Initialize components
    # Note: mcp_tools would be passed from Claude Code environment
    mcp_tools = None  # In real usage, this comes from MCP integration

    tracker = SessionTracker(config=config, mcp_tools=mcp_tools)
    tracer = LangfuseTracer(config=config)
    prompt_mgr = AssemblyPromptManager(config=config)

    # Get Assembly Team guidance
    print("\n⚡ Jerry's Creative Direction:")
    jerry_prompt = prompt_mgr.get_prompt('jerry')
    if jerry_prompt:
        print(jerry_prompt[:200] + "...")

    # Start session
    result = tracker.start_session(
        ai_assistant='claude',
        issue_number=404,
        agents=['Jerry ⚡', 'Nyro ♠️', 'Aureon 🌿', 'JamAI 🎸', 'Synth 🧵']
    )

    if result['success']:
        session_id = result['session_id']
        print(f"\n✅ Session started: {session_id}")

        # Create Langfuse trace (if MCP tools available)
        if mcp_tools and tracer.is_enabled():
            trace_id = await tracer.create_session_trace(
                session_data=result['session_data'],
                mcp_tools=mcp_tools
            )
            print(f"✅ Langfuse trace created: {trace_id}")

    # Simulate notebook creation
    notebook_data = {
        'id': 'nb-automated-001',
        'url': 'https://notebooklm.google.com/notebook/nb-automated-001',
        'title': 'Automated Research Notebook',
        'sources': [],
        'active': True
    }

    tracker.add_notebook(notebook_data)
    print(f"✅ Notebook created: {notebook_data['id']}")

    # Add notebook observation to trace
    if mcp_tools and tracer.is_enabled():
        obs_id = await tracer.add_notebook_observation(
            trace_id=session_id,
            notebook_data=notebook_data,
            mcp_tools=mcp_tools
        )
        print(f"✅ Notebook observation added: {obs_id}")

    # Add multiple sources
    sources = [
        {'filename': 'intro.md', 'path': './intro.md', 'type': 'md', 'size': 1024},
        {'filename': 'guide.pdf', 'path': './guide.pdf', 'type': 'pdf', 'size': 50000},
        {'filename': 'https://example.com/docs', 'path': 'https://example.com/docs', 'type': 'url', 'size': 0}
    ]

    for source in sources:
        # Add to session tracker
        success = tracker.add_source_to_notebook('nb-automated-001', source)

        if success:
            print(f"✅ Source added: {source['filename']}")

            # Add source observation to trace
            if mcp_tools and tracer.is_enabled():
                source_obs_id = await tracer.add_source_observation(
                    trace_id=session_id,
                    notebook_id='nb-automated-001',
                    source_data=source,
                    mcp_tools=mcp_tools
                )
                print(f"✅ Source observation added: {source_obs_id}")

    # Get session status
    status = tracker.get_session_status()
    print(f"\n📊 Session Status:")
    print(f"   Notebooks: {status['notebooks_count']}")
    print(f"   Sources: {sum(len(nb.get('sources', [])) for nb in tracker.list_notebooks())}")
    print(f"   Duration: {status['created_at']}")

    # End session
    tracker.end_session()
    print("\n✅ Session ended")

    # Finalize trace
    if mcp_tools and tracer.is_enabled():
        final_session = tracker.current_session or result['session_data']
        await tracer.finalize_session_trace(
            trace_id=session_id,
            session_data=final_session,
            mcp_tools=mcp_tools
        )
        print("✅ Langfuse trace finalized")

    print("\n♠️🌿🎸🧵 Session complete!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Run the script**:
```bash
$ python examples/programmatic_session.py

♠️🌿🎸🧵 DeepDiver Programmatic Session Starting...

⚡ Jerry's Creative Direction:
---
name: Jerry ⚡
role: Creative Technical Leader
...

✅ Session started: auto-session-xyz
✅ Langfuse trace created: auto-session-xyz
✅ Notebook created: nb-automated-001
✅ Notebook observation added: nb-automated-001
✅ Source added: intro.md
✅ Source observation added: src-001
✅ Source added: guide.pdf
✅ Source observation added: src-002
✅ Source added: https://example.com/docs
✅ Source observation added: src-003

📊 Session Status:
   Notebooks: 1
   Sources: 3
   Duration: 2025-11-16T...

✅ Session ended
✅ Langfuse trace finalized

♠️🌿🎸🧵 Session complete!
```

---

## Debugging with Traces

### Scenario
Use Langfuse traces to debug why a notebook creation failed.

### Workflow

**Step 1: Attempt Operation (Fails)**

```bash
$ deepdiver notebook create --source ./missing-file.pdf

❌ Error: File not found: ./missing-file.pdf
Session trace updated with error observation
```

**Step 2: View Trace with Error Context**

```bash
$ deepdiver session view-trace --show-errors

📊 Langfuse Trace Tree (with errors)

[TRACE] Session debug-session-001
│
└─ [SPAN] Notebook: Untitled (nb-failed-001)
    ├─ status: failed
    ├─ error: "File not found: ./missing-file.pdf"
    │
    └─ [EVENT] Source Upload: missing-file.pdf (src-failed-001)
        ├─ input_data:
        │   ├─ filename: missing-file.pdf
        │   └─ path: ./missing-file.pdf
        │
        └─ output_data:
            ├─ upload_status: error
            ├─ error_type: FileNotFoundError
            ├─ error_message: "File not found: ./missing-file.pdf"
            └─ timestamp: 2025-11-16T11:45:00
```

**Step 3: Analyze in Langfuse Dashboard**

Navigate to trace:
```
https://cloud.langfuse.com/traces/debug-session-001
```

Benefits:
- ✅ See exact input that caused error
- ✅ View timing of failure
- ✅ Identify patterns across multiple failures
- ✅ Compare failed vs successful operations

**Step 4: Fix and Retry**

```bash
# Fix the file path
$ deepdiver notebook create --source ./correct-path/file.pdf

✅ Notebook created: nb-success-002
✅ Source uploaded: file.pdf
✅ Observation shows: upload_status: success
```

Compare traces to see what changed between failure and success.

---

## Assembly Team Workflow Integration

### Complete Session with Persona Guidance

```bash
# Start with Jerry's creative direction
$ deepdiver assembly prompt-get jerry | head -20
⚡ Jerry - Creative Technical Leader
[Creative vision guidance...]

# Start session
$ deepdiver session start --ai claude --issue 505
✅ Session started: assembly-session-xyz

# Get Nyro's structural advice
$ deepdiver assembly prompt-get nyro | grep -A5 "Notebook Creation"
♠️ Nyro: For notebook creation, consider hierarchical organization...

# Create structured notebooks based on Nyro's guidance
$ deepdiver notebook create --title "Foundation Layer"
$ deepdiver notebook create --title "Application Layer"
$ deepdiver notebook create --title "Interface Layer"

# Get Aureon's emotional perspective
$ deepdiver assembly prompt-get aureon | grep -A5 "Content Curation"
🌿 Aureon: Evaluate source material for emotional depth...

# Curate sources based on Aureon's guidance
$ deepdiver notebook add-source foundation-nb ./emotional-resonant-source.md

# Get JamAI's rhythmic analysis
$ deepdiver assembly prompt-get jamai | grep -A5 "Workflow Rhythm"
🎸 JamAI: This workflow has a 4/4 rhythm...

# Follow JamAI's pacing recommendations
# (Pause between major operations for natural flow)

# Get Synth's execution clarity
$ deepdiver assembly prompt-get synth | grep -A5 "Command Orchestration"
🧵 Synth: Execute in this sequence...

# Follow Synth's orchestration
$ deepdiver session close
✅ Session ended with Assembly Team guidance integrated
```

---

## Summary

These workflows demonstrate:

1. ✅ **Basic Langfuse tracing** - Session → Notebook → Source hierarchy
2. ✅ **Multi-notebook sessions** - Complex research projects
3. ✅ **Assembly Team prompts** - Persona-guided workflows
4. ✅ **History querying** - Finding past sessions
5. ✅ **Collaboration** - Multi-user sessions via cloud
6. ✅ **Programmatic usage** - Python API integration
7. ✅ **Debugging** - Error tracing and analysis

**♠️🌿🎸🧵⚡ Assembly Team Unity: Where workflows become harmonious creative journeys.**

---

## Next Steps

See also:
- `LANGFUSE_ARCHITECTURE.md` - Technical architecture details
- `examples/programmatic_session.py` - Complete Python example
- `examples/cli_examples.sh` - Shell script examples
- `examples/test_integration.py` - Integration test suite
