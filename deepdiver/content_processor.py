"""
Content Processor Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module handles content preparation, formatting, and validation
for documents before they are uploaded to NotebookLM.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import yaml


class ContentProcessor:
    """
    Handles content preparation and processing for NotebookLM.
    
    This class manages document validation, formatting, and preparation
    before upload to NotebookLM for podcast generation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the content processor with configuration."""
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # Content settings
        self.supported_formats = self.config.get('CONTENT_SETTINGS', {}).get(
            'supported_formats', ['pdf', 'docx', 'txt', 'md', 'html']
        )
        self.max_file_size = self.config.get('CONTENT_SETTINGS', {}).get(
            'max_file_size', '50MB'
        )
        self.temp_dir = self.config.get('CONTENT_SETTINGS', {}).get(
            'temp_dir', './temp'
        )
        
        self.logger.info("♠️🌿🎸🧵 ContentProcessor initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('ContentProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a file for NotebookLM upload.
        
        Args:
            file_path (str): Path to the file to validate
            
        Returns:
            Dict[str, Any]: Validation results with success status and details
        """
        result = {
            'success': False,
            'file_path': file_path,
            'file_size': 0,
            'file_format': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['errors'].append(f"File not found: {file_path}")
                return result
            
            # Get file info
            file_path_obj = Path(file_path)
            result['file_size'] = file_path_obj.stat().st_size
            result['file_format'] = file_path_obj.suffix.lower().lstrip('.')
            
            # Check file format
            if result['file_format'] not in self.supported_formats:
                result['errors'].append(
                    f"Unsupported file format: {result['file_format']}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
                return result
            
            # Check file size
            max_size_bytes = self._parse_file_size(self.max_file_size)
            if result['file_size'] > max_size_bytes:
                result['errors'].append(
                    f"File too large: {self._format_file_size(result['file_size'])}. "
                    f"Maximum allowed: {self.max_file_size}"
                )
                return result
            
            # Check if file is readable
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to test readability
            except Exception as e:
                result['errors'].append(f"File not readable: {e}")
                return result
            
            result['success'] = True
            self.logger.info(f"✅ File validation successful: {file_path}")
            
        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
            self.logger.error(f"❌ File validation failed: {e}")
        
        return result
    
    def _parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes."""
        size_str = size_str.upper().strip()
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    number = float(size_str[:-len(suffix)])
                    return int(number * multiplier)
                except ValueError:
                    break
        
        # Default to 50MB if parsing fails
        return 50 * 1024 * 1024
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def prepare_content(self, file_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare content for NotebookLM upload.
        
        Args:
            file_path (str): Path to the source file
            output_dir (str, optional): Directory for processed files
            
        Returns:
            Dict[str, Any]: Preparation results with processed file path
        """
        result = {
            'success': False,
            'original_path': file_path,
            'processed_path': None,
            'preparation_steps': [],
            'errors': []
        }
        
        try:
            # Validate file first
            validation = self.validate_file(file_path)
            if not validation['success']:
                result['errors'] = validation['errors']
                return result
            
            result['preparation_steps'].append("File validation completed")
            
            # Determine output directory
            if output_dir is None:
                output_dir = self.temp_dir
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Process based on file type
            file_format = validation['file_format']
            
            if file_format in ['txt', 'md']:
                # Text files can be used directly
                result['processed_path'] = file_path
                result['preparation_steps'].append("Text file ready for upload")
            
            elif file_format == 'html':
                # HTML files might need cleaning
                processed_path = self._process_html_file(file_path, output_dir)
                result['processed_path'] = processed_path
                result['preparation_steps'].append("HTML file processed")
            
            elif file_format in ['pdf', 'docx']:
                # Binary files can be used directly
                result['processed_path'] = file_path
                result['preparation_steps'].append("Binary file ready for upload")
            
            else:
                result['errors'].append(f"Unsupported file format for processing: {file_format}")
                return result
            
            result['success'] = True
            self.logger.info(f"✅ Content preparation successful: {file_path}")
            
        except Exception as e:
            result['errors'].append(f"Preparation error: {e}")
            self.logger.error(f"❌ Content preparation failed: {e}")
        
        return result
    
    def _process_html_file(self, file_path: str, output_dir: str) -> str:
        """Process HTML file for better NotebookLM compatibility."""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Save processed text
            output_path = os.path.join(output_dir, f"processed_{Path(file_path).stem}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return output_path
            
        except ImportError:
            self.logger.warning("BeautifulSoup not available, using original HTML file")
            return file_path
        except Exception as e:
            self.logger.warning(f"HTML processing failed, using original file: {e}")
            return file_path
    
    def get_content_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a content file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Dict[str, Any]: File information
        """
        info = {
            'file_path': file_path,
            'exists': False,
            'file_size': 0,
            'file_format': None,
            'readable': False,
            'validation': None
        }
        
        try:
            if os.path.exists(file_path):
                info['exists'] = True
                
                file_path_obj = Path(file_path)
                info['file_size'] = file_path_obj.stat().st_size
                info['file_format'] = file_path_obj.suffix.lower().lstrip('.')
                
                # Test readability
                try:
                    with open(file_path, 'rb') as f:
                        f.read(1024)
                    info['readable'] = True
                except:
                    info['readable'] = False
                
                # Run validation
                info['validation'] = self.validate_file(file_path)
            
        except Exception as e:
            self.logger.error(f"Error getting content info: {e}")
        
        return info
    
    def cleanup_temp_files(self, temp_dir: Optional[str] = None):
        """Clean up temporary files."""
        if temp_dir is None:
            temp_dir = self.temp_dir
        
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")


# Example usage and testing
def test_content_processor():
    """Test function for content processor."""
    processor = ContentProcessor()
    
    # Test with a sample file (if it exists)
    test_file = "README.md"
    if os.path.exists(test_file):
        print(f"Testing with file: {test_file}")
        
        # Test validation
        validation = processor.validate_file(test_file)
        print(f"Validation result: {validation}")
        
        # Test content info
        info = processor.get_content_info(test_file)
        print(f"Content info: {info}")
        
        # Test preparation
        preparation = processor.prepare_content(test_file)
        print(f"Preparation result: {preparation}")
    else:
        print("No test file available")


if __name__ == "__main__":
    test_content_processor()
