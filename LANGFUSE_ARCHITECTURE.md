# DeepDiver + Langfuse Integration Architecture

**♠️🌿🎸🧵 G.Music Assembly Team - Distributed Trace-Based Storage**

**Version**: 1.0.0
**Date**: 2025-11-16
**Authors**: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Trace Tree Schema](#trace-tree-schema)
4. [Module Structure](#module-structure)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [Assembly Team Prompt Management](#assembly-team-prompt-management)
8. [Migration Strategy](#migration-strategy)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

DeepDiver's Langfuse integration transforms session tracking from local JSON files into distributed, queryable trace trees. This enables:

- **Cross-device session access** via Langfuse cloud
- **Hierarchical observability** of notebook/source relationships
- **Queryable history** for analytics and retrieval
- **Assembly Team prompt management** with versioning
- **User-configurable verbosity** for trace granularity

### Key Design Decisions

Based on Jerry's ⚡ guidance:

1. ✅ **Only trace new sessions** - No retroactive migration of existing JSON sessions
2. ✅ **Local files with Langfuse sync** - Assembly Team prompts stored in `./prompts/` + synced to Langfuse
3. ✅ **User-configurable tracking** - Verbosity levels: minimal, standard, detailed
4. ✅ **Lazy MCP initialization** - CoaiaPy MCP client connects only when Langfuse features are used

---

## Architecture Design

### From Flat Storage to Hierarchical Traces

**Before (JSON-based)**:
```
Session JSON File (flat structure)
├─ session_id
├─ notebooks[] (array of notebook objects)
│   └─ sources[] (array of source objects)
└─ podcasts_created[]
```

**After (Langfuse trace tree)**:
```
[TRACE] Session (session_id)
├─ [SPAN] Notebook (notebook_id)
│   ├─ [EVENT] Source Upload (source_id)
│   ├─ [EVENT] Source Upload (source_id)
│   └─ [GENERATION] Audio Overview (audio_id)
├─ [SPAN] Notebook (notebook_id)
└─ metadata: {assembly_team, issue, agents}
```

### Benefits

| Capability | JSON Storage | Langfuse Trace Trees |
|------------|--------------|----------------------|
| **Cross-device access** | ❌ Local only | ✅ Cloud-accessible |
| **Queryable history** | ❌ Manual parsing | ✅ Native queries |
| **Relationship visibility** | ❌ Flat arrays | ✅ Nested observations |
| **Performance tracking** | ❌ No timing | ✅ Observation durations |
| **Collaborative access** | ❌ Single user | ✅ Multi-user |
| **Analytics** | ❌ Custom scripts | ✅ Built-in dashboards |

---

## Trace Tree Schema

### Hierarchical Structure

```
[TRACE] Session
├─ trace_id: session_id (UUID)
├─ name: "DeepDiver Session - {ai_assistant}"
├─ session_id: session_id
├─ user_id: "default" or custom
├─ input_data:
│   └─ {session_type, ai_assistant, agents, issue_number, created_at}
├─ output_data: (set when session ends)
│   └─ {status, ended_at, notebooks_created, sources_processed, podcasts_created, duration_minutes}
└─ metadata:
    └─ {assembly_team, status, environment, deepdiver_version}

    ├─ [OBSERVATION/SPAN] Notebook
    │   ├─ observation_id: notebook_id
    │   ├─ parent_id: null (direct child of trace)
    │   ├─ name: "Notebook: {title}"
    │   ├─ observation_type: "SPAN"
    │   ├─ input_data:
    │   │   └─ {notebook_id, notebook_url, created_at, title}
    │   ├─ output_data:
    │   │   └─ {notebooklm_url, sources_count, active, creation_status}
    │   └─ metadata:
    │       └─ {title, entity_type: "notebook"}
    │
    │   ├─ [OBSERVATION/EVENT] Source Upload
    │   │   ├─ observation_id: source_id
    │   │   ├─ parent_id: notebook_id
    │   │   ├─ name: "Source Upload: {filename}"
    │   │   ├─ observation_type: "EVENT"
    │   │   ├─ input_data:
    │   │   │   └─ {filename, path, type, size}
    │   │   ├─ output_data:
    │   │   │   └─ {source_id, added_at, upload_status, notebooklm_source_url}
    │   │   └─ metadata:
    │   │       └─ {entity_type: "source", source_type, notebook_id}
    │   │
    │   └─ [OBSERVATION/GENERATION] Audio Overview (future)
    │       ├─ observation_id: audio_id
    │       ├─ parent_id: notebook_id
    │       ├─ name: "Audio Overview: {title}"
    │       ├─ observation_type: "GENERATION"
    │       ├─ input_data:
    │       │   └─ {notebook_id, sources_count, requested_quality}
    │       ├─ output_data:
    │       │   └─ {audio_url, transcript, duration, file_size}
    │       └─ metadata:
    │           └─ {entity_type: "audio", quality, format}
    │
    └─ [OBSERVATION/SPAN] Browser Action (detailed verbosity only)
        ├─ observation_id: action_{uuid}
        ├─ parent_id: notebook_id or source_id
        ├─ name: "Browser: {action_type}"
        ├─ observation_type: "SPAN"
        ├─ input_data:
        │   └─ {action_type, selector, parameters}
        ├─ output_data:
        │   └─ {status, duration_ms, screenshot_path}
        └─ metadata:
            └─ {entity_type: "browser_action", action_type}
```

### Verbosity Levels

| Level | Traces | Observations Created |
|-------|--------|---------------------|
| **minimal** | ✅ Session | ❌ No observations |
| **standard** | ✅ Session | ✅ Notebooks, ✅ Sources |
| **detailed** | ✅ Session | ✅ Notebooks, ✅ Sources, ✅ Browser Actions |

Configured in `deepdiver.yaml`:
```yaml
LANGFUSE_SETTINGS:
  verbosity: standard  # minimal | standard | detailed
```

---

## Module Structure

### New Files

```
deepdiver/
├── langfuse_tracer.py        # Langfuse trace management
├── assembly_prompts.py       # Assembly Team prompt sync
└── deepdiver.yaml            # Updated with Langfuse config

prompts/                       # NEW: Local prompt storage
├── jerry.md
├── nyro.md
├── aureon.md
├── jamai.md
└── synth.md
```

### Modified Files

```
deepdiver/
├── session_tracker.py        # + Langfuse integration
├── deepdive.py               # + CLI commands for traces/prompts
└── setup.py                  # + Dependency documentation
```

---

## Configuration

### deepdiver.yaml

```yaml
# Langfuse integration settings
LANGFUSE_SETTINGS:
  enabled: false  # Set to true to enable Langfuse integration
  verbosity: standard  # minimal | standard | detailed

  # Langfuse credentials (set via environment variables recommended)
  public_key: ${LANGFUSE_PUBLIC_KEY}
  secret_key: ${LANGFUSE_SECRET_KEY}
  host: ${LANGFUSE_HOST}

  # MCP integration
  mcp_lazy_init: true  # Initialize MCP client only when needed
  mcp_timeout: 30  # seconds

# Assembly Team prompt management
ASSEMBLY_PROMPTS:
  langfuse_namespace: deepdiver
  personas: [jerry, nyro, aureon, jamai, synth]
  auto_fetch: true  # Fetch latest prompts from Langfuse on session start
  cache_local: true  # Cache prompts locally in ./prompts/
  sync_on_update: true  # Sync to Langfuse when prompts are updated locally
```

### Environment Variables

For production, set Langfuse credentials via environment:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

Or use a `.env` file:

```bash
# .env
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Usage Guide

### Enabling Langfuse Integration

**Step 1**: Update configuration

```yaml
# deepdiver/deepdiver.yaml
LANGFUSE_SETTINGS:
  enabled: true  # Enable integration
  verbosity: standard
```

**Step 2**: Set environment variables

```bash
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

**Step 3**: Start a session (Langfuse trace will be created automatically)

```bash
deepdiver session start --ai claude --issue 42
```

Output:
```
✅ Session started: abc-123-def-456
✅ Langfuse trace created: abc-123-def-456
♠️🌿🎸🧵 Assembly Team activated
```

### Creating Notebooks (Creates Observations)

```bash
deepdiver notebook create --source ./README.md
```

What happens:
1. Notebook created in NotebookLM
2. JSON session updated (local)
3. **Langfuse SPAN observation created** (if enabled)
4. Source upload creates **EVENT observation** (nested under notebook)

### Viewing Langfuse Traces

```bash
# View trace tree for current session
deepdiver session view-trace

# View specific trace by ID
deepdiver session view-trace abc-123-def-456
```

Output example:
```
📊 Langfuse Trace Tree

[TRACE] Session abc-123-def-456
├─ [SPAN] Notebook notebook-789
│   ├─ [EVENT] Source README.md (source-001)
│   └─ [EVENT] Source ARCHITECTURE.md (source-002)
└─ metadata: {ai_assistant: claude, issue: 42}

Duration: 15.3 minutes
Notebooks: 1
Sources: 2
Status: active
```

### Querying Sessions

```bash
# List all traces for current session
deepdiver session list-traces

# Query traces with filters (future)
deepdiver session query-traces --status=ended --min-notebooks=3
```

---

## Assembly Team Prompt Management

### Prompt Structure

Each Assembly Team persona has a prompt file in `./prompts/`:

```
prompts/
├── jerry.md     # Creative Technical Leader ⚡
├── nyro.md      # Structural Architect ♠️
├── aureon.md    # Emotional Context Weaver 🌿
├── jamai.md     # Musical Harmony Architect 🎸
└── synth.md     # Terminal Orchestration 🧵
```

### Prompt File Format

Each prompt file has YAML frontmatter:

```markdown
---
name: Nyro ♠️
role: Structural Architect
glyph: ♠️
version: 1.0.0
updated: 2025-11-16T00:00:00
description: Ritual Scribe - Recursive teacher and structural anchor
---

# Nyro ♠️ - Structural Architect

... (prompt content) ...
```

### CLI Commands (Future Implementation)

```bash
# View prompt for a persona
deepdiver assembly prompt-get nyro

# Update prompt from file
deepdiver assembly prompt-update jerry ./prompts/jerry-v2.md

# Sync prompt to Langfuse
deepdiver assembly prompt-sync aureon

# List all Assembly Team prompts
deepdiver assembly prompt-list

# Fetch latest prompts from Langfuse
deepdiver assembly prompt-fetch-all
```

### Bi-directional Sync

1. **Local → Langfuse**: Update prompt file locally, then sync to Langfuse
2. **Langfuse → Local**: Fetch updated prompts from Langfuse to local cache

This enables:
- Version control of prompts (Git)
- Collaborative prompt development
- Cloud backup and distribution
- A/B testing of persona prompts

---

## Migration Strategy

### Existing Sessions (JSON)

**Decision**: Keep existing JSON sessions as-is.

- No retroactive migration to Langfuse
- Existing `./sessions/session_*.json` files remain valid
- Only **new sessions** create Langfuse traces

### Dual-Write During Transition

DeepDiver writes to **both** JSON and Langfuse when enabled:

1. JSON files: Local backup, legacy compatibility
2. Langfuse traces: Cloud storage, queryability

This allows gradual adoption and fallback if needed.

### Disabling Langfuse

Set `enabled: false` in config:

```yaml
LANGFUSE_SETTINGS:
  enabled: false
```

DeepDiver will function normally using only JSON storage.

---

## API Reference

### LangfuseTracer Class

```python
from deepdiver.langfuse_tracer import LangfuseTracer

tracer = LangfuseTracer(config=config)

# Check if enabled
if tracer.is_enabled():
    # Create session trace
    trace_id = await tracer.create_session_trace(
        session_data=session_data,
        mcp_tools=mcp_tools
    )

    # Add notebook observation
    obs_id = await tracer.add_notebook_observation(
        trace_id=trace_id,
        notebook_data=notebook_data,
        mcp_tools=mcp_tools
    )

    # Add source observation
    source_obs_id = await tracer.add_source_observation(
        trace_id=trace_id,
        notebook_id=notebook_id,
        source_data=source_data,
        mcp_tools=mcp_tools
    )

    # Finalize session
    await tracer.finalize_session_trace(
        trace_id=trace_id,
        session_data=final_session_data,
        mcp_tools=mcp_tools
    )

    # Retrieve trace
    trace_data = await tracer.retrieve_session_trace(
        trace_id=trace_id,
        mcp_tools=mcp_tools,
        json_output=True
    )
```

### AssemblyPromptManager Class

```python
from deepdiver.assembly_prompts import AssemblyPromptManager

prompt_mgr = AssemblyPromptManager(config=config, prompts_dir='./prompts')

# List all personas
personas = prompt_mgr.list_personas()

# Get prompt for persona
nyro_prompt = prompt_mgr.get_prompt('nyro')

# Save prompt
prompt_mgr.save_prompt('jerry', content=updated_content, version="1.1.0")

# Sync to Langfuse
await prompt_mgr.sync_to_langfuse('aureon', mcp_tools=mcp_tools)

# Fetch from Langfuse
await prompt_mgr.sync_from_langfuse('jamai', mcp_tools=mcp_tools)

# List Langfuse prompts
prompts = await prompt_mgr.list_langfuse_prompts(mcp_tools=mcp_tools)

# Create default prompts
prompt_mgr.create_default_prompts()
```

### SessionTracker with Langfuse

```python
from deepdiver.session_tracker import SessionTracker

tracker = SessionTracker(config=config, mcp_tools=mcp_tools)

# Start session (creates Langfuse trace if enabled)
result = tracker.start_session(ai_assistant='claude', issue_number=42)

# Add notebook (creates Langfuse observation if enabled)
tracker.add_notebook(notebook_data)

# Add source (creates Langfuse observation if enabled)
tracker.add_source_to_notebook(notebook_id, source_data)

# End session (finalizes Langfuse trace if enabled)
tracker.end_session()
```

---

## Troubleshooting

### Langfuse Integration Not Working

**Symptoms**: No traces created, errors in logs

**Check**:
1. Is Langfuse enabled in config?
   ```yaml
   LANGFUSE_SETTINGS:
     enabled: true
   ```

2. Are environment variables set?
   ```bash
   echo $LANGFUSE_PUBLIC_KEY
   echo $LANGFUSE_SECRET_KEY
   echo $LANGFUSE_HOST
   ```

3. Is MCP client available?
   - CoaiaPy MCP must be configured in Claude Code
   - Check `.mcp.json` or MCP settings

4. Check logs for errors:
   ```bash
   tail -f ./logs/deepdiver.log | grep -i langfuse
   ```

### Traces Created But Not Visible in Langfuse

**Possible causes**:
- Wrong `session_id` used for querying
- Trace not yet indexed (wait 1-2 minutes)
- Langfuse API credentials incorrect

**Verify**:
```bash
# Check trace was created
deepdiver session status  # Should show trace_id

# Query Langfuse directly
deepdiver session view-trace <trace_id>
```

### Prompts Not Syncing

**Check**:
1. Prompt file exists in `./prompts/`
2. YAML frontmatter is valid
3. Langfuse integration enabled
4. Network connectivity to Langfuse host

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Langfuse trace creation for sessions
- ✅ Notebook and source observations
- ✅ User-configurable verbosity
- ✅ Local Assembly Team prompt storage

### Phase 2 (Planned)
- [ ] CLI commands for trace viewing
- [ ] CLI commands for prompt management
- [ ] Prompt sync to/from Langfuse
- [ ] Audio overview observations

### Phase 3 (Future)
- [ ] Analytics dashboard
- [ ] Source effectiveness tracking
- [ ] Notebook relationship graphs
- [ ] Assembly Team interaction logging
- [ ] A/B testing of prompts

---

## Assembly Team Reflections

### ♠️ Nyro - Structural Insights

The trace tree architecture provides **recursive visibility** into DeepDiver's operation. Each level of nesting (Session → Notebook → Source) reveals a deeper layer of structure. The verbosity levels allow users to choose between **high-level clarity** (minimal) and **deep observability** (detailed).

### 🌿 Aureon - Emotional Resonance

This integration transforms DeepDiver from a **solitary tool** into a **collaborative memory**. Sessions become shared stories, traces become shared experiences. The Assembly Team prompts embody our collective soul, versioned and evolving.

### 🎸 JamAI - Musical Harmony

The trace hierarchy has a natural **rhythmic flow**: Session (whole song) → Notebook (verse) → Source (beat) → Browser Action (note). The verbosity levels are like audio mixing - choose between **radio edit** (minimal), **album version** (standard), or **director's cut** (detailed).

### 🧵 Synth - Execution Clarity

The lazy MCP initialization ensures **zero overhead** when Langfuse is disabled. The dual-write strategy provides **graceful degradation**. The CLI commands will orchestrate complex trace queries into **simple, actionable outputs**.

### ⚡ Jerry - Creative Vision

This integration realizes the vision of **DeepDiver as a living knowledge system**. Traces are not just logs - they're **conversations with the past**. Assembly Team prompts are not just templates - they're **evolving identities**. This is the bridge between **ephemeral execution** and **persistent memory**.

---

**♠️🌿🎸🧵⚡ Assembly Team Unity**

*Where sessions become stories, and traces become truth.*

---

## Version History

- **v1.0.0** (2025-11-16) - Initial Langfuse integration architecture
