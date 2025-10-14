"""
Podcast Manager Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module handles podcast file management, organization, and metadata
for generated audio files from NotebookLM.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml


class PodcastManager:
    """
    Manages podcast files and metadata.
    
    This class handles the organization, storage, and metadata management
    of generated podcast files from NotebookLM.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the podcast manager with configuration."""
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # Audio settings
        self.output_dir = self.config.get('AUDIO_SETTINGS', {}).get(
            'output_dir', './output/podcasts'
        )
        self.naming_pattern = self.config.get('AUDIO_SETTINGS', {}).get(
            'naming_pattern', '{title}_{timestamp}'
        )
        self.metadata_embed = self.config.get('AUDIO_SETTINGS', {}).get(
            'metadata_embed', True
        )
        self.quality_check = self.config.get('AUDIO_SETTINGS', {}).get(
            'quality_check', True
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info("♠️🌿🎸🧵 PodcastManager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('PodcastManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def generate_filename(self, title: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate a filename for a podcast based on the naming pattern.
        
        Args:
            title (str): Title of the podcast
            timestamp (datetime, optional): Timestamp for the podcast
            
        Returns:
            str: Generated filename
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Clean title for filename
        clean_title = self._clean_filename(title)
        
        # Format timestamp
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # Generate filename based on pattern
        filename = self.naming_pattern.format(
            title=clean_title,
            timestamp=timestamp_str,
            date=timestamp.strftime('%Y%m%d'),
            time=timestamp.strftime('%H%M%S')
        )
        
        return f"{filename}.mp3"
    
    def _clean_filename(self, filename: str) -> str:
        """Clean a string to be safe for use as a filename."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = '_'.join(filename.split())
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def save_podcast(self, source_path: str, title: str, 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a podcast file with metadata.
        
        Args:
            source_path (str): Path to the source audio file
            title (str): Title of the podcast
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            Dict[str, Any]: Save operation results
        """
        result = {
            'success': False,
            'source_path': source_path,
            'saved_path': None,
            'filename': None,
            'metadata_path': None,
            'errors': []
        }
        
        try:
            # Check if source file exists
            if not os.path.exists(source_path):
                result['errors'].append(f"Source file not found: {source_path}")
                return result
            
            # Generate filename
            filename = self.generate_filename(title)
            saved_path = os.path.join(self.output_dir, filename)
            
            # Copy file to output directory
            shutil.copy2(source_path, saved_path)
            result['saved_path'] = saved_path
            result['filename'] = filename
            
            # Create metadata
            if metadata is None:
                metadata = {}
            
            # Add default metadata
            metadata.update({
                'title': title,
                'created_at': datetime.now().isoformat(),
                'source_file': source_path,
                'saved_file': saved_path,
                'file_size': os.path.getsize(saved_path),
                'assembly_team': ['Jerry ⚡', 'Nyro ♠️', 'Aureon 🌿', 'JamAI 🎸', 'Synth 🧵']
            })
            
            # Save metadata
            metadata_filename = f"{Path(filename).stem}_metadata.json"
            metadata_path = os.path.join(self.output_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            result['metadata_path'] = metadata_path
            
            # Embed metadata in audio file if requested
            if self.metadata_embed:
                self._embed_metadata(saved_path, metadata)
            
            # Quality check if requested
            if self.quality_check:
                quality_result = self._check_audio_quality(saved_path)
                metadata['quality_check'] = quality_result
            
            result['success'] = True
            self.logger.info(f"✅ Podcast saved successfully: {saved_path}")
            
        except Exception as e:
            result['errors'].append(f"Save error: {e}")
            self.logger.error(f"❌ Failed to save podcast: {e}")
        
        return result
    
    def _embed_metadata(self, audio_path: str, metadata: Dict[str, Any]):
        """Embed metadata in audio file."""
        try:
            # This would require a library like mutagen for MP3 metadata
            # For now, we'll just log that metadata embedding is requested
            self.logger.info(f"Metadata embedding requested for: {audio_path}")
            self.logger.info("Note: Metadata embedding requires additional audio processing library")
        except Exception as e:
            self.logger.warning(f"Metadata embedding failed: {e}")
    
    def _check_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        """Check audio file quality."""
        try:
            file_size = os.path.getsize(audio_path)
            
            # Basic quality checks
            quality_result = {
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'has_content': file_size > 1024,  # At least 1KB
                'timestamp': datetime.now().isoformat()
            }
            
            # Check if file is likely a valid audio file
            with open(audio_path, 'rb') as f:
                header = f.read(10)
                # Check for MP3 header
                if header.startswith(b'ID3') or header[0:2] == b'\xff\xfb':
                    quality_result['format_valid'] = True
                else:
                    quality_result['format_valid'] = False
            
            return quality_result
            
        except Exception as e:
            self.logger.warning(f"Quality check failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def list_podcasts(self) -> List[Dict[str, Any]]:
        """
        List all podcasts in the output directory.
        
        Returns:
            List[Dict[str, Any]]: List of podcast information
        """
        podcasts = []
        
        try:
            for file in os.listdir(self.output_dir):
                if file.endswith('.mp3'):
                    file_path = os.path.join(self.output_dir, file)
                    file_info = {
                        'filename': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created': datetime.fromtimestamp(
                            os.path.getctime(file_path)
                        ).isoformat(),
                        'modified': datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    }
                    
                    # Try to load metadata
                    metadata_file = f"{Path(file).stem}_metadata.json"
                    metadata_path = os.path.join(self.output_dir, metadata_file)
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                file_info['metadata'] = json.load(f)
                        except:
                            file_info['metadata'] = None
                    else:
                        file_info['metadata'] = None
                    
                    podcasts.append(file_info)
            
            # Sort by creation time (newest first)
            podcasts.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing podcasts: {e}")
        
        return podcasts
    
    def get_podcast_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific podcast.
        
        Args:
            filename (str): Name of the podcast file
            
        Returns:
            Optional[Dict[str, Any]]: Podcast information or None if not found
        """
        try:
            file_path = os.path.join(self.output_dir, filename)
            
            if not os.path.exists(file_path):
                return None
            
            info = {
                'filename': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
            
            # Load metadata
            metadata_file = f"{Path(filename).stem}_metadata.json"
            metadata_path = os.path.join(self.output_dir, metadata_file)
            
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        info['metadata'] = json.load(f)
                except:
                    info['metadata'] = None
            else:
                info['metadata'] = None
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting podcast info: {e}")
            return None
    
    def delete_podcast(self, filename: str) -> bool:
        """
        Delete a podcast and its metadata.
        
        Args:
            filename (str): Name of the podcast file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            file_path = os.path.join(self.output_dir, filename)
            
            if not os.path.exists(file_path):
                self.logger.warning(f"Podcast file not found: {filename}")
                return False
            
            # Delete audio file
            os.remove(file_path)
            
            # Delete metadata file
            metadata_file = f"{Path(filename).stem}_metadata.json"
            metadata_path = os.path.join(self.output_dir, metadata_file)
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            self.logger.info(f"✅ Podcast deleted: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting podcast: {e}")
            return False
    
    def cleanup_old_podcasts(self, days: int = 30) -> int:
        """
        Clean up podcasts older than specified days.
        
        Args:
            days (int): Number of days to keep podcasts
            
        Returns:
            int: Number of podcasts deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        try:
            for file in os.listdir(self.output_dir):
                if file.endswith('.mp3'):
                    file_path = os.path.join(self.output_dir, file)
                    
                    if os.path.getctime(file_path) < cutoff_time:
                        if self.delete_podcast(file):
                            deleted_count += 1
            
            self.logger.info(f"✅ Cleaned up {deleted_count} old podcasts")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        return deleted_count


# Example usage and testing
def test_podcast_manager():
    """Test function for podcast manager."""
    manager = PodcastManager()
    
    # Test filename generation
    filename = manager.generate_filename("Test Podcast")
    print(f"Generated filename: {filename}")
    
    # Test listing podcasts
    podcasts = manager.list_podcasts()
    print(f"Found {len(podcasts)} podcasts")
    
    for podcast in podcasts:
        print(f"- {podcast['filename']} ({podcast['size']} bytes)")


if __name__ == "__main__":
    test_podcast_manager()
