"""
Session Tracker Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module handles session management, tracking, and metadata
for DeepDiver podcast creation sessions.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


class SessionTracker:
    """
    Manages DeepDiver sessions and metadata.
    
    This class handles session creation, tracking, and persistence
    for podcast creation workflows.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the session tracker with configuration."""
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # Session settings
        self.session_dir = self.config.get('SESSION_TRACKING', {}).get(
            'session_dir', './sessions'
        )
        self.metadata_format = self.config.get('SESSION_TRACKING', {}).get(
            'metadata_format', 'yaml'
        )
        self.auto_save = self.config.get('SESSION_TRACKING', {}).get(
            'auto_save', True
        )
        self.max_sessions = self.config.get('SESSION_TRACKING', {}).get(
            'max_sessions', 100
        )
        
        # Ensure session directory exists
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Current session
        self.current_session = None
        self.session_file = os.path.join(self.session_dir, 'current_session.json')
        
        self.logger.info("♠️🌿🎸🧵 SessionTracker initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('SessionTracker')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start_session(self, ai_assistant: str = 'claude', 
                     issue_number: Optional[int] = None,
                     agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a new DeepDiver session.
        
        Args:
            ai_assistant (str): Name of the AI assistant
            issue_number (int, optional): Associated issue number
            agents (List[str], optional): List of active agents
            
        Returns:
            Dict[str, Any]: Session information
        """
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Default agents
            if agents is None:
                agents = ['Jerry ⚡', 'Nyro ♠️', 'Aureon 🌿', 'JamAI 🎸', 'Synth 🧵']
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'ai_assistant': ai_assistant,
                'agents': agents,
                'issue_number': issue_number,
                'pr_number': None,
                'created_at': datetime.now().isoformat(),
                'status': 'active',
                'podcasts_created': [],
                'documents_processed': [],
                'notebooks': [],
                'active_notebook_id': None,
                'notes': [],
                'assembly_team': {
                    'leader': 'Jerry ⚡',
                    'nyro': '♠️ Structural Architect',
                    'aureon': '🌿 Emotional Context',
                    'jamai': '🎸 Musical Harmony',
                    'synth': '🧵 Terminal Orchestration'
                }
            }
            
            # Save session
            self.current_session = session_data
            self._save_current_session()
            
            # Create session file
            session_filename = f"session_{session_id}.json"
            session_path = os.path.join(self.session_dir, session_filename)
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Session started: {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'session_data': session_data,
                'session_path': session_path
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def write_to_session(self, message: str, message_type: str = 'note') -> bool:
        """
        Write a message to the current session.
        
        Args:
            message (str): Message to write
            message_type (str): Type of message (note, podcast, document, etc.)
            
        Returns:
            bool: True if write successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session to write to")
                return False
            
            # Create message entry
            message_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': message_type,
                'message': message
            }
            
            # Add to session notes
            self.current_session['notes'].append(message_entry)
            
            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()
            
            self.logger.info(f"✅ Message written to session: {message_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to write to session: {e}")
            return False
    
    def add_podcast_to_session(self, podcast_info: Dict[str, Any]) -> bool:
        """
        Add a podcast to the current session.
        
        Args:
            podcast_info (Dict[str, Any]): Information about the created podcast
            
        Returns:
            bool: True if add successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session to add podcast to")
                return False
            
            # Add podcast info
            podcast_entry = {
                'timestamp': datetime.now().isoformat(),
                'podcast_info': podcast_info
            }
            
            self.current_session['podcasts_created'].append(podcast_entry)
            
            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()
            
            self.logger.info(f"✅ Podcast added to session: {podcast_info.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add podcast to session: {e}")
            return False
    
    def add_document_to_session(self, document_info: Dict[str, Any]) -> bool:
        """
        Add a document to the current session.
        
        Args:
            document_info (Dict[str, Any]): Information about the processed document
            
        Returns:
            bool: True if add successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session to add document to")
                return False
            
            # Add document info
            document_entry = {
                'timestamp': datetime.now().isoformat(),
                'document_info': document_info
            }
            
            self.current_session['documents_processed'].append(document_entry)
            
            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()
            
            self.logger.info(f"✅ Document added to session: {document_info.get('filename', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add document to session: {e}")
            return False
    
    def add_notebook(self, notebook_data: Dict[str, Any]) -> bool:
        """
        Add a notebook to the current session.

        Args:
            notebook_data (Dict[str, Any]): Notebook metadata (id, url, title, etc.)

        Returns:
            bool: True if add successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session to add notebook to")
                return False

            # Ensure notebooks list exists
            if 'notebooks' not in self.current_session:
                self.current_session['notebooks'] = []

            # Add timestamp if not present
            if 'created_at' not in notebook_data:
                notebook_data['created_at'] = datetime.now().isoformat()

            # Add notebook to session
            self.current_session['notebooks'].append(notebook_data)

            # Set as active notebook if it's the first or marked active
            if not self.current_session.get('active_notebook_id') or notebook_data.get('active', False):
                self.current_session['active_notebook_id'] = notebook_data.get('id')

            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()

            self.logger.info(f"✅ Notebook added to session: {notebook_data.get('id', 'Unknown')}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to add notebook to session: {e}")
            return False

    def get_active_notebook(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active notebook.

        Returns:
            Optional[Dict[str, Any]]: Active notebook data or None
        """
        try:
            if not self.current_session:
                return None

            active_id = self.current_session.get('active_notebook_id')
            if not active_id:
                return None

            # Find notebook by ID
            notebooks = self.current_session.get('notebooks', [])
            for notebook in notebooks:
                if notebook.get('id') == active_id:
                    return notebook

            return None

        except Exception as e:
            self.logger.error(f"❌ Error getting active notebook: {e}")
            return None

    def set_active_notebook(self, notebook_id: str) -> bool:
        """
        Set a notebook as active.

        Args:
            notebook_id (str): ID of the notebook to set as active

        Returns:
            bool: True if set successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session")
                return False

            # Verify notebook exists in session
            notebooks = self.current_session.get('notebooks', [])
            notebook_found = False

            for notebook in notebooks:
                if notebook.get('id') == notebook_id:
                    notebook_found = True
                    notebook['active'] = True
                else:
                    notebook['active'] = False

            if not notebook_found:
                self.logger.warning(f"Notebook {notebook_id} not found in session")
                return False

            # Set as active
            self.current_session['active_notebook_id'] = notebook_id

            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()

            self.logger.info(f"✅ Notebook set as active: {notebook_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to set active notebook: {e}")
            return False

    def list_notebooks(self) -> List[Dict[str, Any]]:
        """
        List all notebooks in the current session.

        Returns:
            List[Dict[str, Any]]: List of notebook data
        """
        try:
            if not self.current_session:
                return []

            return self.current_session.get('notebooks', [])

        except Exception as e:
            self.logger.error(f"❌ Error listing notebooks: {e}")
            return []

    def get_notebook_by_id(self, notebook_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific notebook by ID.

        Args:
            notebook_id (str): ID of the notebook to retrieve

        Returns:
            Optional[Dict[str, Any]]: Notebook data or None if not found
        """
        try:
            notebooks = self.list_notebooks()
            for notebook in notebooks:
                if notebook.get('id') == notebook_id:
                    return notebook

            return None

        except Exception as e:
            self.logger.error(f"❌ Error getting notebook: {e}")
            return None

    def update_notebook(self, notebook_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update notebook metadata.

        Args:
            notebook_id (str): ID of the notebook to update
            updates (Dict[str, Any]): Fields to update

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session")
                return False

            notebooks = self.current_session.get('notebooks', [])
            notebook_found = False

            for notebook in notebooks:
                if notebook.get('id') == notebook_id:
                    notebook.update(updates)
                    notebook['updated_at'] = datetime.now().isoformat()
                    notebook_found = True
                    break

            if not notebook_found:
                self.logger.warning(f"Notebook {notebook_id} not found")
                return False

            # Auto-save if enabled
            if self.auto_save:
                self._save_current_session()

            self.logger.info(f"✅ Notebook updated: {notebook_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to update notebook: {e}")
            return False

    def add_source_to_notebook(self, notebook_id: str, source_data: Dict[str, Any]) -> bool:
        """
        Add a source to a notebook in the session.

        Args:
            notebook_id (str): ID of the notebook to add source to
            source_data (Dict[str, Any]): Source metadata (filename, path, type, etc.)

        Returns:
            bool: True if add successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session")
                return False

            # Find the notebook
            notebook = self.get_notebook_by_id(notebook_id)
            if not notebook:
                self.logger.warning(f"Notebook {notebook_id} not found")
                return False

            # Ensure sources list exists
            if 'sources' not in notebook:
                notebook['sources'] = []

            # Add timestamp and ID if not present
            if 'added_at' not in source_data:
                source_data['added_at'] = datetime.now().isoformat()
            if 'source_id' not in source_data:
                # Generate simple source ID from filename and timestamp
                import hashlib
                filename = source_data.get('filename', 'unknown')
                timestamp = datetime.now().isoformat()
                source_id = hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()[:8]
                source_data['source_id'] = source_id

            # Add source to notebook
            notebook['sources'].append(source_data)

            # Update notebook in session
            self.update_notebook(notebook_id, {'sources': notebook['sources']})

            self.logger.info(f"✅ Source added to notebook {notebook_id}: {source_data.get('filename', 'Unknown')}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to add source to notebook: {e}")
            return False

    def list_notebook_sources(self, notebook_id: str) -> List[Dict[str, Any]]:
        """
        List all sources for a notebook.

        Args:
            notebook_id (str): ID of the notebook

        Returns:
            List[Dict[str, Any]]: List of source data
        """
        try:
            notebook = self.get_notebook_by_id(notebook_id)
            if not notebook:
                return []

            return notebook.get('sources', [])

        except Exception as e:
            self.logger.error(f"❌ Error listing notebook sources: {e}")
            return []

    def add_artifact_to_notebook(self, notebook_id: str, artifact_data: Dict[str, Any]) -> bool:
        """
        Add a Studio artifact (Audio Overview, Video, Mind Map) to a notebook.

        🌸 Miette: This tracks the voices we create through Studio.

        Args:
            notebook_id (str): ID of the notebook to add artifact to
            artifact_data (Dict[str, Any]): Artifact metadata
                Expected fields:
                - type: 'audio_overview', 'video_overview', 'mind_map', etc.
                - format: 'deep_dive', 'brief', 'critique', 'debate' (for audio)
                - language: 'English', 'Spanish', etc.
                - length: 'short', 'default', 'long' (for audio)
                - focus_prompt: Optional custom AI host instructions
                - artifact_id: Unique artifact identifier
                - status: 'completed', 'failed', etc.
                - created_at: ISO timestamp
                - generation_time: Time taken to generate (seconds)

        Returns:
            bool: True if add successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session")
                return False

            # Find the notebook
            notebook = self.get_notebook_by_id(notebook_id)
            if not notebook:
                self.logger.warning(f"Notebook {notebook_id} not found")
                return False

            # Ensure artifacts list exists
            if 'artifacts' not in notebook:
                notebook['artifacts'] = []

            # Add timestamp if not present
            if 'created_at' not in artifact_data:
                artifact_data['created_at'] = datetime.now().isoformat()

            # Generate artifact_id if not present
            if 'artifact_id' not in artifact_data:
                import hashlib
                artifact_type = artifact_data.get('type', 'unknown')
                timestamp = datetime.now().isoformat()
                artifact_id = hashlib.md5(f"{artifact_type}{timestamp}".encode()).hexdigest()[:12]
                artifact_data['artifact_id'] = artifact_id

            # Add artifact to notebook
            notebook['artifacts'].append(artifact_data)

            # Update notebook in session
            self.update_notebook(notebook_id, {'artifacts': notebook['artifacts']})

            artifact_type = artifact_data.get('type', 'Unknown')
            artifact_format = artifact_data.get('format', '')
            if artifact_format:
                artifact_name = f"{artifact_type} ({artifact_format})"
            else:
                artifact_name = artifact_type

            self.logger.info(f"✅ Artifact added to notebook {notebook_id}: {artifact_name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to add artifact to notebook: {e}")
            return False

    def list_notebook_artifacts(self, notebook_id: str) -> List[Dict[str, Any]]:
        """
        List all Studio artifacts for a notebook.

        Args:
            notebook_id (str): ID of the notebook

        Returns:
            List[Dict[str, Any]]: List of artifact data
        """
        try:
            notebook = self.get_notebook_by_id(notebook_id)
            if not notebook:
                return []

            return notebook.get('artifacts', [])

        except Exception as e:
            self.logger.error(f"❌ Error listing notebook artifacts: {e}")
            return []

    def get_session_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the current session status.

        Returns:
            Optional[Dict[str, Any]]: Session status or None if no active session
        """
        if not self.current_session:
            return None

        return {
            'session_id': self.current_session['session_id'],
            'ai_assistant': self.current_session['ai_assistant'],
            'agents': self.current_session['agents'],
            'issue_number': self.current_session['issue_number'],
            'created_at': self.current_session['created_at'],
            'status': self.current_session['status'],
            'podcasts_count': len(self.current_session['podcasts_created']),
            'documents_count': len(self.current_session['documents_processed']),
            'notebooks_count': len(self.current_session.get('notebooks', [])),
            'active_notebook_id': self.current_session.get('active_notebook_id'),
            'notes_count': len(self.current_session['notes'])
        }
    
    def load_session(self, session_id: str) -> bool:
        """
        Load a specific session.
        
        Args:
            session_id (str): ID of the session to load
            
        Returns:
            bool: True if load successful, False otherwise
        """
        try:
            session_filename = f"session_{session_id}.json"
            session_path = os.path.join(self.session_dir, session_filename)
            
            if not os.path.exists(session_path):
                self.logger.error(f"Session file not found: {session_path}")
                return False
            
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.current_session = session_data
            self._save_current_session()
            
            self.logger.info(f"✅ Session loaded: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load session: {e}")
            return False
    
    def end_session(self) -> bool:
        """
        End the current session.
        
        Returns:
            bool: True if end successful, False otherwise
        """
        try:
            if not self.current_session:
                self.logger.warning("No active session to end")
                return False
            
            # Update session status
            self.current_session['status'] = 'ended'
            self.current_session['ended_at'] = datetime.now().isoformat()
            
            # Save final session
            self._save_current_session()
            
            # Save to session file
            session_filename = f"session_{self.current_session['session_id']}.json"
            session_path = os.path.join(self.session_dir, session_filename)
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Session ended: {self.current_session['session_id']}")
            
            # Clear current session
            self.current_session = None
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to end session: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List[Dict[str, Any]]: List of session information
        """
        sessions = []
        
        try:
            for file in os.listdir(self.session_dir):
                if file.startswith('session_') and file.endswith('.json'):
                    session_path = os.path.join(self.session_dir, file)
                    
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        
                        # Extract summary info
                        session_summary = {
                            'session_id': session_data.get('session_id'),
                            'ai_assistant': session_data.get('ai_assistant'),
                            'issue_number': session_data.get('issue_number'),
                            'created_at': session_data.get('created_at'),
                            'status': session_data.get('status'),
                            'podcasts_count': len(session_data.get('podcasts_created', [])),
                            'documents_count': len(session_data.get('documents_processed', [])),
                            'notes_count': len(session_data.get('notes', []))
                        }
                        
                        sessions.append(session_summary)
                        
                    except Exception as e:
                        self.logger.warning(f"Error reading session file {file}: {e}")
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing sessions: {e}")
        
        return sessions
    
    def _save_current_session(self):
        """Save the current session to file."""
        try:
            if self.current_session:
                with open(self.session_file, 'w', encoding='utf-8') as f:
                    json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving current session: {e}")
    
    def _load_current_session(self):
        """Load the current session from file."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    self.current_session = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading current session: {e}")
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up sessions older than specified days.
        
        Args:
            days (int): Number of days to keep sessions
            
        Returns:
            int: Number of sessions deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        try:
            for file in os.listdir(self.session_dir):
                if file.startswith('session_') and file.endswith('.json'):
                    file_path = os.path.join(self.session_dir, file)
                    
                    if os.path.getctime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            self.logger.info(f"✅ Cleaned up {deleted_count} old sessions")
            
        except Exception as e:
            self.logger.error(f"Error during session cleanup: {e}")
        
        return deleted_count


# Example usage and testing
def test_session_tracker():
    """Test function for session tracker."""
    tracker = SessionTracker()
    
    # Test session creation
    result = tracker.start_session(ai_assistant='claude', issue_number=1)
    print(f"Session creation result: {result}")
    
    # Test writing to session
    tracker.write_to_session("Test message", "note")
    
    # Test session status
    status = tracker.get_session_status()
    print(f"Session status: {status}")
    
    # Test listing sessions
    sessions = tracker.list_sessions()
    print(f"Found {len(sessions)} sessions")
    
    # Test ending session
    tracker.end_session()


if __name__ == "__main__":
    test_session_tracker()
