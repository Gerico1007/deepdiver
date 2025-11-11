"""
DeepDiver - NotebookLM Podcast Automation System

A Python-based automation tool for creating podcasts from documents
using NotebookLM's Audio Overview feature through browser automation.

Part of Jerry's G.Music Assembly ecosystem.
"""

__version__ = "0.1.0"
__author__ = "gerico1007"
__email__ = "gerico@jgwill.com"
__description__ = "NotebookLM Podcast Automation System"

# Assembly Team
ASSEMBLY_TEAM = {
    "leader": "Jerry ⚡",
    "nyro": "♠️ Structural Architect",
    "aureon": "🌿 Emotional Context",
    "jamai": "🎸 Musical Harmony",
    "synth": "🧵 Terminal Orchestration"
}

# Core modules
from .deepdive import main
from .notebooklm_automator import NotebookLMAutomator
from .content_processor import ContentProcessor
from .podcast_manager import PodcastManager
from .session_tracker import SessionTracker

__all__ = [
    "main",
    "NotebookLMAutomator",
    "ContentProcessor", 
    "PodcastManager",
    "SessionTracker",
    "ASSEMBLY_TEAM"
]
