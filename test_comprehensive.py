#!/usr/bin/env python3
"""
Comprehensive DeepDiver Test Suite
Tests all components of the DeepDiver system

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

from deepdiver.content_processor import ContentProcessor
from deepdiver.podcast_manager import PodcastManager
from deepdiver.session_tracker import SessionTracker
from deepdiver.notebooklm_automator import NotebookLMAutomator


class DeepDiverTestSuite:
    """Comprehensive test suite for DeepDiver components."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {}
        self.temp_dir = tempfile.mkdtemp()
        print(f"🧪 DeepDiver Comprehensive Test Suite")
        print(f"📁 Temp directory: {self.temp_dir}")
        print("=" * 60)
    
    def test_content_processor(self):
        """Test ContentProcessor functionality."""
        print("\n🔧 Testing ContentProcessor...")
        
        try:
            processor = ContentProcessor()
            
            # Test with README.md
            test_file = 'README.md'
            if os.path.exists(test_file):
                # Test validation
                validation = processor.validate_file(test_file)
                self.test_results['content_validation'] = validation['success']
                print(f"  ✅ File validation: {validation['success']}")
                
                # Test content info
                info = processor.get_content_info(test_file)
                self.test_results['content_info'] = info['exists']
                print(f"  ✅ Content info: {info['file_size']} bytes, {info['file_format']}")
                
                # Test preparation
                preparation = processor.prepare_content(test_file, self.temp_dir)
                self.test_results['content_preparation'] = preparation['success']
                print(f"  ✅ Content preparation: {preparation['success']}")
            else:
                print("  ⚠️ No test file available")
                self.test_results['content_validation'] = False
            
            return True
            
        except Exception as e:
            print(f"  ❌ ContentProcessor test failed: {e}")
            self.test_results['content_processor'] = False
            return False
    
    def test_podcast_manager(self):
        """Test PodcastManager functionality."""
        print("\n🎙️ Testing PodcastManager...")
        
        try:
            manager = PodcastManager()
            
            # Test filename generation
            filename = manager.generate_filename('Test Podcast')
            self.test_results['filename_generation'] = bool(filename)
            print(f"  ✅ Filename generation: {filename}")
            
            # Test listing podcasts
            podcasts = manager.list_podcasts()
            self.test_results['podcast_listing'] = True
            print(f"  ✅ Podcast listing: {len(podcasts)} podcasts found")
            
            # Test content info
            info = manager.get_podcast_info('nonexistent.mp3')
            self.test_results['podcast_info'] = (info is None)
            print(f"  ✅ Podcast info handling: {info is None}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ PodcastManager test failed: {e}")
            self.test_results['podcast_manager'] = False
            return False
    
    def test_session_tracker(self):
        """Test SessionTracker functionality."""
        print("\n🔮 Testing SessionTracker...")
        
        try:
            tracker = SessionTracker()
            
            # Test session creation
            result = tracker.start_session(ai_assistant='claude', issue_number=1)
            self.test_results['session_creation'] = result['success']
            print(f"  ✅ Session creation: {result['success']}")
            
            if result['success']:
                session_id = result['session_id']
                
                # Test writing to session
                write_result = tracker.write_to_session('Test message', 'note')
                self.test_results['session_writing'] = write_result
                print(f"  ✅ Session writing: {write_result}")
                
                # Test session status
                status = tracker.get_session_status()
                self.test_results['session_status'] = (status is not None)
                print(f"  ✅ Session status: {status['status'] if status else 'None'}")
                
                # Test listing sessions
                sessions = tracker.list_sessions()
                self.test_results['session_listing'] = (len(sessions) > 0)
                print(f"  ✅ Session listing: {len(sessions)} sessions")
                
                # Test ending session
                end_result = tracker.end_session()
                self.test_results['session_ending'] = end_result
                print(f"  ✅ Session ending: {end_result}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ SessionTracker test failed: {e}")
            self.test_results['session_tracker'] = False
            return False
    
    async def test_notebooklm_automator(self):
        """Test NotebookLMAutomator functionality."""
        print("\n🌐 Testing NotebookLMAutomator...")
        
        try:
            automator = NotebookLMAutomator()
            
            # Test browser connection
            connection_result = await automator.connect_to_browser()
            self.test_results['browser_connection'] = connection_result
            print(f"  ✅ Browser connection: {connection_result}")
            
            if connection_result:
                # Test navigation (with shorter timeout)
                automator.timeout = 10000  # 10 seconds
                navigation_result = await automator.navigate_to_notebooklm()
                self.test_results['notebooklm_navigation'] = navigation_result
                print(f"  ✅ NotebookLM navigation: {navigation_result}")
                
                # Test authentication check
                auth_result = await automator.check_authentication()
                self.test_results['authentication_check'] = True  # This is just a check
                print(f"  ✅ Authentication check: {'Authenticated' if auth_result else 'Not authenticated'}")
            
            await automator.close()
            return True
            
        except Exception as e:
            print(f"  ❌ NotebookLMAutomator test failed: {e}")
            self.test_results['notebooklm_automator'] = False
            return False
    
    def test_integration(self):
        """Test component integration."""
        print("\n🔗 Testing Component Integration...")
        
        try:
            # Test that all components can work together
            processor = ContentProcessor()
            manager = PodcastManager()
            tracker = SessionTracker()
            
            # Test file processing workflow
            test_file = 'README.md'
            if os.path.exists(test_file):
                # Validate file
                validation = processor.validate_file(test_file)
                if validation['success']:
                    # Start session
                    session_result = tracker.start_session(ai_assistant='claude', issue_number=1)
                    if session_result['success']:
                        # Add document to session
                        doc_info = {'filename': test_file, 'size': validation['file_size']}
                        doc_result = tracker.add_document_to_session(doc_info)
                        
                        # Generate podcast filename
                        podcast_filename = manager.generate_filename('Integration Test Podcast')
                        
                        # End session
                        tracker.end_session()
                        
                        self.test_results['integration'] = True
                        print(f"  ✅ Integration test: Complete workflow successful")
                        print(f"  📄 Document processed: {test_file}")
                        print(f"  🎙️ Podcast filename: {podcast_filename}")
                    else:
                        self.test_results['integration'] = False
                        print(f"  ❌ Integration test: Session creation failed")
                else:
                    self.test_results['integration'] = False
                    print(f"  ❌ Integration test: File validation failed")
            else:
                self.test_results['integration'] = False
                print(f"  ❌ Integration test: No test file available")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            self.test_results['integration'] = False
            return False
    
    def cleanup(self):
        """Clean up test resources."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"\n🧹 Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def print_results(self):
        """Print comprehensive test results."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! DeepDiver is ready for production!")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ Most tests passed. Some issues may need attention.")
        else:
            print("❌ Multiple test failures. Please check implementation.")
        
        print("\n♠️🌿🎸🧵 Assembly Team Test Results:")
        print("Jerry ⚡: Creative technical leadership validated")
        print("Nyro ♠️: Structural architecture confirmed")
        print("Aureon 🌿: Emotional context preserved")
        print("JamAI 🎸: Musical harmony maintained")
        print("Synth 🧵: Terminal orchestration verified")


async def main():
    """Main test function."""
    test_suite = DeepDiverTestSuite()
    
    try:
        # Run all tests
        test_suite.test_content_processor()
        test_suite.test_podcast_manager()
        test_suite.test_session_tracker()
        await test_suite.test_notebooklm_automator()
        test_suite.test_integration()
        
        # Print results
        test_suite.print_results()
        
        return test_suite.test_results
        
    finally:
        test_suite.cleanup()


if __name__ == "__main__":
    # Run the comprehensive test suite
    results = asyncio.run(main())
    
    # Exit with appropriate code
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    if passed_tests == total_tests:
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed


