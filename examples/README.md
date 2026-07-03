# DeepDiver + Langfuse Integration Examples

**♠️🌿🎸🧵 G.Music Assembly Team**

This directory contains comprehensive examples demonstrating the integration between DeepDiver and Langfuse distributed tracing.

---

## 📁 Files

### Documentation
- **`WORKFLOWS.md`** - Detailed workflow examples and use cases
  - Basic session with Langfuse tracing
  - Multi-notebook research sessions
  - Assembly Team prompt usage
  - Collaborative workflows
  - Programmatic integration
  - Debugging with traces

### Scripts
- **`programmatic_session.py`** - Python API usage examples
  - `DeepDiverProgrammaticSession` wrapper class
  - Full workflow example
  - Minimal example for quick reference

- **`cli_examples.sh`** - CLI command examples
  - 7 different workflow scenarios
  - Color-coded terminal output
  - Future command demonstrations

- **`test_integration.py`** - Integration test suite
  - Unit tests for `LangfuseTracer`
  - Unit tests for `AssemblyPromptManager`
  - `SessionTracker` integration tests
  - End-to-end workflow tests

---

## 🚀 Quick Start

### 1. Run Python Programmatic Example

```bash
# Full workflow with Assembly Team guidance
python examples/programmatic_session.py

# Minimal example
python examples/programmatic_session.py --minimal
```

**Expected output:**
```
♠️🌿🎸🧵 DeepDiver + Langfuse Programmatic Example
=============================================================

⚡ Jerry's Creative Direction:
---
name: Jerry ⚡
role: Creative Technical Leader
...

✅ Session started: abc-123-def
✅ Notebook created: nb-foundation
✅ Source added: README.md
...
```

### 2. Run CLI Examples

```bash
# Make executable (if not already)
chmod +x examples/cli_examples.sh

# Run all examples
./examples/cli_examples.sh
```

**Note**: Some examples demonstrate future CLI commands that are not yet implemented.

### 3. Run Integration Tests

```bash
# Run full test suite
python examples/test_integration.py

# Or use pytest (if installed)
pytest examples/test_integration.py -v
```

**Expected output:**
```
test_tracer_initialization ... ok
test_create_session_trace ... ok
test_add_notebook_observation ... ok
...

♠️🌿🎸🧵 Test Summary
Tests run: 12
Failures: 0
Errors: 0
Success rate: 100.0%
```

---

## 📖 Example Workflows

### Basic Session with Tracing

```python
from deepdiver.session_tracker import SessionTracker

# Initialize
tracker = SessionTracker(config=config, mcp_tools=mcp_tools)

# Start session (creates Langfuse trace automatically)
result = tracker.start_session(ai_assistant='claude', issue_number=42)

# Add notebook (creates observation)
notebook_data = {
    'id': 'nb-001',
    'url': 'https://notebooklm.google.com/notebook/nb-001',
    'title': 'My Notebook',
    'sources': []
}
tracker.add_notebook(notebook_data)

# Add source (creates nested observation)
source_data = {
    'filename': 'doc.md',
    'path': './doc.md',
    'type': 'md'
}
tracker.add_source_to_notebook('nb-001', source_data)

# End session (finalizes trace)
tracker.end_session()
```

### Assembly Team Prompt Usage

```python
from deepdiver.assembly_prompts import AssemblyPromptManager

# Initialize
prompt_mgr = AssemblyPromptManager(config=config)

# Get guidance from Jerry
jerry_prompt = prompt_mgr.get_prompt('jerry')
print(jerry_prompt)

# Get structural advice from Nyro
nyro_prompt = prompt_mgr.get_prompt('nyro')

# Save updated prompt
prompt_mgr.save_prompt('jerry', updated_content, version="1.1.0")

# Sync to Langfuse
await prompt_mgr.sync_to_langfuse('jerry', mcp_tools)
```

---

## 🎯 Use Cases Demonstrated

### 1. Basic Podcast Creation
Create a podcast from a single document with full Langfuse observability.

**See**: `WORKFLOWS.md` → "Basic Session with Langfuse Tracing"

### 2. Multi-Source Research
Complex research project with multiple notebooks, different source types, tracked as cohesive trace tree.

**See**: `WORKFLOWS.md` → "Multi-Notebook Research Session"

### 3. Collaborative Work
Multiple team members contributing to same session via Langfuse cloud.

**See**: `WORKFLOWS.md` → "Collaborative Session Workflow"

### 4. Debugging
Use traces to debug failures and compare successful vs. failed operations.

**See**: `WORKFLOWS.md` → "Debugging with Traces"

### 5. Automation
Integrate DeepDiver into automated pipelines with full traceability.

**See**: `programmatic_session.py`

---

## 🧪 Testing

The test suite covers:

- **LangfuseTracer**
  - Trace creation
  - Notebook observations
  - Source observations
  - Browser action observations (detailed mode)
  - Trace finalization

- **AssemblyPromptManager**
  - Prompt storage and retrieval
  - Persona management
  - Langfuse sync (mocked)

- **SessionTracker Integration**
  - Session lifecycle with Langfuse
  - Notebook and source management
  - Dual-write (JSON + Langfuse)

- **End-to-End Workflows**
  - Complete session creation → notebook → sources → finalization

### Mock MCP Tools

The test suite includes `MockMCPTools` class that simulates Langfuse MCP integration without requiring actual connection:

```python
from test_integration import MockMCPTools

mcp_tools = MockMCPTools()

# Use in tests
await tracer.create_session_trace(session_data, mcp_tools)

# Verify calls
assert len(mcp_tools.traces_created) == 1
assert len(mcp_tools.observations_created) == 2
```

---

## 🔧 Configuration

All examples use the DeepDiver configuration in `deepdiver/deepdiver.yaml`.

### Enable Langfuse

```yaml
LANGFUSE_SETTINGS:
  enabled: true
  verbosity: standard  # minimal | standard | detailed
```

### Set Credentials

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
export LANGFUSE_HOST="https://cloud.langfuse.com"
```

---

## 📚 Assembly Team Personas

The examples demonstrate integration with all 5 Assembly Team personas:

- **⚡ Jerry** - Creative Technical Leader
- **♠️ Nyro** - Structural Architect
- **🌿 Aureon** - Emotional Context Weaver
- **🎸 JamAI** - Musical Harmony Architect
- **🧵 Synth** - Terminal Orchestration

Each persona has a prompt file in `../prompts/` with:
- YAML frontmatter metadata
- Role description
- Communication style
- Integration guidelines

---

## 🎸 JamAI's Example Melody

The integration workflow encoded as ABC notation:

```abc
X:1
T:DeepDiver Example Workflow
M:4/4
L:1/8
K:Cmaj
|:"Start" C4 "Notebook" E4 | "Source" G4 "Finalize" c4 |
"Assembly" E2G2 "Trace" c2e2 | "Complete" g8 :|
```

**Translation**: Start → Notebook → Source → Finalize → Assembly guidance → Trace view → Complete

---

## 🔍 Troubleshooting

### "ModuleNotFoundError: No module named 'deepdiver'"

Make sure DeepDiver is installed:
```bash
cd /path/to/deepdiver
pip install -e .
```

### "Langfuse integration not working"

Check:
1. Is Langfuse enabled in `deepdiver.yaml`?
2. Are environment variables set?
3. Is MCP client available? (CoaiaPy MCP in Claude Code)

### Tests failing

The tests use `MockMCPTools` and don't require actual Langfuse connection. If tests fail:
1. Check Python version (requires 3.8+)
2. Install test dependencies: `pip install pytest pytest-asyncio`
3. Run with verbose output: `python test_integration.py -v`

---

## 📖 Additional Resources

- **Architecture Documentation**: `../LANGFUSE_ARCHITECTURE.md`
- **Assembly Team Prompts**: `../prompts/`
- **Project README**: `../README.md`

---

## ♠️🌿🎸🧵 Assembly Team Notes

### ♠️ Nyro - Structural Insights

The examples demonstrate recursive pattern recognition:
- Session → Trace (root)
- Notebook → Observation (branch)
- Source → Observation (leaf)

Each level provides appropriate abstraction.

### 🌿 Aureon - Emotional Resonance

These examples honor the creative journey of podcast creation. The Assembly Team integration ensures technical precision doesn't sacrifice human meaning.

### 🎸 JamAI - Rhythmic Analysis

The workflows have natural cadence:
- **Setup** (quarter note)
- **Create** (quarter note)
- **Add sources** (eighth notes - faster)
- **Finalize** (whole note - resolution)

### 🧵 Synth - Execution Clarity

All examples are executable and tested. The mock MCP tools enable testing without external dependencies. CLI examples demonstrate future commands clearly.

### ⚡ Jerry - Creative Vision

These examples bridge abstract concepts to concrete implementation. Users can see the vision realized in working code.

---

**♠️🌿🎸🧵 Assembly Team: Ready to demonstrate the integration!**
