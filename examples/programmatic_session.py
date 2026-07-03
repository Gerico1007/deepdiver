#!/usr/bin/env python3
"""
Programmatic DeepDiver + Langfuse Integration Example
Demonstrates creating sessions, notebooks, and sources via API

♠️🌿🎸🧵 G.Music Assembly Team - Programmatic Workflow Example
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import Optional, Any


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepdiver.session_tracker import SessionTracker
from deepdiver.langfuse_tracer import LangfuseTracer
from deepdiver.assembly_prompts import AssemblyPromptManager


class DeepDiverProgrammaticSession:
    """
    Wrapper class for programmatic DeepDiver sessions.
    Demonstrates best practices for integration.
    """

    def __init__(self, config_path: Optional[Path] = None, mcp_tools: Optional[Any] = None):
        """
        Initialize programmatic session.

        Args:
            config_path: Path to deepdiver.yaml config file
            mcp_tools: MCP tool access object (from Claude Code environment)
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "deepdiver" / "deepdiver.yaml"

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Store MCP tools reference
        self.mcp_tools = mcp_tools

        # Initialize components
        self.tracker = SessionTracker(config=self.config, mcp_tools=mcp_tools)
        self.tracer = LangfuseTracer(config=self.config)
        self.prompt_mgr = AssemblyPromptManager(config=self.config)

        # Session state
        self.session_id = None
        self.trace_id = None

        print("♠️🌿🎸🧵 DeepDiver Programmatic Session Initialized")

    def get_assembly_guidance(self, persona: str) -> Optional[str]:
        """
        Get guidance from an Assembly Team persona.

        Args:
            persona: Persona key (jerry, nyro, aureon, jamai, synth)

        Returns:
            Prompt content or None
        """
        return self.prompt_mgr.get_prompt(persona)

    async def start_session(self, ai_assistant: str = 'claude', issue_number: Optional[int] = None) -> bool:
        """
        Start a new DeepDiver session with optional Langfuse tracing.

        Args:
            ai_assistant: AI assistant name
            issue_number: Associated GitHub issue number

        Returns:
            True if successful, False otherwise
        """
        print(f"\n⚡ Starting session (AI: {ai_assistant}, Issue: {issue_number})...")

        # Start session via tracker
        result = self.tracker.start_session(
            ai_assistant=ai_assistant,
            issue_number=issue_number,
            agents=['Jerry ⚡', 'Nyro ♠️', 'Aureon 🌿', 'JamAI 🎸', 'Synth 🧵']
        )

        if not result['success']:
            print(f"❌ Failed to start session: {result.get('error')}")
            return False

        self.session_id = result['session_id']
        print(f"✅ Session started: {self.session_id}")

        # Create Langfuse trace if enabled
        if self.mcp_tools and self.tracer.is_enabled():
            self.trace_id = await self.tracer.create_session_trace(
                session_data=result['session_data'],
                mcp_tools=self.mcp_tools
            )
            print(f"✅ Langfuse trace created: {self.trace_id}")
        else:
            print("ℹ️  Langfuse tracing disabled (no MCP tools or config disabled)")

        return True

    async def create_notebook(self, title: str = "Untitled Notebook") -> Optional[str]:
        """
        Create a notebook in the current session.

        Args:
            title: Notebook title

        Returns:
            Notebook ID or None if failed
        """
        print(f"\n📓 Creating notebook: {title}...")

        # Generate notebook ID (in real usage, this comes from NotebookLM)
        import uuid
        notebook_id = f"nb-{uuid.uuid4().hex[:8]}"

        notebook_data = {
            'id': notebook_id,
            'url': f'https://notebooklm.google.com/notebook/{notebook_id}',
            'title': title,
            'sources': [],
            'active': True
        }

        # Add to session tracker
        success = self.tracker.add_notebook(notebook_data)

        if not success:
            print(f"❌ Failed to create notebook")
            return None

        print(f"✅ Notebook created: {notebook_id}")

        # Add observation to Langfuse trace
        if self.mcp_tools and self.tracer.is_enabled() and self.trace_id:
            obs_id = await self.tracer.add_notebook_observation(
                trace_id=self.trace_id,
                notebook_data=notebook_data,
                mcp_tools=self.mcp_tools
            )
            print(f"✅ Langfuse observation added: {obs_id}")

        return notebook_id

    async def add_source(self, notebook_id: str, source_path: str, source_type: str = 'file') -> bool:
        """
        Add a source to a notebook.

        Args:
            notebook_id: Target notebook ID
            source_path: Path to source file or URL
            source_type: Type of source ('file', 'url', 'youtube')

        Returns:
            True if successful, False otherwise
        """
        print(f"\n📄 Adding source: {source_path} to {notebook_id}...")

        # Generate source data
        import hashlib
        from datetime import datetime

        source_id = hashlib.md5(f"{source_path}{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        # Determine file type
        if source_type == 'file':
            file_ext = Path(source_path).suffix.lstrip('.')
            file_size = Path(source_path).stat().st_size if Path(source_path).exists() else 0
        else:
            file_ext = 'url'
            file_size = 0

        source_data = {
            'source_id': source_id,
            'filename': Path(source_path).name if source_type == 'file' else source_path,
            'path': source_path,
            'type': file_ext,
            'size': file_size,
            'added_at': datetime.now().isoformat()
        }

        # Add to session tracker
        success = self.tracker.add_source_to_notebook(notebook_id, source_data)

        if not success:
            print(f"❌ Failed to add source")
            return False

        print(f"✅ Source added: {source_data['filename']}")

        # Add observation to Langfuse trace
        if self.mcp_tools and self.tracer.is_enabled() and self.trace_id:
            source_obs_id = await self.tracer.add_source_observation(
                trace_id=self.trace_id,
                notebook_id=notebook_id,
                source_data=source_data,
                mcp_tools=self.mcp_tools
            )
            print(f"✅ Langfuse observation added: {source_obs_id}")

        return True

    def get_session_status(self) -> Optional[dict]:
        """
        Get current session status.

        Returns:
            Session status dict or None
        """
        return self.tracker.get_session_status()

    async def end_session(self) -> bool:
        """
        End the current session.

        Returns:
            True if successful, False otherwise
        """
        print(f"\n🏁 Ending session {self.session_id}...")

        # Get final session data for Langfuse
        final_session_data = self.tracker.current_session

        # End session via tracker
        success = self.tracker.end_session()

        if not success:
            print("❌ Failed to end session")
            return False

        print("✅ Session ended")

        # Finalize Langfuse trace
        if self.mcp_tools and self.tracer.is_enabled() and self.trace_id:
            await self.tracer.finalize_session_trace(
                trace_id=self.trace_id,
                session_data=final_session_data,
                mcp_tools=self.mcp_tools
            )
            print("✅ Langfuse trace finalized")

        return True

    def print_session_summary(self):
        """Print a summary of the current session."""
        status = self.get_session_status()

        if not status:
            print("❌ No active session")
            return

        print("\n" + "="*60)
        print("📊 Session Summary")
        print("="*60)
        print(f"Session ID: {status['session_id']}")
        print(f"AI Assistant: {status['ai_assistant']}")
        print(f"Issue Number: {status.get('issue_number', 'N/A')}")
        print(f"Status: {status['status']}")
        print(f"Notebooks: {status['notebooks_count']}")
        print(f"Notes: {status['notes_count']}")
        print(f"Created: {status['created_at']}")

        # List notebooks
        notebooks = self.tracker.list_notebooks()
        if notebooks:
            print(f"\nNotebooks ({len(notebooks)}):")
            for nb in notebooks:
                sources_count = len(nb.get('sources', []))
                print(f"  • {nb.get('title', 'Untitled')} ({sources_count} sources)")

        print("="*60)


async def example_workflow():
    """
    Example workflow demonstrating programmatic usage.
    """
    print("♠️🌿🎸🧵 DeepDiver + Langfuse Programmatic Example")
    print("="*60)

    # Initialize session manager
    # Note: In real usage with Claude Code, mcp_tools would be provided
    session = DeepDiverProgrammaticSession(mcp_tools=None)

    # Get creative direction from Jerry
    print("\n⚡ Jerry's Creative Direction:")
    jerry_guidance = session.get_assembly_guidance('jerry')
    if jerry_guidance:
        # Print first 300 characters
        print(jerry_guidance[:300] + "...\n")

    # Start session
    success = await session.start_session(
        ai_assistant='claude',
        issue_number=999
    )

    if not success:
        print("❌ Failed to start session")
        return

    # Get structural guidance from Nyro
    print("\n♠️ Nyro's Structural Advice:")
    nyro_guidance = session.get_assembly_guidance('nyro')
    if nyro_guidance:
        print("  [Using Nyro's hierarchical organization pattern...]")

    # Create multiple notebooks (following Nyro's structural guidance)
    nb1 = await session.create_notebook("Foundation Layer")
    nb2 = await session.create_notebook("Application Layer")
    nb3 = await session.create_notebook("Interface Layer")

    # Get emotional context from Aureon
    print("\n🌿 Aureon's Emotional Context:")
    aureon_guidance = session.get_assembly_guidance('aureon')
    if aureon_guidance:
        print("  [Considering emotional resonance of source selection...]")

    # Add sources to notebooks
    if nb1:
        await session.add_source(nb1, "./README.md", "file")
        await session.add_source(nb1, "./ARCHITECTURE_ANALYSIS.md", "file")

    if nb2:
        await session.add_source(nb2, "https://example.com/api-docs", "url")

    if nb3:
        await session.add_source(nb3, "https://youtube.com/watch?v=example", "youtube")

    # Get rhythmic analysis from JamAI
    print("\n🎸 JamAI's Rhythmic Analysis:")
    jamai_guidance = session.get_assembly_guidance('jamai')
    if jamai_guidance:
        print("  [Workflow has good tempo: create → add sources → review]")

    # Print session summary
    session.print_session_summary()

    # Get execution clarity from Synth
    print("\n🧵 Synth's Execution Status:")
    synth_guidance = session.get_assembly_guidance('synth')
    if synth_guidance:
        print("  [All operations executed successfully]")

    # End session
    await session.end_session()

    print("\n♠️🌿🎸🧵 Example workflow complete!")


async def minimal_example():
    """
    Minimal example for quick reference.
    """
    print("Minimal Programmatic Example")
    print("-" * 40)

    session = DeepDiverProgrammaticSession()

    # Start → Create → Add → End
    await session.start_session(ai_assistant='claude', issue_number=100)

    nb_id = await session.create_notebook("Quick Test")
    if nb_id:
        await session.add_source(nb_id, "./test.md", "file")

    session.print_session_summary()
    await session.end_session()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--minimal":
        asyncio.run(minimal_example())
    else:
        asyncio.run(example_workflow())
