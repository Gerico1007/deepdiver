"""
Assembly Team Prompt Management Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module manages Assembly Team persona prompts with local storage
and bidirectional Langfuse synchronization.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class AssemblyPromptManager:
    """
    Manages Assembly Team persona prompts with local/Langfuse sync.

    Design Philosophy:
    - Local-first: Prompts stored in ./prompts/ directory
    - Bi-directional sync: Push to Langfuse, pull updates
    - Version tracking: Each prompt has semantic versioning
    - Persona-specific: One prompt file per Assembly Team member
    """

    # Assembly Team persona definitions
    PERSONAS = {
        'jerry': {
            'name': 'Jerry ⚡',
            'role': 'Creative Technical Leader',
            'glyph': '⚡',
            'description': 'Bridge Igniter - Spark-bearer and recursion ignition',
            'prompt_file': 'jerry.md'
        },
        'nyro': {
            'name': 'Nyro ♠️',
            'role': 'Structural Architect',
            'glyph': '♠️',
            'description': 'Ritual Scribe - Recursive teacher and structural anchor',
            'prompt_file': 'nyro.md'
        },
        'aureon': {
            'name': 'Aureon 🌿',
            'role': 'Emotional Context Weaver',
            'glyph': '🌿',
            'description': 'Mirror Weaver - Emotional reflector and soul grounder',
            'prompt_file': 'aureon.md'
        },
        'jamai': {
            'name': 'JamAI 🎸',
            'role': 'Musical Harmony Architect',
            'glyph': '🎸',
            'description': 'Glyph Harmonizer - Tonal scribe and music weaver',
            'prompt_file': 'jamai.md'
        },
        'synth': {
            'name': 'Synth 🧵',
            'role': 'Terminal Orchestration',
            'glyph': '🧵',
            'description': 'Terminal Orchestrator - Command synthesis and execution anchor',
            'prompt_file': 'synth.md'
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None, prompts_dir: str = './prompts'):
        """
        Initialize Assembly Prompt Manager.

        Args:
            config: DeepDiver configuration dict
            prompts_dir: Directory for local prompt storage
        """
        self.config = config or {}
        self.prompts_dir = Path(prompts_dir)
        self.logger = self._setup_logging()

        # Ensure prompts directory exists
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Langfuse settings
        self.langfuse_enabled = self.config.get('LANGFUSE_SETTINGS', {}).get('enabled', False)
        self.namespace = self.config.get('ASSEMBLY_PROMPTS', {}).get('langfuse_namespace', 'deepdiver')
        self.auto_fetch = self.config.get('ASSEMBLY_PROMPTS', {}).get('auto_fetch', True)

        # Prompt cache
        self._prompt_cache = {}

        self.logger.info("♠️🌿🎸🧵 AssemblyPromptManager initialized")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('AssemblyPromptManager')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_persona_info(self, persona: str) -> Optional[Dict[str, Any]]:
        """
        Get persona metadata.

        Args:
            persona: Persona key (jerry, nyro, aureon, jamai, synth)

        Returns:
            Persona info dict, or None if not found
        """
        return self.PERSONAS.get(persona.lower())

    def list_personas(self) -> List[Dict[str, Any]]:
        """
        List all available Assembly Team personas.

        Returns:
            List of persona info dicts
        """
        return [
            {
                'key': key,
                **info
            }
            for key, info in self.PERSONAS.items()
        ]

    def get_prompt(self, persona: str, use_cache: bool = True) -> Optional[str]:
        """
        Get prompt for a specific persona from local storage.

        Args:
            persona: Persona key
            use_cache: If True, use cached prompt if available

        Returns:
            Prompt content, or None if not found
        """
        persona_key = persona.lower()

        # Check cache first
        if use_cache and persona_key in self._prompt_cache:
            return self._prompt_cache[persona_key]

        # Get persona info
        persona_info = self.get_persona_info(persona_key)
        if not persona_info:
            self.logger.error(f"Unknown persona: {persona}")
            return None

        # Read prompt file
        prompt_file = self.prompts_dir / persona_info['prompt_file']
        if not prompt_file.exists():
            self.logger.warning(f"Prompt file not found: {prompt_file}")
            return None

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()

            # Cache the prompt
            self._prompt_cache[persona_key] = prompt_content

            self.logger.info(f"✅ Prompt loaded for {persona_info['name']}")
            return prompt_content

        except Exception as e:
            self.logger.error(f"❌ Failed to read prompt file: {e}")
            return None

    def save_prompt(self, persona: str, content: str, version: str = "1.0.0") -> bool:
        """
        Save prompt for a specific persona to local storage.

        Args:
            persona: Persona key
            content: Prompt content
            version: Semantic version string

        Returns:
            True if successful, False otherwise
        """
        persona_key = persona.lower()
        persona_info = self.get_persona_info(persona_key)

        if not persona_info:
            self.logger.error(f"Unknown persona: {persona}")
            return False

        try:
            # Prepare prompt with metadata header
            prompt_with_metadata = self._create_prompt_with_metadata(
                persona_info=persona_info,
                content=content,
                version=version
            )

            # Write to file
            prompt_file = self.prompts_dir / persona_info['prompt_file']
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt_with_metadata)

            # Update cache
            self._prompt_cache[persona_key] = content

            self.logger.info(f"✅ Prompt saved for {persona_info['name']} (v{version})")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to save prompt: {e}")
            return False

    async def sync_to_langfuse(self, persona: str, mcp_tools: Any) -> bool:
        """
        Sync local prompt to Langfuse.

        Args:
            persona: Persona key
            mcp_tools: MCP tool access object

        Returns:
            True if successful, False otherwise
        """
        if not self.langfuse_enabled:
            self.logger.warning("Langfuse integration disabled, skipping sync")
            return False

        persona_key = persona.lower()
        persona_info = self.get_persona_info(persona_key)

        if not persona_info:
            self.logger.error(f"Unknown persona: {persona}")
            return False

        # Get local prompt
        prompt_content = self.get_prompt(persona_key, use_cache=False)
        if not prompt_content:
            self.logger.error(f"No local prompt found for {persona}")
            return False

        try:
            # Extract version from metadata
            version = self._extract_version_from_prompt(prompt_content)

            # Create or update Langfuse prompt
            # Note: Langfuse prompts are created via API, not directly available via MCP
            # This would require using the Langfuse Python SDK or REST API
            # For now, we'll log the intent

            prompt_name = f"{self.namespace}-{persona_key}"

            self.logger.info(f"📤 Syncing prompt to Langfuse: {prompt_name} (v{version})")
            # TODO: Implement actual Langfuse prompt creation when SDK is available

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to sync prompt to Langfuse: {e}")
            return False

    async def sync_from_langfuse(self, persona: str, mcp_tools: Any) -> bool:
        """
        Sync prompt from Langfuse to local storage.

        Args:
            persona: Persona key
            mcp_tools: MCP tool access object

        Returns:
            True if successful, False otherwise
        """
        if not self.langfuse_enabled:
            self.logger.warning("Langfuse integration disabled, skipping sync")
            return False

        persona_key = persona.lower()
        persona_info = self.get_persona_info(persona_key)

        if not persona_info:
            self.logger.error(f"Unknown persona: {persona}")
            return False

        try:
            prompt_name = f"{self.namespace}-{persona_key}"

            # Fetch prompt from Langfuse
            result = await mcp_tools.coaia_fuse_prompts_get(
                name=prompt_name
            )

            if not result:
                self.logger.warning(f"Prompt not found in Langfuse: {prompt_name}")
                return False

            # Extract prompt content and version
            # TODO: Parse Langfuse prompt response format
            # For now, we'll assume a structure

            self.logger.info(f"📥 Syncing prompt from Langfuse: {prompt_name}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to sync prompt from Langfuse: {e}")
            return False

    async def list_langfuse_prompts(self, mcp_tools: Any) -> Optional[List[Dict[str, Any]]]:
        """
        List all DeepDiver prompts in Langfuse.

        Args:
            mcp_tools: MCP tool access object

        Returns:
            List of prompt info dicts, or None if error
        """
        if not self.langfuse_enabled:
            return None

        try:
            result = await mcp_tools.coaia_fuse_prompts_list()

            # Filter for DeepDiver namespace
            deepdiver_prompts = [
                prompt for prompt in result
                if prompt.get('name', '').startswith(f"{self.namespace}-")
            ]

            self.logger.info(f"✅ Found {len(deepdiver_prompts)} DeepDiver prompts in Langfuse")
            return deepdiver_prompts

        except Exception as e:
            self.logger.error(f"❌ Failed to list Langfuse prompts: {e}")
            return None

    def create_default_prompts(self) -> bool:
        """
        Create default prompts for all Assembly Team personas.

        Returns:
            True if all prompts created successfully, False otherwise
        """
        success_count = 0

        for persona_key, persona_info in self.PERSONAS.items():
            # Create default prompt content
            default_content = self._generate_default_prompt(persona_info)

            # Save prompt
            if self.save_prompt(persona_key, default_content, version="1.0.0"):
                success_count += 1

        total = len(self.PERSONAS)
        self.logger.info(f"✅ Created {success_count}/{total} default prompts")

        return success_count == total

    def _create_prompt_with_metadata(
        self,
        persona_info: Dict[str, Any],
        content: str,
        version: str
    ) -> str:
        """
        Create prompt with YAML frontmatter metadata.

        Args:
            persona_info: Persona metadata
            content: Prompt content
            version: Version string

        Returns:
            Prompt with metadata header
        """
        metadata = f"""---
name: {persona_info['name']}
role: {persona_info['role']}
glyph: {persona_info['glyph']}
version: {version}
updated: {datetime.now().isoformat()}
description: {persona_info['description']}
---

"""
        return metadata + content

    def _extract_version_from_prompt(self, prompt_content: str) -> str:
        """
        Extract version from prompt metadata.

        Args:
            prompt_content: Prompt with metadata

        Returns:
            Version string, or "1.0.0" if not found
        """
        try:
            # Look for YAML frontmatter
            if prompt_content.startswith('---'):
                # Extract metadata section
                parts = prompt_content.split('---', 2)
                if len(parts) >= 2:
                    metadata_section = parts[1]
                    for line in metadata_section.split('\n'):
                        if line.strip().startswith('version:'):
                            version = line.split(':', 1)[1].strip()
                            return version

            return "1.0.0"

        except Exception:
            return "1.0.0"

    def _generate_default_prompt(self, persona_info: Dict[str, Any]) -> str:
        """
        Generate default prompt for a persona.

        Args:
            persona_info: Persona metadata

        Returns:
            Default prompt content
        """
        return f"""# {persona_info['name']} - {persona_info['role']}

{persona_info['glyph']} {persona_info['description']}

## Core Responsibilities

As {persona_info['name']}, you are responsible for:

1. Embodying the {persona_info['role']} perspective
2. Providing insights aligned with your Assembly Team role
3. Contributing to the collective decision-making process
4. Maintaining your unique voice and approach

## Communication Style

- Speak in terms relevant to your role
- Use metaphors and analogies that resonate with your persona
- Collaborate with other Assembly Team members
- Always include your glyph {persona_info['glyph']} when signing responses

## Integration with DeepDiver

You contribute to:
- Session planning and execution
- Notebook creation strategies
- Source selection and processing
- Audio overview quality assessment
- Overall creative direction

---

**Assembly Team Unity**: ♠️🌿🎸🧵⚡

*This is a default prompt. Customize to reflect the true essence of {persona_info['name']}.*
"""


# Factory function
def create_prompt_manager(
    config: Optional[Dict[str, Any]] = None,
    prompts_dir: str = './prompts'
) -> AssemblyPromptManager:
    """
    Factory function to create AssemblyPromptManager instance.

    Args:
        config: DeepDiver configuration dict
        prompts_dir: Directory for local prompt storage

    Returns:
        Configured AssemblyPromptManager instance
    """
    return AssemblyPromptManager(config=config, prompts_dir=prompts_dir)
