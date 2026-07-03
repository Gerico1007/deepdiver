"""
Langfuse Tracer Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module integrates CoaiaPy MCP for distributed trace-based storage,
transforming DeepDiver sessions into observable Langfuse trace trees.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio


class LangfuseTracer:
    """
    Manages DeepDiver sessions as Langfuse traces.
    Bridges SessionTracker to distributed observable storage.

    Design Philosophy:
    - Lazy initialization: MCP client connects only when needed
    - Hierarchical traces: Session → Notebook → Source → Audio
    - Configurable verbosity: Control observation granularity
    - Input/Output separation: Operational data vs results
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Langfuse tracer with configuration.

        Args:
            config: DeepDiver configuration dict
        """
        self.config = config or {}
        self.logger = self._setup_logging()

        # Langfuse settings
        self.enabled = self.config.get('LANGFUSE_SETTINGS', {}).get('enabled', False)
        self.verbosity = self.config.get('LANGFUSE_SETTINGS', {}).get('verbosity', 'standard')

        # MCP client (lazy initialization)
        self._mcp_client = None
        self._initialized = False

        self.logger.info("♠️🌿🎸🧵 LangfuseTracer initialized (lazy mode)")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.Logger('LangfuseTracer')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def _ensure_initialized(self):
        """
        Lazy initialization of MCP client.
        Only connects when Langfuse features are first used.
        """
        if self._initialized:
            return

        if not self.enabled:
            self.logger.warning("Langfuse integration disabled in config")
            return

        try:
            # Import MCP client tools (available via Claude Code MCP)
            # Note: These are available as mcp__coaiapy__* functions
            self._initialized = True
            self.logger.info("✅ MCP client initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize MCP client: {e}")
            self._initialized = False

    def is_enabled(self) -> bool:
        """Check if Langfuse integration is enabled."""
        return self.enabled

    def set_verbosity(self, level: str):
        """
        Set trace verbosity level.

        Args:
            level: 'minimal' | 'standard' | 'detailed'
                - minimal: Only session and notebook traces
                - standard: + source observations
                - detailed: + browser action observations
        """
        if level not in ['minimal', 'standard', 'detailed']:
            self.logger.warning(f"Invalid verbosity level: {level}, using 'standard'")
            level = 'standard'

        self.verbosity = level
        self.logger.info(f"✅ Trace verbosity set to: {level}")

    async def create_session_trace(
        self,
        session_data: Dict[str, Any],
        mcp_tools: Any
    ) -> Optional[str]:
        """
        Create root trace for DeepDiver session.

        Args:
            session_data: SessionTracker session dict
            mcp_tools: MCP tool access object (from Claude Code)

        Returns:
            trace_id: Langfuse trace identifier, or None if disabled
        """
        if not self.enabled:
            return None

        await self._ensure_initialized()

        try:
            trace_id = session_data['session_id']

            # Prepare input data (what triggered the session)
            input_data = {
                "session_type": "deepdiver_podcast_automation",
                "ai_assistant": session_data.get('ai_assistant', 'unknown'),
                "agents": session_data.get('agents', []),
                "issue_number": session_data.get('issue_number'),
                "created_at": session_data.get('created_at')
            }

            # Prepare metadata (classification tags)
            metadata = {
                "assembly_team": session_data.get('assembly_team', {}),
                "status": session_data.get('status', 'active'),
                "environment": "notebooklm",
                "deepdiver_version": "0.1.0"
            }

            # Create trace using MCP tool
            result = await mcp_tools.coaia_fuse_trace_create(
                trace_id=trace_id,
                name=f"DeepDiver Session - {session_data.get('ai_assistant', 'unknown')}",
                session_id=trace_id,  # Use session_id as Langfuse session
                user_id=session_data.get('user_id', 'default'),
                input_data=input_data,
                metadata=metadata
            )

            self.logger.info(f"✅ Langfuse trace created: {trace_id}")
            return trace_id

        except Exception as e:
            self.logger.error(f"❌ Failed to create session trace: {e}")
            return None

    async def add_notebook_observation(
        self,
        trace_id: str,
        notebook_data: Dict[str, Any],
        mcp_tools: Any
    ) -> Optional[str]:
        """
        Add notebook as SPAN observation to session trace.

        Args:
            trace_id: Parent session trace ID
            notebook_data: Notebook metadata
            mcp_tools: MCP tool access object

        Returns:
            observation_id: Langfuse observation identifier, or None if disabled
        """
        if not self.enabled or self.verbosity == 'minimal':
            return None

        try:
            observation_id = notebook_data['id']

            # Input: What was requested
            input_data = {
                "notebook_id": notebook_data['id'],
                "notebook_url": notebook_data.get('url'),
                "created_at": notebook_data.get('created_at'),
                "title": notebook_data.get('title', 'Untitled')
            }

            # Output: What was created
            output_data = {
                "notebooklm_url": notebook_data.get('url'),
                "sources_count": len(notebook_data.get('sources', [])),
                "active": notebook_data.get('active', False),
                "creation_status": "success"
            }

            # Metadata: Classification
            metadata = {
                "title": notebook_data.get('title'),
                "entity_type": "notebook"
            }

            # Create observation using MCP tool
            result = await mcp_tools.coaia_fuse_add_observation(
                trace_id=trace_id,
                observation_id=observation_id,
                name=f"Notebook: {notebook_data.get('title', 'Untitled')}",
                observation_type="SPAN",
                input_data=input_data,
                output_data=output_data,
                metadata=metadata
            )

            self.logger.info(f"✅ Notebook observation added: {observation_id}")
            return observation_id

        except Exception as e:
            self.logger.error(f"❌ Failed to add notebook observation: {e}")
            return None

    async def add_source_observation(
        self,
        trace_id: str,
        notebook_id: str,
        source_data: Dict[str, Any],
        mcp_tools: Any
    ) -> Optional[str]:
        """
        Add source upload as EVENT observation to notebook.

        Args:
            trace_id: Root session trace ID
            notebook_id: Parent notebook observation ID
            source_data: Source metadata
            mcp_tools: MCP tool access object

        Returns:
            observation_id: Langfuse observation identifier, or None if disabled
        """
        if not self.enabled or self.verbosity == 'minimal':
            return None

        try:
            observation_id = source_data.get('source_id')
            if not observation_id:
                self.logger.warning("Source missing source_id, skipping observation")
                return None

            # Input: What was uploaded
            input_data = {
                "filename": source_data.get('filename'),
                "path": source_data.get('path'),
                "type": source_data.get('type'),
                "size": source_data.get('size', 0)
            }

            # Output: Upload result
            output_data = {
                "source_id": source_data.get('source_id'),
                "added_at": source_data.get('added_at'),
                "upload_status": "success",
                "notebooklm_source_url": source_data.get('notebooklm_url')
            }

            # Metadata: Classification
            metadata = {
                "entity_type": "source",
                "source_type": source_data.get('type'),
                "notebook_id": notebook_id
            }

            # Create observation using MCP tool (nested under notebook)
            result = await mcp_tools.coaia_fuse_add_observation(
                trace_id=trace_id,
                observation_id=observation_id,
                parent_id=notebook_id,  # Nest under notebook observation
                name=f"Source Upload: {source_data.get('filename', 'unknown')}",
                observation_type="EVENT",
                input_data=input_data,
                output_data=output_data,
                metadata=metadata
            )

            self.logger.info(f"✅ Source observation added: {observation_id}")
            return observation_id

        except Exception as e:
            self.logger.error(f"❌ Failed to add source observation: {e}")
            return None

    async def add_browser_action_observation(
        self,
        trace_id: str,
        parent_id: str,
        action_data: Dict[str, Any],
        mcp_tools: Any
    ) -> Optional[str]:
        """
        Add browser action as SPAN observation (only in 'detailed' mode).

        Args:
            trace_id: Root session trace ID
            parent_id: Parent observation ID (notebook/source)
            action_data: Browser action metadata
            mcp_tools: MCP tool access object

        Returns:
            observation_id: Langfuse observation identifier, or None if disabled
        """
        if not self.enabled or self.verbosity != 'detailed':
            return None

        try:
            import uuid
            observation_id = f"action_{uuid.uuid4().hex[:8]}"

            # Input: Action parameters
            input_data = {
                "action_type": action_data.get('action_type'),
                "selector": action_data.get('selector'),
                "parameters": action_data.get('parameters', {})
            }

            # Output: Action result
            output_data = {
                "status": action_data.get('status', 'success'),
                "duration_ms": action_data.get('duration_ms'),
                "screenshot_path": action_data.get('screenshot_path')
            }

            # Metadata: Classification
            metadata = {
                "entity_type": "browser_action",
                "action_type": action_data.get('action_type')
            }

            # Create observation using MCP tool
            result = await mcp_tools.coaia_fuse_add_observation(
                trace_id=trace_id,
                observation_id=observation_id,
                parent_id=parent_id,  # Nest under parent operation
                name=f"Browser: {action_data.get('action_type', 'unknown')}",
                observation_type="SPAN",
                input_data=input_data,
                output_data=output_data,
                metadata=metadata
            )

            self.logger.debug(f"✅ Browser action observation added: {observation_id}")
            return observation_id

        except Exception as e:
            self.logger.error(f"❌ Failed to add browser action observation: {e}")
            return None

    async def finalize_session_trace(
        self,
        trace_id: str,
        session_data: Dict[str, Any],
        mcp_tools: Any
    ) -> bool:
        """
        Finalize session trace with output data when session ends.

        Args:
            trace_id: Session trace ID
            session_data: Final session data
            mcp_tools: MCP tool access object

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Prepare output data (session results)
            output_data = {
                "status": session_data.get('status', 'ended'),
                "ended_at": session_data.get('ended_at'),
                "notebooks_created": len(session_data.get('notebooks', [])),
                "sources_processed": sum(
                    len(nb.get('sources', []))
                    for nb in session_data.get('notebooks', [])
                ),
                "podcasts_created": len(session_data.get('podcasts_created', [])),
                "duration_minutes": self._calculate_session_duration(session_data)
            }

            # Update trace with output data
            result = await mcp_tools.coaia_fuse_trace_patch_output(
                trace_id=trace_id,
                output_data=output_data
            )

            self.logger.info(f"✅ Session trace finalized: {trace_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to finalize session trace: {e}")
            return False

    async def retrieve_session_trace(
        self,
        trace_id: str,
        mcp_tools: Any,
        json_output: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete session trace tree from Langfuse.

        Args:
            trace_id: Session trace ID
            mcp_tools: MCP tool access object
            json_output: If True, return raw JSON; if False, return formatted tree

        Returns:
            Trace data with all observations, or None if not found
        """
        if not self.enabled:
            return None

        try:
            result = await mcp_tools.coaia_fuse_trace_get(
                trace_id=trace_id,
                json_output=json_output
            )

            self.logger.info(f"✅ Session trace retrieved: {trace_id}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve session trace: {e}")
            return None

    async def query_session_traces(
        self,
        session_id: str,
        mcp_tools: Any,
        json_output: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query all traces for a specific session.

        Args:
            session_id: Langfuse session ID (maps to DeepDiver session_id)
            mcp_tools: MCP tool access object
            json_output: If True, return raw JSON; if False, return formatted

        Returns:
            List of traces, or None if error
        """
        if not self.enabled:
            return None

        try:
            result = await mcp_tools.coaia_fuse_traces_session_view(
                session_id=session_id,
                json_output=json_output
            )

            self.logger.info(f"✅ Session traces queried: {session_id}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to query session traces: {e}")
            return None

    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> float:
        """
        Calculate session duration in minutes.

        Args:
            session_data: Session metadata

        Returns:
            Duration in minutes, or 0.0 if unable to calculate
        """
        try:
            created_at = datetime.fromisoformat(session_data['created_at'])
            ended_at_str = session_data.get('ended_at')

            if not ended_at_str:
                ended_at = datetime.now()
            else:
                ended_at = datetime.fromisoformat(ended_at_str)

            duration = (ended_at - created_at).total_seconds() / 60
            return round(duration, 2)

        except Exception as e:
            self.logger.warning(f"Could not calculate session duration: {e}")
            return 0.0


# Utility function for synchronous contexts
def create_tracer(config: Optional[Dict[str, Any]] = None) -> LangfuseTracer:
    """
    Factory function to create a LangfuseTracer instance.

    Args:
        config: DeepDiver configuration dict

    Returns:
        Configured LangfuseTracer instance
    """
    return LangfuseTracer(config=config)
